"""TriageAgent — the only agent that calls the LLM. Produces structured triage results."""
import json
import time
from sqlalchemy.orm import Session

from src.domain.entities import Incident, TriageResult
from src.application.dto import TriageResultDTO
from src.infrastructure.llm.client import get_llm_client
from src.infrastructure.file_storage import read_as_base64, read_as_text, get_media_type
from src.infrastructure.observability.events import emit_event


class TriageAgent:
    """
    Responsibility: Analyze incident with Claude (multimodal). Persist TriageResult.
    Updates Incident status to 'triaging' then 'ticketed'.
    """

    def __init__(self, db: Session):
        self._db = db
        self._llm = get_llm_client()

    def process(self, incident_id: int) -> TriageResultDTO:
        start = time.monotonic()
        incident: Incident = self._db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")

        # Update status
        incident.status = "triaging"
        self._db.commit()

        # Prepare multimodal content
        attachment_base64 = None
        attachment_text = None
        media_type = "image/png"

        if incident.attachment_path:
            if incident.attachment_type == "image":
                attachment_base64 = read_as_base64(incident.attachment_path)
                media_type = get_media_type(incident.attachment_path)
            elif incident.attachment_type == "log":
                attachment_text = read_as_text(incident.attachment_path)

        # Call LLM
        raw_result = self._llm.triage_incident(
            title=incident.title,
            description=incident.description,
            attachment_type=incident.attachment_type,
            attachment_base64=attachment_base64,
            attachment_text=attachment_text,
            attachment_media_type=media_type,
        )

        suggested_files = raw_result.get("suggested_files", [])

        # Persist TriageResult
        triage = TriageResult(
            incident_id=incident.id,
            severity=raw_result.get("severity", "P3"),
            affected_module=raw_result.get("affected_module", "unknown"),
            technical_summary=raw_result.get("technical_summary", ""),
            suggested_files=json.dumps(suggested_files),
            confidence_score=float(raw_result.get("confidence_score", 0.5)),
            reasoning_chain=json.dumps(raw_result.get("reasoning_chain", [])),
            raw_llm_response=json.dumps(raw_result),
        )
        self._db.add(triage)
        # Leave status as "triaging" — TicketAgent will set it to "ticketed"
        self._db.commit()
        self._db.refresh(triage)

        duration_ms = int((time.monotonic() - start) * 1000)
        emit_event(
            "triage", "success", incident.trace_id, duration_ms,
            incident_id=incident.id,
            metadata={
                "model": "claude-sonnet-4-6",
                "severity_detected": triage.severity,
                "module_detected": triage.affected_module,
                "confidence": triage.confidence_score,
                "files_found": len(suggested_files),
                "multimodal": incident.attachment_type is not None,
            },
        )

        return TriageResultDTO(
            incident_id=incident.id,
            trace_id=incident.trace_id,
            severity=triage.severity,
            affected_module=triage.affected_module,
            technical_summary=triage.technical_summary,
            suggested_files=suggested_files,
            confidence_score=triage.confidence_score,
        )
