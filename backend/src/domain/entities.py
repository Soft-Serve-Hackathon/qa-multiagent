"""SQLAlchemy ORM models — one table per domain entity."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
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
    linked_ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)  # Set when deduplicated
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
    reasoning_chain = Column(Text, nullable=True)         # JSON array of reasoning steps
    raw_llm_response = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class QAScopeResult(Base):
    __tablename__ = "qa_scope_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    reproduced = Column(Boolean, nullable=False, default=False)
    failing_tests = Column(Text, nullable=True)           # JSON array
    new_tests_created = Column(Text, nullable=True)       # JSON array of test snippets
    test_evidence_summary = Column(Text, nullable=True)
    coverage_files = Column(Text, nullable=True)          # JSON array of test file paths found
    qa_incomplete = Column(Boolean, nullable=False, default=False)  # True if qa_scope failed/skipped
    raw_llm_response = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class FixRecommendationResult(Base):
    __tablename__ = "fix_recommendation_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    proposed_fix_summary = Column(Text, nullable=True)
    proposed_files = Column(Text, nullable=True)          # JSON array
    risk_level = Column(String(10), nullable=True)        # low | medium | high
    post_fix_test_result = Column(Text, nullable=True)
    fix_incomplete = Column(Boolean, nullable=False, default=False)
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
    stage = Column(String(30), nullable=False)   # ingest|triage|qa_scope|fix_recommendation|ticket|notify|resolved
    incident_id = Column(Integer, nullable=True)
    status = Column(String(15), nullable=False)  # 'success'|'error'|'deduplicated'|'skipped'
    duration_ms = Column(Integer, nullable=False)
    event_metadata = Column("metadata", Text, nullable=False, default="{}")  # JSON string — DB column name: metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
