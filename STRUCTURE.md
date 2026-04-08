# SRE Incident Intake & Triage Agent - Monorepo Structure

**Multi-agent system for automated incident triage using Claude AI and integrations with Trello, Slack, and SendGrid.**

## 📁 Monorepo Layout

```
project-root/
├── backend/                           # Python FastAPI Backend (Clean Architecture)
│   ├── src/
│   │   ├── main.py                   # FastAPI app entry point + router
│   │   ├── config.py                 # Environment & configuration
│   │   ├── agents/                   # 5 specialized task agents
│   │   │   ├── ingest_agent.py       # Gateway: validation + injection detection
│   │   │   ├── triage_agent.py       # Core: Claude LLM + tool calls to Medusa.js
│   │   │   ├── ticket_agent.py       # Integration: create Trello cards
│   │   │   ├── notify_agent.py       # Communication: Slack + SendGrid
│   │   │   └── resolution_watcher.py # Monitoring: background Trello polling
│   │   ├── api/                      # HTTP API Layer (REST contracts)
│   │   │   ├── routes.py             # FastAPI routes (/api/incidents, health, observability)
│   │   │   └── models.py             # Pydantic request/response schemas
│   │   ├── application/              # Application Layer (Use Cases)
│   │   │   ├── create_incident_use_case.py   # Ingest → validate → persist
│   │   │   ├── triage_incident_use_case.py   # Triage → enrich → update status
│   │   │   ├── ticket_creation_use_case.py   # Create Trello card + link
│   │   │   ├── notify_incident_use_case.py   # Dispatch notifications
│   │   │   └── dto.py                        # Data Transfer Objects
│   │   ├── domain/                   # Domain Layer (Business Logic)
│   │   │   ├── entities.py           # SQLAlchemy models
│   │   │   │   ├── Incident
│   │   │   │   ├── TriageResult
│   │   │   │   ├── Ticket
│   │   │   │   ├── NotificationLog
│   │   │   │   └── ObservabilityEvent
│   │   │   ├── value_objects.py      # TraceId (UUID), Severity, Priority
│   │   │   ├── exceptions.py         # Domain exceptions
│   │   │   └── enums.py              # IncidentStatus, NotificationType, etc
│   │   ├── infrastructure/           # Infrastructure Layer (External Services)
│   │   │   ├── database.py           # SQLAlchemy + SQLite
│   │   │   ├── file_storage.py       # File upload + MIME validation
│   │   │   ├── llm/
│   │   │   │   ├── client.py         # Anthropic Claude wrapper
│   │   │   │   └── tools.py          # Claude tool definitions (read_ecommerce_file)
│   │   │   ├── external/
│   │   │   │   ├── trello_client.py  # Trello API client
│   │   │   │   ├── slack_client.py   # Slack webhook client
│   │   │   │   └── sendgrid_client.py # SendGrid email client
│   │   │   └── observability/
│   │   │       ├── logger.py         # JSON structured logging (trace_id)
│   │   │       └── events.py         # ObservabilityEvent schema
│   │   └── shared/                   # Shared Utilities Layer
│   │       ├── security.py           # Prompt injection detection + sanitization
│   │       ├── validators.py         # Input validation (email, file size, etc)
│   │       └── utils.py              # Helper functions
│   ├── tests/                        # Test Suite
│   │   ├── unit/                     # Unit tests (agents, domain, validators)
│   │   └── integration/              # Integration tests (API, pipeline, observability)
│   ├── requirements.txt              # Python dependencies (FastAPI, SQLAlchemy, Anthropic, etc)
│   ├── Dockerfile                    # Multi-stage Python build for FastAPI
│   ├── .env.example                  # Backend environment template
│   └── .dockerignore                 # Docker build optimization
│
├── frontend/                          # Next.js Frontend (TypeScript + Tailwind CSS)
│   ├── app/                          # Next.js App Router
│   │   ├── page.tsx                  # Home page (state machine: form → tracking → error)
│   │   ├── layout.tsx                # Root layout with metadata
│   │   ├── globals.css               # Global Tailwind styles + custom utilities
│   │   └── components/
│   │       ├── IncidentForm.tsx      # Form component (validation, FormData, POST)
│   │       ├── StatusTracker.tsx     # Status polling (5s interval, timeline visualization)
│   │       └── ui/
│   │           └── FormInput.tsx     # Reusable input component
│   ├── lib/
│   │   └── api.ts                    # Axios client (submitIncident, getIncidentStatus)
│   ├── public/
│   │   └── favicon.ico               # App icon
│   ├── package.json                  # Node dependencies (Next.js, React, Tailwind, Axios)
│   ├── tsconfig.json                 # TypeScript configuration
│   ├── tailwind.config.js            # Tailwind CSS theme
│   ├── postcss.config.js             # PostCSS setup
│   ├── next.config.js                # Next.js config (rewrites for API proxy)
│   ├── .eslintrc.json                # ESLint rules
│   ├── Dockerfile                    # Multi-stage Node build + Next.js standalone
│   ├── README.md                     # Frontend documentation
│   ├── .gitignore                    # Node-specific ignores
│   └── .env.example                  # Environment variables template
│
├── docker-compose.yml                # Service orchestration (backend + frontend)
│                                      # Ports: backend on 8000, frontend on 3000
│                                      # Network: qa-network (internal DNS)
│                                      # Volumes: data/, logs/, uploads/
│
├── .env.example                      # Root environment template (shared config)
├── .gitignore                        # Git ignore patterns
│
├── docs/                             # Documentation
│   ├── architecture/                 # ADRs, API contracts, domain models
│   ├── specs/                        # Functional specifications
│   ├── idea/                         # Problem statements, open questions
│   └── quality/                      # Definition of Done
│
├── data/                             # Volume: SQLite database (incidents.db)
├── logs/                             # Volume: JSON structured logs
├── uploads/                          # Volume: Customer file uploads
│
└── tasks/                            # Implementation tasks
    ├── active/                       # Current sprint work
    └── done/                         # Completed tasks
```

