# Task

## Title
T01 — Diseñar la arquitectura base del sistema multiagente

## Goal
Definir la estructura técnica del sistema: módulos, contratos entre agentes, stack tecnológico, y cómo se conectan GitHub Actions, los modelos IA y las herramientas de gestión. Este diseño guía todas las tareas de implementación posteriores.

## Source
- spec: `docs/specs/mvp/spec.md` — Sección 1 (Summary), 6 (User Flow), 7 (FR), 10 (Dependencies)
- architecture: `docs/architecture/` (a crear)
- acceptance criteria: G7 — arquitectura modular de agentes reemplazables por modelo

## Scope
- Definir la estructura de carpetas del proyecto (`src/`, `agents/`, `workflows/`, `adapters/`, etc.)
- Documentar el sistema de módulos: cómo se llama a cada agente y qué contrato expone
- Definir el stack: lenguaje, runtime, librerías principales
- Documentar el flujo de datos entre GitHub Actions → Agentes → Herramientas de gestión
- Crear `docs/architecture/system-overview.md`
- Crear `docs/architecture/domain-model.md`
- Crear ADR para decisiones de stack y estructura de agentes

## Out of Scope
- Implementar cualquier módulo
- Configurar credenciales o secrets reales

## Files Likely Affected
- `docs/architecture/system-overview.md` (nuevo)
- `docs/architecture/domain-model.md` (nuevo)
- `docs/architecture/adr/ADR-001-stack.md` (nuevo)
- `docs/architecture/adr/ADR-002-agent-model.md` (nuevo)

## Constraints
- La arquitectura debe soportar reemplazo de modelos IA sin cambiar lógica de orquestación
- Debe ser compatible con GitHub Actions como runtime de orquestación
- No sobreingeniería: MVP primero

## Validation Commands
- Revisar que `system-overview.md` responde: ¿qué hace cada módulo?, ¿cómo se comunican?
- Revisar que `domain-model.md` define al menos: PR, Hallazgo, Reporte, Ticket, Propuesta
- Revisar que cada ADR tiene Status, Context, Decision y Consequences

## Done Criteria
- `system-overview.md` creado y describe los 5 módulos con sus contratos
- `domain-model.md` creado con entidades principales
- Al menos 2 ADRs escritos (stack y modelo de agentes)
- Estructura de carpetas del proyecto definida en el overview

## Risks
- La arquitectura puede quedar sobrediseñada para el MVP — priorizar simplicidad

## Handoff
Next recommended role: Architect
Notes: Esta tarea es prerequisito de todas las demás. Sin arquitectura definida, no se puede implementar ningún módulo.
