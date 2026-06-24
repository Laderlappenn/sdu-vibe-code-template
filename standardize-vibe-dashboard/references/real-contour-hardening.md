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

## 4. Maps Must Be Recognizable Offline

Closed contours have no internet tiles. A bare rail/road network on a blank canvas
reads as "the map is missing."

- Bundle an **offline GeoJSON basemap** (country boundary, and region/oblast borders)
  into the image under the frontend's static assets; the app fetches it from its own
  origin, never from the internet.
- Draw a filled country/region layer **beneath** the data layers so the geography is
  recognizable. Reduce coordinate precision (≈4 decimals) to keep the file small.
- Keep all data overlays (flows, loads, risks) on top, theme-aware for light/dark.

## 5. Optional AI Features (Closed-Loop Gateway)

If the dashboard adds an AI brief/assistant against a corporate OpenAI/Anthropic-
compatible gateway:

- **Stream the response.** Return `StreamingResponse` (`text/plain`) and parse the
  gateway SSE (`delta.content` for OpenAI, `content_block_delta` for Anthropic); the
  frontend appends chunks via a `fetch` reader. Send `X-Accel-Buffering: no` so an
  ingress/proxy does not buffer the stream.
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
- [ ] Memory profile on real (or real-sized) data shows no whole-table payloads.
