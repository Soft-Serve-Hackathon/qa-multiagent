# AI Agent Operating Model

Este archivo define el contrato neutral de colaboración entre agentes IA y humanos.

## Objetivo

Usar agentes especializados para refinar una idea, diseñar un MVP, implementar iterativamente y validar calidad sin perder trazabilidad.

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
- `src/` → Backend / Frontend
- `tests/` → QA + Engineers
- checklists/riesgos → QA + Security