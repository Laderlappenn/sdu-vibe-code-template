# Single FastAPI App Pattern

## Backend

Use FastAPI with SQLAlchemy 2 and the `clickhouse-connect` dialect. The same FastAPI app serves API routes and built React static files.

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

Table names are not env vars in the standard shape. Declarative models use explicit schemas and table names from the data contract.

Required endpoints:

- `GET /health`: return app status and ClickHouse connectivity.
- `GET /api/meta`: return source table metadata.
- `GET /api/dashboard/summary`: return KPI totals and chart-ready aggregates.
- `GET /api/dashboard/<entity>` or domain-specific routes as needed.

Backend rules:

- Define one declarative model per ClickHouse source and use SQLAlchemy `Session` dependencies.
- Build queries with `select()`, `func`, `case`, joins, and bound filters over model columns.
- Do not use raw SQL strings, SQLAlchemy `text()`, driver `.query()`/`.command()`, or runtime reads from `sql/`.
- Keep matching analyst references in `sql/<schema>.<table>.<query_name>.sql`, one query per file, without consuming them from the backend.
- Do not require `DASHBOARD_TABLE` or one env var per CSV/table.
- Serve the Vite `dist/` output from FastAPI, including `/assets/*` and SPA fallback to `index.html`.
- Return frontend-ready JSON with stable field names.
- Do not expose ClickHouse errors or credentials in responses.
- Aggregate at million-row scale: every endpoint returns a `GROUP BY` aggregate or an explicit `LIMIT`/sample, never a whole table. Cap high-cardinality filter values (`/api/filters`) to the top-N most frequent. See `real-contour-hardening.md`.
- For an optional AI brief/assistant, stream the gateway response with `StreamingResponse` (`text/plain`, header `X-Accel-Buffering: no`) and parse SSE deltas; the backend computes numbers, the model only phrases them.

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
- Do not bundle full CSV/JSON exports in production; consume aggregated DTOs only.
- Use loading, empty, and error states.
- Keep all dashboard labels domain-specific; avoid generic placeholder text in final UI.
- Design charts/filters for real cardinality: hundreds of long category names must not break layout. Pair a structure pie with a top-N list, truncate long labels with ellipsis, bound tooltip width, and use distinguishable colors for many slices.
- In closed networks, render maps from a bundled GeoJSON basemap (country/region boundaries beneath the data layers); never depend on internet tiles. Render AI chat/brief output as Markdown. See `real-contour-hardening.md`.

## Docker Compose

Local compose should support:

- one app service that serves `/` and `/api`
- optional local ClickHouse for dev/test
- a stable app image tag, for example `image: ${APP_IMAGE:-<app-slug>-app:latest}`
- an explicit app platform, `platform: ${APP_PLATFORM:-linux/amd64}`

Do not mount or copy `sql/` into any service. It is analyst documentation only. Add both `sql/` and `*.sql` to the root `.dockerignore`.

## Final Image Export

Every completed app must be exported for the deployment server platform, `linux/amd64` by default:

```bash
python3 <skill-folder>/scripts/export_app_image.py \
  --project-dir . \
  --app-slug <app-slug>
```

The script builds through Compose with `APP_PLATFORM=linux/amd64`, verifies the inspected OS/architecture, rejects `.sql` content, saves the platform-labelled tar, and copies `.env.example`. Pass `--platform linux/arm64` only when that is the declared server target. Do not infer the target architecture from a developer Mac. If Docker is unavailable, report that blocker explicitly instead of treating the artifact as optional. Do not save the ClickHouse image unless the user explicitly requests an offline bundle.

## Contour Portability

A dashboard is portable when moving from local/prototype to internal contour requires only:

- changing ClickHouse host/port/user/password env or secret
- keeping the same fully-qualified `schema.table` contract available in ClickHouse, usually as real tables or compatibility views
- redeploying the same app image

If code or env changes are required to rename tables for a different contour, expose views with the contract names instead.
