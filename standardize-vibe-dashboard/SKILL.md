---
name: standardize-vibe-dashboard
description: Standardize CSV-first dashboard vibe coding into lightweight React + FastAPI + ClickHouse services with SQLAlchemy ORM runtime access, analyst-only SQL SELECT artifacts excluded from the app image, Docker Compose, SDU Data Portal UI rules, hot-swap database integration, and a mandatory Linux server image export under image/. Use when business analysts have only CSV files plus wishes/prompts and want to vibe-code a dashboard, when converting static HTML/CSV dashboards, replacing static JSON/HTML data with ClickHouse-backed APIs, preparing future analyst SQL from CSV-backed ClickHouse tables, or making a dashboard project easy to connect to an internal ClickHouse contour.
---

# Standardize Vibe Dashboard

Use this skill to guide dashboard work from the first business-analyst prompt, not only after a prototype exists. Start from CSV files and plain-language wishes, then produce a lightweight service that can be connected to the internal contour: one FastAPI app serves both `/api/*` and the built React static files, React reads only from the API, runtime data access goes through SQLAlchemy ORM models and statements, and ClickHouse source tables are mapped as explicit `schema.table` names. Keep `.sql` files only as future analyst documentation; the app must never load or execute them.

## Default Workflow

1. Inspect the current project before editing:
   - CSV/data files: `data/`, `dataset/`, `csv/`, `exports/`, `*.csv`, `*.json`, `*.geojson`
   - static dashboard code: `index.html`, `app.js`, `styles.css`, map/chart libraries
   - app stack files: `package.json`, `requirements.txt`, `Dockerfile`, `docker-compose.yml`
2. If the repository is empty or contains only CSV plus a prompt/idea, switch to the business-analyst starter workflow in `references/business-analyst-start.md`.
3. If CSV files exist, map every CSV export to a target ClickHouse source table:
   - `data/` may contain several table exports, one table per CSV
   - prefer CSV names shaped like `schema.table.csv`, for example `gold.citizen_appeals.csv`
   - otherwise use a clear default such as `gold.<csv_stem>`
   - document every source table as a fully-qualified `schema.table` name in the README, ORM model, and analyst SQL files
   - run `scripts/inspect_csv_exports.py data/` when helpful to infer headers, ClickHouse types, and local seed DDL
4. If only prebuilt dashboard JSON exists, document the API response shape and find the upstream CSV/ClickHouse source before wiring APIs. Do not invent table names from aggregated JSON unless the user approves that source contract.
5. Create or adapt the project to the lightweight layout in `references/project-layout.md`.
6. Move business aggregation out of static JS/JSON:
   - keep frontend formatting, filters, maps, and interactions in React
   - map every production source table/view as a SQLAlchemy declarative model with an explicit schema
   - implement repositories with `Session`, `select()`, `func`, `case`, joins, and bound filter values; do not use raw SQL strings, `text()`, driver `.query()`/`.command()`, or runtime `.sql` file reads
   - after the ORM behavior works, add equivalent SELECT-only files under `sql/` for future data analysts
   - name analyst files as `<schema>.<table>.<query_name>.sql`, for example `gold.citizen_appeals.kpi_summary.sql`, with exactly one query per file
   - do not make runtime reads from local CSV/JSON except as a dev fallback explicitly marked as such
7. Apply the SDU Data Portal visual system from `references/sdu-data-portal-design.md` to new React UI:
   - light theme by default, dark theme persisted in `localStorage`
   - Inter typography, blue brand accent, pill controls, and token-based card/input styles
8. Implement the service contract:
   - app: FastAPI, SQLAlchemy 2 with the `clickhouse-connect` dialect, `/health`, `/api/meta`, `/api/dashboard/*`, and React static serving
   - frontend: React + Vite built into the FastAPI image, `VITE_API_BASE_URL=/api`, no direct DB credentials
   - database: every ORM model maps an explicit `schema.table`; do not use `CLICKHOUSE_DATABASE`
9. Add local runtime assets:
   - `docker-compose.yml` for one app container and optional local ClickHouse
   - local seed/bootstrap creates and reloads every `data/*.csv` table needed for the demo; keep bootstrap logic in dev-only code, never in analyst `sql/` and never in the production app startup path
10. Validate with at least:
   - backend tests or `python -m compileall backend`
   - frontend `npm run build` when dependencies are available
   - `docker compose config`
   - a runtime scan confirming the backend does not load `.sql` files or execute raw SQL strings
11. Always finish app creation by exporting a Linux server image into `image/`:
   - ensure the app service has a stable image tag such as `<app-slug>-app:latest`
   - default `APP_PLATFORM` to `linux/amd64`; change it only when the deployment team specifies another Linux architecture
   - run `python3 <skill-folder>/scripts/export_app_image.py --project-dir . --app-slug <app-slug>` so the build, platform inspection, no-SQL-content check, tar naming, and env copy are enforced together
   - expect `image/<app-slug>-app_linux-amd64_<YYYY-MM-DD>.tar` plus `image/.env.example`; pass `--platform` only when another Linux target is requested
   - do not include a ClickHouse image tar unless explicitly requested

