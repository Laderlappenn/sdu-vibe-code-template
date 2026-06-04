from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .clickhouse import get_client, qualified_identifier_parts, rows, table_preview
from .settings import settings


STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
INDEX_HTML = STATIC_DIR / "index.html"
SOURCE_TABLES = ["gold.example_table"]

app = FastAPI(title="Dashboard API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    get_client().query("select 1")
    return {"status": "ok", "clickhouse": "ok"}


@app.get("/api/meta")
def meta() -> dict[str, object]:
    tables: list[dict[str, object]] = []
    for source_table in SOURCE_TABLES:
        schema, table_name = qualified_identifier_parts(source_table)
        tables.extend(
            rows(
                """
                select
                  database,
                  name,
                  total_rows,
                  total_bytes
                from system.tables
                where database = {database:String}
                  and name = {table:String}
                order by name
                """,
                {"database": schema, "table": table_name},
            )
        )
    return {"sourceTables": SOURCE_TABLES, "tables": tables}


@app.get("/api/dashboard/summary")
def dashboard_summary() -> dict[str, object]:
    tables = []
    for source_table in SOURCE_TABLES:
        schema, table_name = qualified_identifier_parts(source_table)
        tables.extend(
            rows(
                "select concat(database, '.', name) as name from system.tables where database = {database:String} and name = {table:String}",
                {"database": schema, "table": table_name},
            )
        )
    return {
        "sourceTables": SOURCE_TABLES,
        "tableCount": len(tables),
        "tables": [item["name"] for item in tables],
    }


@app.get("/api/tables/{table_name}/preview")
def preview_table(table_name: str, limit: int = Query(default=100, ge=1, le=500)) -> dict[str, object]:
    try:
        data = table_preview(table_name, limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Table is unavailable") from exc
    return {"table": table_name, "rows": data}


if (STATIC_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")


def frontend_index() -> FileResponse:
    if not INDEX_HTML.exists():
        raise HTTPException(status_code=404, detail="Frontend build is unavailable")
    return FileResponse(INDEX_HTML)


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return frontend_index()


@app.get("/{full_path:path}", include_in_schema=False)
def spa_fallback(full_path: str) -> FileResponse:
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API route is unavailable")
    candidate = STATIC_DIR / full_path
    if candidate.is_file():
        return FileResponse(candidate)
    return frontend_index()