## 🏗️ Clean Architecture Layers

Backend follows **Clean Architecture** with 5 concentric rings:

```
                  ┌─────────────────────┐
                  │   Presentation      │  (API routes, HTTP models)
                  │   (routes.py,       │
                  │    models.py)       │
                  ├─────────────────────┤
                  │  Application        │  (Use cases, DTOs)
                  │  (use_case*.py,     │
                  │   dto.py)           │
                  ├─────────────────────┤
                  │  Domain             │  (Entities, enums, exceptions)
                  │  (entities.py,      │
                  │   value_objects.py) │
                  ├─────────────────────┤
                  │  Infrastructure     │  (DB, LLM, external APIs)
                  │  (database.py,      │
                  │   llm/, external/)  │
                  └─────────────────────┘
                  ↓
                  Shared Utilities
                  (security, validators, utils)
```

**Vertical Slices (Agents):** 5 specialized agents that cut through all layers:
- `ingest_agent.py` → Validates, detects injection, persists
- `triage_agent.py` → Calls Claude, enriches data
- `ticket_agent.py` → Creates Trello card
- `notify_agent.py` → Sends Slack + email
- `resolution_watcher.py` → Monitors Trello for completion

## 🐳 Docker & Orchestration

### Container Images

1. **Backend** (`backend/Dockerfile`)
   - Base: `python:3.11-slim`
   - Exposes: port 8000
   - Health check: `curl http://localhost:8000/api/health`
   - Cmd: `python -m uvicorn src.main:app --host 0.0.0.0 --port 8000`

2. **Frontend** (`frontend/Dockerfile`)
   - Base: `node:20-alpine`
   - Exposes: port 3000
   - Health check: `node -e "require('http').get(...)"`
   - Cmd: `node server.js` (Next.js standalone server)

### Service Communication

```
User Browser
    │
    ├─→ Frontend (Next.js:3000)
    │        │
    │        ├─→ React components (IncidentForm, StatusTracker)
    │        └─→ API Client (axios) → http://backend:8000/api/*
    │
    └─→ Backend (fastapi:8000) ←─ Internal network only
         │
         ├─→ SQLite (data/incidents.db)
         ├─→ Anthropic Claude API
         ├─→ Trello REST API
         └─→ Slack + SendGrid (external)
```

