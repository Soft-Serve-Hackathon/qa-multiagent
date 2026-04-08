# System Overview — QA Multiagente

**Versión:** 0.1  
**Fecha:** 2026-04-08  
**Estado:** Draft

---

## Visión general

El sistema es una plataforma de QA automatizado que orquesta agentes IA especializados a lo largo del ciclo de vida de un Pull Request. GitHub Actions actúa como runtime de orquestación: dispara los agentes en respuesta a eventos del repositorio, y los agentes interactúan con GitHub API, modelos IA y herramientas de gestión de tickets.

```
GitHub (PR event)
       │
       ▼
┌─────────────────────────────────────────────────────┐
│                  GitHub Actions                      │
│  Workflow: pr-review.yml   Workflow: qa-trigger.yml  │
└────────────┬───────────────────────┬────────────────┘
             │                       │ (post-aprobación manual)
             ▼                       ▼
     ┌───────────────┐      ┌─────────────────────┐
     │  PR Reviewer  │      │      QA Agent        │
     │   (Claude)    │      │  ┌───────────────┐   │
     └───────┬───────┘      │  │ Code Analyzer │   │
             │              │  │ (Claude)      │   │
             │ comentario   │  └───────┬───────┘   │
             ▼              │          │            │
         GitHub PR          │  ┌───────▼───────┐   │
                            │  │ Regression    │   │
                            │  │ Analyzer      │   │
                            │  └───────┬───────┘   │
                            └──────────┼────────────┘
                                       │ findings[]
                          ┌────────────┴────────────┐
                          │                         │
                          ▼                         ▼
               ┌──────────────────┐    ┌─────────────────────┐
               │ Technical        │    │ Business Reporter    │
               │ Reporter         │    │ (GPT-4o / OpenAI)   │
               │ (Claude)         │    └──────────┬──────────┘
               └────────┬─────────┘               │
                        │  technical_report        │ business_report
                        └───────────┬─────────────┘
                                    │
                                    ▼
                         ┌──────────────────┐
                         │  Ticket Creator  │
                         │  (Jira Adapter)  │
                         └────────┬─────────┘
                                  │ ticket creado
                                  ▼
                         ┌──────────────────┐
                         │ Solution Proposer│
                         │ (Claude)         │
                         └────────┬─────────┘
                                  │ comentario en ticket Jira
                                  ▼
                               Jira ticket
                               (completo)
```

**Flujo B alternativo:**
```
Google Forms / Notion (webhook)
       │
       ▼
Bug Report Ingestion → QA Agent (desde findings) → mismo pipeline
```

---

## Módulos del sistema

### Módulo 1 — PR Reviewer
| Atributo | Valor |
|---|---|
| Trigger | `pull_request: [opened, reopened, synchronize]` |
| Input | diff del PR, metadatos (título, autor, rama) |
| Modelo | Claude (Anthropic API) |
| Output | Comentario markdown en el PR: resumen, riesgos, recomendaciones |
| Archivos | `src/agents/pr_reviewer.py`, `src/prompts/pr_review_prompt.py` |

### Módulo 2 — QA Agent
| Atributo | Valor |
|---|---|
| Trigger | PR aprobado (gate manual) |
| Input | diff del PR + archivos del repositorio (para análisis de impacto) |
| Modelo | Claude (Anthropic API) |
| Output | `findings[]` — lista de hallazgos con severidad, archivo, función, descripción |
| Archivos | `src/agents/qa_agent.py`, `src/agents/regression_analyzer.py` |

### Módulo 3 — Generación de Reportes Dual
| Atributo | Valor |
|---|---|
| Trigger | `findings[]` disponibles |
| Input | Lista de hallazgos del QA Agent |
| Modelos | Claude (reporte técnico) + GPT-4o (reporte de negocio) |
| Output | `TechnicalReport` + `BusinessReport` siguiendo esquema común |
| Archivos | `src/agents/technical_reporter.py`, `src/agents/business_reporter.py` |
| Ejecución | Paralela — ambos agentes corren simultáneamente |

### Módulo 4 — Ticket Creator
| Atributo | Valor |
|---|---|
| Trigger | Ambos reportes disponibles |
| Input | `TechnicalReport` + `BusinessReport` + metadatos del PR |
| Integración | Jira API (via `JiraAdapter`) |
| Output | Ticket creado en Jira con ambas perspectivas |
| Archivos | `src/adapters/ticket_provider.py`, `src/adapters/jira_adapter.py` |

