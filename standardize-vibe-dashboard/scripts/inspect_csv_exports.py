#!/usr/bin/env python3
"""Inspect CSV exports and suggest ClickHouse table contracts.

The script is intentionally dependency-free so agents can run it in fresh
dashboard folders before wiring local ClickHouse seed logic.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable


IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass
class ColumnStats:
    name: str
    values: int = 0
    empty: int = 0
    bools: int = 0
    ints: int = 0
    floats: int = 0
    dates: int = 0
    datetimes: int = 0

    def observe(self, raw_value: str) -> None:
        value = raw_value.strip()
        if value == "":
            self.empty += 1
            return
        self.values += 1
        lowered = value.lower()
        if lowered in {"true", "false", "0", "1", "yes", "no"}:
            self.bools += 1
        if _is_int(value):
            self.ints += 1
        if _is_float(value):
            self.floats += 1
        if _is_date(value):
            self.dates += 1
        if _is_datetime(value):
            self.datetimes += 1

    def clickhouse_type(self) -> str:
        if self.values == 0:
            base = "String"
        elif self.bools == self.values:
            base = "Bool"
        elif self.ints == self.values:
            base = "Int64"
        elif self.floats == self.values:
            base = "Float64"
        elif self.datetimes == self.values:
            base = "DateTime64(3)"
        elif self.dates == self.values:
            base = "Date"
        else:
            base = "String"
        if self.empty and base != "String":
            return f"Nullable({base})"
        return base


def _is_int(value: str) -> bool:
    try:
        int(value)
    except ValueError:
        return False
    return True


def _is_float(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True


def _is_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _is_datetime(value: str) -> bool:
    if ":" not in value:
        return False
    candidates = [value, value.replace(" ", "T")]
    for candidate in candidates:
        try:
            datetime.fromisoformat(candidate)
        except ValueError:
            continue
        return True
    return False


def quote_identifier(value: str) -> str:
    if IDENTIFIER_RE.fullmatch(value):
        return f"`{value}`"
    return "`" + value.replace("`", "``") + "`"


def table_from_path(path: Path, default_schema: str) -> str:
    stem = path.name[:-4] if path.name.lower().endswith(".csv") else path.stem
    parts = stem.split(".")
    if len(parts) == 2 and all(parts):
        return stem
    table = re.sub(r"[^A-Za-z0-9_]+", "_", path.stem).strip("_").lower()
    if not table or table[0].isdigit():
        table = f"table_{table}"
    return f"{default_schema}.{table}"


def inspect_csv(path: Path, default_schema: str, sample_size: int) -> dict[str, object]:
    table_name = table_from_path(path, default_schema)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"{path} has no header row")
        columns = [ColumnStats(name=field) for field in reader.fieldnames]
        row_count = 0
        for row in reader:
            row_count += 1
            if row_count > sample_size:
                break
            for column in columns:
                column.observe(row.get(column.name, ""))
    schema, table = table_name.split(".", 1)
    ddl_lines = [
        f"CREATE DATABASE IF NOT EXISTS {quote_identifier(schema)};",
        f"CREATE TABLE IF NOT EXISTS {quote_identifier(schema)}.{quote_identifier(table)}",
        "(",
    ]
    for index, column in enumerate(columns):
        comma = "," if index < len(columns) - 1 else ""
        ddl_lines.append(f"  {quote_identifier(column.name)} {column.clickhouse_type()}{comma}")
    ddl_lines.extend([")", "ENGINE = MergeTree", "ORDER BY tuple();"])
    return {
        "file": str(path),
        "table": table_name,
        "sampled_rows": min(row_count, sample_size),
        "columns": [{"name": column.name, "type": column.clickhouse_type()} for column in columns],
        "ddl": "\n".join(ddl_lines),
        "insert": f"INSERT INTO {table_name} FORMAT CSVWithNames < {path}",
    }


def iter_csv_files(paths: Iterable[str]) -> list[Path]:
    result: list[Path] = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_dir():
            result.extend(sorted(path.glob("*.csv")))
        elif path.suffix.lower() == ".csv":
            result.append(path)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", default=["data"], help="CSV files or directories to inspect")
    parser.add_argument("--default-schema", default="gold")
    parser.add_argument("--sample-size", type=int, default=1000)
    args = parser.parse_args()

    reports = [inspect_csv(path, args.default_schema, args.sample_size) for path in iter_csv_files(args.paths)]
    note = (
        "CSV header casing and inferred types are HINTS for the local seed only. "
        "The real contour is case-sensitive and often stores dates/numbers as String. "
        "Verify against SHOW CREATE TABLE before finalizing ORM models — see "
        "references/real-contour-hardening.md."
    )
    print(json.dumps({"_note": note, "tables": reports}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
