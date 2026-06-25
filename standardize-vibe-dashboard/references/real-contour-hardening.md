# Real-Contour Hardening

Use this when moving a CSV-prototyped dashboard onto a **real internal ClickHouse
contour**. Local CSV fixtures lie about two things — exact schema and scale — and
the dashboard breaks on deploy if you trust them. These rules come from production
incidents; apply them before handing off.

## 1. The CSV Is A Hint, The Contour Is The Truth

A local seed builds tables from CSV headers, so the prototype "works" even when the
real contour table is shaped differently. ClickHouse is **case-sensitive** and the
ingestion pipeline often keeps source-system casing and loose types.

- **Verify the real schema, do not infer it from CSV.** Before wiring models, get
  `SHOW CREATE TABLE <schema>.<table>` for every source. If you only have CSV,
  treat header casing/types as a guess to be confirmed.
- **Map ORM attribute → real column name explicitly when they differ.** Keep the
  Python attribute lowercase/pythonic, bind the real (often capitalized) column name:

  ```python
  # contour column is "Data_prinjatija_gruza_k_perevozke", "Massa", "Kod_gruza_GNG"
  data_prinjatija: Mapped[str] = mapped_column("Data_prinjatija_gruza_k_perevozke", String)
  massa: Mapped[float] = mapped_column("Massa", Float64)
  ```

  A lowercase attribute silently querying a capitalized column raises ClickHouse
  `UNKNOWN_IDENTIFIER (code 47)`.

- **Datetime-looking columns are frequently stored as `String`.** Non-standard
  source formats (`12.06.2026 00:00`, `2026-05-02T23:00+05:00`, `...:00.000` millis)
  get ingested as text. Calling `toStartOfWeek`/`toStartOfMonth`/`dateDiff` on a
  `String` raises `ILLEGAL_TYPE_OF_ARGUMENT (code 43)`. Declare such columns as
  `String` and wrap every date operation with a type-agnostic helper:

  ```python
  def _dt(col):
      # works whether the column is String (raw) or already DateTime:
      # toString(DateTime) -> canonical text -> parseDateTimeBestEffort parses both
      return func.parseDateTimeBestEffortOrNull(func.toString(col))
  ```

  Use `_dt(col)` inside `toStartOf*`, `dateDiff`, `min/max`, and comparisons; add
  `WHERE _dt(col) IS NOT NULL` so unparseable rows degrade to empty, not 500.

- **Numeric-looking columns can also be `String`.** If `sum(col)` raises code 43,
  wrap with `func.toFloat64OrZero(func.toString(col))`.

- **Same names, different contour.** Keep the model's `schema.table` as the contract.
  If the real names differ, ask the DBA for a compatibility view rather than editing
  the image (see the ORM contract reference).

## 2. Aggregate In ClickHouse — Never Pull Raw Rows

Contour tables routinely hold **millions of rows** (a 6M-row table is normal). Any
endpoint that selects row-level data and reduces it in Python streams the whole
table over the wire and explodes both backend memory and the browser heap (DOM-node
and Object/Array bloat shows up immediately in a memory profile).

- **Do all reduction in SQL.** Histograms, heatmaps, time buckets, and structure
  charts must be `GROUP BY` aggregates that return tens/hundreds of rows, not the
  raw set. Examples:
  - heatmap by weekday×hour → `group_by(toDayOfWeek(dt), toHour(dt))` → ≤168 rows,
    not one row per ticket.
  - value histogram → compute the bucket index as an expression and `GROUP BY` it:

    ```python
    bucket = literal(0)
    for e in edges:
        bucket = bucket + case((expr >= e, 1), else_=0)  # 0..len = bucket index
    select(bucket.label("b"), func.count()).where(expr.isnot(None)).group_by(bucket)
    ```

- **If you genuinely need raw rows (e.g. a scatter), LIMIT or sample.** Never return
  hundreds of thousands of points to a chart. Use a fixed sample:
  `select(...).order_by(func.rand()).limit(2000)`.

- **Cap categorical option lists.** Filter dropdowns built from a high-cardinality
  column (thousands of cargo/product names) render thousands of `<option>` nodes and
  bloat the DOM. Return only the **top-N most frequent** values from `/api/filters`:

  ```python
  select(Model.name.label("name")).group_by(Model.name)
      .order_by(func.count().desc()).limit(100)
  ```

  For full lookup, prefer a search/autocomplete input over a giant `<select>`.

- **Frontend never bundles or fetches whole tables.** It consumes aggregated DTOs
  only. Confirm with a quick memory profile on real data before handoff.

## 3. Charts Must Survive Real Cardinality And Long Labels

Prototype data has a handful of short category names; the contour has hundreds of
long ones, which overflow legends and break layout.

- **Structure/pie charts:** render all slices for proportion, but do not print every
  name. Pair the pie with a compact **top-10 list** (rank, value, % of total) and
  show the full name + value + percent in the tooltip. Truncate long names with
  `text-overflow: ellipsis`; cap tooltip width and allow word-break.
- **Distinct colors for many slices:** cycle a brand palette for the first few, then
  generate golden-angle HSL hues so hundreds of categories stay distinguishable.
- **Bar charts with name axes:** fix the label column width and truncate; never let a
  label dictate layout width.

