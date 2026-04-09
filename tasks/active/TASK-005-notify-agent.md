# Task: TASK-005 — NotifyAgent (Slack + Email)

## Goal
Implementar el NotifyAgent que envía notificaciones al equipo técnico vía Slack y al reporter vía email.

## Source
- spec: `docs/specs/mvp/spec.md` (FR8, FR9, FR10, AC4, AC5)
- architecture: `docs/architecture/api-contracts.md` (Slack message structure, Email templates)

## Scope
- `src/agents/notify_agent.py`: clase `NotifyAgent` con método `process(incident_id, notification_type, ticket)`
- Tipos de notificación: `team_alert` (Slack), `reporter_confirmation` (email), `reporter_resolution` (email)
- Integración Slack: POST al `SLACK_WEBHOOK_URL` con mensaje formateado
- Integración Email: SendGrid API o mock si `MOCK_EMAIL=true`
- Persistir NotificationLog en SQLite para cada notificación enviada
- Modo mock: si `MOCK_INTEGRATIONS=true`, loggear el contenido del mensaje en lugar de enviarlo

## Message templates (ver api-contracts.md para el formato completo)
- **Slack (team_alert):** `[P{severity}] {title}` + módulo + confianza + link a Card
- **Email reporter_confirmation:** subject `[Incident received] {title}` + card ID + severity + ETA
- **Email reporter_resolution:** subject `[Resolved] {title}` + confirmation + link a Card

## Out of Scope
- Detección de resolución (TASK-008 — ResolutionWatcher)

## Files Likely Affected
- `src/agents/notify_agent.py` (nuevo)
- `requirements.txt` (agregar `sendgrid` si se usa email real)

## Constraints
- `reporter_email` se obtiene de la DB — no se pasa directamente en el pipeline para mantener privacidad
- Si Slack falla: loggear error, continuar con email (no detener el pipeline)
- Si email falla: loggear error, marcar NotificationLog con `status=failed`
- Ver `.claude/agents/backend-engineer.md` para el patrón de mock

## Validation Commands
```bash
# Con MOCK_INTEGRATIONS=true — verificar logs
docker compose logs -f | grep '"stage": "notify"'
# Expected: evento con slack_sent=true, email_sent=true, mock=true

# Con Slack real — verificar canal #incidents
# Con email real — verificar inbox del reporter
```

## Done Criteria
- [ ] Slack #incidents recibe mensaje dentro de 30 segundos (AC4) o logs muestran mensaje mock
- [ ] Reporter recibe email de confirmación con card ID (AC5) o logs muestran email mock
- [ ] NotificationLog persistido en SQLite para cada notificación
- [ ] Evento `stage=notify` en observability con `slack_sent`, `email_sent`, `mock`
- [ ] Si Slack o email fallan → error en logs, pipeline no se detiene

## Risks
- SendGrid requiere verificar el dominio del sender. Si no hay dominio verificado, usar `MOCK_EMAIL=true` para el demo y documentarlo en AGENTS_USE.md como limitación conocida.

## Handoff
Next recommended role: Backend Engineer (TASK-006 — Observability endpoint) o Frontend Engineer (TASK-007)
Notes: Una vez que notify funciona, el flujo e2e ingest→triage→ticket→notify está completo. TASK-008 (ResolutionWatcher) puede implementarse en paralelo.
