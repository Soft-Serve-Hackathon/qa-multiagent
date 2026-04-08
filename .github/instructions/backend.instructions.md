# Backend Instructions — FastAPI + Python 3.11

## Contexto
Backend del SRE Incident Intake & Triage Agent. Clean Architecture con 5 capas:
`api/` → `application/` (use cases) → `domain/` → `infrastructure/` → `shared/`

Los 5 agentes viven en `backend/src/agents/`:
- `ingest_agent.py` — validación + detección de prompt injection
- `triage_agent.py` — Claude LLM + tool calls a Medusa.js
- `ticket_agent.py` — crea cards en Trello
- `notify_agent.py` — Slack webhook + SendGrid email
- `resolution_watcher.py` — polling de Trello en background

## Reglas

- Implementa siempre a partir de contratos en `docs/architecture/api-contracts.md`.
- Mantén separadas: reglas de negocio (`domain/`), use cases (`application/`), infra (`infrastructure/`).
- Todo input de usuario pasa por `IngestAgent` primero — nunca llames al LLM sin validar.
- Usa `trace_id` (UUID v4) en todos los eventos de observabilidad (`infrastructure/observability/`).
- Los clientes externos (Trello, Slack, SendGrid, Anthropic) viven en `infrastructure/external/` — no los instancies en agentes directamente.
- Agrega tests unitarios en `backend/tests/unit/` para toda lógica de agente o dominio.
- Si cambias contratos de API, actualiza `docs/architecture/api-contracts.md`.
- Variables de entorno: solo via `backend/src/config.py` — nunca hardcodeadas.
