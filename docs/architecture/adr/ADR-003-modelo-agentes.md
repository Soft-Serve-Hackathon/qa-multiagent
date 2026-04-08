# ADR-003: Modelo de orquestación de agentes

## Status
Accepted

## Context
El sistema requiere coordinar 5 agentes IA especializados que procesan un incidente SRE en secuencia, cada uno con una responsabilidad clara:

1. **IngestAgent** — Validación y detección de injection
2. **TriageAgent** — Análisis con Claude LLM + tool calls a Medusa.js
3. **TicketAgent** — Creación de card en Trello
4. **NotifyAgent** — Notificaciones vía Slack + SendGrid
5. **ResolutionWatcher** — Polling de Trello para detectar resolución

Hay dos enfoques para coordinarlos:

1. **Orquestación via framework** (LangChain, LlamaIndex, CrewAI): abstracciones de alto nivel con memoria, retry automático y herramientas integradas.
2. **Orquestación manual directa**: cada agente es un módulo Python con una función `run()` tipada, y la coordinación la maneja el use case correspondiente.

El riesgo del enfoque con framework es el acoplamiento a APIs inestables entre versiones, overhead de configuración y dificultad de debugging en el contexto de un hackathon con tiempo limitado.

## Decision
**Orquestación manual directa** sin frameworks de agentes en el MVP.

Cada agente es un módulo Python con:
- Una función principal `run(input) -> output` con tipos explícitos (Pydantic / dataclasses)
- El cliente LLM inyectado como dependencia (facilita testing con mocks)
- Sin estado interno persistente entre llamadas — el estado vive en SQLite

La coordinación entre agentes la manejan los **use cases** en `application/`, que llaman a los agentes en el orden correcto:

```python
# Ejemplo: create_incident_use_case.py
async def execute(self, dto: CreateIncidentDTO) -> IncidentResponse:
    # 1. Ingest
    validated = await self.ingest_agent.run(dto)
    incident = await self.repo.save(validated)

    # 2. Triage (async, no bloquea respuesta HTTP)
    asyncio.create_task(self._triage_and_notify(incident))

    return IncidentResponse(trace_id=incident.trace_id, status="received")

async def _triage_and_notify(self, incident: Incident):
    # 3. Triage
    triage_result = await self.triage_agent.run(incident)

    # 4. Ticket
    ticket = await self.ticket_agent.run(incident, triage_result)

    # 5. Notify
    await self.notify_agent.run(incident, triage_result, ticket)
```

**ResolutionWatcher** corre como background task de FastAPI (`BackgroundTask`) con polling periódico a Trello.

## Consequences
**Positivo:**
- Sin dependencias externas de frameworks — el código es Python puro + SDKs oficiales
- Debugging directo: el flujo de datos es explícito y trazable via `trace_id`
- Fácil de testear: cada agente se prueba de forma aislada con mocks del cliente LLM
- Reemplazar Claude por otro modelo solo requiere cambiar el cliente inyectado
- La respuesta HTTP al usuario es inmediata — el triage corre en background

**Negativo:**
- Sin retry automático ni circuit breaker — manejar errores manualmente por agente
- Sin memoria compartida entre agentes — todo el estado pasa por parámetros o SQLite
- El manejo de estado parcial (si falla TicketAgent después de TriageAgent) es responsabilidad del código

**Trade-offs:**
- Se acepta más código boilerplate a cambio de control total, trazabilidad y menor complejidad en el MVP

## Alternatives Considered
- **LangChain**: ecosistema amplio pero API inestable entre versiones — riesgo en hackathon con tiempo limitado
- **CrewAI**: orientado a agentes con roles colaborativos — más expresivo pero over-engineering para flujo secuencial
- **LlamaIndex**: enfocado en RAG y recuperación de documentos — no aplica al flujo de ingesta/triage
- **Celery/RQ**: queue distribuida para los tasks — correcta para Phase 2, innecesaria para MVP con SQLite
