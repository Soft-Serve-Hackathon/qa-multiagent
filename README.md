# Project Name

Repositorio base para desarrollar una idea y convertirla en un MVP usando una metodología híbrida de:

- Spec Driven Development
- agentes especializados de IA
- documentación versionada
- validación incremental

## Objetivo

Este repositorio existe para:

1. refinar una idea de producto
2. convertirla en especificaciones claras
3. dividir el trabajo en tareas pequeñas
4. implementar un MVP con validación técnica y funcional
5. documentar decisiones, riesgos y handoffs

## Flujo de trabajo

1. Refinar idea en `docs/idea/`
2. Consolidar una spec en `docs/specs/mvp/`
3. Revisar impacto técnico en `docs/architecture/`
4. Crear tareas en `tasks/active/`
5. Implementar en `src/` y `tests/`
6. Validar con `scripts/validate.sh`
7. Mover tarea a `tasks/done/`

## Roles disponibles

- Product Analyst
- Architect
- Backend Engineer
- Frontend Engineer
- QA Engineer
- Security Engineer

## Reglas principales

- Ningún cambio inicia sin contexto documentado.
- Toda tarea debe tener definición de terminado.
- Toda implementación debe incluir validación.
- Las decisiones importantes se documentan.

## Estructura

- `docs/idea/`: refinamiento de problema, usuarios y preguntas abiertas
- `docs/specs/`: especificaciones funcionales
- `docs/architecture/`: decisiones técnicas y contratos
- `tasks/`: trabajo delegable entre agentes
- `.claude/`: agentes y comandos para Claude
- `.github/`: instrucciones y agentes para Copilot

## Estado actual

Fase inicial de definición de idea y levantamiento del MVP.