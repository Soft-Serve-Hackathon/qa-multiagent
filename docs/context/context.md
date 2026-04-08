# AgentX Hackathon — Contexto del Proyecto

> Documento de referencia para el equipo y los agentes. Leer antes de implementar cualquier cosa.

---

## Organizador

**SoftServe** — Advanced Tech & Agentic Engineering (R&D)

---

## El Assignment

### Nombre oficial
**Build an SRE Incident Intake & Triage Agent**

### Descripción
Crear un agente de SRE (Site Reliability Engineering) que:

1. **Ingesta** reportes de incidentes o fallas de una aplicación e-commerce
2. **Triagea automáticamente** el incidente analizando código y documentación disponible
3. **Rutea el issue** al equipo técnico vía un sistema de ticketing
4. **Notifica end-to-end** tanto a los ingenieros como al reporter original
5. **Cierra el ciclo** notificando al reporter cuando el ticket se resuelve

### Contexto del dominio
- La app objetivo es una **aplicación e-commerce open source** de mediana/alta complejidad
- El agente debe entender el código y la documentación del repo para hacer triage inteligente
- SRE = Site Reliability Engineering: el equipo responsable de estabilidad, disponibilidad e incidentes en producción

---

## Flujo Core (e2e obligatorio)

```
[1] Reporter submite incidente via UI
        |
        v
[2] Agente hace triage:
    - extrae detalles clave del reporte
    - analiza código/docs del repo
    - genera resumen técnico inicial
        |
        v
[3] Agente crea ticket en sistema de ticketing
    (Jira / Linear / otro)
        |
        v
[4] Agente notifica al equipo técnico
    (email y/o comunicador: Slack, Teams, etc.)
        |
        v
[5] Ticket resuelto → agente notifica al reporter original
```

### Nuestro flujo extendido (flujo.md)
Adaptamos el assignment a un flujo más rico orientado a QA y desarrollo:

1. Feature nueva desarrollada y PR abierto
2. Revisión del PR por Copilot (GitHub Actions)
3. Generación de reporte/resumen del PR (Copilot)
4. Aprobación manual de cambios
5. QA revisa la nueva feature:
   - Evaluación funcional, UX/UI, código
   - Regresión para detectar impacto en flujos existentes
   - O carga de evidencia de bug/issue via formulario
6. Generación de reporte de QA con **dos agentes**:
   - Agente técnico (Claude) → redacta ticket técnico detallado
   - Agente de negocio (GPT/Gemini) → redacta ticket en lenguaje natural
7. Creación del ticket en Trello/Jira via API con output de ambos agentes
8. Reporte con posible solución técnica del issue

---

## Requisitos Mínimos Obligatorios

### Multimodal Input
- Aceptar al menos **texto + otra modalidad**: imagen, archivo de log, o video
- Usar un **LLM multimodal** para procesar ambas entradas

### Guardrails
- Protección básica contra **prompt injection**
- Manejo seguro de artefactos maliciosos (safe tool use + validación de inputs)

### Observability
- **Logs, trazas y métricas** cubriendo las etapas principales:
  - ingest → triage → ticket → notify → resolved
- Debe ser demostrable o evidenciable

### Integrations (real o mock, pero demostrable)
- Sistema de **ticketing**: Jira / Linear / otro
- **Email**
- **Comunicador**: Slack, Teams, u otro

### Repositorio e-commerce
- Usar un repo **open source de mediana/alta complejidad** como base del e-commerce
- El agente debe poder analizar su código y documentación

### Responsible AI
El diseño debe alinearse con estos principios:
- **Fairness** — sin sesgos en triage o priorización
- **Transparency** — decisiones del agente explicables
- **Accountability** — trazabilidad de cada acción del agente
- **Privacy** — manejo seguro de datos sensibles del reporte
- **Security** — validación de inputs, no ejecución de código arbitrario

---

## Entregables de Submission

