# Backend Instructions

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
- Implement from clear contracts.
- Keep business rules, data access, and transport separate.
- Add input validation and explicit error handling.
- Include unit tests for business logic.
- If you change contracts, update technical documentation.

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