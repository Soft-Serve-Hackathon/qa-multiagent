# MVP Spec — Plataforma de QA Automatizado con Agentes IA

**Versión:** 0.1  
**Fecha:** 2026-04-07  
**Estado:** Draft  
**Autor:** Product Analyst (IA) + Decisiones del equipo

---

## 1. Summary

Construir una plataforma modular de QA automatizado que cubra el ciclo completo desde la apertura de un Pull Request hasta la creación automática de tickets en herramientas de gestión (Jira/Trello). El sistema orquesta múltiples agentes IA especializados por rol: análisis de código (Claude), reporte en lenguaje natural de negocio (GPT/Gemini), y generación de propuestas de solución técnica (Claude). La implementación será iterativa por fases, comenzando por la integración con GitHub y terminando con el sistema de tickets y soluciones.

---

## 2. Problem Statement

Los equipos de desarrollo pierden tiempo y calidad porque el QA es manual, tardío e inconsistente:
- Los PRs se mergean sin revisión de calidad automatizada.
- Cuando se detectan bugs, documentarlos y asignarlos es lento y depende de personas disponibles.
- Los tickets resultantes carecen de contexto suficiente para resolverlos sin consultar al autor.
- Los stakeholders no técnicos no entienden los reportes técnicos, y los técnicos no confían en reportes simplificados.

---

## 3. Target Users

| Rol | Contexto de uso |
|---|---|
| **Desarrollador** | Abre un PR y recibe feedback automatizado antes del merge |
| **QA Engineer** | Recibe reportes automáticos y supervisa la evaluación del agente |
| **Tech Lead / Reviewer** | Hace la aprobación manual del paso 4 con contexto suficiente |
| **Product Manager / Stakeholder** | Consume el reporte en lenguaje natural sin necesidad de traducción |

---

## 4. Goals

- **G1:** Automatizar la revisión de PRs con un agente IA integrado a GitHub Actions.
- **G2:** Generar un reporte estructurado de cada PR (resumen, cambios, riesgos detectados).
- **G3:** Implementar un agente QA que analice código del PR, detecte posibles bugs y evalúe regresión básica.
- **G4:** Generar dos versiones del reporte de hallazgos: técnica (Claude) y de negocio (GPT/Gemini).
- **G5:** Crear tickets automáticamente en Jira o Trello vía API con ambas perspectivas del reporte.
- **G6:** Generar una propuesta de solución técnica para cada issue detectado.
- **G7:** Diseñar la arquitectura como sistema modular de agentes y subagentes, reemplazables por modelo.

---

## 5. Non-Goals

- **NG1:** No se construirá interfaz gráfica (UI) propia en el MVP — la interacción es vía GitHub, formularios y las herramientas de gestión existentes.
- **NG2:** No se harán pruebas de ejecución de código (no hay sandbox de runtime) — el QA es análisis estático y contextual del PR.
- **NG3:** No se implementará revisión de UX/UI visual (capturas de pantalla, Figma) en el MVP — queda para una fase posterior.
- **NG4:** No se hará fine-tuning de modelos — se usan los modelos base via API.
- **NG5:** No se reemplazará el proceso de aprobación humana — el paso 4 siempre requiere acción manual.
- **NG6:** No se soportará más de un repositorio de GitHub simultáneamente en el MVP.

---

## 6. User Flow

### Flujo A — PR de feature nueva

```
1. Dev abre un PR en GitHub
       ↓
2. GitHub Actions dispara el agente de revisión (Claude)
       ↓
3. El agente analiza el diff, genera reporte del PR y lo publica como comentario en el PR
       ↓
4. Reviewer humano lee el reporte, aprueba o solicita cambios (acción manual en GitHub)
       ↓
5. Al aprobarse el PR, el agente QA analiza el código:
   - detecta bugs potenciales
   - evalúa cobertura de tests existentes
   - ejecuta análisis de regresión básica (cambios que impactan otros módulos)
       ↓
6. Se generan dos reportes de hallazgos:
   - Reporte técnico (Claude): stack trace, función afectada, severidad técnica
   - Reporte de negocio (GPT/Gemini): descripción en lenguaje natural, impacto para el usuario
       ↓
7. Se crea un ticket en Jira o Trello vía API con ambas perspectivas incluidas
       ↓
8. Claude genera una propuesta de solución técnica y la adjunta al ticket
```

