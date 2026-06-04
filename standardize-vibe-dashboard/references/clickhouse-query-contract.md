# ClickHouse Query Contract

Use this when wiring CSV-backed dashboard data to ClickHouse.

## Source Table Naming

- Use explicit `schema.table` names everywhere, for example `gold.citizen_appeals`.
- Do not introduce `CLICKHOUSE_DATABASE` in the app project.
- `data/` may contain several CSV exports, one source table per file.
- Prefer CSV fixture names that preserve the target table: `gold.citizen_appeals.csv`.
- If the CSV file has only a table stem, choose a clear schema such as `gold` and document the resulting `schema.table` name.
- Do not create per-table env vars such as `DASHBOARD_TABLE`. The table contract lives in CSV filenames, SQL filenames, README, and the fully-qualified names inside queries.
- Use `scripts/inspect_csv_exports.py data/` for a first-pass type contract, then adjust types manually where domain knowledge is clearer than inference.

## SQL Folder

`sql/` contains the SELECT queries used by dashboard visuals:

```text
sql/
├── gold.citizen_appeals.kpi_summary.sql
├── gold.citizen_appeals.daily_dynamics.sql
├── gold.citizen_appeals.breakdown_by_status.sql
├── gold.citizen_appeals.breakdown_by_applicant_type.sql
├── gold.citizen_appeals.recent_rows.sql
└── gold.citizen_appeals.filter_status_options.sql
```

Do not put DDL, grants, migrations, bootstrap scripts, or table creation files in `sql/`.
Each `.sql` file must contain exactly one query.
Name each file as `<schema>.<table>.<query_name>.sql`. For joins, use the primary table/view that owns the dashboard visual as the filename prefix.

## Query Rules

- Every `FROM` and `JOIN` uses a fully-qualified table/view.
- One query per `.sql` file; split grouped breakdown/filter files into separate files.
- Filename prefix identifies the source table first; query purpose comes last.
- Backend query code uses the same fully-qualified tables as the SQL files. If a production table has a different physical name, expose a ClickHouse view with the contract name.
- Use parameterized filters in FastAPI.
- Keep query output names aligned with frontend API fields.
- Keep SQL files readable enough for analysts to understand which chart they power.
- Local Docker Compose or a seed script may create and seed demo tables internally, but that bootstrap does not belong in `sql/`.
