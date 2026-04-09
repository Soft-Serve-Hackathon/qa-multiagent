"""Prompt injection detection — guardrail that runs before any LLM call."""
import re

# Patterns that indicate prompt injection attempts
INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"ignore (previous|prior|all|above|earlier) instructions?", re.IGNORECASE),
    re.compile(r"forget (everything|all|your|previous|prior)", re.IGNORECASE),
    re.compile(r"you are now", re.IGNORECASE),
    re.compile(r"new (persona|role|identity|instructions?|prompt)", re.IGNORECASE),
    re.compile(r"act as (an?|the)\s+\w+", re.IGNORECASE),
    re.compile(r"pretend (you are|to be|that)", re.IGNORECASE),
    re.compile(r"(system|admin|root)\s*prompt", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
    re.compile(r"DAN\s*(mode)?", re.IGNORECASE),
    re.compile(r"<\s*(system|prompt|instruction)\s*>", re.IGNORECASE),
    re.compile(r"\[INST\]|\[\/INST\]", re.IGNORECASE),
    re.compile(r"###\s*(system|instruction|prompt)", re.IGNORECASE),
    re.compile(r"(reveal|show|print|output|display|return)\s+(your )?(system prompt|instructions?|context)", re.IGNORECASE),
    re.compile(r"bypass\s+(safety|filter|guardrail|restriction)", re.IGNORECASE),
    re.compile(r"do not (follow|apply|use)\s+(safety|filter|rule|restriction|any)", re.IGNORECASE),
]


def contains_injection(text: str) -> tuple[bool, str | None]:
    """
    Check text for prompt injection patterns.
    Returns (is_injected, matched_pattern_description).
    """
    for pattern in INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            return True, match.group(0)
    return False, None


def scan_all_fields(**fields: str) -> tuple[bool, str | None]:
    """
    Scan multiple text fields for injection. Returns (detected, field_name).
    """
    for field_name, value in fields.items():
        if not value:
            continue
        detected, _ = contains_injection(value)
        if detected:
            return True, field_name
    return False, None
