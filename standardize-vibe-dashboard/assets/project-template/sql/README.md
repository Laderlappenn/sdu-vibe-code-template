# Analyst SQL References

Put future-analyst, human-readable dashboard SELECT references here. The FastAPI service must implement its runtime queries independently with SQLAlchemy ORM models/statements and must never load or execute files from this folder.

Rules:

- One query per `.sql` file.
- Use filenames shaped as `<schema>.<table>.<query_name>.sql`, for example `gold.citizen_appeals.kpi_summary.sql`.
- For joins, use the primary table/view for the filename prefix and keep every `FROM` and `JOIN` table fully qualified inside the query.
- Do not parameterize table names through env vars. If contour table names differ, expose ClickHouse views with the contract names.
- Do not put DDL, grants, migrations, bootstrap scripts, or ClickHouse table creation files here.
- Exclude this folder and all `*.sql` files from the Docker build context and final app image.
