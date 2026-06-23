from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Base, ExampleRecord, SystemTable


# Replace the placeholder model and register every concrete dashboard source.
SOURCE_MODELS: tuple[type[Base], ...] = (ExampleRecord,)


def source_table_name(model: type[Base]) -> str:
    table = model.__table__
    if not table.schema:
        raise ValueError(f"ORM model {model.__name__} must declare an explicit schema")
    return f"{table.schema}.{table.name}"


def source_table_names() -> list[str]:
    return [source_table_name(model) for model in SOURCE_MODELS]


def source_table_metadata(session: Session) -> list[dict[str, int | str | None]]:
    tables: list[dict[str, int | str | None]] = []
    for model in SOURCE_MODELS:
        table = model.__table__
        item = session.scalar(
            select(SystemTable)
            .where(
                SystemTable.database == table.schema,
                SystemTable.name == table.name,
            )
            .limit(1)
        )
        if item:
            tables.append(
                {
                    "name": source_table_name(model),
                    "total_rows": item.total_rows,
                    "total_bytes": item.total_bytes,
                }
            )
    return tables


def count_rows(session: Session, model: type[Base]) -> int:
    """Use this ORM expression pattern in concrete dashboard repositories."""

    value = session.scalar(select(func.count()).select_from(model))
    return int(value or 0)
