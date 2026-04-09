# Instructivo de Implementacion
## Flujos Ausentes y Mejora de Asignacion en Slack

Fecha: 2026-04-09
Proyecto: SRE Incident Intake & Triage Agent

---

## 1. Objetivo

Implementar tres capacidades nuevas sobre la arquitectura existente:

1. Segundo disparador por eventos de desarrollo (commits, checks, PR).
2. Flujo opcional de rama + propuesta de fix + Pull Request en modo controlado.
3. Asignacion automatica de responsable con mencion en Slack y asignacion en Trello.

---

## 2. Estado Actual (Base)

Actualmente el sistema ya cubre:

- Ingestion desde formulario web.
- Triage multimodal con LLM.
- Creacion de card en Trello.
- Notificacion por Slack y email.
- Notificacion de resolucion por watcher.

Limites actuales:

- No hay disparador por eventos de repositorio.
- No hay automatizacion de rama/commit/PR.
- No hay asignacion automatica de responsables.

---

## 3. Fase 1 - Asignacion de responsables (prioridad alta)

### 3.1 Politica de asignacion

Definir reglas de negocio:

- P1/P2 -> asignar on-call del modulo.
- P3/P4 -> round-robin por modulo.
- Sin mapeo -> fallback a owner por defecto.

### 3.2 Modelo de mapeo sugerido

Crear tabla (o archivo de configuracion inicial) con:

- affected_module
- slack_user_id
- trello_member_id
- active
- priority_order

### 3.3 Cambios funcionales

1. Resolver owner en TicketAgent antes de crear la card.
2. Asignar miembro en Trello al crear card o justo despues.
3. Notificar en Slack con mencion directa al owner.
4. Guardar evidencia de asignacion en observabilidad.

### 3.4 Payload recomendado para observabilidad

- assignment_strategy
- assigned_slack_user_id
- assigned_trello_member_id
- fallback_used
- reason

### 3.5 Criterios de aceptacion

- Cada incidente con modulo conocido termina con owner asignado.
- Slack incluye mencion al owner.
- Trello card queda asignada (idMembers).
- Si falla asignacion, se aplica fallback y queda logueado.

---

## 4. Fase 2 - Segundo disparador (SCM Webhooks)

### 4.1 Endpoints recomendados

- POST /api/webhooks/github
- POST /api/webhooks/gitlab (opcional)

### 4.2 Eventos recomendados para MVP

- push
- pull_request
- check_run/check_suite con estado failed

### 4.3 Normalizacion a incidente comun

Transformar evento SCM a modelo equivalente al formulario:

- title: resumen del fallo
- description: contexto repo/branch/sha
- reporter_email: correo tecnico del equipo o bot
- attachment: log de CI o screenshot de test visual

Despues, reutilizar pipeline existente:

ingest -> triage -> ticket -> notify

### 4.4 Guardrails

- Verificar firma webhook (HMAC).
- Lista de repositorios permitidos.
- Limitar tamano de payload.

---

## 5. Fase 3 - Rama + Fix + PR (modo seguro y opcional)

### 5.1 Politica de entrada

Habilitar solo cuando:

- confianza >= umbral (ej. 0.75)
- severidad permitida para autofix (ej. P3/P4)
- repo esta en allowlist
- tests de base disponibles

### 5.2 Flujo propuesto

1. Crear rama: incident/{trace_id}/{modulo}
2. Generar patch propuesto (LLM + reglas).
3. Ejecutar validaciones: lint + unit tests + smoke.
4. Si pasa: commit y PR draft.
5. Si falla: guardar patch en ticket y marcar requiere revision humana.

### 5.3 Guardrails de seguridad

- No merge automatico.
- No cambios en secretos/config sensible.
- Limite de archivos modificados.
- Explicabilidad del patch (resumen + riesgos).

### 5.4 Observabilidad adicional

Agregar etapas:

- code_fix
- branch_created
- pr_opened
- pr_validation

---

## 6. Mejora UX: Timeline profesional por iteracion

Construir vista por trace_id con:

1. Header ejecutivo: estado final, duracion total, owner.
2. Timeline secuencial: ingest, triage, ticket, notify, resolved.
3. Evidencia por etapa: status, duration_ms, metadata clave.
4. Outcome final: decision, ticket, notificaciones y riesgo.

Recomendacion visual:

- Layout limpio, fondo claro, tarjetas con jerarquia.
- Colores consistentes por estado (success/error/deduplicated).
- Animacion minima de aparicion secuencial.

---

## 7. Plan de implementacion sugerido (2 sprints)

Sprint 1:

- Asignacion owner (Slack + Trello).
- Persistencia de mapping.
- Observabilidad de assignment.
- Tests unitarios para resolver owner y fallback.

Sprint 2:

- Webhooks SCM y normalizacion a incidente.
- Flujo opcional de branch/fix/PR draft.
- Guardrails de seguridad y validaciones CI.
- Dashboard de timeline por iteracion.

---

## 8. Riesgos y mitigaciones

Riesgo: mapeo incompleto de owners.
Mitigacion: fallback global + alerta de configuracion.

Riesgo: ruido por falsos positivos desde CI.
Mitigacion: filtros por tipo de evento + umbral de confianza.

Riesgo: PRs de baja calidad.
Mitigacion: PR draft obligatorio + checks en verde + aprobacion humana.

Riesgo: exposicion de datos sensibles.
Mitigacion: redaccion de payloads, no log de secretos, allowlist estricta.

---

## 9. Checklist de salida

- Owner asignado en Trello y mencionado en Slack.
- Pipeline activable desde formulario y desde SCM.
- Flujo de PR automatizado solo en modo controlado.
- Eventos observability completos por trace_id.
- Pruebas de edge cases y fallback ejecutadas.

---

## 10. Recomendaciones finales de implementacion

1. Implementar primero asignacion de owner: mayor impacto con menor riesgo.
2. Reutilizar el pipeline actual para nuevos disparadores, evitando duplicacion.
3. Mantener autofix en modo "draft only" hasta tener confianza operativa.
4. Medir exito con KPIs: tiempo de triage, tiempo a asignacion, tasa de fallback.
5. Revisar seguridad en cada fase con checklist formal antes de desplegar.
