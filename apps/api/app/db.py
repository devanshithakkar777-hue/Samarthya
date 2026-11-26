from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    pass


_engine = None
_Session = None


def engine_options(settings) -> dict:
    """Pool settings that suit a serverless Postgres such as Neon.

    pool_pre_ping + pool_recycle: the database suspends when idle and drops connections.
    prepare_threshold=None: Neon's pooled endpoint (PgBouncer) does not support SQL PREPARE, which psycopg
    would otherwise start using after a few repeats of the same statement.
    """
    opts: dict = {"pool_pre_ping": True}
    if settings.database_url.startswith("postgresql"):
        opts.update(pool_size=settings.db_pool_size, max_overflow=settings.db_pool_size,
                    pool_recycle=settings.db_pool_recycle_seconds,
                    connect_args={"prepare_threshold": None, "connect_timeout": 15})
    return opts


def get_engine():
    global _engine, _Session
    if _engine is None:
        _engine = create_engine(get_settings().database_url, **engine_options(get_settings()))
        _Session = sessionmaker(bind=_engine, expire_on_commit=False)
    return _engine


def reset_engine() -> None:
    global _engine, _Session
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _Session = None


def get_db() -> Iterator[Session]:
    get_engine()
    assert _Session is not None
    db = _Session()
    try:
        yield db
    finally:
        db.close()
