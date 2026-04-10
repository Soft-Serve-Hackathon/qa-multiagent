"""Anthropic Claude client — multimodal triage, QA scope, and fix recommendation."""
import json
import re
import anthropic
from src.config import settings
from src.infrastructure.llm.tools import TOOLS, handle_tool_call

# ─── Triage System Prompt ─────────────────────────────────────────────────────

TRIAGE_SYSTEM_PROMPT = """You are an expert SRE (Site Reliability Engineer) specialized in e-commerce systems built with Medusa.js v2.

Your task is to triage incident reports by analyzing the description and any attached files (screenshots or logs), then inspect the relevant Medusa.js source code using the available tools.

Use list_ecommerce_files to discover the available files in a module directory, then read_ecommerce_file to inspect the relevant source files before generating your assessment.

Real Medusa.js v2 module structure:
- packages/modules/<module>/src/services/<module>-module.ts  (main service)
- packages/modules/<module>/src/models/  (data models)
- Available modules: cart, order, payment, inventory, product, customer, fulfillment, pricing, promotion, region, auth, user, notification, tax

Always respond with a valid JSON object using EXACTLY this structure — reasoning_chain is REQUIRED:
{
  "reasoning_chain": [
    {"step": "symptom_analysis", "analysis": "What is the primary symptom? Active or resolved? User scope?"},
    {"step": "severity_reasoning", "analysis": "Revenue impact + user impact + service impact → why this severity?", "selected_severity": "P2"},
    {"step": "module_identification", "analysis": "Which Medusa.js module owns this behavior? Evidence from code?", "identified_module": "cart"},
    {"step": "codebase_correlation", "analysis": "What did you find in the source files? Which lines/methods are relevant?"},
    {"step": "confidence_assessment", "analysis": "How confident are you? What assumptions were made?", "confidence_score": 0.85}
  ],
  "severity": "P1" | "P2" | "P3" | "P4",
  "affected_module": "cart" | "order" | "payment" | "inventory" | "product" | "customer" | "fulfillment" | "pricing" | "promotion" | "region" | "auth" | "user" | "notification" | "tax" | "unknown",
  "technical_summary": "<2-3 sentence technical summary of the issue and likely root cause based on code inspection>",
  "suggested_files": ["packages/modules/cart/src/services/cart-module.ts"],
  "confidence_score": 0.0
}

Severity guide:
- P1: System completely down, checkout inaccessible, data loss risk
- P2: Critical functionality degraded (slow payments, cart errors affecting all users)
- P3: Non-critical functionality affected (search, recommendations, partial errors)
- P4: Minor bug, cosmetic issue, edge case

Show your work step by step in reasoning_chain BEFORE writing the final severity/module/summary."""

# ─── QA Scope System Prompt ───────────────────────────────────────────────────

QA_SCOPE_SYSTEM_PROMPT = """You are a QA Engineer specialized in Medusa.js e-commerce systems.

Given an incident triage result, your job is to:
1. Attempt to find existing test files related to the affected module using the tools
2. Assess whether the incident scenario is covered by existing tests
3. ALWAYS propose at least one regression test snippet (TypeScript/Jest) in new_tests_created

Use list_ecommerce_files to find test directories, and read_ecommerce_file to inspect test files.

Test file locations in Medusa.js v2:
- packages/modules/<module>/integration-tests/__tests__/services/
- packages/modules/<module>/src/services/__tests__/

CRITICAL RULES:
- new_tests_created MUST always contain at least one test snippet — even if the repo is unavailable
- If tools return "not found" or "empty", still propose a realistic test based on the incident description
- reproduced=true only if you found an existing test that directly covers this exact failure scenario
- reproduced=false in all other cases (missing tests, insufficient coverage, repo unavailable)

Always respond with a valid JSON object using EXACTLY this structure:
{
  "reproduced": true | false,
  "failing_tests": ["path/to/test.spec.ts::test name"],
  "new_tests_created": ["describe('<module> module', () => { it('should <scenario>', async () => { /* test body */ }) })"],
  "test_evidence_summary": "2-3 sentence summary of test coverage findings and proposed test rationale",
  "coverage_files": ["packages/modules/<module>/integration-tests/__tests__/services/<module>.spec.ts"]
}"""

# ─── Fix Recommendation System Prompt ────────────────────────────────────────

