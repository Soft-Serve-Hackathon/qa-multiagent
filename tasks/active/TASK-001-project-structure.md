# Task: TASK-001 — Project Structure & Docker Base

## Goal
Crear la estructura de directorios del proyecto y los archivos Docker base. Esta tarea es P0 — nada más puede implementarse sin ella.

## Source
- spec: `docs/specs/mvp/spec.md` (FR13, AC8)
- architecture: `docs/architecture/system-overview.md`
- acceptance criteria: AC8 — `docker compose up --build` debe funcionar

## Scope
- Crear todos los directorios del proyecto
- Crear `Dockerfile` base para la app Python + FastAPI
- Crear `docker-compose.yml` con todos los servicios y volúmenes
- Crear `requirements.txt` con dependencias
- Crear `src/main.py` con el esqueleto de FastAPI y el endpoint GET /api/health
- Crear `src/database.py` con configuración de SQLAlchemy + SQLite
- Crear `src/models.py` con todos los modelos del domain model

## Directorios a crear
```
src/
├── agents/
├── frontend/
data/           # SQLite DB (volumen Docker)
logs/           # logs de observability (volumen Docker)
uploads/        # archivos adjuntos temporales (volumen Docker)
tests/
```

## Out of Scope
- Implementación de los agentes (TASK-002 a TASK-006)
- Frontend HTML (TASK-007)
- Clonar Medusa.js (TASK-010)

## Files Likely Affected
- `Dockerfile` (nuevo)
- `docker-compose.yml` (nuevo)
- `requirements.txt` (nuevo)
- `src/main.py` (nuevo)
- `src/database.py` (nuevo)
- `src/models.py` (nuevo)
- `.gitignore` (nuevo o modificar)

## Constraints
- Python 3.11
- FastAPI + Uvicorn
- SQLAlchemy 2.x con SQLite
- Docker Compose v2 syntax (`services:` sin `version:`)
- Solo exponer el puerto definido en `APP_PORT` (default 3000)
- Los volúmenes `./data`, `./logs`, `./uploads` deben estar en `.gitignore`

## Validation Commands
```bash
docker compose up --build
curl http://localhost:3000/api/health
# Expected: {"status": "ok", "version": "1.0.0", ...}
```

## Done Criteria
- [ ] `docker compose up --build` levanta sin errores
- [ ] `GET /api/health` retorna HTTP 200 con `{"status": "ok"}`
- [ ] Directorios `src/`, `data/`, `logs/`, `uploads/`, `tests/` existen
- [ ] Modelos SQLAlchemy definidos para: Incident, TriageResult, Ticket, NotificationLog, ObservabilityEvent
- [ ] `.gitignore` incluye: `.env`, `data/`, `logs/`, `uploads/`, `__pycache__/`, `*.db`

## Risks
- Si Medusa.js se clona en este Dockerfile, el build puede ser lento. Mitigación: separar el clone de Medusa.js en TASK-010, usando multi-stage build o un servicio separado.

## Handoff
Next recommended role: Backend Engineer (TASK-002 — IngestAgent)
Notes: Una vez que el health check funciona y los modelos están definidos, el Backend Engineer puede empezar TASK-002 en paralelo con otras tareas.
