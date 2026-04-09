"""Anthropic Claude client — multimodal incident triage with tool use."""
import json
import anthropic
from src.config import settings
from src.infrastructure.llm.tools import TOOLS, handle_tool_call

SYSTEM_PROMPT = """You are an expert SRE (Site Reliability Engineer) specialized in e-commerce systems built with Medusa.js.

Your task is to triage incident reports by analyzing the description and any attached files (screenshots or logs), then inspect the relevant Medusa.js source code using the read_ecommerce_file tool.

Always respond with a valid JSON object using exactly this structure:
{
  "severity": "P1" | "P2" | "P3" | "P4",
  "affected_module": "cart" | "order" | "payment" | "inventory" | "product" | "customer" | "shipping" | "discount" | "unknown",
  "technical_summary": "<2-3 sentence technical summary of the issue and likely root cause>",
  "suggested_files": ["path/to/file1.ts", "path/to/file2.ts"],
  "confidence_score": 0.0 to 1.0
}

Severity guide:
- P1: System completely down, checkout inaccessible
- P2: Critical functionality degraded (slow payments, cart errors)
- P3: Non-critical functionality affected (search, recommendations)
- P4: Minor bug, cosmetic issue

Use read_ecommerce_file to inspect the relevant source files before generating your assessment."""


class LLMClient:
    def __init__(self):
        self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self._model = settings.ANTHROPIC_MODEL

    def triage_incident(
        self,
        title: str,
        description: str,
        attachment_type: str | None = None,
        attachment_base64: str | None = None,
        attachment_text: str | None = None,
        attachment_media_type: str = "image/png",
    ) -> dict:
        """
        Call Claude to triage an incident. Supports multimodal input (image or log).
        Returns a parsed dict with severity, affected_module, technical_summary, etc.
        """
        # Build user message content
        content: list = []

        text_parts = [f"Incident Title: {title}", f"Description: {description}"]

        if attachment_type == "log" and attachment_text:
            text_parts.append(f"\nAttached Log File:\n```\n{attachment_text}\n```")

        content.append({"type": "text", "text": "\n".join(text_parts)})

        if attachment_type == "image" and attachment_base64:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": attachment_media_type,
                    "data": attachment_base64,
                },
            })

        messages = [{"role": "user", "content": content}]

        # Agentic loop — handle tool calls until Claude returns final JSON
        raw_response = ""
        for _ in range(10):  # max 10 tool call rounds
            response = self._client.messages.create(
                model=self._model,
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )

            # Collect text blocks
            text_blocks = [b.text for b in response.content if hasattr(b, "text")]
            if text_blocks:
                raw_response = text_blocks[-1]

            # If no tool use, we're done
            tool_uses = [b for b in response.content if b.type == "tool_use"]
            if not tool_uses:
                break

            # Add assistant message with tool use
            messages.append({"role": "assistant", "content": response.content})

            # Execute tool calls and add results
            tool_results = []
            for tool_use in tool_uses:
                result = handle_tool_call(tool_use.name, tool_use.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": result,
                })
            messages.append({"role": "user", "content": tool_results})

        return self._parse_response(raw_response)

    def _parse_response(self, raw: str) -> dict:
        """Extract JSON from Claude's response."""
        # Try to find JSON block in the response
        import re
        json_match = re.search(r"\{[\s\S]*\}", raw)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        # Fallback defaults
        return {
            "severity": "P3",
            "affected_module": "unknown",
            "technical_summary": raw[:500] if raw else "Could not parse triage result.",
            "suggested_files": [],
            "confidence_score": 0.5,
        }


# Singleton — re-used across requests
_client_instance: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = LLMClient()
    return _client_instance
