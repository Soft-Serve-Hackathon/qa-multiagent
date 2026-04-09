# General Development Instructions

## Mission
Review the solution for exposure, abuse, permissions, and data handling.

## Focus
- authentication
- authorization
- input validation
- secrets
- attack surface

## Outputs
- security observations
- risk checklist
- minimum MVP recommendations

---

## Rules
- Follow the active spec before touching code.
- Prefer small, reversible changes.
- Maintain consistency of names, contracts, and structure.
- If you detect ambiguity, turn it into a documented open question.
- Every implementation must be verifiable.
- Document important assumptions.

## SRE Domain — Threat Model

The system receives untrusted input from external users via a web form. The LLM is the most sensitive component.

| ID | Threat | Vector | Mitigation implemented |
|---|---|---|---|
| T1 | Prompt injection | `description` or `title` field with malicious instructions | `validate_injection()` in IngestAgent — ADR-003 |
| T2 | Malicious file upload | image with malicious EXIF payload, script disguised as .txt | Validate real MIME type with `python-magic`, do not trust the extension |
| T3 | Credentials in logs | `reporter_email` or API keys appear in observability events | `reporter_email` not included in LLM prompts. API keys only in `.env`. |
| T4 | Exposed API token | `TRELLO_API_TOKEN`, `ANTHROPIC_API_KEY` hardcoded in code | Only in `.env`. `.env` in `.gitignore`. `.env.example` uses placeholders. |
| T5 | SSRF via attachment | If the system accepted file URLs, SSRF would be possible | MVP only accepts local uploads, not URLs. |
| T6 | Context overflow | Very large log file overflowing the LLM context | IngestAgent reads only the first 50KB of log files. |

## Security checklist for the MVP

Before submission, verify:
- [ ] `validate_injection()` in `src/guardrails.py` covers ADR-003 patterns
- [ ] MIME type validation uses `python-magic`, not only file extension
- [ ] `.env` is in `.gitignore`
- [ ] `.env.example` contains placeholders for all values (no real values)
- [ ] `reporter_email` does NOT appear in any observability log or LLM prompt
- [ ] API keys are not hardcoded in any source file
- [ ] `description` is truncated to 2000 chars before sending to the LLM
- [ ] POST /api/incidents returns HTTP 400 (not 500) on invalid inputs
- [ ] AC7 passes: input with "ignore previous instructions" → HTTP 400, no `stage=triage` event in logs

## Responsible AI — Verification

| Principle | How it is implemented | Where to verify |
|---|---|---|
| Fairness | Triage is based on technical content, not reporter email | `reporter_email` excluded from LLM prompt |