**Network:** `qa-network` (bridge driver)
- Frontend can reach backend at `http://backend:8000`
- Both isolated from external networks by default

### Volumes (Persistent Data)

| Volume | Mount Path | Purpose |
|--------|-----------|---------|
| `data/` | `/app/data` | SQLite database (incidents.db) |
| `logs/` | `/app/logs` | JSON structured logs |
| `uploads/` | `/app/uploads` | Customer file uploads |

### Environment Variables

**Backend (.env)**
- `DATABASE_URL` → SQLite path
- `ANTHROPIC_API_KEY` → Claude authentication
- `TRELLO_KEY`, `TRELLO_TOKEN` → Trello credentials
- `SLACK_WEBHOOK_URL` → Slack incoming webhook
- `SENDGRID_API_KEY` → SendGrid authentication
- `LOG_LEVEL` → info | debug | warning
- `DEBUG` → true | false

## 🧪 Testing Strategy

### Unit Tests (`backend/tests/unit/`)
- Agent business logic (IngestAgent, TriageAgent, etc)
- Domain validation (entities, value objects)
- Security guardrails (injection detection, sanitization)
- Validators (email, file size, character count)

### Integration Tests (`backend/tests/integration/`)
- Full API endpoint flows (POST /api/incidents)
- End-to-end pipeline (ingest → triage → ticket → notify)
- Observability trace_id consistency across all agents
- External service mocks (LLM, Trello, Slack, SendGrid)

### Test Fixtures (`backend/tests/conftest.py`)
- Mock Anthropic Claude client
- Mock Trello API client
- Mock Slack webhook client
- Mock SendGrid email client

## 🚀 Build & Deploy

### Local Development

```bash
# Start all services
docker-compose up --build

# Access endpoints
curl http://localhost:8000/api/health          # Backend health
curl http://localhost:3000                      # Frontend
```

### Production Deployment

1. Build images: `docker build -t backend:latest ./backend`
2. Push to registry (ECR, DockerHub, etc)
3. Deploy via: docker-compose, Kubernetes, ECS, etc
4. Ensure volumes mounted for data persistence
5. Set production `.env` variables

## 📊 Data Flow

### Incident Intake Flow

```
1. User submits form (Frontend)
   └─→ POST /api/incidents (title, description, file, email)

2. IngestAgent validates
   ├─→ Check injection patterns
   ├─→ Validate email format
   ├─→ Check file size/MIME
   └─→ Generate TraceId (UUID v4)

3. Persist to SQLite
   └─→ Create Incident entity + ObservabilityEvent

4. TriageAgent enriches
   ├─→ Call Claude LLM
   ├─→ Use read_ecommerce_file tool for context
   └─→ Store TriageResult

5. TicketAgent creates Trello card
   ├─→ POST /1/cards (Trello API)
   └─→ Link ticket_id to incident

6. NotifyAgent dispatches
   ├─→ POST to Slack webhook
   └─→ POST to SendGrid email API

7. Frontend polls for status
   └─→ GET /api/incidents/{trace_id} every 5s until resolved
```

## 🔐 Security Boundaries

**Ingest Agent Guardrails:**
- Prompt injection detection (10+ regex patterns)
- File size limits (10MB max)
- MIME type validation (image/plain-text only)
- Email regex validation

**API Security:**
- CORS disabled by default (frontend on same network)
- Rate limiting ready (can add via middleware)
- Input validation at API layer (Pydantic)

## 📈 Scalability Roadmap

### Phase 1 (MVP)
- SQLite (current)
- Single FastAPI instance
- Synchronous task execution

### Phase 2 (Growth)
- PostgreSQL (replace SQLite)
- Redis caching for poll responses
- Async task queue (Celery/RQ)

### Phase 3 (Scale)
- Load balancer (nginx, HAProxy)
- Multiple FastAPI replicas
- Distributed tracing (Jaeger)

### Phase 4 (Enterprise)
- Kubernetes orchestration
- Auto-scaling based on queue depth
- Vault for secrets management

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
