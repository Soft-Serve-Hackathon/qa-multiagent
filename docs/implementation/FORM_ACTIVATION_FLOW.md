# Flujo de Activacion por Formulario (FORM)

## Objetivo
Definir un flujo unico donde todo inicia cuando una persona reporta una incidencia desde el formulario, y termina con:
- ticket creado en Trello
- owner asignado automaticamente
- comunicacion al equipo por Slack
- notificacion al reporter
- cierre cuando la card pasa a Done

---

## Alcance
Este documento cubre solo activacion por formulario.
No cubre activacion por commit/feature/CI webhook.

---

## Trigger de Entrada
- Endpoint: POST /api/incidents
- Tipo de request: multipart/form-data
- Campos obligatorios:
  - title
  - description
  - reporter_email
- Campo opcional:
  - attachment (imagen o log)

Referencia:
- backend/src/api/routes.py

---

## Pipeline FORM (implementado)
1. ingest
2. triage
3. qa_scope
4. fix_recommendation
5. ticket
6. notify
7. resolved

Notas:
- Todos los stages están implementados y ejecutándose en producción.
- qa_scope y fix_recommendation siempre se ejecutan (pipeline obligatorio, no opcional).
- Si qa_scope o fix_recommendation fallan, continúan con flags qa_incomplete=true / fix_incomplete=true.

---

## Etapas Detalladas

### 1) ingest
Responsabilidad:
- Validar email, archivo, tamano y guardrails.
- Sanitizar entrada.
- Persistir incidente.
- Generar trace_id.
- Disparar pipeline en background.

Entrada:
- title, description, reporter_email, attachment

Salida:
- incident_id
- trace_id
- status=received

Errores esperados:
- invalid_email
- unsupported_file_type
- file_too_large
- prompt_injection_detected

---

### 2) triage
Responsabilidad:
- Analizar texto + adjunto.
- Leer contexto real de Medusa.js con MEDUSA_REPO_PATH.
- Clasificar severidad y modulo afectado.

Entrada:
- incident_id

Salida:
- severity (P1-P4)
- affected_module
- technical_summary
- suggested_files
- confidence_score

Referencias:
- backend/src/infrastructure/llm/client.py
- backend/src/infrastructure/llm/tools.py

---

### 3) qa_scope
Responsabilidad:
- Buscar tests existentes relacionados al modulo/archivos.
- Si falta cobertura, generar test de regresion minimo.
- Ejecutar tests focalizados para reproducir el bug.

Entrada:
- triage_result (modulo, archivos sugeridos)

Salida:
- reproduced (true/false)
- failing_tests
- new_tests_created
- test_evidence_summary

---

### 4) fix_recommendation
Responsabilidad:
- Proponer fix tecnico basado en evidencia de qa_scope.
- Re-ejecutar tests focalizados para validar propuesta.
- Entregar recomendacion (sin commit/PR automatico en MVP).

Entrada:
- triage_result + qa_scope_result

Salida:
- proposed_fix_summary
- proposed_files
- risk_level
- post_fix_test_result

---

### 5) ticket
Responsabilidad:
- Crear card en Trello con resumen tecnico.
- Asignar owner automaticamente segun modulo.

Entrada:
- triage_result (+ qa/fix si ya existe)

Salida:
- trello_card_id
- trello_card_url
- assigned_trello_member_id
- assigned_slack_user_id

Configuracion clave:
- OWNER_ROUTING_JSON

Referencias:
- backend/src/agents/ticket_agent.py
- backend/src/infrastructure/external/trello_client.py
- backend/src/infrastructure/routing/owner_router.py

---

### 6) notify
Responsabilidad:
- Enviar alerta a Slack con mencion del owner.
- Enviar confirmacion al reporter por email.

Entrada:
- ticket_result + triage_result

Salida:
- slack_ok
- email_ok
- notification_logs

