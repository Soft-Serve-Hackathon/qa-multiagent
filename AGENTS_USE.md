# AGENTS_USE.md — Agent Architecture Documentation

> This document describes the multi-agent architecture of the SRE Incident Intake & Triage Agent, including use cases, implementation details, observability evidence, and safety measures.

---

## System Overview

The system implements a pipeline of **5 specialized agents** with unique, non-overlapping responsibilities. Each agent is stateless (state lives in SQLite). The LLM is invoked **only by TriageAgent** — all other agents are deterministic integrations.

```
IngestAgent → TriageAgent → TicketAgent → NotifyAgent
                                          ↑
                         ResolutionWatcher (background)
```

A single `trace_id` (UUID v4) is assigned at ingestion and flows through every agent, enabling end-to-end observability.

---

## Agent Registry

### 1. IngestAgent

**Role:** Gateway. Validates, sanitizes, and persists incoming incident reports.

**Responsibility boundary:**
- Receives raw user input from the HTTP API
- Does NOT make business decisions
- Does NOT call the LLM
- Does NOT create tickets or send notifications

**Input:** `multipart/form-data` with `title`, `description`, `reporter_email`, optional `attachment`

**Output:** `{ incident_id: int, trace_id: str }` → triggers async pipeline

**Guardrails implemented:**
- Prompt injection detection: regex pattern matching against known injection phrases (`ignore previous`, `disregard`, `you are now`, `jailbreak`, etc.)
- MIME type validation: uses `python-magic` to verify real file type (not just extension)
- Input sanitization: removes control characters, truncates `description` to 2000 chars
- Email format validation before persistence

**Observability event emitted:**
```json
{
  "stage": "ingest",
  "trace_id": "f47ac10b-...",
  "status": "success",
  "duration_ms": 45,
  "metadata": {
    "attachment_type": "image",
    "injection_check": "passed",
    "description_length": 342
  }
}
```

---

### 2. TriageAgent

**Role:** Intelligence core. Analyzes the incident using Claude claude-sonnet-4-6 (multimodal) and the Medusa.js codebase.

**Responsibility boundary:**
- **Only agent that calls the LLM**
- Receives `incident_id`, retrieves full incident from DB
- Does NOT create tickets
- Does NOT send notifications
- Does NOT access external APIs other than Anthropic

**Input:** `incident_id` → retrieves Incident from DB

**Output:** `TriageResult { severity, affected_module, technical_summary, suggested_files, confidence_score }`

**LLM Integration:**
- Model: `claude-sonnet-4-6`
- Multimodal handling:
  - Image (PNG/JPG): read bytes → encode base64 → include as `image` content block in Claude message
  - Log file (.txt/.log): read first 50KB as text → include in text content
  - Text only: no attachment processing
- Tool use: `read_ecommerce_file(path)` → reads files from Medusa.js codebase at `/app/medusa-repo/`
- Output format: structured JSON validated with Pydantic

**Prompt design (high-level):**
- System prompt: agent role, Medusa.js domain context, severity scale (P1-P4), expected JSON output format
- User message: incident text + multimodal content + retrieved codebase snippets
- Output structure enforced: `severity`, `affected_module`, `technical_summary`, `suggested_files[]`, `confidence_score`

**Observability event emitted:**
```json
{
  "stage": "triage",
  "trace_id": "f47ac10b-...",
  "status": "success",
  "duration_ms": 2341,
  "metadata": {
    "model": "claude-sonnet-4-6",
    "severity_detected": "P2",
    "module_detected": "cart",
    "confidence": 0.87,
    "files_found": 3,
    "multimodal": true
  }
}
```

---

### 3. TicketAgent

**Role:** Ticketing integration. Translates the triage result into a Trello Card.

**Responsibility boundary:**
- Does NOT analyze the incident
- Receives a fully-formed `TriageResult` and maps it to Trello's API format
- Handles Trello API failures gracefully (persists `ticket_pending` state for retry)

**Input:** `triage_result + incident`

**Output:** `{ trello_card_id: str, trello_card_url: str }`

**Trello Card structure:**
- Name: `[P{severity}] {title}`
- Description: technical summary + affected module + suggested files + trace_id
- Labels: severity color-coded (P1=red, P2=orange, P3=yellow, P4=green)
- Checklist "Files to investigate": list of suggested Medusa.js files

**Mock mode:** If `MOCK_INTEGRATIONS=true`, returns a simulated card response and logs `status=mocked`.

**Observability event emitted:**
```json
{
  "stage": "ticket",
  "trace_id": "f47ac10b-...",
  "status": "success",
  "duration_ms": 312,
  "metadata": {
    "trello_card_id": "6471abc123",
    "mock": false
  }
}
```

---

### 4. NotifyAgent

**Role:** External communication. Dispatches pre-formatted messages to Slack and email.

**Responsibility boundary:**
- Does NOT generate technical content
- Receives message payloads from other agents and dispatches them
- Handles multiple notification types: `team_alert`, `reporter_confirmation`, `reporter_resolution`

**Input:** `incident_id`, `notification_type`, `ticket_result`

**Output:** `NotificationLog` entry per channel

**Channels:**
- **Slack:** POST to `SLACK_WEBHOOK_URL` → #incidents channel
- **Email:** SendGrid API → reporter's email (or mock log if `MOCK_EMAIL=true`)

