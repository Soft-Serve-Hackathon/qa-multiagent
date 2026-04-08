# API Contracts — SRE Incident Intake & Triage Agent

**Version:** 1.0  
**Owner:** Architect  
**Last updated:** 2026-04-08

---

## Base URL

```
http://localhost:8000
```

El backend (FastAPI) corre en el puerto 8000. El frontend (Next.js) corre en el puerto 3000 y hace proxy de `/api/*` → `http://localhost:8000/api/*` via rewrites.

---

## Endpoints

### POST /api/incidents
**Descripción:** Ingesta un reporte de incidente. Inicia el pipeline de triage en background.  
**Content-Type:** `multipart/form-data`

**Request fields:**

| Campo | Tipo | Requerido | Validaciones |
|---|---|---|---|
| `title` | string | Sí | max 200 chars |
| `description` | string | Sí | max 2000 chars (truncado si excede) |
| `reporter_email` | string | Sí | formato email válido |
| `attachment` | file | No | PNG, JPG, TXT, LOG — max 10MB |

**Response 201 — Success:**
```json
{
  "incident_id": 42,
  "trace_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "received",
  "message": "Your incident report has been received. Ticket creation is in progress. You will be notified by email."
}
```

**Response 400 — Validation error:**
```json
{
  "error": "prompt_injection_detected",
  "message": "Your report contains content that cannot be processed. Please rephrase and try again."
}
```

Posibles valores de `error`:
- `prompt_injection_detected` — el input contiene patrones de inyección
- `invalid_email` — formato de email inválido
- `unsupported_file_type` — tipo de archivo no permitido
- `file_too_large` — archivo excede 10MB
- `empty_or_corrupt_attachment` — archivo vacío o no legible
- `missing_required_field` — campo requerido ausente

**Response 500 — Server error:**
```json
{
  "error": "internal_server_error",
  "trace_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "message": "An unexpected error occurred. Please try again."
}
```

---

### GET /api/incidents/:trace_id
**Descripción:** Consulta el estado actual de un incidente en el pipeline.

**Path params:** `trace_id` — UUID string, el trace_id retornado por POST /api/incidents

**Response 200:**
```json
{
  "incident_id": 42,
  "trace_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "title": "Checkout fails with 500 error",
  "status": "notified",
  "severity": "P2",
  "affected_module": "cart",
  "trello_card_id": "6471abc123def456",
  "trello_card_url": "https://trello.com/c/6471abc123def456",
  "created_at": "2026-04-09T14:30:00Z",
  "updated_at": "2026-04-09T14:30:45Z"
}
```

**Response 404:**
```json
{
  "error": "incident_not_found"
}
```

---

### GET /api/health
**Descripción:** Health check para Docker y monitoreo. Retorna el estado del sistema.

**Response 200:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "uptime_seconds": 342,
  "database": "connected",
  "mock_mode": false
}
```

---

### GET /api/observability/events
**Descripción:** Retorna los eventos de observability del pipeline. Usado en el video demo para mostrar la trazabilidad end-to-end.

**Query params:**

| Param | Tipo | Default | Descripción |
|---|---|---|---|
| `trace_id` | string | null | Filtrar por trace_id específico |
| `stage` | string | null | Filtrar por stage: ingest, triage, ticket, notify, resolved |
| `limit` | integer | 50 | Máximo de eventos a retornar |

**Response 200:**
```json
{
  "events": [
    {
      "id": 1,
      "trace_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "stage": "ingest",
      "incident_id": 42,
      "status": "success",
      "duration_ms": 45,
      "metadata": {
        "attachment_type": "image",
        "injection_check": "passed"
      },
      "created_at": "2026-04-09T14:30:00.123Z"
    },
    {
      "id": 2,
      "trace_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "stage": "triage",
      "incident_id": 42,
      "status": "success",
      "duration_ms": 2341,
      "metadata": {
        "model": "claude-sonnet-4-6",
        "severity_detected": "P2",
        "module_detected": "cart",
        "confidence": 0.87,
        "files_found": 3
      },
      "created_at": "2026-04-09T14:30:02.464Z"
    }
  ],
  "total": 5
}
```

---

### POST /api/webhooks/trello
**Descripción:** Recibe webhooks de Trello cuando una Card cambia de columna. Alternativa al polling del ResolutionWatcher.  
**Nota:** En el MVP se usa polling. Este endpoint está disponible para habilitar webhooks en el futuro sin cambios de código.

**Request body (Trello webhook format):**
```json
{
  "action": {
    "type": "updateCard",
    "data": {
      "card": { "id": "6471abc123def456", "name": "..." },
      "listAfter": { "id": "LIST_DONE_ID", "name": "Done" }
    }
  }
}
```

**Response 200:**
```json
{ "received": true }
```

---

## Integrations (Trello, Slack, Email)

### Trello Card — estructura

Cada incidente crea una Card con la siguiente estructura:

```
Card name: "[P2] Checkout fails with 500 error"
Card description:
  ## Technical Summary
  [technical_summary del TriageAgent]

  ## Affected Module
  cart (confidence: 87%)

  ## Suggested Files
  - packages/medusa/src/services/cart.ts
  - packages/medusa/src/api/routes/store/carts/index.ts

  ## Reporter
  reporter@example.com

  ## Trace ID
  f47ac10b-58cc-4372-a567-0e02b2c3d479

Labels: P2 (orange), e-commerce, auto-triage
Checklist "Files to investigate":
  □ packages/medusa/src/services/cart.ts
  □ packages/medusa/src/api/routes/store/carts/index.ts
```

---

### Slack message — estructura

```
*[P2] New incident: Checkout fails with 500 error*
> Users cannot complete purchase. Error appears after adding items to cart.
:orange_circle: Severity: P2 | Module: cart | Confidence: 87%
:trello: <https://trello.com/c/6471abc123def456|View Card>
:mag: trace_id: f47ac10b-58cc-4372-a567-0e02b2c3d479
```

---

### Email al reporter — estructura

**Subject:** `[Incident received] Checkout fails with 500 error — Ref: TRELLO-6471abc`

```
Hi,

We've received your incident report and created a ticket to track it.

Incident: Checkout fails with 500 error
Reference: TRELLO-6471abc123def456
Severity: P2 — Expected response time: < 4 hours
Ticket link: https://trello.com/c/6471abc123def456

Our team has been notified and is working on it.
We will let you know when the issue is resolved.

SRE Team
```

**Email de resolución — Subject:** `[Resolved] Checkout fails with 500 error — Ref: TRELLO-6471abc`

```
Hi,

Your incident report has been resolved.

Incident: Checkout fails with 500 error
Reference: TRELLO-6471abc123def456
Resolved at: 2026-04-09T16:45:00Z

Thank you for reporting. Let us know if the issue persists.

SRE Team
```
