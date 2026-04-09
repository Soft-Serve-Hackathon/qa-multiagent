"""Claude tool definitions — read_ecommerce_file and list_ecommerce_files for Medusa.js repo inspection."""
import os
from src.config import settings

# Real Medusa.js v2 repo structure (packages/modules/<module>/src/services/)
# Modules available: cart, order, payment, inventory, product, customer,
#   fulfillment, pricing, promotion, region, auth, user, notification, tax

TOOLS = [
    {
        "name": "read_ecommerce_file",
        "description": (
            "Read a source file from the Medusa.js e-commerce repository to understand "
            "the codebase context. Use this to inspect services, models, or configuration "
            "files relevant to the incident being triaged. "
            "Real repo structure: packages/modules/<module>/src/services/<module>-module.ts "
            "Examples: "
            "'packages/modules/cart/src/services/cart-module.ts', "
            "'packages/modules/payment/src/services/payment-module.ts', "
            "'packages/modules/order/src/services/order-module-service.ts', "
            "'packages/modules/inventory/src/services/inventory-module.ts'"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": (
                        "Relative path from the repo root. "
                        "e.g. 'packages/modules/cart/src/services/cart-module.ts'"
                    ),
                }
            },
            "required": ["path"],
        },
    },
    {
        "name": "list_ecommerce_files",
        "description": (
            "List files and subdirectories inside a directory of the Medusa.js repository. "
            "Use this to discover available files before reading them. "
            "Examples: "
            "'packages/modules/cart/src', "
            "'packages/modules/payment/src/services', "
            "'packages/modules'"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": (
                        "Relative directory path from repo root. "
                        "e.g. 'packages/modules/cart/src/services'"
                    ),
                },
                "extension_filter": {
                    "type": "string",
                    "description": "Optional file extension to filter by, e.g. '.ts'. Leave empty for all files.",
                },
            },
            "required": ["directory"],
        },
    },
]


def handle_tool_call(tool_name: str, tool_input: dict) -> str:
    """Execute a tool call requested by Claude and return the result as a string."""
    if tool_name == "read_ecommerce_file":
        return _read_ecommerce_file(tool_input["path"])
    if tool_name == "list_ecommerce_files":
        return _list_ecommerce_files(
            tool_input["directory"],
            tool_input.get("extension_filter", ""),
        )
    return f"Unknown tool: {tool_name}"


def _read_ecommerce_file(relative_path: str) -> str:
    """Read a file from the Medusa.js repo. Returns content or an error message."""
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
        if len(content) > 3000:
            content = content[:3000] + "\n... [truncated]"
        return content
    except Exception as e:
        return f"Error reading file: {e}"


def _list_ecommerce_files(directory: str, extension_filter: str = "") -> str:
    """List files in a directory of the Medusa.js repo."""
    clean_dir = os.path.normpath(directory).lstrip("/\\")
    if ".." in clean_dir:
        return "Error: Path traversal not allowed."

    full_path = os.path.join(settings.MEDUSA_REPO_PATH, clean_dir)

    if not os.path.exists(full_path):
        return f"Directory not found: {directory}"
    if not os.path.isdir(full_path):
        return f"Not a directory: {directory}"

    try:
        entries = []
        for name in sorted(os.listdir(full_path)):
            entry_path = os.path.join(full_path, name)
            if os.path.isdir(entry_path):
                entries.append(f"[dir]  {name}/")
            elif not extension_filter or name.endswith(extension_filter):
                entries.append(f"[file] {name}")

        if not entries:
            return f"Empty directory: {directory}"
        return f"Contents of {directory}:\n" + "\n".join(entries[:60])
    except Exception as e:
        return f"Error listing directory: {e}"
