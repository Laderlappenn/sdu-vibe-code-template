import re
from collections.abc import Sequence
from typing import Any

import clickhouse_connect

from .settings import settings


IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def quote_identifier(value: str) -> str:
    if not value:
        raise ValueError("Identifier is empty")
    if IDENTIFIER_RE.fullmatch(value):
        return f"`{value}`"
    return "`" + value.replace("`", "``") + "`"


def qualified_identifier_parts(value: str) -> tuple[str, str]:
    parts = [part.strip() for part in value.split(".")]
    if len(parts) != 2 or not all(parts):
        raise ValueError("Expected a fully-qualified ClickHouse name: schema.table")
    return parts[0], parts[1]


def quote_qualified_identifier(value: str) -> str:
    schema, table = qualified_identifier_parts(value)
    return f"{quote_identifier(schema)}.{quote_identifier(table)}"


def get_client():
    return clickhouse_connect.get_client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        username=settings.clickhouse_user,
        password=settings.clickhouse_password,
        secure=settings.clickhouse_secure,
        verify=settings.clickhouse_verify,
    )


def rows(query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    result = get_client().query(query, parameters=parameters or {})
    return [dict(zip(result.column_names, row)) for row in result.result_rows]


def table_preview(table_name: str, limit: int = 100) -> list[dict[str, Any]]:
    limit = max(1, min(limit, 500))
    table = quote_qualified_identifier(table_name)
    return rows(f"select * from {table} limit {limit}")


def first_row(table_names: Sequence[str]) -> dict[str, Any]:
    for table_name in table_names:
        data = table_preview(table_name, limit=1)
        if data:
            return data[0]
    return {}
