# Domain Model — QA Multiagente

**Versión:** 0.1  
**Fecha:** 2026-04-08

---

## Entidades principales

### PullRequest
Representa el PR de GitHub que dispara el flujo.

```
PullRequest
├── id: int
├── number: int
├── title: str
├── author: str
├── base_branch: str
├── head_branch: str
├── diff: str                  # diff completo (puede estar truncado)
├── files_changed: list[str]   # rutas de archivos modificados
├── url: str
└── is_approved: bool          # resultado del gate de aprobación manual
```

---

### Finding
Un hallazgo individual detectado por el QA Agent.

```
Finding
├── id: str                    # uuid generado
├── file: str                  # ruta del archivo afectado
├── function: str | None       # función o clase afectada
├── line: int | None           # línea aproximada
├── description: str           # descripción del problema
├── severity: Literal["critical", "high", "medium", "low"]
├── type: Literal["bug", "antipattern", "code_smell", "regression_risk"]
├── confidence: float          # 0.0–1.0, certeza del agente
└── source: Literal["pr_analysis", "bug_report"]  # Flujo A o B
```

---

### TechnicalReport
Reporte técnico generado por Claude a partir de los hallazgos.

```
TechnicalReport
├── pr_url: str | None         # link al PR de origen (None si viene del Flujo B)
├── findings: list[FindingDetail]
│   └── FindingDetail
│       ├── finding_id: str    # referencia al Finding
│       ├── file: str
│       ├── function: str | None
│       ├── description: str   # descripción técnica expandida
│       ├── severity: str
│       └── estimated_stack_trace: str | None
├── impacted_modules: list[str]  # del análisis de regresión
├── test_coverage_note: str    # nota sobre cobertura de tests (o ausencia)
└── generated_at: datetime
```

---

### BusinessReport
Reporte en lenguaje natural generado por GPT-4o.

```
BusinessReport
├── pr_url: str | None
├── findings: list[BusinessFinding]
│   └── BusinessFinding
│       ├── finding_id: str    # referencia al Finding
│       ├── user_impact: str   # qué falla en términos del usuario
│       ├── steps_to_reproduce: str
│       ├── expected_behavior: str
│       ├── actual_behavior: str
│       └── severity_label: str  # "crítico", "importante", "menor"
├── status: Literal["complete", "pending"]  # "pending" si GPT-4o falló (EC8)
└── generated_at: datetime
```

---

### Ticket
Modelo de ticket independiente del proveedor de gestión.

```
Ticket
├── title: str
├── technical_section: str     # contenido del TechnicalReport formateado
├── business_section: str      # contenido del BusinessReport formateado
├── severity: str              # severidad más alta de los hallazgos
├── affected_files: list[str]
├── pr_url: str | None
├── provider_ticket_id: str    # ID del ticket creado en Jira (ej: "QA-42")
└── provider_ticket_url: str   # URL del ticket en Jira
```

---

### SolutionProposal
Propuesta de solución técnica generada por Claude para un hallazgo.

```
SolutionProposal
├── finding_id: str
├── approach: str              # descripción del enfoque sugerido
├── files_to_modify: list[str] # archivos que deben cambiarse
├── risk_notes: str            # consideraciones de riesgo de la solución
└── jira_comment_id: str       # ID del comentario creado en Jira
```

---

### BugReport (Flujo B)
Evidencia de bug enviada via formulario externo.

```
BugReport
├── title: str
├── description: str
├── steps_to_reproduce: str
├── expected_behavior: str
├── actual_behavior: str
├── context: str | None        # información adicional opcional
└── submitted_at: datetime
```

---

## Relaciones entre entidades

```
PullRequest ──────────────────► Finding[] (1 PR genera N hallazgos)
BugReport  ──────────────────► Finding[] (1 reporte genera N hallazgos)

Finding[] ───┬──────────────► TechnicalReport (N hallazgos → 1 reporte técnico)
             └──────────────► BusinessReport  (N hallazgos → 1 reporte de negocio)

TechnicalReport + BusinessReport ──► Ticket (se combinan en 1 ticket)

Finding[] ──────────────────────► SolutionProposal[] (1 hallazgo → 1 propuesta)
SolutionProposal ───────────────► Ticket (adjunta como comentario)
```
