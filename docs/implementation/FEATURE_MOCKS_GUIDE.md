# Feature/Mocks: Flujo Completo con Visualización

## Objetivo

En la rama `feature/mocks` correremos **todo el flujo totalmente mockado** — sin dependencias externas, pero **con visualización clara** de qué está pasando en cada paso.

## ¿Qué significa "mockado"?

### Integraciones Externas (Mockadas)
- ❌ **Trello:** No crea tarjetas reales, pero simula la creación y las logs muestran dónde hubiera ido
- ❌ **Slack:** No envía mensajes reales, pero registra lo que hubiera enviado
- ❌ **SendGrid:** No envía emails reales, pero loggea los contenidos
- ❌ **Anthropic Claude:** Usa mock responses (opcional, o real si tienes API key)

### Flujo del Sistema (Completo)
- ✅ **API HTTP:** Funciona 100% ('POST /api/incidents' acepta reportes)
- ✅ **Ingest Agent:** Valida, sanitiza, detecta inyección
- ✅ **Triage Agent:** Analiza con Claude (o mock LLM si lo configuras)
- ✅ **Ticket Agent:** Simula creación de Trello card
- ✅ **Notify Agent:** Simula notificaciones Slack + email
- ✅ **Resolution Watcher:** Simula polling hasta "Done"
- ✅ **Base de datos:** SQLite real, persistencia completa

### Visualización (Nuevo)
- 📺 **Observabilidad mejorada:** GET `/api/observability/events` muestra quién fue mockado
- 📺 **Indicador "MOCK MODE":** Frontend y logs lo indican claramente
- 📺 **Mock audit trail:** Cada acción está loggueada con `[MOCK 🎭]` prefix

---

## Setup Rápido

### 1. Estar en rama feature/mocks
```bash
git checkout feature/mocks
```

### 2. Cargar configuración de mocks
```bash
# Copy .env.mocks a .env (o source en cada comando)
cp .env.mocks .env

# O alternativamente, para un solo comando:
export $(cat .env.mocks | xargs)
```

### 3. Iniciar backend
```bash
source .venv/bin/activate
cd backend/src

# Opción A: Con explicit env
MOCK_INTEGRATIONS=true MEDUSA_REPO_PATH=../mock-medusa-repo \
  uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Opción B: Si copiaste .env
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Verificar que está en mock mode
```bash
curl -s http://localhost:8000/api/health | jq
# Debe salir:
# {
#   "status": "ok",
#   "mock_mode": true,  ← ¡Eso!
#   "version": "1.0.0",
#   "database": "connected"
# }
```

---

## Ejemplo: Flujo Completo

### Paso 1: Crear un incidente
```bash
curl -X POST http://localhost:8000/api/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Carrito rechaza items premium",
    "description": "Nuevos clientes no pueden agregar items premium al carrito",
    "reporter_email": "dev@example.com",
    "attachment_type": "log",
    "attachment_text": "POST /carts/cart-123/line-items returned 400 Unauthorized variant"
  }'
```

**Respuesta:**
```json
{
  "incident_id": "inc_1234567890",
  "trace_id": "trace_abc123xyz",
  "status": "created",
  "message": "Incident created successfully"
}
```

### Paso 2: Ver qué pasó en el backend (logs)
En tu terminal con uvicorn, verás:

```
INFO:    [MOCK 🎭 TRELLO] Created card: mock-trello-a1b2c3d4
         Title: [P2] Carrito rechaza items premium
         Board: 🎭 MOCK Incident Board

INFO:    [MOCK 🎭 SLACK] Posted alert:
         🔴 [P2] New incident: Carrito rechaza items premium
         > Nuevos clientes no pueden agregar... 
         Trello: https://trello.com/c/mock-trello-a1b2c3d4
         confidence: 92%

INFO:    [MOCK 🎭 SENDGRID] Queued confirmation email to dev@example.com
         Subject: Incident inc_1234567890 reported successfully
