from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import URL, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .settings import settings


@lru_cache
def get_engine() -> Engine:
    url = URL.create(
        drivername="clickhousedb",
        username=settings.clickhouse_user,
        password=settings.clickhouse_password,
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        database="default",
        query={
            "secure": str(settings.clickhouse_secure).lower(),
            "verify": str(settings.clickhouse_verify).lower(),
        },
    )
    return create_engine(url, pool_pre_ping=True)


SessionLocal = sessionmaker(
    bind=get_engine(),
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
)


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
