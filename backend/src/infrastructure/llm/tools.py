"""Claude tool definitions — read_ecommerce_file lets the LLM inspect Medusa.js source."""
import os
from src.config import settings

# Tool schema sent to Claude
TOOLS = [
    {
        "name": "read_ecommerce_file",
        "description": (
            "Read a source file from the Medusa.js e-commerce repository to understand "
            "the codebase context. Use this to inspect services, routes, or configuration "
            "files relevant to the incident being triaged."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": (
                        "Relative path from the repo root, e.g. "
                        "'packages/medusa/src/services/cart.ts'"
                    ),
                }
            },
            "required": ["path"],
        },
    }
]


def handle_tool_call(tool_name: str, tool_input: dict) -> str:
    """Execute a tool call requested by Claude and return the result as a string."""
    if tool_name == "read_ecommerce_file":
        return _read_ecommerce_file(tool_input["path"])
    return f"Unknown tool: {tool_name}"


def _read_ecommerce_file(relative_path: str) -> str:
    """Read a file from the Medusa.js repo. Returns content or an error message."""
    # Sanitize: prevent directory traversal
    clean_path = os.path.normpath(relative_path).lstrip("/\\")
    if ".." in clean_path:
        return "Error: Path traversal not allowed."

    full_path = os.path.join(settings.MEDUSA_REPO_PATH, clean_path)

    if not os.path.exists(full_path):
        return f"File not found: {relative_path}"

    if not os.path.isfile(full_path):
        return f"Not a file: {relative_path}"

    try:
        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        # Return first 3000 chars to avoid filling the context window
        if len(content) > 3000:
            content = content[:3000] + "\n... [truncated]"
        return content
    except Exception as e:
        return f"Error reading file: {e}"
