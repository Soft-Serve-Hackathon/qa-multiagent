"""
Logger.

Structured JSON logging configuration for all agents.
ADR-002: every log line is a JSON object with timestamp, level, message, and context.
"""

import logging
import os
import sys


class _JsonFormatter(logging.Formatter):
    """Emit each log record as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        import json
        from datetime import datetime, timezone

        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging(level: str = "INFO", log_file: str | None = None) -> None:
    """
    Configure root logger with structured JSON output.
    Writes to stdout always; optionally also to log_file.
    Safe to call multiple times (idempotent).
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    formatter = _JsonFormatter()

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    if log_file:
        try:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            handlers.append(file_handler)
        except OSError:
            pass  # log dir not writable — stdout only

    root = logging.getLogger()
    # Avoid adding duplicate handlers on repeated calls
    if not root.handlers:
        for handler in handlers:
            handler.setFormatter(formatter)
            root.addHandler(handler)

    root.setLevel(numeric_level)

    # Quiet noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