### Flujo B — Reporte manual de bug/issue

```
1. Usuario completa un formulario con evidencia del bug (descripción, pasos, screenshots opcionales)
       ↓
2. El agente QA recibe la evidencia y la analiza
       ↓
3. Continúa desde el paso 6 del Flujo A
```

---

## 7. Functional Requirements

### Módulo 1 — Integración GitHub / PR Review
- **FR1:** El sistema debe detectar automáticamente la apertura de un PR vía GitHub Actions webhook.
- **FR2:** El agente de revisión debe analizar el diff del PR (archivos cambiados, líneas agregadas/eliminadas).
- **FR3:** El agente debe publicar un comentario estructurado en el PR con: resumen del cambio, riesgos identificados y recomendaciones.
- **FR4:** El sistema debe esperar confirmación de aprobación manual antes de continuar al paso 5.

### Módulo 2 — QA Agent
- **FR5:** El agente QA debe analizar el código del PR en busca de bugs potenciales, antipatrones y code smells.
- **FR6:** El agente debe identificar qué módulos o funciones existentes pueden verse afectadas por los cambios del PR (análisis de impacto básico).
- **FR7:** El agente debe generar una lista priorizada de hallazgos con severidad (crítico, alto, medio, bajo).
- **FR8:** El sistema debe aceptar evidencia externa de bugs mediante formulario (texto, pasos para reproducir, contexto).

### Módulo 3 — Generación de Reportes Dual
- **FR9:** Claude debe generar un reporte técnico con: función/archivo afectado, descripción técnica del issue, severidad, stack trace estimado si aplica.
- **FR10:** GPT o Gemini debe generar un reporte en lenguaje natural con: descripción del impacto para el usuario, pasos para reproducir, comportamiento esperado vs actual.
- **FR11:** Ambos reportes deben estructurarse siguiendo un esquema común para poder combinarse en el ticket.

### Módulo 4 — Integración con Herramientas de Gestión
- **FR12:** El sistema debe soportar creación de tickets en Jira y en Trello mediante una capa de abstracción.
- **FR13:** El ticket creado debe incluir: título, descripción técnica, descripción de negocio, severidad, archivos afectados y link al PR.
- **FR14:** El sistema debe poder configurarse para apuntar a un board/proyecto específico de Jira o Trello.

### Módulo 5 — Propuesta de Solución Técnica
- **FR15:** Claude debe generar una propuesta de solución para cada hallazgo, incluyendo: enfoque sugerido, archivos a modificar, consideraciones de riesgo.
- **FR16:** La propuesta debe adjuntarse al ticket creado (como campo adicional o comentario).

---

## 8. Acceptance Criteria

### PR Review (pasos 1-4)
- **AC1:** Dado que se abre un PR, el agente publica un comentario en menos de 5 minutos con al menos: resumen del cambio y lista de riesgos.
- **AC2:** El comentario del agente sigue un formato consistente y legible (markdown estructurado).
- **AC3:** El sistema no continúa al paso 5 si el PR no tiene al menos una aprobación humana registrada.

### QA Agent (paso 5)
- **AC4:** El agente identifica al menos un hallazgo por PR que contenga código con antipatrones conocidos.
- **AC5:** El análisis de impacto menciona al menos los módulos directamente importados o llamados por el código modificado.
- **AC6:** El formulario de evidencia manual produce el mismo tipo de reporte que el análisis automático del PR.

### Reportes (paso 6)
- **AC7:** El reporte técnico incluye: nombre del archivo, función afectada, descripción técnica y severidad.
- **AC8:** El reporte de negocio está redactado en español (o idioma configurado) sin jerga técnica.
- **AC9:** Ambos reportes son generados en la misma ejecución y están disponibles antes de crear el ticket.

### Ticket (paso 7)
- **AC10:** El ticket se crea exitosamente en el board/proyecto configurado de Jira o Trello.
- **AC11:** El ticket contiene ambas perspectivas (técnica y negocio) como secciones diferenciadas.
- **AC12:** El ticket incluye el link al PR de origen cuando aplica.

### Propuesta de solución (paso 8)
- **AC13:** Cada ticket creado tiene adjunta al menos una propuesta de solución generada por Claude.
- **AC14:** La propuesta menciona al menos: enfoque, archivo(s) a modificar y riesgo de la solución.

