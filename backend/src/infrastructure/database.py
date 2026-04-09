"""Database layer — SQLAlchemy engine, session factory, and table initialization."""
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from src.domain.entities import Base
from src.config import settings


def _get_engine():
    db_url = settings.DATABASE_URL
    # Ensure the data directory exists for SQLite
    if db_url.startswith("sqlite"):
        db_path = db_url.replace("sqlite:///", "").replace("./", "")
        dir_path = os.path.dirname(os.path.abspath(db_path))
        os.makedirs(dir_path, exist_ok=True)
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
        echo=settings.DEBUG,
    )
    if "sqlite" in db_url:
        @event.listens_for(engine, "connect")
        def set_wal(dbapi_conn, _):
            dbapi_conn.execute("PRAGMA journal_mode=WAL")
    return engine


engine = _get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables. Safe to call multiple times."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency — yields a DB session and closes it after the request."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
