"""
Validators.

Input validation and guardrails for injection detection and data integrity.
ADR-003: three-layer protection — injection detection, sanitization, MIME validation.
"""

import re
import unicodedata
from typing import Optional

# ---------------------------------------------------------------------------
# Layer 1 — Prompt injection detection (ADR-003)
# ---------------------------------------------------------------------------

_INJECTION_PATTERNS = re.compile(
    r"ignore\s+(previous|all)|"
    r"disregard|"
    r"forget\s+your|"
    r"new\s+instructions|"
    r"you\s+are\s+now|"
    r"system\s+prompt|"
    r"jailbreak|"
    r"\bDAN\b|"
    r"act\s+as|"
    r"pretend\s+you\s+are|"
    r"reveal\s+your|"
    r"bypass",
    re.IGNORECASE,
)


def validate_injection(text: str) -> bool:
    """
    Return True if the text is clean, False if it contains injection patterns.
    Called on both title and description before any LLM interaction.
    """
    return _INJECTION_PATTERNS.search(text) is None


# ---------------------------------------------------------------------------
# Layer 2 — Input sanitization (ADR-003)
# ---------------------------------------------------------------------------

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def sanitize_input(text: str, max_length: int = 2000) -> str:
    """
    Remove control characters and truncate to max_length.
    Does NOT remove newlines (\n) or tabs (\t) — those are valid in descriptions.
    """
    text = _CONTROL_CHARS.sub("", text)
    text = text[:max_length]
    return text


# ---------------------------------------------------------------------------
# Layer 3 — File / MIME validation (ADR-003)
# ---------------------------------------------------------------------------

_ALLOWED_MIMES = {"image/png", "image/jpeg", "text/plain"}
_MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB


def validate_mime(content: bytes, declared_content_type: Optional[str] = None) -> tuple[bool, str]:
    """
    Validate the real MIME type of file content using python-magic.
    Falls back to declared content-type if python-magic is unavailable.

    Returns (is_valid, detected_mime).
    """
    try:
        import magic
        detected = magic.from_buffer(content[:2048], mime=True)
    except Exception:
        # Fallback: trust the declared content-type from the upload
        detected = declared_content_type or "application/octet-stream"

    return detected in _ALLOWED_MIMES, detected


def validate_file_size(content: bytes) -> bool:
    """Return True if file is within the 10MB limit."""
    return len(content) <= _MAX_FILE_BYTES


# ---------------------------------------------------------------------------
# Email validation
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def validate_email(email: str) -> bool:
    """Basic structural email validation."""
    return bool(_EMAIL_RE.match(email))
