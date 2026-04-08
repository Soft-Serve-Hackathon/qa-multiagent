# Task

## Title
T10 — Implementar integración con herramientas de gestión (Jira / Trello)

## Goal
Implementar la capa de abstracción y al menos un adaptador concreto (Jira o Trello) para crear tickets automáticamente con los reportes técnico y de negocio combinados.

## Source
- spec: `docs/specs/mvp/spec.md` — FR12, FR13, FR14, AC10, AC11, AC12, EC4, OQ1
- architecture: `docs/architecture/system-overview.md` (T01)
- acceptance criteria: AC10 — ticket creado exitosamente; AC11 — contiene ambas perspectivas; AC12 — incluye link al PR

## Scope
- Definir interfaz abstracta `TicketProvider` con método `create_ticket(ticket_data)`
- Implementar `JiraAdapter` (decisión OQ1 resuelta: Jira en el MVP)
- El ticket debe incluir: título, sección técnica, sección de negocio, severidad, archivos afectados, link al PR
- Configuración del board/proyecto objetivo vía variables de entorno
- Manejar EC4: reintentar en caso de error de API; si persiste, serializar el ticket como JSON local para creación manual

## Out of Scope
- Implementar el segundo adaptador (queda para post-MVP)
- Interfaz de gestión de tickets (solo creación)

## Files Likely Affected
- `src/adapters/ticket_provider.py` (nuevo — interfaz abstracta)
- `src/adapters/jira_adapter.py` (nuevo)
- `src/models/ticket.py` (nuevo — modelo de datos del ticket)
- `tests/adapters/test_ticket_adapter.py` (nuevo)

## Constraints
- Las credenciales (API key, board ID) deben venir de variables de entorno, nunca hardcodeadas
- El modelo `Ticket` debe ser independiente del proveedor
- EC4 debe manejarse: máximo 3 reintentos con backoff antes de serializar localmente

## Validation Commands
- `pytest tests/adapters/test_ticket_adapter.py` (con mock del cliente HTTP)
- Test de integración: crear un ticket real en el board de prueba y verificar que aparece
- Test AC11: verificar que el ticket tiene secciones diferenciadas técnica y de negocio
- Test EC4: simular error 500 de la API y verificar el comportamiento de retry

## Done Criteria
- Interfaz abstracta `TicketProvider` implementada
- Al menos un adaptador concreto funcional y testeado
- AC10, AC11 y AC12 cumplidos
- EC4 manejado con retry y fallback a JSON local
- Variables de entorno documentadas en `.env.example`

## Risks
- La abstracción `TicketProvider` facilita agregar Trello post-MVP sin reescribir lógica

## Handoff
Next recommended role: Backend Engineer
Notes: Depende de T08 y T09. ✅ OQ1 resuelto: implementar JiraAdapter. Prerequisito de T11.
