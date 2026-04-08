# Task

## Title
T07 — Implementar QA Agent: análisis de impacto y regresión básica

## Goal
Extender el QA Agent para que identifique qué módulos o funciones existentes del repositorio pueden verse afectados por los cambios del PR, generando un análisis básico de regresión.

## Source
- spec: `docs/specs/mvp/spec.md` — FR6, AC5
- architecture: `docs/architecture/system-overview.md` (T01)
- acceptance criteria: AC5 — menciona al menos los módulos directamente importados/llamados por el código modificado

## Scope
- Analizar los archivos modificados del PR e identificar: imports externos al PR, funciones o clases referenciadas desde otros módulos
- Generar lista de módulos potencialmente impactados con nivel de confianza
- Indicar si los módulos impactados tienen tests existentes
- Manejar EC7: si no hay tests de regresión, indicarlo explícitamente sin inferir cobertura

## Out of Scope
- Ejecución real de tests (no hay sandbox de runtime — NG2)
- Análisis de dependencias transitivas profundas (solo primer nivel)

## Files Likely Affected
- `src/agents/regression_analyzer.py` (nuevo)
- `src/prompts/regression_prompt.py` (nuevo)
- `tests/agents/test_regression_analyzer.py` (nuevo)

## Constraints
- El análisis es estático — solo lectura de código, no ejecución
- El resultado debe integrarse con la lista de hallazgos de T06 como una sección adicional

## Validation Commands
- `pytest tests/agents/test_regression_analyzer.py`
- Test: modificar una función que es importada por otro módulo y verificar que el analizador la detecta
- Test EC7: repo sin tests → verificar que el reporte indica ausencia de cobertura sin inventar datos

## Done Criteria
- El analizador retorna lista de módulos potencialmente afectados con nivel de confianza
- AC5 cumplido: al menos los módulos directamente referenciados están identificados
- EC7 manejado correctamente
- Output se integra en el reporte general del QA Agent (T06)

## Risks
- En repos grandes, el análisis de imports puede generar demasiado ruido — limitar a los archivos del PR y sus importadores directos

## Handoff
Next recommended role: Backend Engineer
Notes: Depende de T06. Se ejecuta en la misma pasada del QA Agent. Prerequisito de T08.
