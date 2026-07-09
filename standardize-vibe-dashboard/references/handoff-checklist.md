# Handoff Checklist

Use this before finalizing a lightweight standardized dashboard.

## For Vibe Coders

- Static HTML/JS data loading has been replaced by FastAPI calls.
- React is built into and served by the FastAPI app; there is no separate frontend nginx/container.
- React app has loading, empty, and error states.
- React UI follows `references/sdu-data-portal-design.md`: Inter, tokenized colors, blue accent, pill primary controls, themed cards, and light/dark coverage.
- UI labels and charts match the source dashboard domain.
- Local fixtures are small and anonymized.
- No credentials are committed.
- Backend data access uses SQLAlchemy declarative models and expression statements; no raw SQL strings or `.sql` file loading remains.

## For Data/SQL Review

- `data/` fixtures, if present, are table exports named `schema.table.csv`; multiple exports are allowed.
- SQL files under `sql/` are future-analyst SELECT references and map to visible KPIs/charts/tables/filters.
- SQL files are named `<schema>.<table>.<query_name>.sql`.
- Each `.sql` file contains exactly one query.
- Every query uses explicit `schema.table`, not `CLICKHOUSE_DATABASE`.
- Backend repositories independently implement the runtime behavior through ORM models/statements.
- No app code, app test, Docker stage, volume, or startup command reads or executes `sql/`.
- Any local bootstrap DDL lives only in dev seed logic, not in `sql/` or the production app startup path.

## For Integration Review

- Switching from local ClickHouse to internal ClickHouse does not require frontend changes.
- The service starts with only ClickHouse host/user/password/secure/verify env vars; table names come from ORM models.
- The internal contour exposes the same fully-qualified `schema.table` contract, using views when physical table names differ.
- Model column names/casing and types were verified against `SHOW CREATE TABLE` (not CSV); date/numeric columns stored as `String` are handled with `parseDateTimeBestEffortOrNull(toString(col))` / `toFloat64OrZero`.
- No endpoint returns row-level data without `GROUP BY` or `LIMIT`; histograms/heatmaps are computed in SQL and a memory profile on real-sized data shows no whole-table payloads.
- High-cardinality filter lists are capped (top-N); structure charts survive many long category names; maps render offline from a bundled GeoJSON basemap.
- `/health` checks the API and ClickHouse.
- `docker image inspect` reports the requested Linux target, `linux/amd64` by default.
- The app image contains neither `/app/sql` nor any `.sql` files.
- `image/` contains the platform-labelled Linux app tar and `.env.example`; ClickHouse image tar is included only when requested.
- Final answer names any missing upstream work, such as who will own the internal `schema.table` refresh.
