"""
File Storage.

Handles multimodal input file storage (logs, images, traces).
"""

import base64
import logging
from pathlib import Path
from typing import Optional

import magic

logger = logging.getLogger(__name__)


class FileStorageManager:
    """
    Manages file storage and retrieval for multimodal incident analysis.
    Prevents path traversal attacks, auto-detects MIME types, and handles
    encoding/decoding for LLM consumption.
    """

    BASE_DIR = Path(__file__).parent.parent.parent.parent / "uploads"

    @staticmethod
    def _validate_path(path: Path) -> bool:
        """
        Ensure path is within BASE_DIR (prevent path traversal).
        Returns True if safe, False otherwise.
        """
        try:
            path.resolve().relative_to(FileStorageManager.BASE_DIR.resolve())
            return True
        except ValueError:
            return False

    @staticmethod
    def read_attachment(file_path: str) -> tuple[str, bytes] | None:
        """
        Read attachment file and detect MIME type.
        Returns (mime_type, data_bytes) or None if file doesn't exist or is unsafe.
        """
        try:
            path = Path(file_path)
            if not FileStorageManager._validate_path(path):
                logger.warning(f"Path traversal attempt: {file_path}")
                return None

            if not path.exists() or not path.is_file():
                return None

            data = path.read_bytes()
            mime = magic.Magic(mime=True)
            mime_type = mime.from_buffer(data)

            return mime_type, data
        except Exception as exc:
            logger.error(f"Error reading attachment {file_path}: {exc}")
            return None

    @staticmethod
    def get_image_base64(trace_id: str) -> str | None:
        """
        Find and read image attachment for trace_id, return base64 encoded.
        Searches for {trace_id}.png or {trace_id}.jpg in uploads/.
        Returns base64 string or None if not found/invalid.
        """
        for ext in ("png", "jpg", "jpeg"):
            file_path = FileStorageManager.BASE_DIR / f"{trace_id}.{ext}"
            result = FileStorageManager.read_attachment(str(file_path))
            if result:
                mime_type, data = result
                if mime_type.startswith("image/"):
                    return base64.b64encode(data).decode("utf-8")
        return None

    @staticmethod
    def get_log_text(trace_id: str, max_bytes: int = 50000) -> str | None:
        """
        Find and read log/text attachment for trace_id, return text content.
        Searches for {trace_id}.txt or {trace_id}.log in uploads/.
        Limits content to max_bytes (50KB default). Returns text or None.
        Uses UTF-8 with fallback to latin-1 for encoding issues.
        """
        for ext in ("txt", "log"):
            file_path = FileStorageManager.BASE_DIR / f"{trace_id}.{ext}"
            result = FileStorageManager.read_attachment(str(file_path))
            if result:
                mime_type, data = result
                if "text" in mime_type or mime_type == "application/octet-stream":
                    try:
                        text = data.decode("utf-8", errors="replace")
                        if len(data) > max_bytes:
                            text = text[:max_bytes] + "\n... (content truncated)"
                        return text
                    except Exception as exc:
                        logger.error(f"Error decoding log {file_path}: {exc}")
                        continue
        return None
