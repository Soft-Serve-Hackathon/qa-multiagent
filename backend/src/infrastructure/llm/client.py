"""
LLM Client.

Claude API wrapper for incident analysis with multimodal support.
Handles tool use (agentic) loops and structured output parsing.
"""

import json
import logging
import re
from typing import Any, Optional

from anthropic import Anthropic

from src.infrastructure.llm.tools import ToolRegistry

logger = logging.getLogger(__name__)

# System prompt for Claude as SRE triage specialist
TRIAGE_SYSTEM_PROMPT = """You are a SRE (Site Reliability Engineer) incident triage specialist for a Medusa.js e-commerce platform.
Your job is to analyze incident reports and provide structured triage results.

**Severity Scale:**
- P1: Critical — Platform down, revenue impact, immediate action required (< 1 hour response)
- P2: High — Critical feature degraded, significant functionality impacted (< 4 hours response)
- P3: Medium — Non-critical feature affected, workaround available (< 24 hours response)
- P4: Low — Minor bug, cosmetic issue, can be scheduled (< 1 week response)

**Affected Modules in Medusa.js:**
- cart: Shopping cart service
- order: Order creation and management
- payment: Payment processing integrations
- inventory: Product inventory tracking
- product: Product catalog and search
- customer: Customer profile and authentication
- shipping: Shipping calculation and tracking
- discount: Discount and promotion codes
- unknown: Other modules or unclear

**Your response MUST be valid JSON exactly matching this structure:**
{
    "severity": "P1" | "P2" | "P3" | "P4",
    "affected_module": "cart" | "order" | "payment" | "inventory" | "product" | "customer" | "shipping" | "discount" | "unknown",
    "technical_summary": "2-3 sentence summary of the root cause and impact",
    "suggested_files": ["path/to/file1.ts", "path/to/file2.ts"],
    "confidence_score": <float between 0.0 and 1.0>
}

**Important Guidelines:**
- Do NOT include reporter email in your response
- Use the read_ecommerce_file tool if you need to understand the codebase structure
- Be precise about file paths — they must exist and be realistic for the module
- confidence_score: 1.0 = very confident, 0.5 = uncertain, < 0.4 = needs investigation
- If unsure, set severity to P3 and confidence_score between 0.3–0.5
- suggested_files should contain 0-5 relevant files; empty list is acceptable
- Return ONLY valid JSON — no markdown code blocks or extra text"""


class AnthropicLLMClient:
    """
    Wrapper around Anthropic API for incident triage.
    Supports multimodal input (images, logs) and tool use (codebase queries).
    """

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        """
        Initialize Anthropic client.

        Args:
            api_key: Anthropic API key
            model: Claude model name (default: claude-sonnet-4-6)
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def process_triage(
        self,
        incident_title: str,
        incident_description: str,
        attachment_image_base64: Optional[str] = None,
        attachment_log_text: Optional[str] = None,
        trace_id: str = "",
    ) -> dict[str, Any]:
        """
        Process incident triage using Claude with multimodal support and tool use.

        Args:
            incident_title: Incident title
            incident_description: Incident description
            attachment_image_base64: Optional image as base64 string
            attachment_log_text: Optional log file text (first 50KB)
            trace_id: Trace ID for logging

        Returns:
            Dictionary with keys:
            - severity: P1-P4
            - affected_module: module name
            - technical_summary: string
            - suggested_files: list of file paths
            - confidence_score: 0.0-1.0
        """
        # Build multimodal content
        content: list[dict[str, Any]] = [
            {
                "type": "text",
                "text": f"**Incident Title:** {incident_title}\n\n**Description:** {incident_description}",
            }
        ]

        # Add image if provided
        if attachment_image_base64:
            # Detect format (assume PNG by default, caller provides format)
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": attachment_image_base64,
                    },
                }
            )

        # Add log text if provided
        if attachment_log_text:
            content.append(
                {
                    "type": "text",
                    "text": f"\n**Attached Log/Trace:**\n```\n{attachment_log_text}\n```",
                }
            )

        # Prepare messages for agentic loop
        messages: list[dict[str, Any]] = [{"role": "user", "content": content}]

        # Agentic loop: keep calling Claude until we get a final answer
        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2048,
                    system=TRIAGE_SYSTEM_PROMPT,
                    tools=ToolRegistry.TOOLS,
                    messages=messages,
                )
            except Exception as exc:
                logger.error(f"Claude API error [{trace_id}]: {exc}")
                return self._fallback_result("P3", "unknown", f"LLM error: {exc}")

            # Check if we have a tool use in the response
            if response.stop_reason == "tool_use":
                # Find tool use block
                tool_use_block = next(
                    (b for b in response.content if b.type == "tool_use"), None
                )
                if not tool_use_block:
                    logger.warning(f"Tool use indicated but no tool_use block found [{trace_id}]")
                    break

                # Execute tool
                tool_result = ToolRegistry.execute_tool(
                    tool_use_block.name, tool_use_block.input
                )

                # Add assistant response and tool result to messages
                messages.append({"role": "assistant", "content": response.content})
                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use_block.id,
                                "content": tool_result,
                            }
                        ],
                    }
                )
                # Continue loop to next iteration

            elif response.stop_reason == "end_turn":
                # Claude finished — extract text and parse JSON
                text_block = next(
                    (b for b in response.content if b.type == "text"), None
                )
                if not text_block:
                    logger.warning(f"No text block in response [{trace_id}]")
                    return self._fallback_result("P3", "unknown", "No text in response")

                result_text = text_block.text
                return self._parse_triage_json(result_text, trace_id)

            else:
                logger.warning(f"Unexpected stop_reason: {response.stop_reason} [{trace_id}]")
                break

        # If we exit loop without final answer, return fallback
        logger.error(f"Max iterations reached without final answer [{trace_id}]")
        return self._fallback_result("P3", "unknown", "Max iterations reached")

    @staticmethod
    def _parse_triage_json(text: str, trace_id: str = "") -> dict[str, Any]:
        """
        Extract and parse JSON from Claude's text response.
        Handles markdown code blocks and validates structure.
        """
        try:
            # Try direct JSON parse first
            result = json.loads(text)
            # Validate required fields
            if all(k in result for k in ["severity", "affected_module", "technical_summary", "suggested_files", "confidence_score"]):
                return result
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code blocks
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group(1))
                if all(k in result for k in ["severity", "affected_module", "technical_summary", "suggested_files", "confidence_score"]):
                    return result
            except json.JSONDecodeError:
                pass

        # Last resort: extract any JSON object using regex
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                if all(k in result for k in ["severity", "affected_module", "technical_summary", "suggested_files", "confidence_score"]):
                    return result
            except json.JSONDecodeError:
                pass

        # Failed to parse
        logger.error(f"Failed to parse JSON from response: {text[:200]} [{trace_id}]")
        return AnthropicLLMClient._fallback_result("P3", "unknown", "Failed to parse JSON")

    @staticmethod
    def _fallback_result(
        severity: str = "P3",
        module: str = "unknown",
        error_msg: str = "Unable to analyze incident",
    ) -> dict[str, Any]:
        """
        Return a safe fallback triage result when LLM fails.
        """
        return {
            "severity": severity,
            "affected_module": module,
            "technical_summary": f"Triage analysis failed: {error_msg}. Please review manually.",
            "suggested_files": [],
            "confidence_score": 0.1,
        }
