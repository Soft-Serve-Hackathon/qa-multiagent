# Problem Statement

## Idea inicial
Construir una plataforma de QA automatizada con agentes IA que cubra el ciclo completo desde la apertura de un PR hasta la creación de tickets de bugs en herramientas de gestión (Trello/Jira), integrando múltiples modelos de IA especializados por rol.

## Flujo objetivo

1. **Feature nueva** — el desarrollador termina el trabajo y abre un PR.
2. **Revisión del PR por Copilot** — GitHub Actions dispara un agente que analiza el PR.
3. **Reporte del PR** — el agente genera un resumen estructurado del PR.
4. **Aprobación manual** — un humano revisa y aprueba o solicita cambios.
5. **QA automático** — un agente evalúa UX/UI, código y regresión de la feature. Alternativamente, alguien sube evidencia de un bug/issue a través de un formulario para que el agente lo analice.
6. **Reporte de QA dual** — dos agentes redactan el ticket:
   - Agente técnico (Claude): redacta el ticket en lenguaje técnico.
   - Agente de negocio (GPT o Gemini): redacta el mismo hallazgo en lenguaje natural para stakeholders.
7. **Creación del ticket** — integración con la API de Trello o Jira para crear el ticket con ambas perspectivas.
8. **Propuesta de solución** — un agente genera un reporte con la posible solución técnica del issue encontrado.

## Problema principal
Los equipos de desarrollo pierden tiempo y calidad porque el QA es manual, tardío e inconsistente. Los bugs llegan a producción porque no hay un ciclo automatizado que revise cada PR antes de mergearlo, y cuando se detectan issues en producción, el proceso de documentarlos y asignarlos es lento y depende de la disponibilidad del equipo.

## A quién le duele
- **Desarrolladores**: reciben feedback tardío y sin contexto suficiente.
- **QA Engineers**: hacen trabajo repetitivo y tedioso de documentación.
- **Product Managers / Tech Leads**: no tienen visibilidad rápida de la calidad de cada release.
- **Stakeholders de negocio**: los reportes son muy técnicos o muy vagos, nunca en el formato que necesitan.

## Impacto
Sin esta solución, el equipo sigue dependiendo de revisiones manuales lentas, la deuda técnica y de calidad crece silenciosamente, y los tickets de bugs carecen de la información necesaria para resolverlos rápido.

## Señales de valor
- Tiempo promedio entre PR abierto y ticket creado se reduce.
- Porcentaje de bugs detectados antes de merge aumenta.
- Los tickets creados incluyen suficiente contexto para ser resueltos sin ir al desarrollador original.
- Los stakeholders no técnicos entienden los reportes sin traducción manual.
