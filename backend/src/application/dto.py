"""Data Transfer Objects — typed dicts passed between use cases and agents."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class IncidentDTO:
    id: int
    trace_id: str
    title: str
    description: str
    reporter_email: str
    attachment_type: Optional[str] = None
    attachment_path: Optional[str] = None


@dataclass
class TriageResultDTO:
    incident_id: int
    trace_id: str
    severity: str
    affected_module: str
    technical_summary: str
    suggested_files: list[str] = field(default_factory=list)
    confidence_score: float = 0.5
    raw_llm_response: Optional[str] = None


@dataclass
class TicketDTO:
    incident_id: int
    trace_id: str
    trello_card_id: str
    trello_card_url: str
    trello_list_id: str
    assigned_trello_member_id: Optional[str] = None
    assigned_slack_user_id: Optional[str] = None
