# Data Fixtures

Put local CSV exports here when sample data is needed.

Rules:

- One source table export per CSV file.
- `data/` may contain several exports.
- Prefer filenames shaped as `<schema>.<table>.csv`, for example `gold.citizen_appeals.csv` or `dict.regions.csv`.
- Do not add one env var per table. The filename is the local table contract.
- Keep files small and anonymized. Production should read ClickHouse, not local CSV files.
