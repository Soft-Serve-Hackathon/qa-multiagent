"""
LLM Tools.

Tool definitions for Claude to query codebase, logs, and domain knowledge.
Handles tool execution with safety checks (path traversal prevention).
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

ECOMMERCE_REPO_PATH = Path("/app/medusa-repo")
MAX_FILE_SIZE = 10000  # 10KB


class ToolRegistry:
    """
    Manages tools available to Claude during incident triage analysis.
    Tools allow Claude to read files from the ecommerce codebase for context.
    """

    TOOLS = [
        {
            "name": "read_ecommerce_file",
            "description": (
                "Reads a file from the Medusa.js e-commerce codebase to provide context "
                "for incident analysis. Use this when you need to understand the code "
                "structure related to the incident."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": (
                            "Relative path from /app/medusa-repo/, "
                            "e.g., 'packages/medusa/src/services/cart.ts'"
                        ),
                    }
                },
                "required": ["file_path"],
            },
        }
    ]

    @staticmethod
    def _validate_path(file_path: str) -> bool:
        """
        Validate path doesn't escape ECOMMERCE_REPO_PATH (prevent traversal attacks).
        Returns True if safe, False otherwise.
        """
        if ".." in file_path or file_path.startswith("/"):
            return False

        try:
            abs_path = (ECOMMERCE_REPO_PATH / file_path).resolve()
            abs_path.relative_to(ECOMMERCE_REPO_PATH.resolve())
            return True
        except ValueError:
            return False

    @staticmethod
    def execute_tool(tool_name: str, tool_input: dict) -> str:
        """
        Execute a tool and return its result as a string.
        All tools return string responses (consumed by Claude in agentic loop).
        """
        if tool_name != "read_ecommerce_file":
            return f"ERROR: Unknown tool '{tool_name}'"

        file_path = tool_input.get("file_path", "").strip()
        if not file_path:
            return "ERROR: file_path is required"

        # Validate path safety
        if not ToolRegistry._validate_path(file_path):
            logger.warning(f"Rejected unsafe path: {file_path}")
            return "ERROR: Invalid path (path traversal detected)"

        abs_path = ECOMMERCE_REPO_PATH / file_path

        # Check file exists and is a file
        if not abs_path.exists():
            return f"File not found: {file_path}"
        if not abs_path.is_file():
            return f"Not a file: {file_path}"

        try:
            with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(MAX_FILE_SIZE)
            if len(content) >= MAX_FILE_SIZE:
                content = content + f"\n... (file truncated to {MAX_FILE_SIZE} bytes)"
            return content
        except Exception as exc:
            logger.error(f"Error reading file {abs_path}: {exc}")
            return f"ERROR: Could not read file ({exc})"
