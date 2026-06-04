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

## For Data/SQL Review

- `data/` fixtures, if present, are table exports named `schema.table.csv`; multiple exports are allowed.
- SQL files under `sql/` are SELECT-only and map to visible KPIs/charts/tables/filters.
- SQL files are named `<schema>.<table>.<query_name>.sql`.
- Each `.sql` file contains exactly one query.
- Every query uses explicit `schema.table`, not `CLICKHOUSE_DATABASE`.
- Any local bootstrap DDL lives only in local compose/seed logic, not in `sql/`.

## For Integration Review

- Switching from local ClickHouse to internal ClickHouse does not require frontend changes.
- The service starts with only ClickHouse host/user/password/secure/verify env vars.
- The internal contour exposes the same fully-qualified `schema.table` contract, using views when physical table names differ.
- `/health` checks the API and ClickHouse.
- `image/` contains the exported app image tar and `.env.example`; ClickHouse image tar is included only when requested.
- Final answer names any missing upstream work, such as who will own the internal `schema.table` refresh.
