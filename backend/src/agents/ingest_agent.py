"""IngestAgent — gate of the pipeline: validates, sanitizes, persists, generates trace_id."""
import time
from typing import Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session

from src.domain.entities import Incident
from src.domain.value_objects import generate_trace_id
from src.domain.exceptions import PromptInjectionDetected
from src.shared.security import scan_all_fields
from src.shared.validators import validate_email, validate_title, validate_description
from src.infrastructure.file_storage import save_attachment
from src.infrastructure.observability.events import emit_event


class IngestAgent:
    """
    Responsibility: Validate incoming incident data, apply guardrails,
    assign trace_id, persist to DB. Does NOT call the LLM.
    """

    def __init__(self, db: Session):
        self._db = db

    async def process(
        self,
        title: str,
        description: str,
        reporter_email: str,
        attachment: Optional[UploadFile] = None,
    ) -> Incident:
        start = time.monotonic()
        trace_id = generate_trace_id()

        # 1. Validate inputs
        title = validate_title(title)
        description = validate_description(description)
        reporter_email = validate_email(reporter_email)

        # 2. Prompt injection detection
        detected, field = scan_all_fields(title=title, description=description)
        if detected:
            duration_ms = int((time.monotonic() - start) * 1000)
            emit_event("ingest", "error", trace_id, duration_ms,
                       metadata={"error": "prompt_injection_detected", "field": field})
            raise PromptInjectionDetected(f"Injection pattern detected in field: {field}")

        # 3. Handle attachment
        attachment_type = None
        attachment_path = None
        if attachment and attachment.filename:
            attachment_type, attachment_path = await save_attachment(attachment, trace_id)

        # 4. Persist to DB
        incident = Incident(
            trace_id=trace_id,
            title=title,
            description=description,
            reporter_email=reporter_email,
            attachment_type=attachment_type,
            attachment_path=attachment_path,
            status="received",
        )
        self._db.add(incident)
        self._db.commit()
        self._db.refresh(incident)

        # 5. Emit observability event
        duration_ms = int((time.monotonic() - start) * 1000)
        emit_event(
            "ingest", "success", trace_id, duration_ms,
            incident_id=incident.id,
            metadata={"attachment_type": attachment_type, "injection_check": "passed"},
        )
        return incident
