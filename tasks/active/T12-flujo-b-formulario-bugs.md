# Task

## Title
T12 — Implementar Flujo B: ingesta de evidencia de bugs por formulario

## Goal
Implementar el punto de entrada alternativo del sistema: un formulario donde un usuario puede reportar un bug con evidencia (descripción, pasos, contexto) y el sistema lo procesa con el mismo pipeline del QA Agent (desde el paso 6 del Flujo A).

## Source
- spec: `docs/specs/mvp/spec.md` — FR8, AC6, EC3, OQ2
- architecture: `docs/architecture/system-overview.md` (T01)
- acceptance criteria: AC6 — produce el mismo tipo de reporte que el análisis automático del PR

## Scope
- Definir el esquema de campos del formulario: título, descripción del bug, pasos para reproducir, comportamiento esperado, comportamiento actual, contexto adicional (opcional)
- Implementar validación de campos mínimos requeridos (EC3)
- Crear entrypoint que recibe el formulario y llama al QA Agent con la evidencia como input
- El pipeline posterior es el mismo: T08 + T09 + T10 + T11
- Usar **Google Forms o Notion** como formulario externo (decisión OQ2 resuelta) — integrar vía webhook

## Out of Scope
- Construir una UI web propia (NG1) — usar herramienta existente (Google Forms, Typeform, etc.)
- Integración con email o notificaciones

## Files Likely Affected
- `src/entrypoints/bug_report_ingestion.py` (nuevo)
- `src/models/bug_report.py` (nuevo — modelo del formulario)
- `tests/entrypoints/test_bug_report_ingestion.py` (nuevo)
- Configuración del formulario externo (Google Forms u otro — según OQ2)

## Constraints
- EC3: si faltan campos obligatorios, rechazar el envío con mensaje claro de qué falta
- El modelo `BugReport` debe ser convertible al mismo formato de hallazgos que usa el QA Agent
- La herramienta de formulario debe poder enviar datos via webhook o API

## Validation Commands
- `pytest tests/entrypoints/test_bug_report_ingestion.py`
- Test AC6: enviar un bug report y verificar que el ticket generado tiene la misma estructura que los del Flujo A
- Test EC3: enviar formulario incompleto y verificar que retorna error con campos faltantes listados

## Done Criteria
- El formulario acepta evidencia de bugs con los campos definidos
- EC3 manejado: validación de campos mínimos con feedback claro
- AC6 cumplido: el reporte generado es indistinguible del Flujo A en formato y estructura
- ✅ OQ2 resuelto: formulario externo (Google Forms o Notion) vía webhook

## Risks
- La integración via webhook (Google Forms/Notion) puede tener latencia o fallar silenciosamente — implementar confirmación de recepción

## Handoff
Next recommended role: Backend Engineer
Notes: Depende de T06 (QA Agent), T08, T09, T10. Esta tarea completa el Flujo B. Es la última tarea del MVP.
