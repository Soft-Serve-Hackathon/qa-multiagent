# Task

## Title
T06 — Implementar QA Agent: análisis de código y detección de bugs

## Goal
Implementar el agente QA que analiza el código del PR en busca de bugs potenciales, antipatrones y code smells, y genera una lista priorizada de hallazgos con severidad.

## Source
- spec: `docs/specs/mvp/spec.md` — FR5, FR7, AC4
- architecture: `docs/architecture/system-overview.md` (T01)
- acceptance criteria: AC4 — identifica al menos un hallazgo en PRs con antipatrones conocidos

## Scope
- Diseñar prompt para Claude que analiza código y detecta: bugs potenciales, antipatrones, code smells, validaciones faltantes
- Cada hallazgo debe tener: archivo, función, descripción, severidad (crítico/alto/medio/bajo)
- Generar lista priorizada de hallazgos ordenada por severidad
- Manejar EC7: si no hay tests en el repo, indicarlo en el reporte
- Manejar EC5: si el diff es muy grande, procesar por chunks y consolidar hallazgos

## Out of Scope
- Análisis de impacto/regresión en otros módulos (eso es T07)
- Generación de reportes técnico y de negocio (eso es T08 y T09)

## Files Likely Affected
- `src/agents/qa_agent.py` (nuevo)
- `src/prompts/qa_analysis_prompt.py` (nuevo)
- `src/models/finding.py` (nuevo — modelo de datos para un hallazgo)
- `tests/agents/test_qa_agent.py` (nuevo)

## Constraints
- El output del agente debe ser JSON estructurado (no texto libre) para facilitar el procesamiento posterior
- Un hallazgo debe tener al mínimo: `file`, `function`, `description`, `severity`, `type`
- El agente no debe inventar bugs — si no hay evidencia clara, usar severidad `bajo` con nota de incertidumbre

## Validation Commands
- `pytest tests/agents/test_qa_agent.py`
- Test con un snippet de código con bug conocido → verificar que lo detecta
- Test con código limpio → verificar que la lista de hallazgos está vacía o tiene solo observaciones de bajo impacto
- Test EC7: repositorio sin tests → verificar que el reporte lo indica

## Done Criteria
- El agente retorna lista de hallazgos en formato JSON estructurado
- AC4 cumplido: detecta hallazgos en código con antipatrones
- EC5 y EC7 manejados
- Tests unitarios con casos de código bueno y malo

## Risks
- Alta tasa de falsos positivos — ajustar el prompt para pedir solo hallazgos con evidencia clara
- El chunking de diffs grandes puede generar hallazgos duplicados — implementar deduplicación básica

## Handoff
Next recommended role: Backend Engineer
Notes: Depende de T05 (gate) y T03 (cliente GitHub). Prerequisito de T07, T08 y T09.
