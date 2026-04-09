# Task: TASK-009 — Docker Setup & Validation

## Goal
Crear `docker-compose.yml` funcional que levante el stack completo (backend FastAPI, frontend, base de datos, volúmenes) y pasar validación `docker compose up --build` sin errores.

## Source
- spec: `docs/specs/mvp/spec.md` (FR13, AC8)
- architecture: `docs/architecture/system-overview.md`
- acceptance criteria: AC8 — `docker compose up --build` debe funcionar

## Scope
- Crear `docker-compose.yml` v2+ con servicios: backend, frontend, sqlite (volúmenes)
- Crear `Dockerfile` final para el backend (basado en TASK-001)
- Crear `Dockerfile` para el frontend (nginx serving html + proxy /api)
- Configurar volúmenes: `./data` (SQLite DB), `./logs` (agent logs), `./uploads` (archivos adjuntos temporales)
- Configurar health checks para backend (`GET /api/health`)
- Configurar variables de entorno desde `.env` o defaults documentados
- Soportar `MOCK_INTEGRATIONS=true` para ejecución sin credenciales reales
- Documentar en comentarios por qué cada volumen/variable es necesario

## Out of Scope
- Orquestación Kubernetes
- Certificados SSL/TLS
- Swagger/OpenAPI servido en `/docs`

## Files Likely Affected
- `docker-compose.yml` (nuevo)
- `Dockerfile` (nuevo o refinado de TASK-001)
- `Dockerfile.frontend` (nuevo)
- `nginx.conf` (nuevo, para frontend)
- `.env` (incluido en .gitignore, usuario debe crear a partir de `.env.example`)
- `.dockerignore` (nuevo)

## Constraints
- Docker Compose v2 syntax (sin `version: '3'`)
- Backend expone puerto `APP_PORT` (default 3000)
- Frontend expone puerto `FRONTEND_PORT` (default 80)
- Usar Python 3.11 slim image para reducir tamaño
- SQLite en `./data/qa-agent.db` (volumen persistente)
- Logs estructurados en `./logs/agent.log` (volumen)
- Uploads temporales en `./uploads/` (volumen, limpiado cada 24h o por job)
- Health check cada 10 segundos, timeout 5 segundos, 3 intentos fallidos = unhealthy
- Build time target: <5 minutos en máquina de desarrollo

## Validation Commands
```bash
# 1. Build y start
docker compose up --build

# 2. Verificar servicios levantados (en otra terminal)
docker compose ps
# Expected: 2 services (backend + frontend)

# 3. GET /api/health
curl http://localhost:3000/api/health
# Expected: {"status": "ok", "version": "1.0.0", "database": "sqlite", ...}

# 4. GET /
curl http://localhost/
# Expected: HTML del formulario (200 OK)

# 5. Verificar volúmenes
ls -la ./data/qa-agent.db  # Debe existir
ls -la ./logs/agent.log    # Debe existir

# 6. MOCK mode
cp .env.example .env
sed -i '' 's/^MOCK_INTEGRATIONS=false/MOCK_INTEGRATIONS=true/' .env
docker compose down
docker compose up --build
# Debe levantar sin errores incluso sin credenciales Trello/Slack/SendGrid
```

## Done Criteria
- [ ] `docker-compose.yml` existe con servicios backend + frontend
- [ ] `Dockerfile` para backend (Python 3.11, FastAPI, all agents)
- [ ] `Dockerfile.frontend` para frontend (nginx, serving static HTML + proxy `/api`)
- [ ] Health check endpoint `/api/health` responde en <5 segundos
- [ ] Volúmenes creados: `./data`, `./logs`, `./uploads`
- [ ] `.dockerignore` existe y excluye: `.git`, `__pycache__`, `*.pyc`, `.env`, `tasks/`, `docs/`
- [ ] `docker compose up --build` completa sin errores en <5 minutos
- [ ] `GET /api/health` retorna HTTP 200 con JSON valido
- [ ] `GET /` retorna HTML de formulario
- [ ] MOCK_INTEGRATIONS=true funciona sin credenciales externas
- [ ] Logs en `./logs/agent.log` contienen eventos estructurados JSON
- [ ] Frontend proxy a `/api/*` funciona: `curl http://localhost/api/health` retorna el mismo que backend

## Risks
- **Image size:** Python + FastAPI + anthropic SDK puede ser >500MB. Mitigación: usar `python:3.11-slim`, multi-stage build si es necesario.
- **Database lock:** SQLite con múltiples workers puede tener contention. Mitigación: limitar Uvicorn a 1 worker en docker-compose, o usar PostgreSQL en post-MVP.
- **Volume permissions:** `./logs` podría tener permission denied si el container user no coincide con host. Mitigación: crear directorio con `chmod 777` antes del compose, o usar named volume.

## Handoff
Next recommended role: QA Engineer (validar AC8) + Security Engineer (revisar credenciales en env)
Notes: Una vez que este task pasa, todo el stack es ejecutable. Backend engineer puede replicar entorno localmente con `docker compose up`. Importante no pushear `.env` contaminado al repo.
