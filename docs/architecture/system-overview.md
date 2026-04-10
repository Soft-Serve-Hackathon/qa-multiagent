# System Overview — SRE Incident Intake & Triage Agent

**Version:** 1.0  
**Owner:** Architect  
**Last updated:** 2026-04-09

---

## Descripción del sistema

Pipeline de 7 agentes especializados que procesan un reporte de incidente de extremo a extremo. Cada agente tiene una responsabilidad única y no solapada. El sistema es stateless entre agentes — el estado compartido vive en la base de datos SQLite.

---

## Diagrama de componentes

```
┌─────────────────────────────────────────────────────────┐
│                     Web UI (HTML + JS)                   │
│         Formulario: título + descripción + adjunto       │
└──────────────────────────┬──────────────────────────────┘
                           │ POST /api/incidents
                           │ (multipart/form-data)
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    IngestAgent                           │
│  • Detecta prompt injection (guardrails)                 │
│  • Valida MIME type del adjunto                          │
│  • Asigna trace_id único (UUID v4)                       │
│  • Persiste Incident en SQLite                           │
│  • Emite log: stage=ingest                               │
└──────────────────────────┬──────────────────────────────┘
                           │ incident_id + trace_id
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    TriageAgent                           │
│  • Único agente que llama al LLM                         │
│  • Claude claude-sonnet-4-6 (multimodal)                 │
│  • Imagen → base64, Log → texto en el prompt             │
│  • Tool: read_ecommerce_file(path) → Medusa.js           │
│  • Produce: severity, module, summary, files, confidence │
│  • Emite log: stage=triage                               │
└──────────┬──────────────────────────┬───────────────────┘
           │ triage_result            │ tool calls
           │                          ▼
           │              ┌───────────────────────┐
           │              │  Medusa.js Codebase    │
           │              │  (volumen read-only)   │
           │              │  /app/medusa-repo/     │
           │              │  packages/medusa/src/  │
           │              └───────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────┐
│                     QAAgent                              │
│  • Claude claude-sonnet-4-6 (agentic loop)               │
│  • Inspecciona suite de tests del módulo afectado        │
│  • Evalúa cobertura existente                            │
│  • Propone snippet de test de regresión si falta         │
│  • Emite log: stage=qa_scope                             │
└──────────────────────────┬──────────────────────────────┘
                           │ qa_scope_result
                           ▼
┌─────────────────────────────────────────────────────────┐
│               FixRecommendationAgent                     │
│  • Claude claude-sonnet-4-6 (agentic loop)               │
│  • Lee archivos fuente del módulo afectado               │
│  • Propone fix técnico concreto con risk assessment      │
│  • Emite log: stage=fix_recommendation                   │
└──────────────────────────┬──────────────────────────────┘
                           │ fix_recommendation_result
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    TicketAgent                           │
│  • Construye payload de la Card de Trello                │
│  • Crea Card via Trello REST API                         │
│  • Persiste trello_card_id en DB                         │
│  • Emite log: stage=ticket                               │
└──────────────────────────┬──────────────────────────────┘
                           │ trello_card_id + url
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    NotifyAgent                           │
│  • Slack: POST a Incoming Webhook → #incidents           │
│  • Email: SendGrid API → reporter                        │
│  • Persiste NotificationLog en DB                        │
│  • Emite log: stage=notify                               │
└─────────────────────────────────────────────────────────┘

                    (proceso en background)
┌─────────────────────────────────────────────────────────┐
│                  ResolutionWatcher                       │
│  • Polling Trello cada 60s                               │
│  • Detecta Cards movidas a columna "Done"                │
│  • Delega a NotifyAgent → email de resolución            │
│  • Emite log: stage=resolved                             │
└─────────────────────────────────────────────────────────┘
```

---

## Separación de responsabilidades (crítica)

| Agente | Responsabilidad única | Lo que NO hace |
|---|---|---|
| **IngestAgent** | Validación, sanitización, persistencia | No toma decisiones de negocio. No llama al LLM. No crea tickets. |
| **TriageAgent** | Análisis y clasificación del incidente | No crea tickets. No notifica. No persiste directamente (solo el resultado del análisis). |
| **QAAgent** | Evalúa cobertura de tests del módulo afectado y propone tests de regresión | No clasifica el incidente. No crea tickets. Si falla, el pipeline continúa con `qa_incomplete=True`. |
| **FixRecommendationAgent** | Propone fix técnico concreto con risk assessment | No valida ni ejecuta el fix. No crea tickets. Si falla, el pipeline continúa con `fix_incomplete=True`. |
| **TicketAgent** | Integración con el sistema de ticketing (Trello) | No interpreta el reporte. No analiza el codebase. |
| **NotifyAgent** | Comunicación externa (Slack + email) | No genera contenido técnico. Recibe mensajes formateados y los despacha. |
| **ResolutionWatcher** | Detección de tickets resueltos | No notifica directamente. Delega siempre a NotifyAgent. |

