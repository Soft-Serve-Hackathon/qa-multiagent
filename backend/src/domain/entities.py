"""SQLAlchemy ORM models — one table per domain entity."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trace_id = Column(String(36), unique=True, nullable=False, index=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    reporter_email = Column(String(254), nullable=False)
    attachment_type = Column(String(10), nullable=True)   # 'image' | 'log' | None
    attachment_path = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="received")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class TriageResult(Base):
    __tablename__ = "triage_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    severity = Column(String(5), nullable=False)          # P1 | P2 | P3 | P4
    affected_module = Column(String(50), nullable=False)
    technical_summary = Column(Text, nullable=False)
    suggested_files = Column(Text, nullable=False)        # JSON array as string
    confidence_score = Column(Float, nullable=False)
    raw_llm_response = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    trello_card_id = Column(String(100), nullable=True)
    trello_card_url = Column(Text, nullable=True)
    trello_list_id = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    channel = Column(String(10), nullable=False)          # 'slack' | 'email'
    recipient = Column(String(254), nullable=False)
    notification_type = Column(String(30), nullable=False)
    content_summary = Column(Text, nullable=False)
    status = Column(String(10), nullable=False)           # 'sent' | 'failed' | 'mocked'
    sent_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    error_message = Column(Text, nullable=True)


class ObservabilityEvent(Base):
    __tablename__ = "observability_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trace_id = Column(String(36), nullable=False, index=True)
    stage = Column(String(20), nullable=False)            # ingest | triage | ticket | notify | resolved
    incident_id = Column(Integer, nullable=True)
    status = Column(String(10), nullable=False)           # 'success' | 'error'
    duration_ms = Column(Integer, nullable=False)
    event_metadata = Column(Text, nullable=False, default="{}")  # JSON string
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