## 4. Maps (deck.gl / GeoJSON): Recognizable Offline AND Memory-Safe

Closed contours have no internet tiles, and GeoJSON is the single **heaviest** thing a
dashboard puts in the browser. Handle both.

### 4.1 Recognizable without tiles
- Bundle an **offline GeoJSON basemap** (country boundary + region/oblast borders) into
  the image's static assets; the app fetches it from its own origin, never the internet.
- Draw a filled country/region layer **beneath** the data layers so it reads as a map
  (a bare network on blank canvas looks broken). Theme-aware light/dark.

### 4.2 GeoJSON is the #1 memory consumer — size the geometry down
A ~4 MB GeoJSON can become **~200 MB of browser heap**. The chain:
- `JSON.parse` expands text ~15–20×: every `[lon,lat]` becomes a JS Array object
  (header + backing store + boxed numbers) — ~15 bytes of text → ~100 bytes in memory.
- deck.gl **tessellates** geometry into WebGL attribute buffers (the biggest part): a
  line becomes a triangle ribbon, each point exploding into several vertices × several
  Float32 buffers (PathLayer even duplicates start/end positions). These live as CPU
  `ArrayBuffer`s **and** in GPU VRAM.
- It is held in several forms at once (parsed objects + CPU buffers + GPU).

**Point count drives all of it.** A 166k-point rail network is absurd at country zoom.
- **Simplify geometry** (Douglas–Peucker / decimation) to ~10–25k points and round
  coordinates to ~4 decimals (~11 m) — visually identical, cuts parsed arrays,
  tessellation, GPU memory **and** transfer proportionally (often 5–8×).
- Delete unused geo files from `public/` (they bloat the image even if never fetched).

### 4.3 Never re-mount the map — it accumulates copies
Re-creating the deck.gl component re-fetches + re-parses the GeoJSON and rebuilds GPU
buffers; if old instances linger, the heap holds **several copies** and memory spikes
(e.g. 250 MB instead of 90 MB). Triggers: a `key={section-…}` on a parent that forces
remount, unmounting the map on tab switch, remounting on theme/lang toggles.
- **Keep the map mounted persistently**; hide with CSS (`display`) instead of
  unmounting. One deck.gl instance for the app's life.
- **Cache the parsed GeoJSON at module level** — fetched + parsed exactly once, shared
  by reference across renders.
- **Memoize** the map and pass **stable prop references** (don't build new `?? []`
  arrays inline each render) so unrelated state changes don't rebuild layers.
- Verify with heap snapshots: navigate / reload / toggle theme repeatedly — the
  `JSArrayBufferData` and `Array` counts must stay flat, not grow.

### 4.4 Serve geo compressed and cached
- Enable **gzip** on the FastAPI app (`GZipMiddleware`) — geo and the JS bundle shrink
  ~3–4× (a 2.9 MB geojson → ~450 KB on the wire).
- Send a long **`Cache-Control`** for `/geo/*` so reloads don't re-download it.

### 4.5 Readable, not a spiderweb
- Show **one layer at a time** via a switcher (station load / cargo flow / passengers /
  regions / risks), each with a legend explaining size and colour.
- Aggregate flows to a coarser unit (**region→region**) so a few thick arcs tell the
  story instead of hundreds of crossing station→station lines; keep cross-border arcs.
- Don't hard-filter map data by a localized string (e.g. `country == "Казахстан"`): on
  the real contour the spelling differs and the layer silently goes empty. Join by code
  and degrade gracefully.

## 5. Optional AI Features (Closed-Loop Gateway)

If the dashboard adds an AI brief/assistant against a corporate OpenAI/Anthropic-
compatible gateway:

- **Prefer a single (non-streaming) response in closed contours.** Streaming
  (`StreamingResponse` + SSE) looks nice but **breaks behind many k8s ingresses/proxies**
  that buffer the body — the answer never arrives. Observed in production: switching the
  AI brief/chat to streaming made them stop responding in the closed network. Return the
  full text in one JSON response and render it; only use streaming if you control the
  proxy and have set `X-Accel-Buffering: no` end-to-end and verified it.
- **Render Markdown** in chat/brief output (a tiny dependency-free renderer is enough
  for closed networks: headings, lists, bold, code, links).
- Keep the principle: the backend computes the numbers, the model only phrases them.
  Degrade softly when the gateway key is absent.

## Quick Pre-Deploy Checklist

- [ ] Model column names/casing verified against `SHOW CREATE TABLE`, not CSV.
- [ ] Every date op wrapped in `parseDateTimeBestEffortOrNull(toString(col))`.
- [ ] No endpoint returns row-level data without `GROUP BY` or `LIMIT`.
- [ ] Filter option lists capped (top-N) or replaced with search.
- [ ] Structure charts: top-N list + ellipsis + capped tooltip; many-slice colors.
- [ ] Offline map basemap bundled; no runtime internet fetch.
- [ ] Map GeoJSON simplified (≤~25k points) and served gzipped + cached.
- [ ] Map mounted once (no `key`-driven remount); parsed GeoJSON module-cached; map memoized.
- [ ] Heap snapshot stable across tab/theme/reload navigation (no growing `ArrayBuffer`/`Array`).
- [ ] Memory profile on real (or real-sized) data shows no whole-table payloads.
