# Task

## Title
T11 — Implementar agente de propuesta de solución técnica (Claude)

## Goal
Implementar el agente que, dado un hallazgo del QA Agent, genera una propuesta de solución técnica con enfoque sugerido, archivos a modificar y consideraciones de riesgo. La propuesta se adjunta al ticket creado.

## Source
- spec: `docs/specs/mvp/spec.md` — FR15, FR16, AC13, AC14, OQ5
- architecture: `docs/architecture/system-overview.md` (T01)
- acceptance criteria: AC13 — cada ticket tiene propuesta adjunta; AC14 — menciona enfoque, archivos y riesgo

## Scope
- Diseñar prompt para Claude que recibe un hallazgo y genera una propuesta de solución
- La propuesta debe incluir: enfoque sugerido, lista de archivos a modificar, consideraciones de riesgo
- Adjuntar la propuesta como **comentario del ticket** en Jira (decisión OQ5 resuelta)
- Manejar el caso de múltiples hallazgos: generar una propuesta por hallazgo o una consolidada (definir)

## Out of Scope
- Implementar la solución propuesta (el agente solo propone, no ejecuta)
- Validar que la propuesta es técnicamente correcta (responsabilidad del desarrollador)

## Files Likely Affected
- `src/agents/solution_proposer.py` (nuevo)
- `src/prompts/solution_prompt.py` (nuevo)
- `tests/agents/test_solution_proposer.py` (nuevo)

## Constraints
- La propuesta no debe inventar archivos que no existen en el repo — trabajar solo con los archivos del diff y los mencionados en el análisis de impacto
- Incluir siempre una sección de riesgo de la solución propuesta

## Validation Commands
- `pytest tests/agents/test_solution_proposer.py`
- Test AC14: verificar que la propuesta tiene las tres secciones (enfoque, archivos, riesgo)
- Test de integración: verificar que la propuesta aparece adjunta en el ticket creado por T10

## Done Criteria
- El agente genera propuesta por hallazgo con las 3 secciones requeridas
- AC13 y AC14 cumplidos
- La propuesta está correctamente adjunta al ticket (OQ5 resuelto)
- Tests con hallazgos de ejemplo

## Risks
- Las propuestas pueden ser demasiado genéricas sin contexto suficiente del repo — incluir el diff completo del archivo afectado en el prompt

## Handoff
Next recommended role: QA Engineer
Notes: Depende de T06 y T10. ✅ OQ5 resuelto: propuesta va como comentario en Jira. Cierra el Flujo A completo (pasos 1-8).
