"""Input validators — email format, field lengths, file constraints."""
import re
from src.domain.exceptions import InvalidEmailError

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


def validate_email(email: str) -> str:
    """Validate email format. Returns normalized email or raises InvalidEmailError."""
    email = email.strip().lower()
    if not EMAIL_REGEX.match(email):
        raise InvalidEmailError(f"Invalid email format: {email}")
    return email


def truncate(text: str, max_chars: int) -> str:
    """Truncate text to max_chars. Adds '...' if truncated."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars - 3] + "..."


def validate_title(title: str) -> str:
    title = title.strip()
    if not title:
        raise ValueError("Title cannot be empty.")
    return truncate(title, 200)


def validate_description(description: str) -> str:
    description = description.strip()
    if not description:
        raise ValueError("Description cannot be empty.")
    return truncate(description, 2000)
