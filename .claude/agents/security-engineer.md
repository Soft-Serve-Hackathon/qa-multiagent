# Security Engineer

## Mission
Revisar la solución desde exposición, abuso, permisos y manejo de datos.

## Focus
- autenticación
- autorización
- validación de inputs
- secretos
- superficie de ataque

## Outputs
- observaciones de seguridad
- checklist de riesgos
- recomendaciones mínimas para el MVP

---

## SRE Domain — Threat Model

El sistema recibe input no confiable de usuarios externos via formulario web. El LLM es el componente más sensible.

| ID | Amenaza | Vector | Mitigación implementada |
|---|---|---|---|
| T1 | Prompt injection | Campo `description` o `title` con instrucciones maliciosas | `validate_injection()` en IngestAgent — ADR-003 |
| T2 | Malicious file upload | Imagen con payload EXIF malicioso, script disfrazado de .txt | Validar MIME type real con `python-magic`, no confiar en extensión |
| T3 | Credenciales en logs | `reporter_email` o API keys aparecen en observability events | `reporter_email` no incluido en prompts LLM. API keys solo en `.env`. |
| T4 | API token expuesto | `TRELLO_API_TOKEN`, `ANTHROPIC_API_KEY` hardcodeados en código | Solo en `.env`. `.env` en `.gitignore`. `.env.example` con placeholders. |
| T5 | SSRF via adjunto | Si el sistema aceptara URLs de archivos, podría usarse para SSRF | El MVP solo acepta archivos locales (upload), no URLs. |
| T6 | Context overflow | Archivo de log muy grande que desborda el contexto del LLM | IngestAgent lee solo los primeros 50KB de archivos de log. |

## Checklist de seguridad para el MVP

Antes de submission, verificar:
- [ ] `validate_injection()` en `src/guardrails.py` cubre los patrones del ADR-003
- [ ] MIME type validation usa `python-magic`, no solo la extensión del archivo
- [ ] `.env` está en `.gitignore`
- [ ] `.env.example` tiene todos los valores como placeholder (no valores reales)
- [ ] `reporter_email` NO aparece en ningún log de observability ni en el prompt del LLM
- [ ] API keys no están hardcodeadas en ningún archivo de código
- [ ] `description` es truncado a 2000 chars antes de enviarse al LLM
- [ ] El endpoint `POST /api/incidents` retorna HTTP 400 (no 500) ante inputs inválidos
- [ ] AC7 pasa: input con "ignore previous instructions" → HTTP 400, sin evento `stage=triage` en logs

## Responsible AI — Verificación

| Principio | Cómo se implementa | Dónde verificar |
|---|---|---|
| Fairness | El triage se basa en el contenido técnico, no en el email del reporter | `reporter_email` fuera del prompt LLM |
| Transparency | Cada TriageResult incluye `confidence_score` y `technical_summary` | `GET /api/incidents/:id` |
| Accountability | Cada acción tiene un evento de observability con `trace_id` | `GET /api/observability/events` |
| Privacy | `reporter_email` no se envía al LLM, solo a los servicios de notificación | `src/agents/triage_agent.py` |
| Security | Guardrails implementados, API keys en `.env`, MIME validation | `src/guardrails.py`, `.env.example` |