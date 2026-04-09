"""General utilities used across the application."""
import time
from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def utcnow_iso() -> str:
    return utcnow().isoformat()


def ms_since(start: float) -> int:
    """Return elapsed milliseconds since a time.monotonic() start point."""
    return int((time.monotonic() - start) * 1000)
