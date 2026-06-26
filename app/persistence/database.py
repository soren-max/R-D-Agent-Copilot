import os
from pathlib import Path

from sqlalchemy import create_engine as sqlalchemy_create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import sessionmaker

from app.persistence.models import Base

DEFAULT_DATABASE_URL = "sqlite:///data/runs.db"


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def ensure_sqlite_directory(database_url: str) -> None:
    url = make_url(database_url)
    if url.drivername != "sqlite":
        raise ValueError("Only SQLite DATABASE_URL values are supported.")

    database = url.database
    if not database or database == ":memory:":
        return

    db_path = Path(database)
    if db_path.parent != Path("."):
        db_path.parent.mkdir(parents=True, exist_ok=True)


def create_engine(database_url: str | None = None) -> Engine:
    url = database_url or get_database_url()
    ensure_sqlite_directory(url)
    return sqlalchemy_create_engine(
        url,
        connect_args={"check_same_thread": False},
        future=True,
    )


def create_session_factory(database_url: str | None = None) -> sessionmaker:
    engine = create_engine(database_url)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def init_db(database_url: str | None = None) -> Engine:
    engine = create_engine(database_url)
    Base.metadata.create_all(bind=engine)
    return engine
