"""File storage — save multimodal attachments and encode them for the LLM."""
import base64
import os
from pathlib import Path
from fastapi import UploadFile
from src.config import settings
from src.domain.value_objects import ALLOWED_EXTENSIONS, ALLOWED_MIME_TYPES
from src.domain.exceptions import UnsupportedFileTypeError, FileTooLargeError, EmptyOrCorruptAttachmentError


os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


def get_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def is_image(filename: str) -> bool:
    return get_extension(filename) in {".png", ".jpg", ".jpeg"}


def is_log(filename: str) -> bool:
    return get_extension(filename) in {".txt", ".log"}


async def save_attachment(file: UploadFile, trace_id: str) -> tuple[str, str]:
    """
    Validate and save an uploaded file.
    Returns (attachment_type, file_path).
    Raises domain exceptions on validation failure.
    """
    ext = get_extension(file.filename or "")
    if ext not in ALLOWED_EXTENSIONS:
        raise UnsupportedFileTypeError(f"File type '{ext}' is not allowed.")

    content = await file.read()
    if not content:
        raise EmptyOrCorruptAttachmentError("Uploaded file is empty.")

    max_bytes = settings.max_file_size_bytes
    if len(content) > max_bytes:
        raise FileTooLargeError(f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit.")

    attachment_type = "image" if is_image(file.filename or "") else "log"
    file_path = os.path.join(settings.UPLOAD_DIR, f"{trace_id}{ext}")

    with open(file_path, "wb") as f:
        f.write(content)

    return attachment_type, file_path


def read_as_base64(file_path: str) -> str:
    """Read a file and return its base64-encoded content (for Claude image input)."""
    with open(file_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def read_as_text(file_path: str) -> str:
    """Read a text/log file and return its content (for Claude text input)."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()[:8000]  # Truncate very large logs


def get_media_type(file_path: str) -> str:
    """Return MIME type for Claude image messages."""
    ext = Path(file_path).suffix.lower()
    return {"png": "image/png", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}.get(ext, "image/png")
