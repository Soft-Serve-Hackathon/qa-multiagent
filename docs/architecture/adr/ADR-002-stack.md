# ADR-002: Stack tecnológico del sistema

## Status
Accepted

## Context
El sistema es un agente multi-agente de ingesta y triage de incidentes SRE para una aplicación e-commerce (Medusa.js). Necesita:
- Recibir reportes multimodales (texto + imagen/log) vía formulario web
- Procesar los reportes con un LLM (Claude) y herramientas de contexto
- Crear cards en Trello, notificar vía Slack y email
- Monitorear resolución de incidentes (polling)
- Correr localmente y en cualquier entorno con Docker Compose

Las opciones evaluadas consideraron el ecosistema de SDKs disponibles para Anthropic, Trello, Slack y SendGrid, y la capacidad de entregar un MVP funcional en el contexto del AgentX Hackathon de SoftServe.

## Decision

### Backend
**Python 3.11+** con **FastAPI** como framework HTTP.

- Framework HTTP: `fastapi` + `uvicorn` (ASGI server)
- ORM: `sqlalchemy` + `aiosqlite` (SQLite en MVP, reemplazable por PostgreSQL)
- LLM: `anthropic` SDK oficial (Claude claude-sonnet-4-6)
- Integraciones externas: `httpx` para Trello REST API, Slack webhooks, SendGrid
- Validación de archivos: `python-magic` (MIME type detection)
- Testing: `pytest` + `pytest-mock` + `httpx` (test client)
- Variables de entorno: `python-dotenv`
- Gestión de dependencias: `pip` + `requirements.txt`

### Frontend
**Next.js 14** con **TypeScript** y **Tailwind CSS**.

- Framework: Next.js 14 (App Router)
- Lenguaje: TypeScript
- Estilos: Tailwind CSS
- HTTP client: Axios
- Comunicación con backend: proxy via `next.config.js` rewrites → `http://backend:8000`

### Infraestructura
- Orquestación local: **Docker Compose** (backend:8000, frontend:3000)
- Red interna: `qa-network` (bridge driver)
- Persistencia: SQLite (Docker volume `data/`)
- Logs: JSON estructurado a `logs/` (Docker volume)
- Uploads: archivos temporales en `uploads/` (Docker volume)

## Consequences
**Positivo:**
- Python tiene SDKs oficiales de primera clase para Anthropic y los servicios de integración
- FastAPI genera documentación OpenAPI automática — útil para evaluadores del hackathon
- Next.js 14 con App Router permite frontend reactivo sin complejidad excesiva
- Docker Compose simplifica el setup: un solo `docker-compose up --build`
- SQLite elimina la necesidad de un servicio de base de datos separado en MVP

**Negativo:**
- SQLite no es apto para producción con múltiples instancias — mitigar en Phase 2 con PostgreSQL
- Sin tipado estático estricto en Python por defecto — mitigar con type hints en todo el código
- Next.js agrega un proceso adicional al compose vs un frontend estático

**Trade-offs:**
- Se prefiere velocidad de entrega y experiencia del equipo sobre optimización de infra en MVP

## Alternatives Considered
- **Flask**: más simple que FastAPI pero sin generación de docs automática ni validación Pydantic nativa
- **Node.js/Express (backend)**: buen soporte de SDKs pero ecosistema Python es superior para agentes IA
- **HTML vanilla (frontend)**: sin build step pero sin type safety ni componentes reutilizables
- **PostgreSQL**: más robusto pero requiere servicio adicional — innecesario para el MVP del hackathon
