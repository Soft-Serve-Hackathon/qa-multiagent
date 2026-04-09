# Documentation Instructions

## Mission
Translate the MVP spec into a minimal, coherent, and scalable technical solution.

## Focus
- core architecture
- system boundaries
- contracts
- trade-offs
- technical risks

## Inputs
- `docs/specs/mvp/`
- `docs/idea/`

## Outputs
- `docs/architecture/system-overview.md`
- `docs/architecture/domain-model.md`
- `docs/architecture/api-contracts.md`
- ADRs if applicable

## Rules
- prioritize simplicity for the MVP
- do not overarchitect
- make trade-offs explicit
- Use clear, verifiable language.
- Do not mix product decisions with architecture decisions.
- Maintain traceability between idea, spec, task, and change.
- If you add an important decision, reference the affected file and the reason.

---

## SRE Domain Context
This agent works on the **SRE Incident Intake & Triage Agent** for the SoftServe AgentX Hackathon.

**Core system pipeline:**
```
IngestAgent → TriageAgent → TicketAgent → NotifyAgent
                                           ↑
                          ResolutionWatcher (background)
```

**Decided technical stack:**
- LLM: Claude claude-sonnet-4-6 (native multimodal)
- Backend: Python 3.11 + FastAPI
- Ticketing: Trello REST API (key + token)
- Communicator: Slack Incoming Webhooks
- E-commerce base: Medusa.js (medusajs/medusa)
- Persistence: SQLite + SQLAlchemy
- Deployment: Docker + Docker Compose (required)

**Active ADRs — read before making decisions:**
- ADR-001: Medusa.js as e-commerce repo → `docs/architecture/adr/ADR-001-ecommerce-repo.md`