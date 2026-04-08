"""
Triage Agent.

Analyzes incident data using LLM (supports multimodal input: logs, images).
Generates triage results with severity, impact, and resolution recommendations.
Persists results and emits observability events.
"""

import json
import logging
from typing import Any, Optional

from src.config import get_settings
from src.domain.enums import IncidentStatus, ObservabilityStage, ObservabilityStatus
from src.infrastructure.database import (
    IncidentModel,
    TriageResultModel,
    get_db,
)
from src.infrastructure.file_storage import FileStorageManager
from src.infrastructure.llm.client import AnthropicLLMClient
from src.infrastructure.observability.events import emit_event

logger = logging.getLogger(__name__)


class TriageAgent:
    """
    Analyzes incident reports using Claude with multimodal support.
    Determines severity, affected module, technical analysis, and suggested files.
    Persists triage results and emits observability events.
    """

    def __init__(self) -> None:
        """Initialize agent with settings."""
        self.settings = get_settings()
        self.llm_client = AnthropicLLMClient(
            api_key=self.settings.anthropic_api_key,
            model=self.settings.llm_model,
        )

    def process(self, incident_id: int, trace_id: str) -> Optional[dict[str, Any]]:
        """
        Triage an incident: read incident + attachments, call Claude, persist result.

        Args:
            incident_id: ID of incident to triage
            trace_id: Trace ID for observability

        Returns:
            Dictionary with triage result or None on error
        """
        import time
        start_time = time.monotonic()

        try:
            # ── 1️⃣ Read incident from database ────────────────────────────────
            with get_db() as db:
                incident = (
                    db.query(IncidentModel)
                    .filter(IncidentModel.id == incident_id)
                    .first()
                )

                if not incident:
                    logger.error(f"[{trace_id}] Incident not found: {incident_id}")
                    self._emit_error_event(
                        trace_id, incident_id, "incident_not_found", start_time
                    )
                    return None

                # ── 2️⃣ Update status to TRIAGING ──────────────────────────────────
                incident.status = IncidentStatus.TRIAGING.value
                db.commit()

            # ── 3️⃣ Read multimodal attachments ────────────────────────────────
            attachment_image_base64 = FileStorageManager.get_image_base64(trace_id)
            attachment_log_text = FileStorageManager.get_log_text(trace_id)

            # ── 4️⃣ Call Claude with multimodal content ────────────────────────
            logger.info(
                f"[{trace_id}] Calling Claude for triage"
                f" (image={bool(attachment_image_base64)}, log={bool(attachment_log_text)})"
            )

            triage_data = self.llm_client.process_triage(
                incident_title=incident.title,
                incident_description=incident.description,
                attachment_image_base64=attachment_image_base64,
                attachment_log_text=attachment_log_text,
                trace_id=trace_id,
            )

            # ── 5️⃣ Validate triage result structure ────────────────────────────
            required_fields = [
                "severity",
                "affected_module",
                "technical_summary",
                "suggested_files",
                "confidence_score",
            ]
            if not all(field in triage_data for field in required_fields):
                logger.error(f"[{trace_id}] Incomplete triage result: {triage_data}")
                self._emit_error_event(
                    trace_id,
                    incident_id,
                    "invalid_triage_result",
                    start_time,
                )
                return None

            # ── 6️⃣ Persist triage result ───────────────────────────────────────
            with get_db() as db:
                triage_result = TriageResultModel(
                    incident_id=incident_id,
                    severity=triage_data["severity"],
                    affected_module=triage_data["affected_module"],
                    technical_summary=triage_data["technical_summary"],
                    suggested_files=json.dumps(triage_data.get("suggested_files", [])),
                    confidence_score=triage_data.get("confidence_score", 0.5),
                    raw_llm_response=None,  # Only store if debugging is needed
                )
                db.add(triage_result)
                db.flush()

                # ── 7️⃣ Update incident status to TICKETED ───────────────────────────
                # (Ready for next agent in pipeline)
                incident_model = (
                    db.query(IncidentModel)
                    .filter(IncidentModel.id == incident_id)
                    .first()
                )
                if incident_model:
                    incident_model.status = IncidentStatus.TICKETED.value
                    db.commit()

            # ── 8️⃣ Emit success event with metadata ────────────────────────────
            duration_ms = int((time.monotonic() - start_time) * 1000)

            metadata = {
                "severity_detected": triage_data["severity"],
                "module_detected": triage_data["affected_module"],
                "confidence_score": triage_data["confidence_score"],
                "model": self.settings.llm_model,
                "has_image_attachment": bool(attachment_image_base64),
                "has_log_attachment": bool(attachment_log_text),
                "num_suggested_files": len(triage_data.get("suggested_files", [])),
            }

            emit_event(
                trace_id=trace_id,
                stage=ObservabilityStage.TRIAGE,
                status=ObservabilityStatus.SUCCESS,
                duration_ms=duration_ms,
                incident_id=incident_id,
                metadata=metadata,
            )

            logger.info(
                f"[{trace_id}] Triage completed:"
                f" severity={triage_data['severity']}"
                f" module={triage_data['affected_module']}"
                f" confidence={triage_data['confidence_score']:.2f}"
            )

            return {
                "incident_id": incident_id,
                "trace_id": trace_id,
                "triage_result": triage_data,
            }

        except Exception as exc:
            logger.exception(f"[{trace_id}] TriageAgent error: {exc}")
            self._emit_error_event(trace_id, incident_id, str(exc), start_time)
            return None

    def _emit_error_event(
        self,
        trace_id: str,
        incident_id: Optional[int],
        error_msg: str,
        start_time: Optional[float] = None,
    ) -> None:
        """Helper to emit error observability event."""
        import time
        duration_ms = 0
        if start_time is not None:
            duration_ms = int((time.monotonic() - start_time) * 1000)

        try:
            emit_event(
                trace_id=trace_id,
                stage=ObservabilityStage.TRIAGE,
                status=ObservabilityStatus.ERROR,
                duration_ms=duration_ms,
                incident_id=incident_id,
                metadata={"error": error_msg},
            )
        except Exception as exc:
            logger.error(f"Failed to emit error event: {exc}")