### Módulo 5 — Solution Proposer
| Atributo | Valor |
|---|---|
| Trigger | Ticket creado en Jira |
| Input | Hallazgos del QA Agent + diff del PR |
| Modelo | Claude (Anthropic API) |
| Output | Propuesta de solución técnica como comentario del ticket en Jira |
| Archivos | `src/agents/solution_proposer.py` |

---

## Estructura de carpetas del proyecto

```
qa-multiagent/
├── .github/
│   └── workflows/
│       ├── pr-review.yml          # Trigger: PR abierto → PR Reviewer
│       └── qa-trigger.yml         # Trigger: PR aprobado → QA pipeline
├── src/
│   ├── agents/
│   │   ├── pr_reviewer.py         # Módulo 1
│   │   ├── qa_agent.py            # Módulo 2 — análisis de código
│   │   ├── regression_analyzer.py # Módulo 2 — análisis de impacto
│   │   ├── technical_reporter.py  # Módulo 3 — reporte técnico
│   │   ├── business_reporter.py   # Módulo 3 — reporte de negocio
│   │   └── solution_proposer.py   # Módulo 5
│   ├── clients/
│   │   ├── github_client.py       # GitHub API (diff, comentarios, reviews)
│   │   ├── claude_client.py       # Anthropic API
│   │   └── openai_client.py       # OpenAI API (GPT-4o)
│   ├── adapters/
│   │   ├── ticket_provider.py     # Interfaz abstracta
│   │   └── jira_adapter.py        # Implementación Jira
│   ├── models/
│   │   ├── finding.py             # Hallazgo individual del QA Agent
│   │   ├── report.py              # Esquema común de reporte (técnico + negocio)
│   │   ├── ticket.py              # Modelo de ticket independiente del proveedor
│   │   └── bug_report.py          # Modelo del formulario de bugs (Flujo B)
│   ├── prompts/
│   │   ├── pr_review_prompt.py
│   │   ├── qa_analysis_prompt.py
│   │   ├── regression_prompt.py
│   │   ├── technical_report_prompt.py
│   │   ├── business_report_prompt.py
│   │   └── solution_prompt.py
│   └── entrypoints/
│       ├── pr_review.py           # Llamado por pr-review.yml
│       ├── qa_trigger.py          # Llamado por qa-trigger.yml
│       └── bug_report_ingestion.py # Webhook del formulario externo (Flujo B)
├── tests/
│   ├── agents/
│   ├── clients/
│   ├── adapters/
│   └── entrypoints/
├── docs/
├── tasks/
├── .env.example                   # Variables de entorno requeridas
└── requirements.txt
```

---

## Variables de entorno requeridas

| Variable | Módulo | Descripción |
|---|---|---|
| `ANTHROPIC_API_KEY` | PR Reviewer, QA Agent, Solution Proposer | API key de Anthropic (Claude) |
| `OPENAI_API_KEY` | Business Reporter | API key de OpenAI (GPT-4o) |
| `GITHUB_TOKEN` | GitHub Client | Token de GitHub Actions (automático en CI) |
| `JIRA_BASE_URL` | Jira Adapter | URL base de la instancia Jira (ej: `https://tuempresa.atlassian.net`) |
| `JIRA_API_TOKEN` | Jira Adapter | API token de Jira |
| `JIRA_EMAIL` | Jira Adapter | Email del usuario de servicio en Jira |
| `JIRA_PROJECT_KEY` | Jira Adapter | Clave del proyecto donde se crean los tickets (ej: `QA`) |

---

## Principios de diseño

1. **Modularidad**: cada agente es un módulo independiente con contrato claro (input/output).
2. **Reemplazabilidad de modelos**: los clientes IA (`claude_client`, `openai_client`) son intercambiables — cambiar de modelo no afecta la lógica del agente.
3. **Graceful degradation**: si un agente falla, el flujo continúa con estado parcial en lugar de bloquearse.
4. **Análisis estático**: no hay ejecución de código ni sandbox — todo es análisis contextual del diff.
5. **Trazabilidad**: cada artefacto (reporte, ticket) referencia el PR de origen.
