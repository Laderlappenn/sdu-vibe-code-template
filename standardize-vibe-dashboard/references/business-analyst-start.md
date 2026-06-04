# Business Analyst Starter Workflow

Use this when the analyst has only CSV files, business wishes, and a prompt such as "build me a dashboard".

## Intake

Ask at most three blocking questions. If the analyst cannot answer, proceed with assumptions and keep them visible in the README or final handoff.

Prefer these questions:

1. What is the dashboard name and primary audience?
2. What decisions should this dashboard help make?
3. Which fields in the CSV are the main dimensions, dates, geography, statuses, or measures?

Do not block on perfect requirements. Build a standard scaffold and document uncertainty lightly.

## First Output

For a new repository, create these files before or alongside UI work:

```text
data/
sql/
backend/
frontend/
docker-compose.yml
README.md
```

The README must capture:

- dashboard title
- CSV source files, including every source table export under `data/`
- expected source tables as fully-qualified `schema.table` names
- local run command
- key assumptions

## Build Order

1. Put CSV fixtures under `data/`; multiple table exports are allowed, one source table per CSV, with names like `gold.citizen_appeals.csv`.
2. Run `scripts/inspect_csv_exports.py data/` when useful to infer headers and a first-pass ClickHouse type contract.
3. Choose and document every source table as `schema.table`; do not add one env var per table.
4. Scaffold or adapt React + FastAPI + ClickHouse from `assets/project-template/`.
5. Add local ClickHouse seed/bootstrap for every CSV table needed by the demo; keep DDL outside `sql/`.
6. Create SELECT-only SQL files under `sql/` for the actual dashboard KPIs/charts/tables, one query per file, named as `<schema>.<table>.<query_name>.sql`.
7. Apply the SDU Data Portal visual system from `references/sdu-data-portal-design.md`.
8. Implement FastAPI endpoints over ClickHouse tables shaped exactly like API responses.
9. Build React into the FastAPI image and serve static files from FastAPI; do not add a separate frontend nginx container.
10. Finalize by creating `image/`, building the app image, saving it as `image/<app-slug>-app_<YYYY-MM-DD>.tar`, and writing `image/.env.example`.

## Agent Behavior

- Treat the analyst prompt as product intent, not as permission to ignore integration standards.
- If the analyst asks for "static HTML", satisfy the visual goal in React and keep production data behind FastAPI/ClickHouse.
- Convert vague wishes into documented KPIs and charts. Example: "show problem districts" becomes a ranked table plus map/filter if geography exists.
- Use CSV headers to infer possible measures/dimensions, but mark inferred semantics as assumptions.
- Keep domain vocabulary from the analyst's language in UI labels.
- Treat vague requests for a "modern", "beautiful", or "portal-like" design as requests to use the SDU Data Portal tokens, Inter typography, blue accents, pill controls, themed cards, and complete dark mode.
- Avoid hardcoding sample values into React components. Read them through API responses.

## Done Criteria

The first vibe-coded version is acceptable when:

- it runs locally with Docker Compose or documented commands
- it has a visible React dashboard
- the React UI follows the SDU Data Portal design system and has light/dark theme coverage
- API calls come from FastAPI, not direct CSV reads in the browser
- the React build is served by the same FastAPI app that serves `/api`
- ClickHouse connection is controlled by env vars
- queries use explicit `schema.table` names from the data/SQL contract
- `sql/` contains dashboard SELECT queries, no DDL, and exactly one query per file
- SQL filenames start with the source `schema.table`, then the query name
- local Docker Compose can seed every sample CSV table needed by the dashboard
- `image/` exists and contains the exported app image tar plus `image/.env.example`
