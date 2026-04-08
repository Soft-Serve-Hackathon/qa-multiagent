# Task: TASK-007 — Frontend (Formulario de reporte de incidentes)

## Goal
Implementar el formulario web HTML para reportar incidentes. Debe ser simple, funcional y demostrable en el video demo.

## Source
- spec: `docs/specs/mvp/spec.md` (FR1-FR3, AC1)
- architecture: `docs/architecture/api-contracts.md` (POST /api/incidents)
- agent: `.claude/agents/frontend-engineer.md` (campos, estados UI, multimodal UX)

## Scope
- `src/frontend/index.html`: formulario principal
- `src/frontend/styles.css`: estilos básicos (sin frameworks CSS pesados)
- `src/frontend/app.js`: lógica de submit, validación cliente, estados UI
- FastAPI sirve los archivos estáticos: `app.mount("/", StaticFiles(directory="src/frontend"))`

## Campos del formulario
| Campo | Tipo | Validación | Requerido |
|---|---|---|---|
| title | text input | max 200 chars | Sí |
| description | textarea | max 2000 chars + contador | Sí |
| reporter_email | email input | formato email | Sí |
| attachment | file input | PNG/JPG/TXT/LOG, max 10MB | No |

## Estados UI requeridos (todos obligatorios)
| Estado | Qué mostrar |
|---|---|
| idle | Formulario vacío listo |
| loading | "Analyzing your incident report..." + spinner, botón deshabilitado |
| success | "✓ Ticket created. Reference: {trace_id}. You will be notified by email." |
| error-injection | "Your report contains content that cannot be processed. Please rephrase and try again." |
| error-validation | Mensaje específico del error (email inválido, archivo muy grande, etc.) |
| error-server | "Something went wrong. Please try again in a few minutes." |

## Multimodal UX
- Si se adjunta imagen: mostrar preview thumbnail + nombre del archivo
- Si se adjunta log: mostrar icono de documento + nombre del archivo
- Texto de ayuda: "Supported: PNG, JPG, TXT, LOG — max 10MB"
- Validar tamaño en cliente antes de enviar

## Out of Scope
- Dashboard de incidentes
- Página de estado en tiempo real (polling)
- Login / autenticación

## Files Likely Affected
- `src/frontend/index.html` (nuevo)
- `src/frontend/styles.css` (nuevo)
- `src/frontend/app.js` (nuevo)
- `src/main.py` (modificar — agregar mount de StaticFiles)

## Constraints
- HTML5 + Vanilla JS — sin React, Vue, ni frameworks SPA
- El formulario usa `fetch()` con `FormData` para el submit
- Código limpio y legible — los mentores pueden leer el HTML durante la evaluación

## Validation Commands
```bash
# Abrir http://localhost:3000 en browser
# Probar happy path: llenar formulario + adjuntar imagen + submit
# Verificar estado loading → success con trace_id
# Probar error: dejar reporter_email vacío → validación cliente
# Probar injection: poner "ignore previous instructions" en description → error-injection
```

## Done Criteria
- [ ] Formulario carga en http://localhost:3000
- [ ] Submit con imagen adjunta → estado loading → estado success con trace_id
- [ ] Preview de imagen visible antes de submit
- [ ] Validación cliente: email inválido no permite submit
- [ ] Todos los estados UI implementados y visibles

## Risks
- FastAPI StaticFiles puede tener conflictos con los endpoints API si las rutas no están bien ordenadas. Mitigación: registrar los endpoints API antes del mount de StaticFiles en `main.py`.

## Handoff
Next recommended role: QA Engineer
Notes: El formulario es el punto de entrada del video demo. Debe verse bien en pantalla — una UI clara y sin errores de consola es importante para la impresión visual del demo.
