# Documentation Instructions — SRE Incident Triage Agent

## Jerarquía de documentos

```
AGENTS_USE.md          ← arquitectura de agentes (fuente de verdad)
docs/specs/mvp/spec.md ← requisitos funcionales y criterios de aceptación
docs/architecture/
  system-overview.md   ← diagrama de pipeline y módulos
  domain-model.md      ← entidades SQLAlchemy
  api-contracts.md     ← contratos de endpoints
  adr/ADR-001 a 006    ← decisiones arquitectónicas
tasks/active/          ← TASK-001 a TASK-010 (sistema SRE únicamente)
tasks/done/            ← tareas completadas o descartadas
```

## Reglas

- Usa lenguaje claro y verificable. Evita afirmaciones que no se puedan comprobar en el código.
- No mezcles decisiones de producto (spec.md) con decisiones de arquitectura (adr/).
- Mantén trazabilidad: toda tarea en `tasks/active/` debe referenciar FR o AC de `spec.md`.
- Si agregas una decisión técnica importante, crea o actualiza un ADR en `docs/architecture/adr/`.
- Los ADRs siguen la numeración ADR-001 a ADR-006 — el siguiente sería ADR-007.
- No documentes features que no están implementadas como si estuvieran disponibles.
- Al cerrar una tarea, muévela a `tasks/done/` con evidencia de validación en el handoff.
