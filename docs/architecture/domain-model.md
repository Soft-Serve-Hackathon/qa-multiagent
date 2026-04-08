# Domain Model — SRE Incident Intake & Triage Agent

**Version:** 1.0  
**Owner:** Architect  
**Last updated:** 2026-04-08

---

## Entidades del dominio

### Incident
Representa el reporte de incidente recibido del reporter.

```
Incident
├── id                  INTEGER  PRIMARY KEY AUTOINCREMENT
├── trace_id            TEXT     NOT NULL UNIQUE  -- UUID v4, fluye por todo el pipeline
├── title               TEXT     NOT NULL
├── description         TEXT     NOT NULL         -- truncado a 2000 chars
├── reporter_email      TEXT     NOT NULL
├── attachment_type     TEXT                      -- 'image' | 'log' | null
├── attachment_path     TEXT                      -- ruta local: uploads/{trace_id}.{ext}
├── status              TEXT     NOT NULL DEFAULT 'received'
│                                -- 'received' | 'triaging' | 'ticketed' | 'notified' | 'resolved'
├── created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
└── updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
```

### TriageResult
Resultado del análisis del TriageAgent. Producido por Claude claude-sonnet-4-6.

```
TriageResult
├── id                  INTEGER  PRIMARY KEY AUTOINCREMENT
├── incident_id         INTEGER  NOT NULL REFERENCES Incident(id)
├── severity            TEXT     NOT NULL  -- 'P1' | 'P2' | 'P3' | 'P4'
├── affected_module     TEXT     NOT NULL  -- ej. 'cart', 'payment', 'inventory'
├── technical_summary   TEXT     NOT NULL  -- resumen técnico generado por el LLM
├── suggested_files     TEXT     NOT NULL  -- JSON array de rutas de archivos de Medusa.js
├── confidence_score    REAL     NOT NULL  -- 0.0 - 1.0
├── raw_llm_response    TEXT              -- respuesta completa del LLM (para debugging)
└── created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
```

### Ticket
Representa la Card creada en Trello.

```
Ticket
├── id                  INTEGER  PRIMARY KEY AUTOINCREMENT
├── incident_id         INTEGER  NOT NULL REFERENCES Incident(id)
├── trello_card_id      TEXT                      -- null si pendiente de creación
├── trello_card_url     TEXT                      -- URL directa a la Card
├── trello_list_id      TEXT     NOT NULL          -- columna donde se creó (ej. "To Do")
├── status              TEXT     NOT NULL DEFAULT 'pending'
│                                -- 'pending' | 'created' | 'failed'
├── created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
└── resolved_at         DATETIME                  -- cuando se detecta como Done en Trello
```

### NotificationLog
Registro de todas las notificaciones enviadas (Slack + email).

```
NotificationLog
├── id                  INTEGER  PRIMARY KEY AUTOINCREMENT
├── incident_id         INTEGER  NOT NULL REFERENCES Incident(id)
├── channel             TEXT     NOT NULL  -- 'slack' | 'email'
├── recipient           TEXT     NOT NULL  -- email del reporter o '#incidents' para Slack
├── notification_type   TEXT     NOT NULL
│                                -- 'team_alert' | 'reporter_confirmation' | 'reporter_resolution'
├── content_summary     TEXT     NOT NULL  -- resumen del mensaje enviado
├── status              TEXT     NOT NULL  -- 'sent' | 'failed' | 'mocked'
├── sent_at             DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
└── error_message       TEXT              -- solo si status = 'failed'
```

### ObservabilityEvent
Registro de cada evento emitido por los agentes del pipeline.

```
ObservabilityEvent
├── id                  INTEGER  PRIMARY KEY AUTOINCREMENT
├── trace_id            TEXT     NOT NULL  -- mismo trace_id que el Incident
├── stage               TEXT     NOT NULL  -- 'ingest' | 'triage' | 'ticket' | 'notify' | 'resolved'
├── incident_id         INTEGER            -- puede ser null si el error es antes de persistir
├── status              TEXT     NOT NULL  -- 'success' | 'error'
├── duration_ms         INTEGER  NOT NULL
├── metadata            TEXT     NOT NULL  -- JSON con datos específicos de cada stage
└── created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
```

---

## Diagrama de relaciones

```
Incident (1) ──────── (1) TriageResult
    │
    │ (1) ──────── (1) Ticket
    │
    │ (1) ──────── (N) NotificationLog
    │
    │ (via trace_id)
    └──────────── (N) ObservabilityEvent
```

---

## Estados del Incident (máquina de estados)

```
received ──→ triaging ──→ ticketed ──→ notified ──→ resolved
    │             │            │
    └─────────────┴────────────┴──→ (error: se registra en ObservabilityEvent)
```

| Transición | Trigger | Agente responsable |
|---|---|---|
| received → triaging | IngestAgent persiste el reporte | IngestAgent |
| triaging → ticketed | TriageAgent completa el análisis | TriageAgent |
| ticketed → notified | TicketAgent crea la Card y NotifyAgent envía notificaciones | TicketAgent + NotifyAgent |
| notified → resolved | ResolutionWatcher detecta Card en columna "Done" | ResolutionWatcher |

---

## Escala de severidad

| Nivel | Descripción | Tiempo estimado de respuesta |
|---|---|---|
| **P1** | Sistema e-commerce completamente caído o checkout inaccesible | < 1 hora |
| **P2** | Funcionalidad crítica degradada (pagos lentos, errores intermitentes en cart) | < 4 horas |
| **P3** | Funcionalidad no crítica afectada (filtros de búsqueda, recomendaciones) | < 24 horas |
| **P4** | Mejora menor o bug cosmético sin impacto en ventas | < 1 semana |

---

## Módulos de Medusa.js mapeados al dominio de triage

El TriageAgent usa estos módulos como vocabulario para `affected_module`:

| Módulo | Path en Medusa.js | Descripción |
|---|---|---|
| `cart` | `packages/medusa/src/services/cart.ts` | Gestión del carrito de compras |
| `order` | `packages/medusa/src/services/order.ts` | Procesamiento de órdenes |
| `payment` | `packages/medusa/src/services/payment.ts` | Integración de pagos |
| `inventory` | `packages/medusa/src/services/inventory.ts` | Control de inventario |
| `product` | `packages/medusa/src/services/product.ts` | Catálogo de productos |
| `customer` | `packages/medusa/src/services/customer.ts` | Gestión de clientes y auth |
| `shipping` | `packages/medusa/src/services/shipping.ts` | Métodos de envío |
| `discount` | `packages/medusa/src/services/discount.ts` | Cupones y descuentos |
| `unknown` | N/A | No se pudo determinar el módulo afectado |
