# Task: TASK-003 — TriageAgent (LLM Multimodal + Medusa.js lookup)

## Goal
Implementar el TriageAgent — el corazón del sistema. Es el único agente que llama al LLM (Claude claude-sonnet-4-6) con soporte multimodal. Analiza el incidente y produce un TriageResult estructurado con contexto del codebase de Medusa.js.

## Source
- spec: `docs/specs/mvp/spec.md` (FR6, AC1, AC2)
- architecture: `docs/architecture/system-overview.md` (TriageAgent section)
- domain model: `docs/architecture/domain-model.md` (TriageResult, módulos Medusa.js)

## Scope
- `src/agents/triage_agent.py`: clase `TriageAgent` con método `process(incident_id)`
- Manejo multimodal:
  - Imagen (PNG/JPG): leer bytes → encode base64 → `image` content block en el mensaje de Claude
  - Log (.txt/.log): leer primeros 50KB → incluir como texto en el mensaje
  - Solo texto: sin procesamiento de adjunto
- Tool: `read_ecommerce_file(path)` → lee archivos de `/app/medusa-repo/`
- System prompt del TriageAgent con: rol, dominio Medusa.js, escala P1-P4, módulos disponibles, formato JSON esperado
- Output validado con Pydantic: `TriageResult { severity, affected_module, technical_summary, suggested_files, confidence_score }`
- Persistir TriageResult en SQLite
- Actualizar estado del Incident a `triaging` al inicio y a `ticketed` al completar

## Out of Scope
- Crear el ticket (TASK-004)
- Notificaciones (TASK-005)

## Files Likely Affected
- `src/agents/triage_agent.py` (nuevo)
- `src/schemas.py` (nuevo — Pydantic models para TriageResult)
- `requirements.txt` (agregar `anthropic`)

## Constraints
- **Solo este agente llama al LLM** — ningún otro agente debe importar `anthropic`
- `reporter_email` NO debe incluirse en el prompt enviado a Claude
- El tool `read_ecommerce_file` debe validar que la ruta está dentro de `/app/medusa-repo/` (no path traversal)
- Si `confidence_score < 0.4`, agregar nota en `technical_summary`: "Low confidence — attachment may not be relevant for technical triage"
- Ver `.claude/agents/backend-engineer.md` para el patrón de observability

## Validation Commands
```bash
# Verificar que TriageAgent procesa un incidente existente
# (crear un incidente primero con TASK-002)
curl "http://localhost:3000/api/incidents/1"
# Expected: status=triaging o ticketed, con severity y affected_module

# Verificar evento de triage en observability
curl "http://localhost:3000/api/observability/events?stage=triage"
# Expected: evento con severity_detected, module_detected, confidence, multimodal
```

## Done Criteria
- [ ] TriageAgent produce TriageResult con todos los campos (AC1, AC2)
- [ ] Imagen adjunta es procesada como multimodal en el mensaje de Claude
- [ ] Log adjunto es incluido como texto en el mensaje de Claude
- [ ] `suggested_files` contiene rutas reales de Medusa.js
- [ ] Evento `stage=triage` en observability con `model`, `severity_detected`, `module_detected`, `confidence`, `multimodal`
- [ ] TriageResult persistido en SQLite

## Risks
- El codebase de Medusa.js debe estar disponible en `/app/medusa-repo/` antes de que este agente corra. Depende de TASK-010 (ecommerce integration). Para desarrollo local, se puede mockear el tool `read_ecommerce_file` retornando snippets hardcodeados.
- El formato JSON del output del LLM puede variar. Mitigación: usar `response_format` de Claude con structured outputs o parsear el JSON con manejo de errores robusto.

## Handoff
Next recommended role: Backend Engineer (TASK-004 — TicketAgent)
Notes: El TriageResult completo (con todos los campos) es el input de TicketAgent. Confirmar que el schema de TriageResult en Pydantic es correcto antes de pasar a TASK-004.