**Observability event emitted:**
```json
{
  "stage": "notify",
  "trace_id": "f47ac10b-...",
  "status": "success",
  "duration_ms": 187,
  "metadata": {
    "slack_sent": true,
    "email_sent": true,
    "notification_type": "reporter_confirmation",
    "mock": false
  }
}
```

---

### 5. ResolutionWatcher

**Role:** Closure detection. Polls Trello every 60 seconds to detect resolved incidents.

**Responsibility boundary:**
- Does NOT notify directly — delegates to NotifyAgent
- Does NOT modify Trello cards
- Only reads card status from Trello API

**Mechanism:** Background thread running alongside FastAPI. Queries cards in the "Done" list every `RESOLUTION_WATCHER_INTERVAL_SECONDS` (default: 60).

**Observability event emitted:**
```json
{
  "stage": "resolved",
  "trace_id": "f47ac10b-...",
  "status": "success",
  "duration_ms": 89,
  "metadata": {
    "trello_card_id": "6471abc123",
    "resolution_detected_at": "2026-04-09T16:45:00Z"
  }
}
```

---

## Orchestration Model

```
FastAPI Application Server
│
├── POST /api/incidents (sync)
│   ├── IngestAgent.process(request) → incident_id + trace_id
│   ├── Returns HTTP 201 immediately to client
│   └── BackgroundTask: run_pipeline(incident_id)
│           ├── TriageAgent.process(incident_id) → triage_result
│           ├── TicketAgent.process(triage_result) → ticket
│           └── NotifyAgent.process(ticket, "team_alert" + "reporter_confirmation")
│
└── Background Thread: ResolutionWatcher
        └── Poll loop (every 60s) → NotifyAgent.process(incident, "reporter_resolution")
```

**Key design decision:** HTTP 201 is returned immediately after ingestion. The analysis pipeline runs asynchronously as a background task. This avoids frontend timeouts when LLM calls take several seconds.

---

## Observability Architecture

### End-to-End Trace

Every agent imports `from src.observability import emit_event`. The `trace_id` assigned at ingestion flows unmodified through all agents:

```
ingest (45ms) → triage (2341ms) → ticket (312ms) → notify (187ms) → resolved (89ms)
    └─────────────────────────── trace_id: f47ac10b-... ──────────────────────────┘
```

### Output Destinations
1. **stdout** — visible in `docker compose logs`
2. **`logs/agent.log`** — persistent file (Docker volume: `./logs:/app/logs`)
3. **SQLite `observability_events` table** — queryable via API

### Evidence Endpoint
```
GET /api/observability/events?trace_id=f47ac10b-...
```
Returns all events for a single incident in chronological order, showing the complete pipeline trace.

---

## Safety Measures

### Prompt Injection Protection

Implemented in `IngestAgent` **before** any LLM call:

```python
# src/guardrails.py
INJECTION_PATTERNS = [
    r"ignore\s+(previous|all|prior)",
    r"disregard\s+(all|previous|instructions)",
    r"you\s+are\s+now",
    r"act\s+as\s+if",
    r"pretend\s+you\s+are",
    r"forget\s+your\s+(instructions|training)",
    r"jailbreak",
    r"reveal\s+your\s+system\s+prompt",
    r"bypass\s+(safety|filter|guardrail)",
    r"\bDAN\b",
]
```

If any pattern matches (case-insensitive): HTTP 400 returned, no LLM call made, attempt logged in observability.

**Demonstrated in AC7:** Input with "ignore previous instructions" → HTTP 400, no `stage=triage` event in logs.

### Responsible AI Implementation

| Principle | Implementation | Verification |
|---|---|---|
| **Fairness** | Triage based solely on technical content — `reporter_email` excluded from LLM prompt | Inspect `src/agents/triage_agent.py` prompt construction |
| **Transparency** | Every `TriageResult` includes `confidence_score` (0-1) and full `technical_summary` | `GET /api/incidents/:id` exposes triage reasoning |
| **Accountability** | Every agent action has an observability event with `trace_id` | `GET /api/observability/events` |
| **Privacy** | `reporter_email` not sent to LLM, only to notification services | `src/agents/triage_agent.py` |
| **Security** | API keys only in `.env`, not in code. MIME type validation on uploads. Input length limited. | `.env.example`, `src/guardrails.py` |

---

## Known Limitations

1. **Guardrails are first-level only.** Regex-based injection detection can be bypassed by sophisticated encoding or obfuscation. Production hardening would use LLM-as-judge for secondary validation.

2. **ResolutionWatcher uses polling, not webhooks.** Introduces up to 60 seconds of latency in resolution notification. Trello webhook endpoint (`POST /api/webhooks/trello`) is implemented and ready — webhook configuration in Trello is the only missing step.

3. **Deduplication not implemented.** Identical or similar incidents create separate Trello cards. A post-MVP improvement would use semantic similarity to detect duplicates before ticket creation.

4. **Medusa.js context is file-based, not vectorized.** The agent reads specific files via `read_ecommerce_file()`. A vector database (ChromaDB, Pinecone) would enable semantic search over the entire codebase for more accurate triage.

5. **Single-tenant.** The MVP supports one Trello board and one Slack channel. Multi-tenant support (multiple teams, boards, routing rules) is designed but not implemented.