FIX_RECOMMENDATION_SYSTEM_PROMPT = """You are a senior Medusa.js engineer providing fix recommendations for production incidents.

Given triage analysis and QA scope results, your job is to:
1. Read the relevant source files identified in triage
2. Propose a concrete technical fix
3. Assess the risk of applying the fix
4. Describe what tests should be run after the fix

Use read_ecommerce_file to inspect the specific files before proposing the fix.

Always respond with a valid JSON object using EXACTLY this structure:
{
  "proposed_fix_summary": "2-3 sentence description of the proposed fix and how it addresses the root cause",
  "proposed_files": ["packages/modules/cart/src/services/cart-module.ts"],
  "risk_level": "low" | "medium" | "high",
  "post_fix_test_result": "Description of tests to run and expected outcomes to validate the fix",
  "code_snippet": "Optional: minimal code change snippet showing the key fix"
}

Risk assessment:
- low: Isolated change, no side effects, test coverage exists
- medium: Moderate scope, some side effects possible, partial test coverage
- high: Wide impact, affects core flow, limited test coverage or complex change"""


# ─── LLM Client ───────────────────────────────────────────────────────────────

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
        """Call Claude to triage an incident. Returns parsed dict with reasoning_chain."""
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

        return self._run_agentic_loop(
            system=TRIAGE_SYSTEM_PROMPT,
            initial_content=content,
            parser=self._parse_triage_json,
        )

    def qa_scope_incident(self, triage: dict) -> dict:
        """Call Claude to find/propose tests for the incident module."""
        text = (
            f"Incident Triage Results:\n"
            f"- Severity: {triage.get('severity', 'unknown')}\n"
            f"- Affected Module: {triage.get('affected_module', 'unknown')}\n"
            f"- Technical Summary: {triage.get('technical_summary', '')}\n"
            f"- Suggested Files: {', '.join(triage.get('suggested_files', []))}\n\n"
            f"Find existing tests for this module and assess coverage for this incident scenario."
        )
        return self._run_agentic_loop(
            system=QA_SCOPE_SYSTEM_PROMPT,
            initial_content=[{"type": "text", "text": text}],
            parser=self._parse_qa_json,
        )

    def generate_regression_test(self, context: dict) -> list[str]:
        """Fallback: generate at least one regression test snippet when qa_scope_incident returned none."""
        module = context.get("affected_module", "unknown")
        summary = context.get("technical_summary", "")
        severity = context.get("severity", "P3")
        text = (
            f"Write ONE minimal TypeScript/Jest regression test for this Medusa.js incident:\n"
            f"- Module: {module}\n"
            f"- Severity: {severity}\n"
            f"- Summary: {summary}\n\n"
            f"Return ONLY a JSON array with one string element containing the test snippet:\n"
            f'["describe(\\"{module} module\\", () => {{ it(\\"should ...\\", async () => {{ ... }}) }})"]'
        )
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=512,
                messages=[{"role": "user", "content": text}],
            )
            raw = next((b.text for b in response.content if hasattr(b, "text")), "")
            # Try to extract a JSON array
            import re
            match = re.search(r'\[[\s\S]*\]', raw)
            if match:
                parsed = json.loads(match.group())
                if isinstance(parsed, list) and parsed:
                    return [str(parsed[0])]
            # Fallback: return the raw text as a single test
            if raw.strip():
                return [raw.strip()[:1000]]
        except Exception:
            pass
        return [
            f"describe('{module} module', () => {{\n"
            f"  it('should handle {summary[:80]}', async () => {{\n"
            f"    // TODO: implement regression test for this incident\n"
            f"    expect(true).toBe(true);\n"
            f"  }});\n"
            f"}});"
        ]

    def fix_recommendation_incident(self, triage: dict, qa: dict) -> dict:
        """Call Claude to propose a technical fix based on triage + QA results."""
        text = (
            f"Incident Triage:\n"
            f"- Severity: {triage.get('severity', 'unknown')}\n"
            f"- Module: {triage.get('affected_module', 'unknown')}\n"
            f"- Summary: {triage.get('technical_summary', '')}\n"
            f"- Suggested Files: {', '.join(triage.get('suggested_files', []))}\n\n"
            f"QA Scope:\n"
            f"- Reproduced: {qa.get('reproduced', False)}\n"
            f"- Failing Tests: {qa.get('failing_tests', [])}\n"
            f"- Evidence: {qa.get('test_evidence_summary', '')}\n\n"
            f"Inspect the suggested files and propose a concrete fix."
        )
        return self._run_agentic_loop(
            system=FIX_RECOMMENDATION_SYSTEM_PROMPT,
            initial_content=[{"type": "text", "text": text}],
            parser=self._parse_fix_json,
        )

    # ─── Agentic loop ─────────────────────────────────────────────────────────

    def _run_agentic_loop(self, system: str, initial_content: list, parser) -> dict:
        """Generic tool-use loop: runs up to 10 rounds of tool calls, returns parsed dict."""
        messages = [{"role": "user", "content": initial_content}]
        raw_response = ""

        for _ in range(10):
            response = self._client.messages.create(
                model=self._model,
                max_tokens=2048,
                system=system,
                tools=TOOLS,
                messages=messages,
            )

            text_blocks = [b.text for b in response.content if hasattr(b, "text")]
            if text_blocks:
                raw_response = text_blocks[-1]

            tool_uses = [b for b in response.content if b.type == "tool_use"]
            if not tool_uses:
                break

            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for tool_use in tool_uses:
                result = handle_tool_call(tool_use.name, tool_use.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": result,
                })
            messages.append({"role": "user", "content": tool_results})

        return parser(raw_response)

    # ─── Parsers ──────────────────────────────────────────────────────────────

    def _parse_triage_json(self, raw: str) -> dict:
        """Extract and validate triage JSON from Claude's response."""
        def _valid(val, t, default):
            return val if isinstance(val, t) else default

        parsed = self._extract_json(raw)
        if not parsed:
            return {
                "severity": "P3",
                "affected_module": "unknown",
                "technical_summary": raw[:500] if raw else "Could not parse triage result.",
                "suggested_files": [],
                "confidence_score": 0.5,
                "reasoning_chain": [],
            }

        return {
            "severity": parsed.get("severity", "P3") if parsed.get("severity") in ("P1", "P2", "P3", "P4") else "P3",
            "affected_module": _valid(parsed.get("affected_module"), str, "unknown"),
            "technical_summary": _valid(parsed.get("technical_summary"), str, ""),
            "suggested_files": _valid(parsed.get("suggested_files"), list, []),
            "confidence_score": float(parsed.get("confidence_score", 0.5)),
            "reasoning_chain": _valid(parsed.get("reasoning_chain"), list, []),
        }

    def _parse_qa_json(self, raw: str) -> dict:
        """Extract and validate QA scope JSON."""
        parsed = self._extract_json(raw)
        if not parsed:
            return {
                "reproduced": False,
                "failing_tests": [],
                "new_tests_created": [],
                "test_evidence_summary": raw[:300] if raw else "Could not parse QA result.",
                "coverage_files": [],
            }
        return {
            "reproduced": bool(parsed.get("reproduced", False)),
            "failing_tests": parsed.get("failing_tests", []) if isinstance(parsed.get("failing_tests"), list) else [],
            "new_tests_created": parsed.get("new_tests_created", []) if isinstance(parsed.get("new_tests_created"), list) else [],
            "test_evidence_summary": str(parsed.get("test_evidence_summary", "")),
            "coverage_files": parsed.get("coverage_files", []) if isinstance(parsed.get("coverage_files"), list) else [],
        }

    def _parse_fix_json(self, raw: str) -> dict:
        """Extract and validate fix recommendation JSON."""
        parsed = self._extract_json(raw)
        if not parsed:
            return {
                "proposed_fix_summary": raw[:300] if raw else "Could not parse fix result.",
                "proposed_files": [],
                "risk_level": "medium",
                "post_fix_test_result": "",
                "code_snippet": "",
            }
        return {
            "proposed_fix_summary": str(parsed.get("proposed_fix_summary", "")),
            "proposed_files": parsed.get("proposed_files", []) if isinstance(parsed.get("proposed_files"), list) else [],
            "risk_level": parsed.get("risk_level", "medium") if parsed.get("risk_level") in ("low", "medium", "high") else "medium",
            "post_fix_test_result": str(parsed.get("post_fix_test_result", "")),
            "code_snippet": str(parsed.get("code_snippet", "")),
        }

    def _extract_json(self, raw: str) -> dict | None:
        """Extract the best JSON object from Claude's response.
        Priority: 1) ```json code block, 2) last {...} block, 3) first {...} block.
        """
        if not raw:
            return None

        # 1. Try to find a ```json ... ``` code block (most reliable)
        code_block = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", raw)
        if code_block:
            try:
                return json.loads(code_block.group(1))
            except json.JSONDecodeError:
                pass

        # 2. Try all {...} matches, prefer the LAST one (Claude puts JSON at end)
        candidates = list(re.finditer(r"\{[\s\S]*?\}", raw))
        for match in reversed(candidates):
            try:
                parsed = json.loads(match.group())
                # Must look like a triage/qa/fix response (has at least one known key)
                if any(k in parsed for k in ("severity", "reasoning_chain", "reproduced", "proposed_fix_summary")):
                    return parsed
            except json.JSONDecodeError:
                pass

        # 3. Fallback: greedy match from first { to last }
        greedy = re.search(r"\{[\s\S]*\}", raw)
        if greedy:
            try:
                return json.loads(greedy.group())
            except json.JSONDecodeError:
                pass

        return None


# Singleton — re-used across requests
_client_instance: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = LLMClient()
    return _client_instance
