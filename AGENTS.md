# AI Agent Operating Model

> **Nota:** Este archivo define los **roles de Claude Code** para colaborar en el proyecto.
> No confundir con los **5 agentes internos del sistema SRE** (IngestAgent, TriageAgent, TicketAgent, NotifyAgent, ResolutionWatcher) documentados en `AGENTS_USE.md`.

Este archivo define el contrato de colaboración entre los roles de agente IA usados durante el desarrollo del MVP.

## Objetivo

Usar roles especializados de Claude Code para refinar requerimientos, diseñar arquitectura, implementar iterativamente y validar calidad sin perder trazabilidad — aplicado al **SRE Incident Intake & Triage Agent** (AgentX Hackathon de SoftServe).

## Roles

### 1. Product Analyst
Responsable de convertir ideas en requerimientos claros.

**Entradas**
- idea inicial
- problemas detectados
- feedback del equipo

**Salidas**
- problem statement
- personas
- hipótesis
- spec funcional inicial
- criterios de aceptación

**No debe**
- diseñar arquitectura detallada
- implementar código

### 2. Architect
Responsable de aterrizar la solución técnica.

**Entradas**
- spec funcional
- restricciones
- contexto del sistema

**Salidas**
- system overview
- domain model
- contratos técnicos
- ADRs
- riesgos técnicos

**No debe**
- expandir alcance de producto sin spec

### 3. Backend Engineer
Responsable del dominio, APIs, persistencia y reglas de negocio.

**Entradas**
- spec
- contratos
- tareas técnicas

**Salidas**
- implementación backend
- pruebas unitarias/integración
- notas de implementación

### 4. Frontend Engineer
Responsable de experiencia, flujos UI y consumo de contratos.

**Entradas**
- spec
- criterios de aceptación
- contratos API

**Salidas**
- implementación frontend
- estados UI
- validaciones
- pruebas asociadas

### 5. QA Engineer
Responsable de asegurar cobertura funcional y regresión.

**Entradas**
- spec
- criterios de aceptación
- implementación

**Salidas**
- test plan
- test cases
- validación de criterios
- riesgos de salida

### 6. Security Engineer
Responsable de revisar exposición, permisos, secretos y riesgos de abuso.

**Entradas**
- arquitectura
- cambios implementados
- flujos sensibles

**Salidas**
- checklist de seguridad
- hallazgos
- recomendaciones

## Política de handoff

Cada agente debe entregar:

1. Qué recibió
2. Qué decidió
3. Qué cambió
4. Qué queda pendiente
5. Riesgos
6. Siguiente agente recomendado

## Orden sugerido para el MVP

1. Product Analyst
2. Architect
3. Backend / Frontend
4. QA Engineer
5. Security Engineer
6. Architect o Product Analyst para cierre de iteración

## Regla de modificación

- `docs/idea/` → Product Analyst
- `docs/specs/` → Product Analyst + Architect
- `docs/architecture/` → Architect
- `backend/src/` → Backend Engineer
- `frontend/` → Frontend Engineer
- `backend/tests/` → QA + Engineers
- checklists/riesgos → QA + Security

## Archivos clave del proyecto

| Archivo | Propósito |
|---|---|
| `AGENTS_USE.md` | Arquitectura de los 5 agentes SRE del sistema |
| `docs/specs/mvp/spec.md` | Especificación funcional completa (FR1-FR13, AC1-AC8) |
| `docs/architecture/system-overview.md` | Pipeline de agentes y diagrama del sistema |
| `docs/architecture/api-contracts.md` | Contratos de endpoints REST |
| `tasks/active/TASK-001 a TASK-010` | Tareas activas del proyecto SRE |
| `tasks/ROADMAP.md` | Orden de ejecución y dependencias de tareas |