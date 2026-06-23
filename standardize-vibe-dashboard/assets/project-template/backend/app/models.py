from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from clickhouse_connect.cc_sqlalchemy.datatypes.sqltypes import String, UInt64


class Base(DeclarativeBase):
    pass


class SystemTable(Base):
    """Read-only ORM mapping used by the metadata endpoint."""

    __tablename__ = "tables"
    __table_args__ = {"schema": "system"}

    database: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, primary_key=True)
    total_rows: Mapped[int | None] = mapped_column(UInt64, nullable=True)
    total_bytes: Mapped[int | None] = mapped_column(UInt64, nullable=True)


class ExampleRecord(Base):
    """Replace this placeholder with columns inferred from the real CSV/source."""

    __tablename__ = "example_table"
    __table_args__ = {"schema": "gold"}

    record_id: Mapped[str] = mapped_column("id", String, primary_key=True)