## Hard Rules

- `data/` may contain multiple CSV fixtures/exports. Prefer one source table per file and name each file as `schema.table.csv` when the target ClickHouse table is known.
- Define runtime queries through SQLAlchemy ORM models and expression statements. Do not call `text()`, `exec_driver_sql()`, `clickhouse_connect.Client.query()`/`.command()`, or read `.sql` files from backend code.
- Map every source with an explicit schema, for example `__tablename__ = "citizen_appeals"` plus `__table_args__ = {"schema": "gold"}`. Do not derive runtime table names from env vars or request strings.
- Name analyst SQL files as `<schema>.<table>.<query_name>.sql`, for example `gold.citizen_appeals.kpi_summary.sql`. For joins, prefix the file with the primary table that owns the visual and keep all joined tables fully qualified inside the query.
- Do not set or require `CLICKHOUSE_DATABASE`, `DASHBOARD_TABLE`, or per-table env vars in the standard app project.
- Keep `sql/` for analyst-readable SELECT references behind dashboard KPIs, charts, tables, and filters. These are documentation artifacts, not the runtime source of truth. Do not put DDL, grants, migrations, or bootstrap files there.
- Keep one query per analyst `.sql` file. Never copy, mount, import, parse, test-execute, or otherwise consume `sql/` in the app service or image.
- Keep credentials out of source. Use env vars and Kubernetes Secrets:
  `CLICKHOUSE_HOST`, `CLICKHOUSE_PORT`, `CLICKHOUSE_USER`, `CLICKHOUSE_PASSWORD`, `CLICKHOUSE_SECURE`, `CLICKHOUSE_VERIFY`.
- Make dashboards portable by requiring the same fully-qualified `schema.table` names in each contour. If the internal source names differ, DBAs should expose compatibility views with the dashboard contract names instead of changing the app image.
- Keep the first version lightweight: do not add `contracts/`, `dbt/`, `deploy/helm/`, or `docs/` unless the user explicitly asks for that phase.
- Do not run a separate frontend nginx/container in the standard app shape. Build React in the app image and serve static files from FastAPI.
- Every completed dashboard app must include a platform-labelled Linux app tar such as `image/<app-slug>-app_linux-amd64_<YYYY-MM-DD>.tar` and `image/.env.example` before final delivery.
- Prefer stable ClickHouse tables/views owned by the contour. FastAPI should query them through SQLAlchemy expressions over declarative models, not reimplement large transformations in Python.
- Include `/health` that checks API liveness and ClickHouse through the ORM session, for example `Session.scalar(select(literal(1)))`, without a raw SQL string.
- Keep static exports as fixture/dev data only. Production reads ClickHouse.
- Put only deployment inputs in `image/`: the app image tar and `.env.example`. ClickHouse images are contour-owned unless the user asks for an offline bundle.
- Build final app artifacts for an explicit Linux target. Never accept `darwin/*` or an implicit Apple Silicon `linux/arm64` image when the deployment target is `linux/amd64`.
- Do not deliver plain static HTML as the final shape. A quick visual prototype is allowed only if the same repository also contains the standard FastAPI/React/ClickHouse shape.
- New React dashboards must follow the SDU Data Portal tokens and component rules in `references/sdu-data-portal-design.md`. Do not introduce random brand palettes, one-off radii, or unthemed dark-mode gaps.

## Reference Files

- Read `references/business-analyst-start.md` when the input is only CSV files plus analyst wishes/prompts, or when creating a new dashboard from scratch.
- Read `references/project-layout.md` when creating or reviewing repository structure.
- Read `references/clickhouse-orm-contract.md` when working with source model naming, runtime data access, analyst SQL files, or ClickHouse query rules.
- Read `references/fastapi-react-compose.md` when implementing service code, env vars, Docker Compose, or runtime integration.
- Read `references/sdu-data-portal-design.md` when creating or changing React UI, visual tokens, layout, theme support, dashboard cards, buttons, inputs, charts, or prompt guidance for design.
- Read `references/handoff-checklist.md` before finalizing deliverables for data analysts, DBA, admins, or DevOps.

## Templates

If the target repository is empty or the user asks for a starter, copy from `assets/project-template/` and then adapt names, endpoints, charts, and UI to the concrete dashboard. The template already includes the SDU Data Portal token baseline; keep it token-based when adding components. Treat the template as a baseline, not as a reason to overwrite existing project-specific code.

Use `assets/analyst-start-prompt.md` as the standard prompt business analysts can paste into Codex, Claude Code, or another coding agent before attaching CSV files.

Use `scripts/inspect_csv_exports.py` as a helper only; the final table names, query semantics, and UI must still be reviewed against the analyst's domain intent.

Use `scripts/export_app_image.py` for every final image export. It rejects non-Linux targets and platform mismatches, checks that the image has no `.sql` content, labels the tar with the target platform, and copies `.env.example`.

If this skill folder is dropped into another project and the user asks to install it, run `python3 <skill-folder>/scripts/install_skill.py` from that project. It installs into both Codex and Claude Code by default; use `--target codex` or `--target claude` only when they ask for one agent.
