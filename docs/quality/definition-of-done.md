# Definition of Done — SRE Incident Intake & Triage Agent

Una tarea se considera terminada cuando cumple **todos** los criterios siguientes:

## Criterios generales

- [ ] Contexto leído: `docs/specs/mvp/spec.md`, `AGENTS_USE.md`, tarea activa
- [ ] Implementación respeta la spec (FR y AC referenciados en la tarea)
- [ ] Criterios de aceptación aplicables están cubiertos y verificables
- [ ] Validación ejecutada o evidencia documentada en el handoff
- [ ] Riesgos remanentes escritos en la sección Handoff de la tarea
- [ ] Documentación afectada actualizada (`api-contracts.md`, `system-overview.md`, ADRs si aplica)

## Criterios específicos por tipo

### Agentes backend (IngestAgent, TriageAgent, TicketAgent, NotifyAgent, ResolutionWatcher)

- [ ] Tests unitarios en `backend/tests/unit/` — happy path + edge cases
- [ ] Cliente LLM/externo inyectado como dependencia (mockeable)
- [ ] `trace_id` propagado correctamente en todos los eventos de observabilidad
- [ ] Errores de integración externa manejados explícitamente (no swallowed)

### Guardrails (IngestAgent / shared/security.py)

- [ ] Test de detección de prompt injection con al menos 3 patrones maliciosos
- [ ] Validación de MIME type y tamaño de archivo verificada
- [ ] Input nunca llega al LLM sin pasar por validación

### API (FastAPI routes + Pydantic models)

- [ ] Contrato de endpoint coincide con `docs/architecture/api-contracts.md`
- [ ] Test de integración en `backend/tests/integration/` para el endpoint
- [ ] Respuesta incluye `trace_id` para trazabilidad del cliente

### Frontend (Next.js 14)

- [ ] Flujo implementado cubre el criterio de aceptación correspondiente (AC1-AC8)
- [ ] Estados UI cubiertos: loading, success, error
- [ ] Validación de formulario en cliente: campos requeridos, email, tamaño de archivo
- [ ] Comunicación con backend via `lib/api.ts` (no fetch directo)

### Docker / Infraestructura

- [ ] `docker-compose up --build` levanta backend + frontend sin errores
- [ ] `GET /api/health` retorna 200
- [ ] Variables de entorno documentadas en `.env.example`

## Handoff requerido

Al cerrar una tarea, el archivo de tarea debe incluir:

1. Qué se implementó
2. Comandos de validación ejecutados y resultado
3. Criterios de aceptación cubiertos
4. Qué queda pendiente o fuera de scope
5. Riesgos identificados
6. Siguiente tarea recomendada