---

## Modelo de orquestación

```
FastAPI Application Server
│
├── POST /api/incidents
│   ├── [sync]  IngestAgent.process(request) → incident_id
│   ├── [sync]  Retorna HTTP 201 al cliente con trace_id
│   └── [async] BackgroundTask → pipeline(incident_id)
│                   ├── TriageAgent.process(incident_id)
│                   ├── QAAgent.process(triage_result)
│                   ├── FixRecommendationAgent.process(triage_result, qa_result)
│                   ├── TicketAgent.process(triage_result, qa_result, fix_result)
│                   └── NotifyAgent.process(ticket_result, "team_alert" + "reporter_confirmation")
│
├── GET /api/incidents/:id → estado del pipeline
├── GET /api/observability/events → log viewer para el demo
└── GET /api/health → health check de Docker

ResolutionWatcher (thread separado)
└── Polling loop cada 60s → Trello API → NotifyAgent si hay resoluciones
```

**Punto clave:** El cliente recibe respuesta HTTP 201 inmediatamente después de la ingestión. El pipeline de análisis corre en background. Esto evita timeouts en el frontend si el LLM tarda varios segundos.

---

## Observability — Contrato de eventos

Cada agente emite un evento al completar su etapa usando `src/observability.emit_event()`:

```json
{
  "timestamp": "2026-04-09T14:32:11.542Z",
  "trace_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "stage": "triage",
  "incident_id": 42,
  "status": "success",
  "duration_ms": 2341,
  "metadata": {
    "model": "claude-sonnet-4-6",
    "severity_detected": "P2",
    "module_detected": "cart",
    "confidence": 0.87,
    "files_found": 3
  }
}
```

Los eventos se escriben a:
- stdout (visible en `docker compose logs`)
- `logs/agent.log` (archivo persistente via volumen Docker)
- SQLite tabla `observability_events` (consultable via GET /api/observability/events)

---

## Stack tecnológico

| Componente | Tecnología | Razón |
|---|---|---|
| Backend / Orchestrator | Python 3.11 + FastAPI | Mejor integración con Anthropic SDK. Async nativo. |
| LLM | Claude claude-sonnet-4-6 (Anthropic) | Multimodal nativo. Imagen + texto en el mismo request. |
| Ticketing | Trello REST API | El equipo tiene cuenta. API REST simple con key+token. |
| Comunicador | Slack Incoming Webhooks | No requiere OAuth. URL única por canal. |
| Email | SendGrid API / MOCK | Free tier suficiente para el demo. |
| Persistencia | SQLite + SQLAlchemy | Sin servicios externos. Compatible con PostgreSQL para escala. |
| E-commerce base | Medusa.js (medusajs/medusa) | TypeScript, alta complejidad real, bien documentado. |
| Contenedores | Docker + Docker Compose | Obligatorio para submission. |
| Frontend | HTML5 + Vanilla JS | Formulario simple servido como estático por FastAPI. |

---

## Flujo de datos multimodal

```
1. Cliente sube formulario con imagen PNG (ej. screenshot de error 500)
2. FastAPI recibe multipart/form-data
3. IngestAgent guarda el archivo en uploads/{trace_id}.{ext}
4. TriageAgent lee el archivo:
   - Si es imagen (PNG/JPG): encode en base64 → Claude message con image_url
   - Si es log (.txt/.log): leer como texto → incluir en el texto del mensaje
5. Claude claude-sonnet-4-6 procesa imagen + descripción en un solo request
6. Respuesta estructurada (JSON) es parseada y validada con Pydantic
```

---

## ADRs relevantes

- [ADR-001](adr/ADR-001-ecommerce-repo.md) — Selección de Medusa.js como repo e-commerce
- [ADR-002](adr/ADR-002-observability-strategy.md) — Estrategia de observability
- [ADR-003](adr/ADR-003-guardrails-strategy.md) — Guardrails y prompt injection
- [ADR-004](adr/ADR-004-ticketing-trello.md) — Trello como sistema de ticketing
