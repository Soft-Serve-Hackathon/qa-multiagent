# Task

## Title
T08 — Implementar agente de reporte técnico (Claude)

## Goal
Implementar el agente que toma los hallazgos del QA Agent (T06/T07) y genera un reporte técnico detallado por hallazgo, listo para ser incluido en el ticket.

## Source
- spec: `docs/specs/mvp/spec.md` — FR9, FR11, AC7, AC9
- architecture: `docs/architecture/system-overview.md` (T01)
- acceptance criteria: AC7 — incluye archivo, función, descripción técnica y severidad; AC9 — generado antes de crear el ticket

## Scope
- Recibir la lista de hallazgos (JSON de T06) y generar un reporte técnico por hallazgo
- Cada entrada del reporte debe incluir: archivo afectado, función/línea, descripción técnica, severidad, stack trace estimado si aplica
- Estructurar el reporte siguiendo el esquema común definido en T01 (para combinarse con T09)
- Manejar EC6: deduplicar hallazgos antes de redactar

## Out of Scope
- Generar el reporte en lenguaje de negocio (eso es T09)
- Crear el ticket (eso es T10)

## Files Likely Affected
- `src/agents/technical_reporter.py` (nuevo)
- `src/prompts/technical_report_prompt.py` (nuevo)
- `src/models/report.py` (nuevo — esquema común de reporte)
- `tests/agents/test_technical_reporter.py` (nuevo)

## Constraints
- El reporte debe seguir el esquema común (`report.py`) para ser combinable con el reporte de negocio
- Si un hallazgo no tiene función identificada, dejar el campo vacío — no inventar

## Validation Commands
- `pytest tests/agents/test_technical_reporter.py`
- Test: pasar lista de hallazgos conocidos y verificar que el reporte tiene todas las secciones requeridas
- Test AC7: verificar que cada entrada tiene archivo, función, descripción y severidad

## Done Criteria
- El agente genera reporte técnico estructurado en el esquema común
- AC7 cumplido: todos los campos requeridos presentes
- EC6 manejado: hallazgos duplicados consolidados antes de redactar
- Test con lista de hallazgos de ejemplo

## Risks
- El prompt puede generar descripciones demasiado largas — definir límite de caracteres por campo

## Handoff
Next recommended role: Backend Engineer
Notes: Depende de T06 y T07. Debe ejecutarse en paralelo con T09. Prerequisito de T10.
