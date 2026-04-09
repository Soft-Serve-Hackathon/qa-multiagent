# ADR-004: Trello como sistema de ticketing

## Status
Accepted

## Context
El assignment requiere integración con un sistema de ticketing ("Jira / Linear / Other"). El sistema debe crear tickets automáticamente con el análisis técnico del incidente y detectar cuando un ticket es resuelto para cerrar el ciclo de notificación.

El equipo necesita una solución que:
- Tenga API REST accesible (para automatización)
- Permita crear tickets con contexto técnico rico (descripción, etiquetas, checklists)
- Permita detectar cuando un ticket cambia a estado "resuelto"
- Sea gratuita o de bajo costo para el demo
- Sea configurable sin overhead de setup empresarial

## Decision
Usar **Trello** como sistema de ticketing via Trello REST API.

Configuración:
- Un Board de Trello con columnas: "To Do" → "In Progress" → "Done"
- Autenticación: `TRELLO_API_KEY` + `TRELLO_API_TOKEN` (generados en trello.com/app-key)
- Cada incidente crea una **Card** en la columna "To Do" con:
  - Nombre: `[P{severity}] {title}`
  - Descripción: resumen técnico + módulo afectado + archivos sugeridos + trace_id
  - Etiquetas: severidad (color-coded: P1=red, P2=orange, P3=yellow, P4=green)
  - Checklist "Files to investigate": lista de archivos de Medusa.js sugeridos

Detección de resolución:
- **MVP:** ResolutionWatcher hace polling a Trello cada 60 segundos consultando las Cards en la columna "Done"
- **Post-MVP:** Webhook de Trello hacia `POST /api/webhooks/trello` (el endpoint ya existe)

Variables de entorno requeridas:
- `TRELLO_API_KEY` — clave de la aplicación Trello
- `TRELLO_API_TOKEN` — token de autorización del usuario
- `TRELLO_BOARD_ID` — ID del board de incidentes
- `TRELLO_LIST_ID` — ID de la columna "To Do" donde se crean las Cards
- `TRELLO_DONE_LIST_ID` — ID de la columna "Done" para detección de resolución

## Consequences

**Positivos:**
- El equipo ya tiene cuenta de Trello — sin fricción de setup de credenciales
- API REST bien documentada, simple de integrar (key+token, sin OAuth complejo)
- Trello es visualmente claro para el demo: mostrar la Card creada en pantalla es immediato
- Free tier ilimitado para el uso del hackathon
- `MOCK_INTEGRATIONS=true` sigue funcionando si las credenciales no están disponibles en un entorno limpio

**Negativos / Trade-offs:**
- Trello no es "enterprise" — en producción real, Jira o Linear serían más apropiados. Se documenta en `SCALING.md` como migración natural hacia Jira para equipos grandes.
- El polling cada 60 segundos introduce latencia en la notificación de resolución. Se documenta como limitación conocida; los webhooks de Trello resuelven esto en post-MVP.

## Alternatives Considered

**Jira Cloud:**
- Descartado: el equipo no tiene cuenta de Jira Cloud disponible para el demo. La configuración de una cuenta de evaluación durante el hackathon introduce riesgo de tiempo.

**Linear:**
- Alternativa válida técnicamente, pero el equipo ya usa Trello. Se mantiene como opción documentada en `SCALING.md`.

**Trello mock-only:**
- Descartado: el equipo tiene credenciales reales de Trello. Usar la integración real es más valioso para el demo y para la evaluación.