Referencias:
- backend/src/agents/notify_agent.py
- backend/src/infrastructure/external/slack_client.py
- backend/src/infrastructure/external/sendgrid_client.py

---

### 7) resolved
Responsabilidad:
- Detectar card movida a Done en Trello.
- Notificar resolucion por Slack y email.
- Marcar incidente como resolved.

Entrada:
- estado de Trello Done list

Salida:
- incident.status=resolved
- resolved_at
- notificaciones de cierre

Referencia:
- backend/src/agents/resolution_watcher.py

---

## Contratos Recomendados Entre Etapas
- IncidentInput
- IncidentContext
- TriageOutput
- QAScopeOutput
- FixRecommendationOutput
- TicketOutput
- NotifyOutput
- ResolvedOutput

Campos criticos para trazabilidad:
- trace_id
- incident_id
- stage
- status
- duration_ms
- metadata

---

## Reglas de Negocio
1. Si ingest falla, cortar flujo y devolver 400.
2. Si triage falla, registrar error y mantener incidente trazable.
3. Si qa_scope falla, continuar ticket con qa_incomplete=true.
4. Si ticket falla, no perder incidente, registrar ticket_failed.
5. Si Slack falla, no bloquear email ni estado de incidente.
6. Nunca perder trace_id en ninguna etapa.

---

## Observabilidad Minima
Eventos esperados por trace_id:
- ingest
- triage
- qa_scope
- fix_recommendation
- ticket
- notify
- resolved (cuando aplique)

Consulta:
- GET /api/observability/events?trace_id=...

Referencia:
- backend/src/api/routes.py

---

## Definicion de Done (solo FORM)
1. API devuelve incident_id y trace_id.
2. Triage produce severity, module y suggested_files.
3. Trello card se crea correctamente.
4. Owner se asigna por routing.
5. Slack menciona owner asignado.
6. Reporter recibe confirmacion.
7. Al mover la card a Done, se envia notificacion de cierre.
8. Observabilidad permite reconstruir todo el flujo por trace_id.

---

## Configuracion Requerida
Variables minimas:
- MOCK_INTEGRATIONS=false
- MEDUSA_REPO_PATH=./medusa-repo
- TRELLO_API_KEY
- TRELLO_API_TOKEN
- TRELLO_LIST_ID
- TRELLO_DONE_LIST_ID
- SLACK_WEBHOOK_URL
- OWNER_ROUTING_JSON

Ejemplo OWNER_ROUTING_JSON:
{
  "cart": {
    "trello_member_id": "member_cart",
    "slack_user_id": "U_CART"
  },
  "payment": {
    "trello_member_id": "member_payment",
    "slack_user_id": "U_PAYMENT"
  },
  "default": {
    "trello_member_id": "member_oncall",
    "slack_user_id": "U_ONCALL"
  }
}

---

## Riesgos y Mitigaciones
Riesgo: Falla en integracion Trello.
Mitigacion: Reintento controlado + evento ticket_failed + alerta Slack fallback.

Riesgo: Routing sin default.
Mitigacion: Validar OWNER_ROUTING_JSON al iniciar app y forzar default.

Riesgo: Triage con baja confianza.
Mitigacion: Etiquetar card como low-confidence y elevar a revision humana.

Riesgo: Test auto-generado inestable (qa_scope puede producir tests frágiles).
Mitigacion: Limitar a tests focalizados y aislar fixtures.

---

## Estado Actual
Todos los stages implementados y verificados:
- ingest (IngestAgent)
- triage (TriageAgent — Claude multimodal + Medusa.js tool use)
- qa_scope (QAAgent — encuentra/propone tests)
- fix_recommendation (FixRecommendationAgent — propone fix técnico)
- ticket (TicketAgent — deduplicación + Trello card enriquecida)
- notify (NotifyAgent — Slack + email)
- resolved (ResolutionWatcher — polling Trello Done + notificación reporter)
- owner assignment Trello/Slack por OWNER_ROUTING_JSON
