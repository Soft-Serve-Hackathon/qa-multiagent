# Claude Code Workspace Instructions

## Mission
Ayudar a transformar una idea en un MVP usando desarrollo guiado por especificaciones, tareas pequeñas y validación continua.

## Working Rules

1. No implementes cambios sin revisar primero el contexto en `README.md`, `AGENTS.md` y la carpeta `docs/`.
2. Si la idea todavía es ambigua, trabaja primero sobre `docs/idea/` o `docs/specs/` antes de generar código.
3. Siempre propone cambios mínimos, reversibles y verificables.
4. No expandas el alcance sin documentarlo.
5. Si una decisión técnica cambia el diseño, documenta el cambio en `docs/architecture/`.
6. Toda tarea debe terminar con evidencia de validación.

## Preferred Flow

1. revisar idea y open questions
2. consolidar spec
3. revisar arquitectura
4. descomponer tareas
5. implementar una tarea a la vez
6. validar
7. documentar handoff

## Done Checklist

Antes de cerrar una tarea, confirma:

- contexto leído
- archivos impactados identificados
- criterios de aceptación cubiertos
- pruebas o validación ejecutadas
- riesgos documentados
- handoff preparado

## Output Format

Responde preferiblemente con esta estructura:

1. Understanding
2. Plan
3. Changes
4. Validation
5. Risks
6. Handoff

## File Priorities

Prioridad de lectura:

1. `AGENTS.md`
2. `docs/specs/`
3. `docs/architecture/`
4. `tasks/active/`
5. código impactado

## Guardrails

- evita refactors masivos no solicitados
- no borres documentación sin reemplazo claro
- no asumas requisitos no escritos
- si detectas huecos, escríbelos en `docs/idea/open-questions.md` o en el handoff