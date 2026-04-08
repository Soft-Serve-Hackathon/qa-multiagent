# Monorepo Structure - SRE Incident Triage Agent

## 📁 Estructura General

```
.
├── backend/                          # FastAPI Backend (Python)
│   ├── src/
│   │   ├── main.py                  # FastAPI app entry point
│   │   ├── config.py                # Configuration management
│   │   ├── agents/                  # 5 specialized agents
│   │   │   ├── ingest_agent.py
│   │   │   ├── triage_agent.py
│   │   │   ├── ticket_agent.py
│   │   │   ├── notify_agent.py
│   │   │   └── resolution_watcher.py
│   │   ├── api/                     # FastAPI routes & models
│   │   │   ├── routes.py
│   │   │   └── models.py
│   │   ├── application/             # Use cases (Clean Architecture)
│   │   ├── domain/                  # Domain models & entities
│   │   ├── infrastructure/          # External services & persistence
│   │   │   ├── database.py
│   │   │   ├── llm/
│   │   │   ├── external/            # Trello, Slack, SendGrid
│   │   │   └── observability/       # Logging & tracing
│   │   └── shared/                  # Utilities & security
│   ├── requirements.txt             # Python dependencies
│   ├── Dockerfile                   # Backend container image
│   ├── .env.example                 # Environment template
│   ├── .dockerignore                # Docker build optimization
│   └── tests/
│       ├── unit/
│       └── integration/
│
├── frontend/                         # Vanilla HTML/CSS/JS (Nginx)
│   ├── src/
│   │   ├── static/
│   │   │   ├── index.html           # Form & dashboard UI
│   │   │   ├── style.css            # Styling
│   │   │   └── favicon.ico
│   │   ├── js/
│   │   │   ├── app.js               # Main orchestration
│   │   │   ├── form-handler.js      # Form submission & validation
│   │   │   └── status-tracker.js    # Real-time polling
│   │   └── assets/                  # Images & fonts
│   ├── Dockerfile                   # Frontend container image (Nginx)
│   └── .dockerignore
│
├── docker-compose.yml               # Service orchestration
├── .env.example                     # Root environment template
├── .gitignore                       # Git ignore rules
│
├── docs/                            # Architecture & specifications
├── data/                            # Volume: SQLite database
├── logs/                            # Volume: Application logs
├── uploads/                         # Volume: File uploads
└── ...
```

## 🚀 Principios de Diseño

### Clean Architecture en Backend

Cada carpeta en `backend/src/` representa una capa:

1. **API Layer** (`api/`) → HTTP contracts & Pydantic models
2. **Application Layer** (`application/`) → Use cases & DTOs
3. **Domain Layer** (`domain/`) → Entities, enums, business rules
4. **Infrastructure Layer** (`infrastructure/`) → Database, LLM, external APIs
5. **Shared** (`shared/`) → Cross-cutting concerns (security, validators, utils)
6. **Agents** (`agents/`) → Specialized task agents (vertical slices)

### Separación de Responsabilidades

**Backend:**
- FastAPI on port `8000`
- Manages business logic, persistence, external integrations
- Stateless (state in SQLite)

**Frontend:**
- Nginx on port `3000`
- Vanilla HTML/CSS/JS (no framework dependencies)
- Proxies API calls to backend via nginx `proxy_pass`
- Real-time polling for incident status (trace_id visibility)

## 🐳 Docker Orchestration

### Build & Run

```bash
# Build all services
docker-compose build

# Start services (both backend and frontend)
docker-compose up

# Verify both are running
curl http://localhost:8000/api/health        # Backend
curl http://localhost:3000                    # Frontend
```

### Environment Variables

Copy `.env.example` to `.env` and update:

```bash
cp .env.example .env
```

Each service can have its own `.env.example`:
- `backend/.env.example` → Backend-specific config
- Root `.env.example` → Shared across compose stack

### Network

Both services communicate via named network `qa-network`:
- Backend: `http://backend:8000` (internal DNS)
- Frontend: `http://backend:8000/api/...` (via nginx reverse proxy)

### Volumes

Persistent data:
- `data/` → SQLite incidents database
- `logs/` → JSON structured logs
- `uploads/` → Customer files (screenshots, logs)

## 📋 Development Workflow

### Prerequisites
- Docker & Docker Compose v2+
- (Optional) Python 3.11 for local dev

### Running Locally

```bash
# Without Docker (local Python)
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Frontend: Use any HTTP server
python -m http.server 3000 --directory frontend/src
```

### With Docker

```bash
docker-compose up --build
```

Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/docs (Swagger)
- Health check: http://localhost:8000/api/health

## 🔧 Adding New Features

### New Backend Endpoint

1. Define model in `backend/src/api/models.py`
2. Create use case in `backend/src/application/`
3. Add route in `backend/src/api/routes.py`
4. Add tests in `backend/tests/`

### New Frontend Page

1. Create component in `frontend/src/js/`
2. Add HTML in `frontend/src/static/index.html`
3. Style in `frontend/src/static/style.css`

## 📝 Conventions

- **Python:** Follow PEP-8, use type hints
- **API:** REST conventions, JSON responses
- **Frontend:** Vanilla JS (no frameworks), progressive enhancement
- **Commits:** Small, atomic, focused on single concern
- **Documentation:** Update when architecture changes

## 🧪 Testing

```bash
# Backend unit tests
cd backend
pytest tests/unit -v

# Backend integration tests
pytest tests/integration -v

# Frontend: Manual validation + screenshots
```

## 🔗 Related Documents

- Architecture decisions: [`docs/architecture/`](../docs/architecture/)
- Specifications: [`docs/specs/`](../docs/specs/)
- Implementation tasks: [`tasks/`](../tasks/)
- Problem statement: [`docs/idea/problem-statement.md`](../docs/idea/problem-statement.md)