```

### Paso 3: Ver estado via API
```bash
curl -s http://localhost:8000/api/incidents/inc_1234567890 | jq

# Response:
{
  "incident_id": "inc_1234567890",
  "title": "Carrito rechaza items premium",
  "status": "confirmed",
  "trace_id": "trace_abc123xyz",
  "triage_result": {
    "severity": "P2",
    "affected_module": "cart",
    "technical_summary": "...",
    "suggested_files": ["packages/medusa/src/services/cart-service.ts"],
    "confidence_score": 0.92
  },
  "ticket_info": {
    "card_id": "mock-trello-a1b2c3d4",
    "card_url": "https://trello.com/c/mock-trello-a1b2c3d4",
    "is_mock": true,               ← ¡Eso!
    "mock_board": "🎭 MOCK Incident Board"
  }
}
```

### Paso 4: Ver observabilidad (trace completo)
```bash
curl -s 'http://localhost:8000/api/observability/events?trace_id=trace_abc123xyz' | jq

# Verás toda la cadena de eventos:
{
  "trace_id": "trace_abc123xyz",
  "events": [
    {
      "stage": "ingest",
      "status": "success",
      "timestamp": "2026-04-09T15:30:00Z",
      "metadata": {"email": "dev@example.com"}
    },
    {
      "stage": "triage",
      "status": "success",
      "timestamp": "2026-04-09T15:30:02Z",
      "metadata": {
        "severity": "P2",
        "module": "cart",
        "confidence": 0.92,
        "is_mock_analysis": false  ← si Anthropic API es real
      }
    },
    {
      "stage": "ticket",
      "status": "success",
      "timestamp": "2026-04-09T15:30:03Z",
      "metadata": {
        "card_id": "mock-trello-a1b2c3d4",
        "is_mock": true  ← ¡Eso!
      }
    },
    {
      "stage": "notify",
      "status": "success",
      "timestamp": "2026-04-09T15:30:04Z",
      "metadata": {
        "slack_posted": true,
        "slack_is_mock": true,
        "email_queued": true,
        "email_is_mock": true
      }
    }
  ]
}
```

---

## Frontend en Mock Mode

### Indicador Visual
El frontend mostrará un badge **"🎭 MOCK MODE"** en la esquina:
- Fondo naranja
- Texto centrado
- Visible en todos los estados

### Dashboard Mock
- ✅ Muestra tarjetas "mockadas" de forma clara
- ✅ Indica que Trello/Slack/SendGrid no son reales
- ✅ Muestra trace_id para debugging
- ✅ Permite ver los logs en tiempo real

---

## Arquitectura de Mocks

### Trello Mock
```python
# Sin MOCK_INTEGRATIONS
POST /api/incidents → TrelloClient.create_card()
→ Llamada real a https://api.trello.com/1/cards
→ Requiere API key + token

# Con MOCK_INTEGRATIONS=true
POST /api/incidents → TrelloClient.create_card()
→ Retorna mock_card_id + mock_url + is_mock: true
→ Sin llamada HTTP
```

### Slack Mock
```python
# Sin MOCK_INTEGRATIONS
NotifyAgent.notify() → SlackClient._post()
→ Llamada real a webhook
→ Requiere SLACK_WEBHOOK_URL válido

# Con MOCK_INTEGRATIONS=true
NotifyAgent.notify() → SlackClient._post()
→ Loggea "[MOCK SLACK 🎭]" + mensaje
→ Sin llamada HTTP
```

### SendGrid Mock
```python
# Igual que Slack — loggea sin enviar
[MOCK SENDGRID 🎭] Email queued:
  To: dev@example.com
  Subject: Incident inc_1234567890 reported successfully
