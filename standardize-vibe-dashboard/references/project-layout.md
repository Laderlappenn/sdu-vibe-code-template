# Project Layout Standard

Use this lightweight layout for early dashboard projects that originate from CSV/static prototypes.

```text
.
├── data/
│   ├── <schema>.<table>.csv
│   └── <schema>.<another_table>.csv
├── sql/
│   ├── <schema>.<table>.kpi_summary.sql
│   ├── <schema>.<table>.daily_dynamics.sql
│   ├── <schema>.<table>.breakdown_by_status.sql
│   ├── <schema>.<table>.recent_rows.sql
│   └── <schema>.<table>.filter_status_options.sql
├── backend/
│   ├── app/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   └── package.json
├── image/
│   ├── <app-slug>-app_<YYYY-MM-DD>.tar
│   └── .env.example
├── docker-compose.yml
└── README.md
```

## Ownership

- `data/`: local CSV fixtures/exports only. It may contain several source table exports; prefer names like `gold.citizen_appeals.csv` and `dict.regions.csv`.
- `sql/`: analyst-readable SELECT queries that power dashboard KPIs, charts, filters, and tables.
- `sql/` files contain exactly one query each.
- `backend/`: FastAPI service that reads ClickHouse, exposes dashboard APIs, and serves the built React files.
- `frontend/`: React source built into the FastAPI image. It never contains DB credentials and never queries ClickHouse directly.
- `image/`: required final artifact folder with the exported app image tar and `.env.example`.
- `docker-compose.yml`: local runtime for one app service and optional local ClickHouse.

## Naming

- Backend route prefix: `/api`.
- CSV exports are named by source table: `<schema>.<table>.csv`.
- SQL files are named by source table first, then query purpose: `<schema>.<table>.<query_name>.sql`.
- For multi-table joins, use the primary table/view for the filename prefix and keep all joined tables fully qualified in the query.
- Split every chart, breakdown, filter, and table query into its own `.sql` file.
- Do not use `CLICKHOUSE_DATABASE`; write `schema.table` explicitly.
- Do not add a frontend nginx Dockerfile/container; the backend Dockerfile builds React and FastAPI serves the result.

## Minimum Deliverables

- CSV fixtures under `data/` when sample data is needed, one source table export per file.
- SELECT-only dashboard SQL under `sql/`, with one query per file and filenames shaped as `<schema>.<table>.<query_name>.sql`.
- FastAPI `/health` and at least one dashboard data endpoint.
- React page that loads from FastAPI through `VITE_API_BASE_URL`.
- One Dockerfile for the app image, a stable app image tag, and a local compose file.
- README with local run commands and expected source tables as `schema.table`.
- `image/<app-slug>-app_<YYYY-MM-DD>.tar` and `image/.env.example` created at the end of app creation.
