# Copilot Repository Instructions

Este repositorio sigue una metodología basada en especificaciones y agentes especializados.

## Antes de sugerir código

1. revisa `README.md`
2. revisa `AGENTS.md`
3. revisa la spec relevante en `docs/specs/`
4. revisa contratos y decisiones en `docs/architecture/`
5. revisa la tarea activa si existe en `tasks/active/`

## Flujo preferido de trabajo

1. revisar idea y open questions
2. consolidar spec
3. revisar arquitectura
4. descomponer tareas
5. implementar una tarea a la vez
6. validar
7. documentar handoff

## Reglas

- genera cambios pequeños y consistentes con la spec
- no inventes alcance de producto
- evita lógica no validada por criterios de aceptación
- cuando el cambio afecte diseño, sugiere documentarlo
- incluye pruebas o estrategia de validación cuando corresponda
- respeta separación de responsabilidades entre frontend, backend, QA y seguridad

## Prioridades

1. claridad
2. corrección
3. mantenibilidad
4. validabilidad
5. velocidad

## Formato esperado de ayuda

Responde preferiblemente con esta estructura:

1. Understanding
2. Plan
3. Changes
4. Validation
5. Risks
6. Handoff

## Done Checklist

Antes de cerrar una tarea, confirma:

- contexto leído
- archivos impactados identificados
- criterios de aceptación cubiertos
- pruebas o validación ejecutadas
- riesgos documentados
- handoff preparado

## Guardrails

- evita refactors masivos no solicitados
- no borres documentación sin reemplazo claro
- no asumas requisitos no escritos
- si detectas huecos, escríbelos en `docs/idea/open-questions.md` o en el handoff