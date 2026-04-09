# ADR-001: Selección de Medusa.js como repositorio e-commerce de referencia

## Status
Accepted

## Context
El assignment del hackathon requiere usar un repositorio e-commerce open source de mediana/alta complejidad como base de conocimiento para el agente de triage. El agente necesita analizar el codebase para identificar módulos afectados, citar archivos relevantes y enriquecer el contexto del ticket.

Criterios de selección:
- Código fuente open source disponible en GitHub
- Complejidad real: múltiples módulos de dominio (cart, payment, orders, inventory)
- Documentación de buena calidad para que el agente pueda razonar sobre el dominio
- Activamente mantenido (no un proyecto abandonado)
- Compatible con análisis estático de texto (el agente lee el código, no lo ejecuta)

## Decision
Usar **medusajs/medusa** como repositorio de referencia.

El codebase de Medusa.js se clona durante el build de Docker (tag estable v1.20.x) y se monta como volumen read-only en `/app/medusa-repo`. El TriageAgent accede al código via la herramienta `read_ecommerce_file(path)` que lee archivos del directorio montado.

Para reducir latencia en tiempo real, el agente pre-indexa solo los módulos más relevantes para triage:
- `packages/medusa/src/services/` — lógica de negocio
- `packages/medusa/src/api/routes/store/` — endpoints del storefront

## Consequences

**Positivos:**
- TypeScript bien tipado → el agente puede hacer análisis semántico del código con alta precisión
- Dominio e-commerce rico: cart, payment, orders, inventory, shipping, discounts
- Alta complejidad real → el triage es no-trivial y demuestra capacidad de razonamiento del agente
- Repo activo con documentación de calidad

**Negativos / Trade-offs:**
- El repo de Medusa.js es grande (~500MB completo). Se mitiga clonando solo la versión estable y pre-indexando un subset de directorios.
- El agente necesita un prompt system bien diseñado para orientarse en el codebase. Se resuelve con un índice de módulos en el system prompt del TriageAgent.

## Alternatives Considered

**Saleor** (Python/Django):
- Descartado: diferencia de stack con el resto del sistema (Python backend analizando Python code crea riesgo de confusión en el LLM entre el código del agente y el código analizado). El TypeScript de Medusa.js es más distinguible.

**Spree Commerce** (Ruby on Rails):
- Descartado: Ruby es menos familiar para el equipo y la documentación es menos estructurada para análisis automatizado.

**Magento** (PHP):
- Descartado: complejidad de licencia y overhead de setup en Docker demasiado alto para el tiempo disponible.
