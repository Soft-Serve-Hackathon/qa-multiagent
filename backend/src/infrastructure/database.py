"""
Database Layer.

SQLAlchemy ORM setup, session management, and all ORM models.
Single source of truth for schema — mirrors domain/entities.py without ORM coupling.
"""

import json
from contextlib import contextmanager
from datetime import datetime
from typing import Generator

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    event,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from ..config import get_settings


# ---------------------------------------------------------------------------
# Engine & session factory
# ---------------------------------------------------------------------------

def _make_engine():
    settings = get_settings()
    url = settings.database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args, echo=False)

    # Enable WAL mode for SQLite to reduce write contention
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def set_wal(dbapi_conn, _):
            dbapi_conn.execute("PRAGMA journal_mode=WAL")

    return engine


engine = _make_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# ORM models
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


class IncidentModel(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trace_id = Column(String(36), nullable=False, unique=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    reporter_email = Column(String(254), nullable=False)
    attachment_type = Column(String(10), nullable=True)   # 'image' | 'log' | null
    attachment_path = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False, default="received")
    linked_ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)  # Set when deduplicated
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class TriageResultModel(Base):
    __tablename__ = "triage_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False, index=True)
    severity = Column(String(4), nullable=False)           # P1..P4
    affected_module = Column(String(50), nullable=False)
    technical_summary = Column(Text, nullable=False)
    suggested_files = Column(Text, nullable=False)         # JSON array stored as TEXT
    confidence_score = Column(Float, nullable=False)
    reasoning_chain = Column(Text, nullable=True)          # JSON array: reasoning steps (NEW)
    raw_llm_response = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def get_suggested_files(self) -> list[str]:
        return json.loads(self.suggested_files)

    def set_suggested_files(self, files: list[str]) -> None:
        self.suggested_files = json.dumps(files)
    
    def get_reasoning_chain(self) -> list[dict]:
        """Get structured reasoning chain."""
        if not self.reasoning_chain:
            return []
        return json.loads(self.reasoning_chain)
    
    def set_reasoning_chain(self, chain: list[dict]) -> None:
        """Set reasoning chain from list of step dicts."""
        self.reasoning_chain = json.dumps(chain)


class TicketModel(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False, index=True)
    trello_card_id = Column(String(100), nullable=True)
    trello_card_url = Column(String(500), nullable=True)
    trello_list_id = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class NotificationLogModel(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False, index=True)
    channel = Column(String(10), nullable=False)           # 'slack' | 'email'
    recipient = Column(String(254), nullable=False)
    notification_type = Column(String(30), nullable=False)
    content_summary = Column(Text, nullable=False)
    status = Column(String(10), nullable=False)            # 'sent' | 'failed' | 'mocked'
    sent_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    error_message = Column(Text, nullable=True)


class ObservabilityEventModel(Base):
    __tablename__ = "observability_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trace_id = Column(String(36), nullable=False, index=True)
    stage = Column(String(20), nullable=False)
    incident_id = Column(Integer, nullable=True)
    status = Column(String(10), nullable=False)            # 'success' | 'error'
    duration_ms = Column(Integer, nullable=False)
    event_metadata = Column(Text, name="metadata", nullable=False)  # JSON; 'metadata' is reserved in SA
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def get_metadata(self) -> dict:
        return json.loads(self.event_metadata)


# ---------------------------------------------------------------------------
# Table creation
# ---------------------------------------------------------------------------

def create_tables() -> None:
    """Create all tables if they don't exist. Safe to call multiple times."""
    import os
    # Ensure the data directory exists for SQLite
    settings = get_settings()
    if settings.database_url.startswith("sqlite:///"):
        db_path = settings.database_url.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    Base.metadata.create_all(bind=engine)
