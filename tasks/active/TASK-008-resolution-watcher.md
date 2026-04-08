# Task: TASK-008 — Resolution Watcher & Closure Loop

## Goal
Implementar un job en background que monitoree cambios en Trello, detecte cuando un ticket es movido a "Done" y genere una notificación de cierre para el reporter.

## Source
- spec: `docs/specs/mvp/spec.md` (FR7, AC7)
- architecture: `docs/architecture/adr/ADR-004-ticketing-trello.md`
- acceptance criteria: AC7 — `Email al reporter cuando la Card se mueve a "Done" en Trello`

## Scope
- Crear `src/agents/resolution_watcher.py` con clase `ResolutionWatcher`
- Implementar polling a Trello cada 60 segundos (configurable via `RESOLUTION_WATCHER_INTERVAL_SECONDS`)
- Consultar columna "Done" del Board de Trello (usando `TRELLO_DONE_LIST_ID`)
- Recuperar incidente asociado de la base de datos usando el `trace_id` en la descripción de la Card
- Mantener estado de "últimas Cards vistas" para evitar duplicados
- Llamar a `NotifyAgent.notify_resolution()` cuando se detecte una Card nueva en "Done"
- Generar evento observability con stage="resolution_detected"
- Soportar `MOCK_INTEGRATIONS=true` (simular Cards en "Done" cada N segundos)

## Out of Scope
- Webhooks de Trello (post-MVP)
- Escalation de resoluciones que tarden >24h
- Análisis de archivos modificados en el commit de fix

## Files Likely Affected
- `src/agents/resolution_watcher.py` (nuevo)
- `src/main.py` (agregar startup y shutdown del watcher)
- `src/observability.py` (emitir evento resolution_detected)
- `src/models.py` (campo last_triage_notified_at en Incident)
- `src/database.py` (métodos get_incident_by_trace_id, update_incident)
- `.env.example` (RESOLUTION_WATCHER_INTERVAL_SECONDS)

## Constraints
- Python asyncio para no bloquear el servidor
- Usar cliente Trello abierto con session compartida
- No reutilizar la misma Card si ya fue procesada (guardar Card IDs en set en memoria o en DB)
- Timeout máximo 30 segundos por ciclo de polling
- Logging de cada polling cycle con timestamp

## Validation Commands
```bash
# 1. Verificar que el servidor levanta con el watcher activo
docker compose up --build
sleep 2
curl http://localhost:3000/api/health  # Should include "watcher_status": "running"

# 2. Simular una Card en "Done"
# Mover manualmente una Card a la columna "Done" en Trello
# Esperar 60-120 segundos
# Verificar:
# - Log: "resolution_detected" con trace_id
# - Email enviado al reporter con asunto "Your incident [ticket_num] is resolved"

# 3. En MOCK mode
curl -X POST http://localhost:3000/api/test/simulate-resolution
# Esperar 2 segundos → verificar log, verificar email en MOCK log file
```

## Done Criteria
- [ ] `src/agents/resolution_watcher.py` existe e implementa `ResolutionWatcher` class
- [ ] Watcher se inicia en el `@app.on_event("startup")` de FastAPI
- [ ] Watcher se detiene gracefully en `@app.on_event("shutdown")`
- [ ] Polling a Trello ocurre cada `RESOLUTION_WATCHER_INTERVAL_SECONDS` segundos
- [ ] Evento observability con stage="resolution_detected" se emite para cada resolución
- [ ] `NotifyAgent.notify_resolution(incident, ticket_card)` es llamado y envia email al reporter
- [ ] MOCK mode funciona: simula Cards en "Done" cada N segundos sin llamar Trello
- [ ] No hay duplicados: si una Card fue procesada, no se procesa de nuevo
- [ ] Logs estructurados con trace_id y timestamp en cada ciclo
- [ ] `.env.example` incluye: `RESOLUTION_WATCHER_INTERVAL_SECONDS=60`

## Risks
- **Latencia de polling:** 60 segundos entre ciclos → peor caso 60 segundos de delay en notificación. Mitigación: documentar en SCALING.md; webhooks de Trello resuelven esto en post-MVP.
- **Rate limiting en Trello API:** Si el número de Cards crece, Los requests GET podrían ser throttled. Mitigación: cachear últimas 100 Cards en memoria.
- **Race condition:** Si dos ciclos de polling detectan la misma Card al mismo tiempo (edge case con baja probabilidad). Mitigación: usar `db.update_incident(last_triage_notified_at = now)` para marcar "ya procesada".

## Handoff
Next recommended role: QA Engineer (para validar AC7)
Notes: El watcher debe estar integrado en el main.py antes de que el docker-compose final (TASK-009) sea validado.