```

---

## Visualización de Medusa.js Mock

### Cuando Claude analiza
```
TriageAgent recibe: "Carrito rechaza items premium"
↓
Claude llama: read_ecommerce_file("packages/medusa/src/services/cart-service.ts")
↓
Tool resuelve: MEDUSA_REPO_PATH=./mock-medusa-repo
↓
Lee: ./mock-medusa-repo/packages/medusa/src/services/cart-service.ts
↓
Encuentra: function validateVariantAccess() { if (isPremium && !isVerified) return false }
↓
Claude correlaciona: "Ah, el problema es validación de premiums para nuevos clientes"
↓
Genera: severity: P2, affected_module: cart, suggested_files: [...]
```

### Archivos disponibles
```
mock-medusa-repo/packages/medusa/src/
├── services/
│   ├── cart-service.ts         ← cart module
│   ├── order-service.ts        ← order module
│   ├── payment-service.ts      ← payment module
│   └── inventory-service.ts    ← inventory module
└── models/
    └── index.ts                ← Type definitions
```

---

## Testing del Flujo

### Caso de Prueba 1: Cart Error
```bash
curl -X POST http://localhost:8000/api/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Cart error P2",
    "description": "Carrito lanza error 500 al agregar items",
    "reporter_email": "test@example.com"
  }'

# Espera → Verifica /api/observability/events
# Comprueba: triage_result.affected_module == "cart"
```

### Caso de Prueba 2: Payment Flow
```bash
# Similar, pero con:
"title": "Payment fails with Stripe"
"description": "Payment authorization times out for new customers"

# Espera que module sea "payment"
```

### Caso de Prueba 3: Verificar Mocks
```bash
# Chequea que NO hay llamadas reales:
# - Trello URL es fake (https://trello.com/c/mock-*)
# - Slack timestamp no existe en tu workspace
# - Email no fue enviado realmente

curl -s http://localhost:8000/api/observability/events | jq '.events[] | select(.stage | . == "ticket" or . == "notify")'
# Debe salir is_mock: true en los metadatos
```

---

## Transición a Producción

Cuando quieras usar integraciones reales:

### Opción 1: Cambiar .env
```bash
# En main o develop
MOCK_INTEGRATIONS=false
MEDUSA_REPO_PATH=./medusa-repo  # repo real clonado
TRELLO_API_KEY=<tu key real>
TRELLO_API_TOKEN=<tu token real>
SLACK_WEBHOOK_URL=<tu webhook real>
SENDGRID_API_KEY=<tu key real>
ANTHROPIC_API_KEY=<tu key real>
```

### Opción 2: Reemplazar mock-medusa-repo
```bash
rm -rf mock-medusa-repo
git clone https://github.com/medusajs/medusa.git medusa-repo
export MEDUSA_REPO_PATH=./medusa-repo
```

---

## Resumen

| Componente | feature/mocks | main/develop |
|---|---|---|
| Ingest Agent | ✅ Real | ✅ Real |
| Triage Agent | ✅ Real (Claude) | ✅ Real (Claude) |
| Ticket Agent | 🎭 Mock | ✅ Real (Trello) |
| Notify Agent | 🎭 Mock | ✅ Real (Slack + SendGrid) |
| Medusa.js | 📦 Mock repo | 📦 Real repo (si existe) |
| Database | ✅ SQLite | ✅ SQLite |
| Observabilidad | ✅ + indicadores mock | ✅ |

**Resultado:** Todo funciona, sin costos de API, sin dependencias externas, todo loggueado y visible.

---

## Comandos Rápidos

```bash
# Setup completo
git checkout feature/mocks
cp .env.mocks .env
source .venv/bin/activate

# Backend
cd backend/src
uvicorn main:app --reload --port 8000

# En otra terminal: test
curl -X POST http://localhost:8000/api/incidents \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","description":"Test incident","reporter_email":"me@example.com"}'

# Ver resultados
curl http://localhost:8000/api/health
curl http://localhost:8000/api/observability/events
```

---

**¡Marca la rama y empieza a testear todo sin preocuparte por APIs externas!**
