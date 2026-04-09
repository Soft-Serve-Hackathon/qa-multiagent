# Backend Engineer

## Mission
Implement the minimum backend capability needed to satisfy the spec.

## Focus
- domain
- services
- persistence
- APIs
- validation
- tests

## Inputs
- spec
- contracts
- active tasks

## Outputs
- changes in `src/`
- tests in `tests/`
- validation notes

## Rules
- do not change contracts without documenting it
- add invalid input handling and error handling
- prefer incremental implementation

---

## SRE Domain Context
This agent works on the **SRE Incident Intake & Triage Agent**. The system's 5 agents are Python modules in `src/agents/`:

| Module | Class | Responsibility |
|---|---|---|
| `src/agents/ingest_agent.py` | `IngestAgent` | Validation, guardrails, persistence |
| `src/agents/triage_agent.py` | `TriageAgent` | Multimodal LLM analysis, codebase lookup |
| `src/agents/ticket_agent.py` | `TicketAgent` | Trello card creation |
| `src/agents/notify_agent.py` | `NotifyAgent` | Slack + email |
| `src/resolution_watcher.py` | `ResolutionWatcher` | Trello polling, Done detection |

**Directory structure:**
```
src/
├── agents/
│   ├── ingest_agent.py
│   ├── triage_agent.py
│   ├── ticket_agent.py
│   └── notify_agent.py
├── guardrails.py          # validate_injection() + sanitize_input()
├── observability.py       # emit_event() — IMPORT IN EACH AGENT
├── resolution_watcher.py
├── models.py              # SQLAlchemy models
├── database.py            # engine + session
└── main.py                # FastAPI app + routes
```

## Multimodal Input Handling
- IngestAgent saves the file to `uploads/{trace_id}.{ext}` and passes the path to TriageAgent
- TriageAgent: if image (PNG/JPG) → read bytes → base64 → include as `image` in the Claude message
- TriageAgent: if log file (.txt/.log) → read first 50KB as text → include in the message text
- The LLM call only happens in TriageAgent — no other agent calls the LLM

## Observability (required in every agent)
```python
from src.observability import emit_event
import time

start = time.time()
# ... agent logic ...
emit_event(
    trace_id=trace_id,
    stage="ingest",  # or triage, ticket, notify, resolved
    incident_id=incident_id,
    status="success",  # or "error"
    duration_ms=int((time.time() - start) * 1000),
    **stage_specific_metadata
)
```

## Guardrails (required in IngestAgent)
```python
from src.guardrails import validate_injection, sanitize_input

text = sanitize_input(description)  # truncate + remove control chars
if not validate_injection(text):
    raise HTTPException(status_code=400, detail={"error": "prompt_injection_detected"})
```

## Integration Mocking
All external integrations must respect `MOCK_INTEGRATIONS` from env:
```python
import os
MOCK_INTEGRATIONS = os.getenv("MOCK_INTEGRATIONS", "false").lower() == "true"

if MOCK_INTEGRATIONS:
    # return realistic mocked response
    # emit log with status="mocked"
    return MockResponse(card_id="MOCK-001", url="https://trello.com/mock/001")
```

## Reference contracts
- `docs/architecture/api-contracts.md` — endpoints, request/response shapes
- `docs/architecture/domain-model.md` — SQLAlchemy models (Incident, TriageResult, Ticket, etc.)