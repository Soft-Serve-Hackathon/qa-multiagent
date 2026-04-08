# Task: TASK-004 — TicketAgent (Trello API)

## Goal
Implementar el TicketAgent que crea Cards en Trello con el análisis técnico del incidente.

## Source
- spec: `docs/specs/mvp/spec.md` (FR7, AC3)
- architecture: `docs/architecture/api-contracts.md` (Trello Card structure)
- ADR: `docs/architecture/adr/ADR-004-ticketing-trello.md`

## Scope
- `src/agents/ticket_agent.py`: clase `TicketAgent` con método `process(triage_result, incident)`
- Integración con Trello REST API:
  - `POST https://api.trello.com/1/cards` para crear la Card
  - Incluir: name, description (markdown), labels (severidad), checklist (archivos sugeridos)
- Modo mock: si `MOCK_INTEGRATIONS=true`, retornar Card simulada con ID y URL
- Persistir Ticket en SQLite con `trello_card_id` y `trello_card_url`
- Manejar fallo de Trello API: persistir en estado `ticket_pending` (no lanzar excepción)

## Card structure a crear
```
Name: "[P{severity}] {title}"
Description (markdown):
  ## Technical Summary
  {technical_summary}
  
  ## Affected Module
  {affected_module} (confidence: {confidence_score*100:.0f}%)
  
  ## Suggested Files
  - {file1}
  - {file2}
  
  ## Trace ID
  {trace_id}

Labels: P1=red, P2=orange, P3=yellow, P4=green (crear labels si no existen en el board)
Checklist "Files to investigate": lista de suggested_files
```

## Out of Scope
- Notificaciones (TASK-005)
- Detección de resolución (TASK-008)

## Files Likely Affected
- `src/agents/ticket_agent.py` (nuevo)
- `requirements.txt` (agregar `httpx` o usar `requests`)

## Constraints
- Variables de entorno: `TRELLO_API_KEY`, `TRELLO_API_TOKEN`, `TRELLO_LIST_ID`
- Si la Trello API retorna un error, guardar `status=ticket_pending` en DB — no propagar el error al pipeline
- Ver `.claude/agents/backend-engineer.md` para el patrón de mock y observability

## Validation Commands
```bash
# Con MOCK_INTEGRATIONS=true
MOCK_INTEGRATIONS=true docker compose up
curl -X POST http://localhost:3000/api/incidents \
  -F "title=Test" -F "description=Test incident" -F "reporter_email=test@test.com"
# En los logs debe aparecer: stage=ticket, status=success, mock=true

# Con credenciales reales de Trello
# Verificar que la Card aparece en el board
```

## Done Criteria
- [ ] Card de Trello creada con todos los campos de FR7 (AC3)
- [ ] Mock mode funciona con `MOCK_INTEGRATIONS=true` → logs muestran `mock=true`
- [ ] Ticket persistido en SQLite con `trello_card_id` y `trello_card_url`
- [ ] Evento `stage=ticket` en observability
- [ ] Si Trello falla → `status=ticket_pending` en DB, pipeline no se detiene

## Risks
- Los labels de Trello deben existir en el board antes de poder asignarlos. Mitigación: crear los labels P1-P4 en el board manualmente antes del demo, o usar la Trello API para crearlos si no existen.

## Handoff
Next recommended role: Backend Engineer (TASK-005 — NotifyAgent)
Notes: El `trello_card_url` del Ticket es necesario para incluirlo en el mensaje de Slack y en el email al reporter.
