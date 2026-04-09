"""
Ingest Agent.

Validates incoming incident data, applies guardrails (ADR-003), persists to database,
and saves any file attachment. Returns immediately so the HTTP layer can respond 201
before the pipeline runs in background.
"""

import logging
import os
import uuid
from typing import Optional

from fastapi import HTTPException, UploadFile

from ..domain.enums import AttachmentType, IncidentStatus, ObservabilityStage
from ..infrastructure.database import IncidentModel, get_db
from ..infrastructure.observability.events import timed_stage
from ..shared.validators import (
    sanitize_input,
    validate_email,
    validate_file_size,
    validate_injection,
    validate_mime,
)

logger = logging.getLogger(__name__)

UPLOADS_DIR = os.environ.get("UPLOADS_DIR", "./uploads")


class IngestAgent:
    """
    Synchronous gateway for the pipeline.
    Raises HTTPException on validation failures — caller does NOT need try/except.
    """

    def __init__(self) -> None:
        os.makedirs(UPLOADS_DIR, exist_ok=True)

    async def process(
        self,
        title: str,
        description: str,
        reporter_email: str,
        attachment: Optional[UploadFile] = None,
    ) -> tuple[int, str]:
        """
        Validate, sanitize, and persist the incident.

        Returns (incident_id, trace_id) on success.
        Raises HTTPException on any validation failure.
        """
        trace_id = str(uuid.uuid4())

        with timed_stage(trace_id, ObservabilityStage.INGEST) as meta:
            # ── Layer 1: email validation ──────────────────────────────────
            if not validate_email(reporter_email):
                raise HTTPException(
                    status_code=400,
                    detail={"error": "invalid_email", "message": "Invalid email format."},
                )

            # ── Layer 2: sanitize inputs ───────────────────────────────────
            title = sanitize_input(title, max_length=200)
            description = sanitize_input(description, max_length=2000)

            # ── Layer 3: prompt injection detection ────────────────────────
            for field_name, value in [("title", title), ("description", description)]:
                if not validate_injection(value):
                    meta["injection_check"] = "failed"
                    meta["injection_field"] = field_name
                    logger.warning(
                        "Prompt injection attempt detected",
                        extra={"trace_id": trace_id, "field": field_name},
                    )
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": "prompt_injection_detected",
                            "message": (
                                "Your report contains content that cannot be processed. "
                                "Please rephrase and try again."
                            ),
                        },
                    )

            meta["injection_check"] = "passed"

            # ── Layer 4: file attachment validation ────────────────────────
            attachment_type: Optional[AttachmentType] = None
            attachment_path: Optional[str] = None

            if attachment and attachment.filename:
                content = await attachment.read()

                if not validate_file_size(content):
                    raise HTTPException(
                        status_code=400,
                        detail={"error": "file_too_large", "message": "File exceeds 10MB limit."},
                    )

                is_valid_mime, detected_mime = validate_mime(content, attachment.content_type)
                if not is_valid_mime:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": "unsupported_file_type",
                            "message": f"File type '{detected_mime}' is not allowed.",
                        },
                    )

                # Determine attachment type from MIME
                if detected_mime in ("image/png", "image/jpeg"):
                    attachment_type = AttachmentType.IMAGE
                    ext = "png" if detected_mime == "image/png" else "jpg"
                else:
                    attachment_type = AttachmentType.LOG
                    ext = "txt"

                # Save to disk
                attachment_path = os.path.join(UPLOADS_DIR, f"{trace_id}.{ext}")
                with open(attachment_path, "wb") as f:
                    f.write(content)

                meta["attachment_type"] = attachment_type.value
                meta["attachment_size_bytes"] = len(content)
            else:
                meta["attachment_type"] = None

            # ── Persist to database ────────────────────────────────────────
            with get_db() as db:
                incident = IncidentModel(
                    trace_id=trace_id,
                    title=title,
                    description=description,
                    reporter_email=reporter_email,  # stored in DB, never in observability
                    attachment_type=attachment_type.value if attachment_type else None,
                    attachment_path=attachment_path,
                    status=IncidentStatus.RECEIVED.value,
                )
                db.add(incident)
                db.flush()
                incident_id: int = incident.id

            meta["incident_id"] = incident_id
            # reporter_email intentionally excluded from meta

        return incident_id, trace_id
