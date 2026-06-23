from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import literal, select
from sqlalchemy.orm import Session

from .database import get_session
from .repositories import source_table_metadata, source_table_names
from .settings import settings


STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
INDEX_HTML = STATIC_DIR / "index.html"
DbSession = Annotated[Session, Depends(get_session)]

app = FastAPI(title="Dashboard API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health(db: DbSession) -> dict[str, str]:
    db.scalar(select(literal(1)))
    return {"status": "ok", "clickhouse": "ok"}


@app.get("/api/meta")
def meta(db: DbSession) -> dict[str, object]:
    return {
        "sourceTables": source_table_names(),
        "tables": source_table_metadata(db),
    }


@app.get("/api/dashboard/summary")
def dashboard_summary(db: DbSession) -> dict[str, object]:
    source_tables = source_table_names()
    tables = source_table_metadata(db)
    return {
        "sourceTables": source_tables,
        "tableCount": len(tables),
        "tables": [item["name"] for item in tables],
    }


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