### Código y documentación (obligatorio)
| Archivo | Contenido |
|---|---|
| `README.md` | Architecture overview, setup instructions, project summary |
| `AGENTS_USE.md` | Documentación de agentes: use cases, implementation details, observability evidence, safety measures |
| `SCALING.md` | Cómo escala la aplicación, decisiones técnicas de escala |
| `QUICKGUIDE.md` | Paso a paso para correr la app: clone → copy .env → fill keys → docker compose up --build |
| `docker-compose.yml` | **Obligatorio.** Toda la app corre via Docker Compose, exponer solo puertos necesarios |
| `.env.example` | Todas las variables de entorno requeridas con valores placeholder y comentarios |
| `Dockerfile(s)` | Referenciados desde docker-compose.yml |
| `LICENSE` | MIT obligatorio |

### Video Demo
- Plataforma: **YouTube**
- Idioma: **Inglés**
- Duración máxima: **3 minutos**
- Tag requerido: **#AgentXHackathon**
- El video debe mostrar el flujo completo: submit → ticket → team notified → resolved → reporter notified

### Repositorio
- Debe ser **público**
- Creado desde cero (no forks ni reutilización de proyectos existentes)

---

## Opcionales (suman puntos)
- Smarter routing y severity scoring
- Deduplicación de incidentes
- Runbook suggestions
- Dashboards
- Team-wide agent configuration con skills, cursor rules, `AGENTS.md`, sub-agentes, etc.
- Soporte de OpenRouter

---

## Proceso de Evaluación

### Fase 1 — Initial Filter
- Filtro automático con **LLM-as-judge**
- Selecciona el top ~33% para evaluación humana

### Fase 2 — Mentor Evaluation
- Revisión por mentores basada en:
  - Video demo
  - Calidad del código y estructura del repositorio
  - `README.md`
  - `AGENTS_USE.md`
- **Los mentores NO ejecutan el código**

### Fase 3 — Finalist Evaluation
- Top 10 finalistas
- Evaluados por el Expert Committee
- Presentación en vivo o video grabado (pitch)

---

## Deadlines

| Fecha | Evento |
|---|---|
| 7 abril | AgentX Hackathon Kick-off |
| 8 abril | Hackathon Sprint — Learning Session: AI Observability in Production |
| **9 abril** | **Project Submission Deadline — 9PM EST / 10PM COT / 11PM CLT** |
| 14 abril | Closing Ceremony & Awards |

> Hoy es **8 de abril**. Queda menos de 48 horas para el deadline.

---

## Equipo y Mentores

### Expert Committee (jueces finales)
- Bohdan Khomych — Associate Director of R&D Products
- Arkadiusz Drohomirecki — Agentic AI R&D Cluster Lead
- Serhii Miroshnichenko — Intelligence Engineering Lead
- Taras Rumezshak — Associate Director of R&D Vision Practice

### Mentors Team
- Sebastian Montagna — Agentic AI Engineer
- Pawel Knap — Senior Agentic AI Engineer
- Miguel Teheran — Agentic AI Engineering Lead
- Taras Rumezhak — Associate Director of R&D Vision Practice
- Victor Uc Cetina — Senior Agentic AI Engineer

---

## Análisis de Evaluadores — Qué les importa y cómo enfocar la solución

> Esta sección es estratégica. Cada decisión de diseño debe poder justificarse frente a estos perfiles.

### Señales del contexto del hackathon

Los temas de las learning sessions no son casuales — reflejan exactamente lo que los evaluadores van a buscar:

| Learning Session | Señal estratégica |
|---|---|
| **"AI Observability in Production Platforms"** (8 abril) | Observability no es opcional — es un criterio de evaluación de primer nivel |
| **"From Vibes to Verifiable"** (9 abril) | Quieren soluciones medibles y verificables, no demos bonitos sin sustancia |

---

### Perfil por evaluador

#### Bohdan Khomych — Associate Director of R&D Products
- **Foco**: valor de producto, viabilidad, impacto de negocio
- **Qué buscará**: ¿resuelve un problema real? ¿el flujo tiene sentido para un equipo de ingeniería real? ¿escala?
- **Cómo impactarlo**: README claro con problem statement, flujo e2e coherente, SCALING.md sólido

