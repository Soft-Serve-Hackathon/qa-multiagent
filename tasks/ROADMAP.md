# Roadmap de Tareas — MVP QA Multiagente

**Estado:** En progreso  
**Última actualización:** 2026-04-08

---

## Orden de ejecución y dependencias

```
T01 — Arquitectura base
 ├── T02 — GitHub Actions workflow
 │    └── T04 — Agente revisión PR ← T03 (GitHub client)
 │         └── T05 — Gate aprobación manual
 │              └── T06 — QA Agent: análisis código
 │                   ├── T07 — QA Agent: regresión
 │                   ├── T08 — Reporte técnico (Claude)
 │                   │    └── T10 — Integración tickets
 │                   │         └── T11 — Propuesta solución
 │                   │              └── T12 — Flujo B (formulario)
 │                   └── T09 — Reporte negocio (GPT/Gemini)
 │                        └── T10 (mismo nodo)
 └── T03 — GitHub API client
```

---

## Tabla de tareas

| ID | Título | Fase | Rol | Depende de | Estado |
|---|---|---|---|---|---|
| T01 | Arquitectura base del sistema | Fase 1 | Architect | — | pendiente |
| T02 | GitHub Actions workflow (PR trigger) | Fase 1 | Backend | T01 | pendiente |
| T03 | GitHub API client | Fase 1 | Backend | T01 | pendiente |
| T04 | Agente de revisión de PR (Claude) | Fase 1 | Backend | T02, T03 | pendiente |
| T05 | Gate de aprobación manual | Fase 1 | Backend | T03 | pendiente |
| T06 | QA Agent: análisis de código y bugs | Fase 2 | Backend | T05, T03 | pendiente |
| T07 | QA Agent: análisis de impacto/regresión | Fase 2 | Backend | T06 | pendiente |
| T08 | Agente reporte técnico (Claude) | Fase 3 | Backend | T06, T07 | pendiente |
| T09 | Agente reporte de negocio (GPT/Gemini) | Fase 3 | Backend | T06 | pendiente |
| T10 | Integración tickets Jira/Trello | Fase 4 | Backend | T08, T09 | pendiente |
| T11 | Agente propuesta de solución técnica | Fase 5 | Backend | T06, T10 | pendiente |
| T12 | Flujo B: ingesta de bugs por formulario | Fase 5 | Backend | T06, T08, T09, T10 | pendiente |

---

## Tareas paralelas posibles

- **T02 y T03** pueden desarrollarse en paralelo (misma fase, sin dependencia entre ellas)
- **T08 y T09** deben ejecutarse en paralelo (reportes dual, misma ejecución)
- **T06 y T07** son secuenciales (T07 extiende T06)

---

## Open Questions

| OQ | Pregunta | Estado | Decisión |
|---|---|---|---|
| OQ1 | ¿Jira o Trello primero? | ✅ Resuelto | Jira |
| OQ2 | ¿Qué formulario para bugs? | ✅ Resuelto | Google Forms o Notion (externo, webhook) |
| OQ3 | ¿GPT-4o o Gemini 1.5 Pro? | ✅ Resuelto | GPT-4o (OpenAI) |
| OQ4 | ¿Tokens máximos por ejecución? | ⏳ Pendiente | Definir durante implementación de cada agente |
| OQ5 | ¿Propuesta como campo o comentario? | ✅ Resuelto | Comentario del ticket en Jira |
