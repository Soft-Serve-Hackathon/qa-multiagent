# Task

## Title
T09 — Implementar agente de reporte de negocio (GPT/Gemini)

## Goal
Implementar el agente que toma los hallazgos del QA Agent y genera un reporte en lenguaje natural y de negocio, sin jerga técnica, pensado para stakeholders y Product Managers.

## Source
- spec: `docs/specs/mvp/spec.md` — FR10, FR11, AC8, AC9, EC8
- architecture: `docs/architecture/system-overview.md` (T01)
- acceptance criteria: AC8 — redactado sin jerga técnica; AC9 — disponible antes de crear el ticket

## Scope
- Integración con OpenAI API usando modelo **GPT-4o** (decisión OQ3 resuelta)
- Diseñar prompt que convierte hallazgos técnicos en descripción de impacto para el usuario
- Cada entrada debe incluir: qué falla en términos del usuario, cómo reproducirlo, qué se esperaba vs qué pasó
- Estructurar siguiendo el esquema común (mismo que T08)
- Manejar EC8: si el modelo no está disponible, marcar el reporte de negocio como `pending` y continuar el flujo

## Out of Scope
- Generar el reporte técnico (eso es T08)
- Fine-tuning del modelo (NG4)

## Files Likely Affected
- `src/agents/business_reporter.py` (nuevo)
- `src/clients/openai_client.py` (nuevo)
- `src/prompts/business_report_prompt.py` (nuevo)
- `tests/agents/test_business_reporter.py` (nuevo)

## Constraints
- El cliente del modelo de negocio debe ser intercambiable (GPT ↔ Gemini) con mínimo cambio de config
- El reporte NO debe incluir nombres de archivos ni funciones — solo términos de negocio
- Manejar EC8 con graceful degradation: el flujo no se bloquea si este agente falla

## Validation Commands
- `pytest tests/agents/test_business_reporter.py`
- Test AC8: verificar que el output no contiene términos como `function`, `class`, `import`, `null`, nombres de archivos
- Test EC8: simular fallo del cliente y verificar que el flujo continúa con reporte marcado como `pending`

## Done Criteria
- El agente genera reporte de negocio en lenguaje natural siguiendo el esquema común
- AC8 cumplido: output libre de jerga técnica
- EC8 manejado: fallo del modelo no bloquea el flujo
- Tests con hallazgos de ejemplo y verificación del tono del output

## Risks
- GPT-4o tiene costo por token — definir límite de tokens por ejecución (OQ4) durante implementación

## Handoff
Next recommended role: Backend Engineer
Notes: Depende de T06. Puede ejecutarse en paralelo con T08. Prerequisito de T10. ✅ OQ3 resuelto: GPT-4o (OpenAI).