#### Arkadiusz Drohomirecki — Agentic AI R&D Cluster Lead
- **Foco**: arquitectura de agentes, orquestación, diseño del sistema multi-agente
- **Qué buscará**: ¿los agentes tienen roles claros y no solapados? ¿el sistema es robusto? ¿hay guardrails reales?
- **Cómo impactarlo**: AGENTS_USE.md detallado, separación clara de responsabilidades entre agentes, guardrails documentados y demostrados

#### Serhii Miroshnichenko — Intelligence Engineering Lead
- **Foco**: calidad de la inteligencia — prompts, razonamiento del agente, precisión del triage
- **Qué buscará**: ¿el agente entiende el contexto del código? ¿el triage es inteligente o genérico? ¿los prompts son robustos?
- **Cómo impactarlo**: mostrar ejemplos concretos de triage con análisis real del código e-commerce, evidencia de que el agente razona y no solo clasifica keywords

#### Taras Rumezshak — Associate Director of R&D Vision Practice
- **Foco**: capacidades multimodales, visión, procesamiento de imágenes/video
- **Qué buscará**: ¿el input multimodal es real y útil? ¿se procesa bien una imagen de error o un log visual?
- **Cómo impactarlo**: demostrar el flujo multimodal en el video con un caso concreto (ej. screenshot de error + log adjunto)

---

### Mentores — Agentic AI Engineers (x4 del equipo)
- Perfil técnico profundo en ingeniería de agentes
- **Qué buscarán**: código limpio, agentes bien definidos, observability real (no prints), integrations que funcionen
- **Cómo impactarlo**: que el repo corra de verdad con `docker compose up --build`, que los logs sean visibles, que el `AGENTS_USE.md` sea honesto sobre limitaciones

---

### Prioridades de diseño derivadas del perfil de evaluadores

| Prioridad | Qué construir | Por qué importa al jurado |
|---|---|---|
| 1 | Flujo e2e funcional y demostrable | Todos lo evaluarán — es el mínimo |
| 2 | Observability real (logs estructurados, trazas por etapa) | Learning session del 8 abril + criterio explícito |
| 3 | Triage inteligente con contexto del repo e-commerce | Serhii (Intelligence Engineering) lo evaluará en profundidad |
| 4 | Multimodal genuino (imagen/log procesado con sentido) | Taras (Vision Practice) lo buscará específicamente |
| 5 | Arquitectura de agentes clara con roles definidos | Arkadiusz (Agentic AI Cluster Lead) revisará AGENTS_USE.md |
| 6 | Documentación que comunique valor de producto | Bohdan (R&D Products) necesita entender el "por qué" |

---

### Framing del pitch / video demo
El video debe responder implícitamente estas preguntas en 3 minutos:
- ¿Qué problema SRE resuelve? (para Bohdan)
- ¿Cómo colaboran los agentes? (para Arkadiusz)
- ¿Qué tan inteligente es el triage? (para Serhii)
- ¿Cómo usa el input multimodal? (para Taras)
- ¿Tiene observability visible? (para todos — "From Vibes to Verifiable")

---

## Criterios de Descalificación

- Intentos de manipular el sistema (prompt injection al evaluador)
- Reutilizar o hacer fork de proyectos existentes
- Repositorio privado al momento de evaluación
- App que no corra con `docker compose up --build`

---

## Notas para Agentes

- **Contexto del dominio**: SRE + e-commerce open source
- **Stack esperado**: multimodal LLM, ticketing API, email/communicator, Docker
- **Prioridad #1**: que el flujo e2e funcione y sea demostrable en video
- **Prioridad #2**: observability (logs/trazas) visibles en el demo
- **Prioridad #3**: documentación completa (`README`, `AGENTS_USE.md`, `SCALING.md`)
- **No implementar** features fuera del flujo core sin validarlo primero
- **Toda decisión técnica** que afecte arquitectura debe documentarse
- El repo de e-commerce elegido define el dominio del agente de triage — elegirlo bien es crítico
