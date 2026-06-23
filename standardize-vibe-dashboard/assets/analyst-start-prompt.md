# Standard Analyst Prompt

Use this prompt when starting a dashboard from CSV files.

```text
Use $standardize-vibe-dashboard.

I am attaching CSV files and want to vibe-code a dashboard from them.

Business idea:
<describe what the dashboard should help users see or decide>

Audience:
<who will use it>

Important metrics or questions:
<list KPIs, rankings, comparisons, maps, filters, dates, statuses, or segments>

Rules:
- Start by creating the standard project structure for our integration contour.
- Use explicit ClickHouse `schema.table` names; `data/` may contain several table exports, named like `gold.my_table.csv`.
- Build runtime data access with SQLAlchemy 2 declarative models and ORM statements. Do not execute raw SQL strings or read `.sql` files from the backend.
- Put future-analyst SELECT references in `sql/`; one query per `.sql` file; name files as `<schema>.<table>.<query_name>.sql`; no DDL, grants, dbt, contracts, Helm, or docs folders for the first version.
- Build the service as React + FastAPI + SQLAlchemy + ClickHouse.
- Serve the React build from the same FastAPI app; do not create a separate frontend nginx/container.
- Follow the SDU Data Portal design system: Inter, blue primary accent, token-based light/dark themes, pill controls, and consistent cards.
- Do not make the final result a static HTML/CSV-only dashboard.
- Keep only ClickHouse connection credentials in env vars. Do not use `CLICKHOUSE_DATABASE`, `DASHBOARD_TABLE`, or one env var per source table.
- Add Docker Compose for local development.
- Local Docker Compose should seed all attached CSV table exports needed by the dashboard.
- Do not mount or copy `sql/` into the app container. Exclude `sql/` and `*.sql` from the Docker build context.
- At the end, build explicitly for `linux/amd64` unless another Linux server architecture is specified; verify the image platform and that it contains no `.sql` files.
- Always create an `image/` folder with the platform-labelled Linux app image tar and `image/.env.example`.
- If requirements are unclear, ask at most three blocking questions and keep the rest as explicit assumptions.
```
