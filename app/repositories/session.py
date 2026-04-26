"""Database engine and session lifecycle helpers."""

from functools import lru_cache
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings


def _sqlite_connect_args(database_url: str) -> dict[str, bool]:
    """Return sqlite-specific connect arguments when needed."""

    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


@lru_cache
def get_engine():
    """Create and cache the SQLAlchemy engine."""

    settings = get_settings()
    return create_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
        connect_args=_sqlite_connect_args(settings.database_url),
    )


def get_session() -> Generator[Session, None, None]:
    """Yield a transactional DB session for FastAPI dependencies."""

    with Session(get_engine()) as session:
        yield session


def init_db() -> None:
    """Create all SQLModel tables for local/dev workflows."""

    SQLModel.metadata.create_all(get_engine())
