# Task

## Title
T04 — Implementar agente de revisión de PR (Claude)

## Goal
Implementar el agente que recibe el diff de un PR, lo analiza con Claude y genera un reporte estructurado con: resumen del cambio, riesgos detectados y recomendaciones. El reporte se publica como comentario en el PR.

## Source
- spec: `docs/specs/mvp/spec.md` — FR2, FR3, AC1, AC2
- architecture: `docs/architecture/system-overview.md` (T01)
- acceptance criteria: AC1 — publicado en <5 min; AC2 — formato markdown consistente

## Scope
- Diseñar el prompt para Claude que analiza un diff y produce el reporte
- El reporte debe incluir: resumen del cambio, lista de riesgos identificados, recomendaciones
- Formatear la salida como markdown estructurado para el comentario del PR
- Integrar con `github_client.post_pr_comment` (T03)
- Manejar EC2: si Claude falla o agota timeout, publicar comentario de error sin bloquear el PR

## Out of Scope
- Análisis de QA profundo (eso es T05)
- Análisis de regresión (eso es T06)

## Files Likely Affected
- `src/agents/pr_reviewer.py` (nuevo)
- `src/prompts/pr_review_prompt.py` (nuevo)
- `tests/agents/test_pr_reviewer.py` (nuevo)

## Constraints
- El prompt no debe superar 80% del contexto disponible del modelo
- El reporte generado debe seguir una plantilla fija (secciones siempre presentes aunque vacías)
- Tiempo máximo de respuesta del agente: 3 minutos

## Validation Commands
- `pytest tests/agents/test_pr_reviewer.py`
- Test de integración: ejecutar con un diff real y verificar que el comentario aparece en el PR
- Verificar que el comentario tiene las secciones: Resumen, Riesgos, Recomendaciones

## Done Criteria
- El agente analiza el diff y publica comentario en el PR con las 3 secciones requeridas
- AC2 cumplido: el comentario usa markdown con headers y listas
- EC2 manejado: si Claude falla, se publica un comentario de error con el motivo
- Test unitario con diff de ejemplo y respuesta mockeada de Claude

## Risks
- La calidad del análisis depende del prompt — iterar el prompt puede tomar varias pruebas
- PRs con contexto de dominio muy específico pueden producir análisis genérico o incorrecto

## Handoff
Next recommended role: QA Engineer
Notes: Depende de T02 y T03. Una vez completado, el Flujo A pasos 1-3 está funcional.
