# Single FastAPI App Pattern

## Backend

Use FastAPI with `clickhouse-connect`. The same FastAPI app serves API routes and built React static files.

Required env vars:

```text
CLICKHOUSE_HOST
CLICKHOUSE_PORT
CLICKHOUSE_USER
CLICKHOUSE_PASSWORD
CLICKHOUSE_SECURE
CLICKHOUSE_VERIFY
CORS_ORIGINS
```

Table names are not env vars in the standard shape. The backend queries use fully-qualified `schema.table` names from the SQL/data contract.

Required endpoints:

- `GET /health`: return app status and ClickHouse connectivity.
- `GET /api/meta`: return source table metadata.
- `GET /api/dashboard/summary`: return KPI totals and chart-ready aggregates.
- `GET /api/dashboard/<entity>` or domain-specific routes as needed.

Backend rules:

- Use parameterized ClickHouse queries.
- Use explicit `schema.table` in every query.
- Mirror important dashboard queries in `sql/<schema>.<table>.<query_name>.sql`, with exactly one query per file.
- Do not require `DASHBOARD_TABLE` or one env var per CSV/table.
- Serve the Vite `dist/` output from FastAPI, including `/assets/*` and SPA fallback to `index.html`.
- Return frontend-ready JSON with stable field names.
- Do not expose ClickHouse errors or credentials in responses.

## Frontend

Use React + Vite.

Required env var:

```text
VITE_API_BASE_URL
```

Frontend rules:

- Fetch through FastAPI only.
- Build React into the FastAPI image; do not run a separate nginx/frontend container.
- Keep charts, map interaction, filters, and formatting in React.
- Do not bundle full CSV/JSON exports in production.
- Use loading, empty, and error states.
- Keep all dashboard labels domain-specific; avoid generic placeholder text in final UI.

## Docker Compose

Local compose should support:

- one app service that serves `/` and `/api`
- optional local ClickHouse for dev/test

Do not mount `sql/` as ClickHouse init scripts. `sql/` is for dashboard SELECT queries only.

## Contour Portability

A dashboard is portable when moving from local/prototype to internal contour requires only:

- changing ClickHouse host/port/user/password env or secret
- keeping the same fully-qualified `schema.table` contract available in ClickHouse, usually as real tables or compatibility views
- redeploying the same app image

If code or env changes are required to rename tables for a different contour, expose views with the contract names instead.
