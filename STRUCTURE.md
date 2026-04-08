# SRE Incident Intake & Triage Agent

**Multi-agent system for automated incident triage using Claude AI and integrations with Trello, Slack, and SendGrid.**

## Project Structure

### Backend Architecture (Clean Architecture)

```
src/
├── main.py                    # FastAPI app entry point + router setup
├── config.py                  # Environment config, constants
├── agents/                    # 5 specialized agents
│   ├── ingest_agent.py        # Input validation + prompt injection detection
│   ├── triage_agent.py        # Claude LLM + Medusa.js tool calls
│   ├── ticket_agent.py        # Trello card creation
│   ├── notify_agent.py        # Slack + SendGrid dispatch
│   └── resolution_watcher.py  # Trello polling background task
├── api/                       # HTTP routes (FastAPI)
│   ├── routes.py              # POST /api/incidents, GET /api/incidents/:id, etc
│   └── models.py              # Pydantic request/response schemas
├── domain/                    # Domain logic
│   ├── entities.py            # SQLAlchemy models (Incident, TriageResult, Ticket, etc)
│   ├── value_objects.py       # TraceId, Severity, Priority
│   ├── exceptions.py          # DomainException, PromptInjectionError, etc
│   └── enums.py               # IncidentStatus, NotificationType
├── application/               # Use cases + services
│   ├── create_incident_use_case.py   # Ingest + validate
│   ├── triage_incident_use_case.py   # Triage + update status
│   ├── ticket_creation_use_case.py   # Create Trello card
│   ├── notify_incident_use_case.py   # Send Slack + email
│   └── dto.py                        # Data Transfer Objects
├── infrastructure/            # External services, persistence
│   ├── database.py            # SQLAlchemy setup
│   ├── file_storage.py        # Upload handling
│   ├── llm/
│   │   ├── client.py          # Claude API wrapper
│   │   └── tools.py           # Tool definitions
│   ├── external/
│   │   ├── trello_client.py   # Trello API
│   │   ├── slack_client.py    # Slack webhooks
│   │   └── sendgrid_client.py # SendGrid email
│   └── observability/
│       ├── logger.py          # JSON structured logging
│       └── events.py          # ObservabilityEvent schema
├── shared/                    # Utilities + guardrails
│   ├── security.py            # Prompt injection detection
│   ├── validators.py          # Input validation
│   └── utils.py               # Helper functions
└── frontend/                  # HTML + Vanilla JS
    ├── static/
    │   ├── index.html         # Incident form
    │   └── style.css          # Styling
    └── js/
        ├── app.js             # Main orchestration
        ├── form-handler.js    # Form submission
        └── status-tracker.js  # Polling status updates
```

### Key Directories

| Directory | Purpose | Clean Arch Layer |
|-----------|---------|------------------|
| `agents/` | 5 specialized agents (ingest, triage, ticket, notify, watcher) | Application |
| `domain/` | Core business models, enums, exceptions | Domain |
| `application/` | Use cases, DTOs, service coordination | Application |
| `infrastructure/` | DB, file storage, LLM, external APIs, observability | Infrastructure |
| `api/` | FastAPI routes, Pydantic schemas | Presentation |
| `shared/` | Cross-cutting: guardrails, validators, utils | All layers |
| `frontend/` | HTML form + vanilla JS | Presentation |
| `tests/` | Unit + integration tests | Testing |
| `data/` | SQLite database (Docker volume) | Infrastructure |
| `logs/` | Observability events JSON (Docker volume) | Infrastructure |
| `uploads/` | Temporary file storage (Docker volume) | Infrastructure |

## Quick Start

### Local Development

```bash
# Clone repo
git clone <repo-url>
cd qa-multiagent

# Setup Python environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your Trello, Slack, SendGrid, Anthropic keys

# Run FastAPI server
uvicorn src.main:app --reload --port 8000

# Open browser
open http://localhost:8000
```

### Docker Development

```bash
# Build image
docker build -t qa-multiagent:latest .

# Run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop
docker-compose down
```

## Architecture Decisions

See `docs/architecture/` for:
- **system-overview.md** — 5-agent pipeline, async orchestration
- **domain-model.md** — Core entities (Incident, TriageResult, Ticket, NotificationLog, ObservabilityEvent)
- **api-contracts.md** — OpenAPI specifications for all endpoints
- **adr/** — Architectural decision records (Medusa.js, Trello, Guardrails, etc)

## Testing

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests (requires running app)
pytest tests/integration/ -v

# With coverage
pytest --cov=src tests/ --cov-report=html
```

## Environment Variables

See `.env.example` for all required variables:
- `ANTHROPIC_API_KEY` — Claude API (required)
- `TRELLO_API_KEY`, `TRELLO_API_TOKEN`, `TRELLO_BOARD_ID` — Trello (required unless MOCK_INTEGRATIONS=true)
- `SLACK_WEBHOOK_URL` — Slack (required unless MOCK_INTEGRATIONS=true)
- `SENDGRID_API_KEY` — Email (optional)

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Health check |
| `/api/incidents` | POST | Create incident (multifile upload, text) |
| `/api/incidents/:id` | GET | Get incident details + triage result |
| `/api/observability/events` | GET | Observability logs (trace_id tracking) |

## Logging & Observability

All events logged as JSON to:
- **stdout** — Docker logs
- **data/incidents.db** — SQLite (ObservabilityEvent table)
- **logs/events.jsonl** — File (future)

Each event includes:
- `trace_id` — UUID v4 flows through entire pipeline
- `agent_name` — Which agent processed the event
- `timestamp` — ISO8601
- `level` — INFO, WARNING, ERROR
- `message` — Human-readable description
- `metadata` — Extra context (incident_id, file_count, triage_category, etc)

## Security & Guardrails

All user input validated before reaching LLM:
- **Prompt injection detection** — YAML, JSON, code injection patterns blocked at ingestion
- **File validation** — MIME type checking (magic bytes, python-magic)
- **Rate limiting** — Per-IP throttling (future)
- **Secrets** — No API keys in code, use `.env`

## Deployment

Docker Compose orchestrates:
- **app** — FastAPI + Uvicorn on port 8000
- **db** — SQLite (optional, future PostgreSQL)

Supports:
- `MOCK_INTEGRATIONS=true` — All external APIs return canned responses (no real API calls)
- Health checks every 30s
- Auto-restart on failure

## Contributing

1. Follow Clean Code & Clean Architecture principles
2. Keep agents small and focused (single responsibility)
3. All business logic in `domain/` or `application/`
4. All external service calls in `infrastructure/`
5. Write tests for new features (`tests/unit/` + `tests/integration/`)
6. Commit early and often with clear messages
