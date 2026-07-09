# ClickHouse ORM And Analyst SQL Contract

Use this when wiring CSV-backed dashboard data to ClickHouse.

## Source Model Naming

- Map every runtime source through a SQLAlchemy declarative model.
- Preserve the fully-qualified ClickHouse name in the model: `__tablename__ = "citizen_appeals"` and `__table_args__ = {"schema": "gold"}` map `gold.citizen_appeals`.
- Do not introduce `CLICKHOUSE_DATABASE` or per-table env vars such as `DASHBOARD_TABLE`.
- `data/` may contain several CSV exports, one source table per file. Prefer names such as `gold.citizen_appeals.csv`.
- Give each ORM model a real stable business key, or a stable composite key, for SQLAlchemy identity mapping. Marking a column as ORM `primary_key=True` does not alter an existing ClickHouse table.
- Keep source models aligned with the actual contour tables/views. If physical names differ, expose compatibility views with the documented contract names.
- Verify column names and types against `SHOW CREATE TABLE`, not CSV headers. ClickHouse is **case-sensitive**: bind the real column name explicitly when the contour casing differs from your pythonic attribute, e.g. `massa: Mapped[float] = mapped_column("Massa", Float64)`. A lowercase attribute querying a capitalized column raises `UNKNOWN_IDENTIFIER (code 47)`.
- Datetime/numeric columns are often stored as `String` in the contour (non-standard source formats ingested as text). Declare them `String` and convert in queries — never assume the prototype's typed seed matches production. See `real-contour-hardening.md`.

## Runtime Data Access

- Use SQLAlchemy 2 declarative models, `Session`, `select()`, `func`, `case`, joins, column projections, and bound values.
- Put query composition in repository/service modules. Return API DTOs instead of leaking ORM objects to React.
- Do not call `text()`, `exec_driver_sql()`, or `clickhouse_connect.Client.query()`/`.command()` in application code.
- Do not open, import, parse, mount, or execute files from `sql/` at runtime or in application tests.
- Prefer read-focused ORM usage. The ClickHouse dialect supports declarative models and read queries but is not a full relational ORM; do not depend on foreign-key relationships, cascades, autoincrement, `RETURNING`, or conventional row-by-row updates.
- Aggregate in ClickHouse; do not pull row-level data into Python and reduce it there. Contour tables hold millions of rows, so every endpoint must return a `GROUP BY` aggregate or an explicit `LIMIT`/sample. Compute histograms, heatmaps, and time buckets as SQL expressions. Wrap date columns with `parseDateTimeBestEffortOrNull(toString(col))` since they may be `String`. See `real-contour-hardening.md`.
- Use expression statements for health checks too, for example `session.scalar(select(literal(1)))`.

## Analyst SQL Folder

`sql/` contains human-readable SELECT references for future data analysts:

```text
sql/
├── gold.citizen_appeals.kpi_summary.sql
├── gold.citizen_appeals.daily_dynamics.sql
├── gold.citizen_appeals.breakdown_by_status.sql
├── gold.citizen_appeals.recent_rows.sql
└── gold.citizen_appeals.filter_status_options.sql
```

- Create these files after the ORM-backed behavior is implemented.
- Keep one query per file and use `<schema>.<table>.<query_name>.sql` names.
- Keep every `FROM` and `JOIN` fully qualified.
- Treat the files as analyst handoff material, not runtime source of truth.
- Do not put DDL, grants, migrations, bootstrap scripts, or table creation files in `sql/`.
- Exclude `sql/` and `*.sql` from the Docker build context and verify the exported app image contains none.
