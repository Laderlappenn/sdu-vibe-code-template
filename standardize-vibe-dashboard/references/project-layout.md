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
│   │   ├── database.py
│   │   ├── models.py
│   │   └── repositories.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   └── package.json
├── image/
│   ├── <app-slug>-app_linux-amd64_<YYYY-MM-DD>.tar
│   └── .env.example
├── .dockerignore
├── docker-compose.yml
└── README.md
```

## Ownership

- `data/`: local CSV fixtures/exports only. It may contain several source table exports; prefer names like `gold.citizen_appeals.csv` and `dict.regions.csv`.
- `sql/`: analyst-readable SELECT references for future analysis. The app does not load or execute them; each file contains exactly one query.
- `backend/`: FastAPI service that reads ClickHouse through SQLAlchemy declarative models/repositories, exposes dashboard APIs, and serves the built React files.
- `frontend/`: React source built into the FastAPI image. It never contains DB credentials and never queries ClickHouse directly.
- `image/`: required final artifact folder with the platform-labelled Linux app image tar and `.env.example`.
- `.dockerignore`: excludes `sql/`, `*.sql`, fixtures, local artifacts, and dependency caches from the app build context.
- `docker-compose.yml`: local runtime for one app service and optional local ClickHouse.

## Naming

- Backend route prefix: `/api`.
- CSV exports are named by source table: `<schema>.<table>.csv`.
- SQL files are named by source table first, then query purpose: `<schema>.<table>.<query_name>.sql`.
- For multi-table joins, use the primary table/view for the filename prefix and keep all joined tables fully qualified in the query.
- Split every chart, breakdown, filter, and table reference into its own `.sql` file.
- Map each source as an explicit ORM `schema.table`; do not use `CLICKHOUSE_DATABASE`.
- Keep all runtime query logic in ORM repositories. Do not read or execute `.sql` files from the app.
- Do not add a frontend nginx Dockerfile/container; the backend Dockerfile builds React and FastAPI serves the result.

## Minimum Deliverables

- CSV fixtures under `data/` when sample data is needed, one source table export per file.
- SQLAlchemy declarative models plus repository statements for every runtime dashboard query; no raw SQL strings.
- SELECT-only analyst references under `sql/`, with one query per file and filenames shaped as `<schema>.<table>.<query_name>.sql`.
- FastAPI `/health` and at least one dashboard data endpoint.
- React page that loads from FastAPI through `VITE_API_BASE_URL`.
- One Dockerfile for the app image, a stable app image tag, `APP_PLATFORM=linux/amd64` by default, and a local compose file.
- README with local run commands and expected source tables as `schema.table`.
- `image/<app-slug>-app_linux-amd64_<YYYY-MM-DD>.tar` and `image/.env.example` created at the end, after platform and no-SQL-content checks.
