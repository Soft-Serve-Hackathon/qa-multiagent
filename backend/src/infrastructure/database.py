"""Database layer — SQLAlchemy engine, session factory, table initialization, and inline migrations."""
import os
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from src.domain.entities import Base
from src.config import settings


def _get_engine():
    db_url = settings.DATABASE_URL
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


def _run_migrations() -> None:
    """Apply additive schema changes to existing databases.
    Each statement is wrapped in try/except — silently skips if column already exists."""
    migrations = [
        # incidents: deduplication support
        "ALTER TABLE incidents ADD COLUMN linked_ticket_id INTEGER REFERENCES tickets(id)",
        # triage_results: reasoning chain
        "ALTER TABLE triage_results ADD COLUMN reasoning_chain TEXT",
    ]
    with engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception:
                pass  # Column already exists — skip silently


def init_db() -> None:
    """Create all tables and run additive migrations. Safe to call multiple times."""
    Base.metadata.create_all(bind=engine)
    _run_migrations()


def get_db():
    """FastAPI dependency — yields a DB session and closes it after the request."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