---

## 9. Edge Cases

- **EC1:** El PR no tiene diff (PR vacío o solo cambios de merge) — el agente debe notificarlo y no generar reporte de QA.
- **EC2:** El análisis de la IA falla o agota el timeout — el sistema debe reportar el error sin bloquear el flujo humano.
- **EC3:** El formulario de bug se envía con información insuficiente — el agente debe solicitar los campos mínimos antes de procesar.
- **EC4:** La API de Jira/Trello responde con error o el token expira — el sistema debe reintentar y, si falla, dejar el reporte generado disponible para creación manual.
- **EC5:** El PR tiene miles de líneas cambiadas — el agente debe trabajar sobre el diff resumido y advertir que el análisis puede ser parcial.
- **EC6:** Un mismo issue es detectado por ambos agentes (Claude y GPT/Gemini) — se deben deduplicar antes de crear el ticket.
- **EC7:** El repositorio no tiene tests — el agente de regresión debe indicarlo explícitamente en el reporte y no inferir cobertura.
- **EC8:** El modelo GPT/Gemini no está disponible — el sistema debe completar el flujo con solo el reporte técnico de Claude y marcar el reporte de negocio como pendiente.

---

## 10. Dependencies

| Dependencia | Tipo | Notas |
|---|---|---|
| GitHub Actions | Infraestructura | Para disparar los agentes en eventos de PR |
| GitHub API | API externa | Para leer diffs, comentar en PRs y leer estado de aprobaciones |
| Claude API (Anthropic) | API externa | Análisis técnico, QA, propuesta de solución |
| GPT API (OpenAI) — GPT-4o | API externa | Reporte en lenguaje natural de negocio |
| Jira API | API externa | Creación de tickets |
| Google Forms o Notion | Formulario externo | Ingesta de evidencia de bugs (Flujo B) |

---

## 11. Risks

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Los modelos IA generan falsos positivos frecuentes en el QA | Alta | Alto | Agregar umbral de confianza configurable; revisión humana opcional |
| Costos de API (Claude + GPT/Gemini) escalan con el volumen de PRs | Media | Medio | Cachear resultados por hash de diff; definir límite de tokens por ejecución |
| La abstracción Jira/Trello agrega complejidad sin valor inmediato | Baja | Medio | Implementar primero solo Jira o solo Trello; abstraer después |
| El diff de PRs grandes supera el contexto del modelo | Alta | Alto | Implementar chunking o priorización de archivos críticos |
| Dependencia de múltiples APIs externas aumenta puntos de falla | Media | Alto | Circuit breaker por módulo; logs de fallo claros |
| La aprobación manual puede convertirse en bottleneck | Media | Medio | Documentar claramente que es intencional; considerar timeout configurable |

---

## 12. Open Questions

| OQ | Pregunta | Estado | Decisión |
|---|---|---|---|
| OQ1 | ¿Jira o Trello primero? | ✅ Resuelto | **Jira** en el MVP |
| OQ2 | ¿Qué formulario para evidencia de bugs? | ✅ Resuelto | **Google Forms o Notion** (formulario externo) |
| OQ3 | ¿GPT-4o o Gemini 1.5 Pro? | ✅ Resuelto | **GPT-4o** (OpenAI) |
| OQ4 | ¿Tokens máximos por ejecución? | ⏳ Pendiente | Definir durante implementación de cada agente |
| OQ5 | ¿Propuesta como campo del ticket o comentario? | ✅ Resuelto | **Comentario del ticket** en Jira |

---

## Fases de Implementación

| Fase | Alcance | Objetivo |
|---|---|---|
| **Fase 1** | Módulo 1 (PR Review) | GitHub Actions + agente de revisión + comentario en PR |
| **Fase 2** | Módulo 2 (QA Agent) | Análisis de código + detección de bugs + análisis de impacto |
| **Fase 3** | Módulo 3 (Reportes Dual) | Integración Claude + GPT/Gemini + esquema común |
| **Fase 4** | Módulo 4 (Tickets) | Integración Jira/Trello + abstracción |
| **Fase 5** | Módulo 5 (Solución) + Flujo B | Propuesta técnica + formulario de evidencia manual |
