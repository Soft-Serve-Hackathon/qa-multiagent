# Task: TASK-006 — Observability Module + API Endpoint

## Goal
Implementar el módulo centralizado de observability y el endpoint GET /api/observability/events. Esta tarea es P0 — todos los agentes dependen de `src/observability.py`.

## Source
- spec: `docs/specs/mvp/spec.md` (FR11, AC6)
- ADR: `docs/architecture/adr/ADR-002-observability-strategy.md`

## Scope
- `src/observability.py`: función `emit_event(trace_id, stage, incident_id, status, duration_ms, **metadata)`
  - Escribe a stdout como JSON
  - Escribe a `LOG_FILE` (default: `/app/logs/agent.log`) en modo append
  - Persiste en SQLite tabla `observability_events`
- `src/main.py`: agregar endpoint `GET /api/observability/events`
  - Query params: `trace_id` (optional), `stage` (optional), `limit` (default 50)
  - Retorna lista de ObservabilityEvent en orden cronológico

## Out of Scope
- Los agentes individuales ya llaman a emit_event — su implementación está en cada TASK respectivo
- Configuración de Docker volumes (TASK-009)

## Files Likely Affected
- `src/observability.py` (nuevo — **CRÍTICO, crear primero**)
- `src/main.py` (modificar — agregar endpoint)

## Constraints
- El log JSON en stdout debe usar el formato exacto definido en `system-overview.md`:
  ```json
  {"timestamp": "...", "trace_id": "...", "stage": "...", "incident_id": ..., "status": "...", "duration_ms": ..., "metadata": {...}}
  ```
- `reporter_email` NUNCA debe aparecer en metadata de ningún evento
- El módulo debe funcionar aunque el archivo de log no sea escribible (degradar a solo stdout)
- Thread-safe: múltiples agentes pueden llamar a emit_event concurrentemente

## Validation Commands
```bash
# Después de crear un incidente con TASK-002:
TRACE_ID=$(curl -s -X POST http://localhost:3000/api/incidents \
  -F "title=Test" -F "description=Test" -F "reporter_email=test@test.com" | jq -r '.trace_id')

# Verificar eventos de observability
curl "http://localhost:3000/api/observability/events?trace_id=$TRACE_ID"
# Expected: ≥1 evento con stage=ingest y el mismo trace_id (AC6)

# Verificar logs en archivo
docker compose exec app cat /app/logs/agent.log
# Expected: líneas JSON con trace_id consistente

# Verificar en stdout
docker compose logs app | grep '"stage"'
```

## Done Criteria
- [ ] `emit_event()` escribe a stdout, archivo y SQLite
- [ ] `GET /api/observability/events` retorna eventos filtrados por trace_id (AC6)
- [ ] Logs visibles en `docker compose logs`
- [ ] El mismo `trace_id` aparece en todos los eventos del pipeline de un incidente
- [ ] `reporter_email` no aparece en ningún evento

## Risks
- Si `src/observability.py` no está listo cuando TASK-002 empieza, los otros agentes no pueden importarlo. Mitigación: crear un stub mínimo de `emit_event()` que solo hace print() y completar la implementación completa en paralelo.

## Handoff
Next recommended role: QA Engineer (verificar AC6 con e2e smoke test)
Notes: El endpoint GET /api/observability/events es clave para el video demo — debe mostrar claramente el trace completo de un incidente.
