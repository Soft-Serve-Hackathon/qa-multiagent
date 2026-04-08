# General Development Instructions — SRE Incident Intake & Triage Agent

## Contexto del proyecto
Sistema multi-agente de triage de incidentes SRE para e-commerce (Medusa.js).
5 agentes especializados: IngestAgent → TriageAgent → TicketAgent → NotifyAgent + ResolutionWatcher.
Stack: Python 3.11 + FastAPI (backend) / Next.js 14 + TypeScript (frontend) / Docker Compose.
Integraciones: Anthropic Claude claude-sonnet-4-6, Trello, Slack, SendGrid.

## Reglas generales

- Lee `docs/specs/mvp/spec.md` y `AGENTS_USE.md` antes de tocar código.
- Prefiere cambios pequeños y reversibles.
- Mantén consistencia de nombres, contratos y estructura definidos en `docs/architecture/`.
- Todo `trace_id` (UUID v4) debe propagarse a través de todos los agentes y logs.
- Si detectas ambigüedad, documéntala en `docs/idea/open-questions.md`.
- Toda implementación debe poder validarse con un comando concreto.
- No implementes features fuera del scope de `docs/specs/mvp/spec.md` sin documentarlo.
