# Roadmap de Tareas — SRE Incident Intake & Triage Agent

**Proyecto:** AgentX Hackathon de SoftServe  
**Estado:** En progreso  
**Última actualización:** 2026-04-08

---

## Orden de ejecución y dependencias

```
TASK-001 — Project Structure & Config
 ├── TASK-002 — IngestAgent
 │    └── TASK-003 — TriageAgent
 │         ├── TASK-004 — TicketAgent (Trello)
 │         │    └── TASK-005 — NotifyAgent (Slack + SendGrid)
 │         │         └── TASK-008 — ResolutionWatcher (Trello polling)
 │         └── TASK-006 — Observability & Logging
 ├── TASK-007 — Frontend (Next.js 14)
 └── TASK-009 — Docker Setup
      └── TASK-010 — Ecommerce Integration (Medusa.js)
```

---

## Tabla de tareas

| ID | Título | Stack | Depende de | Estado |
|---|---|---|---|---|
| TASK-001 | Project structure, config, entidades de dominio | Python / FastAPI | — | pendiente |
| TASK-002 | IngestAgent: validación + detección de injection | Python | TASK-001 | pendiente |
| TASK-003 | TriageAgent: Claude LLM + tool calls Medusa.js | Python / Anthropic | TASK-002 | pendiente |
| TASK-004 | TicketAgent: creación de card en Trello | Python / Trello API | TASK-003 | pendiente |
| TASK-005 | NotifyAgent: Slack webhook + SendGrid email | Python / Slack / SendGrid | TASK-004 | pendiente |
| TASK-006 | Observability: JSON logging + trace_id pipeline | Python | TASK-002 | pendiente |
| TASK-007 | Frontend: Next.js 14 form + status tracker | TypeScript / Next.js | TASK-001 | pendiente |
| TASK-008 | ResolutionWatcher: polling Trello background task | Python / FastAPI BG | TASK-005 | pendiente |
| TASK-009 | Docker Compose: backend + frontend + volumes | Docker | TASK-007 | pendiente |
| TASK-010 | Ecommerce integration: Medusa.js file index | Python / Medusa.js | TASK-003 | pendiente |

---

## Tareas paralelas posibles

- **TASK-002 y TASK-007** pueden desarrollarse en paralelo (backend agent vs frontend)
- **TASK-006** puede desarrollarse en paralelo con TASK-003+ (observability es transversal)
- **TASK-004 y TASK-005** son secuenciales (Notify requiere ticket_id de Trello)

---

## Criterios de Done por tarea

Cada tarea se considera completada cuando:
1. Código implementado y con tests unitarios (happy path + edge cases)
2. Criterios de aceptación de `docs/specs/mvp/spec.md` cubiertos
3. `trace_id` propagado correctamente (si aplica)
4. Handoff documentado en el archivo de tarea

---

## Referencia

- Spec: `docs/specs/mvp/spec.md`
- Arquitectura: `docs/architecture/system-overview.md`
- ADRs: `docs/architecture/adr/`
- Definition of Done: `docs/quality/definition-of-done.md`
