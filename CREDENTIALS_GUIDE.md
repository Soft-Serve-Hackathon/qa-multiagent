# 🔐 Guía de Credenciales: Mock vs Real

Este documento explica cómo cambiar entre **modo mock** (para testing) y **modo real** (con integraciones verdaderas).

## 📊 Comparación de Modos

| Aspecto | Mode Mock | Real Mode |
|--------|-----------|-----------|
| `MOCK_INTEGRATIONS` | `true` | `false` |
| LLM (Claude) | Simulado | Real (Anthropic API) |
| Ticketing (Trello) | Mock cards | Cards reales en Trello |
| Slack | Logs locales | Webhooks reales |
| Email | Logs locales | SendGrid real |
| **Requisitos** | Ninguno | 4 API keys |
| **Costo** | $0 | $$$ (pay-per-use) |
| **Velocidad** | ⚡ Instant | ⏱ Real API latency |

---

## 🧪 Modo MOCK (desarrollo/testing)

### Estado Actual (Por Defecto)

```bash
# .env actual
MOCK_INTEGRATIONS=true
MOCK_EMAIL=true
ANTHROPIC_API_KEY=sk-ant-mock-key-for-development
TRELLO_API_KEY=test-api-key-development
```

### Ventajas

✅ **Sin credenciales reales necesarias**  
✅ **Pruebas rápidas (sin latencia)**  
✅ **No da errores por faltan credenciales**  
✅ **Perfecto para CI/CD y demos**  
✅ **No consume cuotas de APIs**

### Cómo Usar

```bash
# 1. Asegurar .env tiene MOCK_INTEGRATIONS=true
grep MOCK_INTEGRATIONS .env  # Debe mostrar: MOCK_INTEGRATIONS=true

# 2. Iniciar Docker
docker compose up --build

# 3. Crear incident
curl -X POST http://localhost:8000/api/incidents \
  -F "title=Test Issue" \
  -F "description=Testing mock mode" \
  -F "reporter_email=test@company.com"

# resultado esperado:
# status: "notified"
# severity: "P2" (simulado)
# ticket_id: "MOCK-XXXXX"
```

### Salida Esperada en Logs Mock

```json
{
  "status": "notified",
  "severity": "P2",
  "affected_module": "backend",
  "triage_summary": "[MOCK] Simulated triage analysis...",
  "ticket_id": "MOCK-024F17C3",
  "confidence_score": 0.8
}
```

---

## 🔌 Modo REAL (producción)

### Paso 1: Obtener Credenciales

#### A) Anthropic Claude API (LLM)

1. Ir a https://console.anthropic.com
2. Crear una API key
3. Copiar clave (formato: `sk-ant-...`)

```bash
# Agregar a .env
ANTHROPIC_API_KEY=sk-ant-YOUR_REAL_KEY_HERE
```

**Costo**: Pay-per-token (Sonnet 4.6 ≈ $3-5 por 1M tokens)

---

#### B) Trello API (Ticketing)

1. Ir a https://trello.com/app-key
2. Generate Token
3. Copiar API Key y Token

```bash
# Agregar a .env
TRELLO_API_KEY=YOUR_KEY_HERE
TRELLO_API_TOKEN=YOUR_TOKEN_HERE
```

**Setup Trello Board**:

```bash
# 1. Crear board en Trello
# 2. Obtener BOARD_ID de URL: https://trello.com/b/{BOARD_ID}/board-name

# 3. Crear dos listas: "To Do" y "Done"

# 4. Obtener LIST IDs:
curl "https://api.trello.com/1/boards/{BOARD_ID}/lists?key={KEY}&token={TOKEN}"

# 5. Agregar a .env:
TRELLO_BOARD_ID=YOUR_BOARD_ID
TRELLO_LIST_ID=YOUR_TODO_LIST_ID
TRELLO_DONE_LIST_ID=YOUR_DONE_LIST_ID
```

---

#### C) Slack Webhook (Notifications)

1. Ir a https://api.slack.com/apps
2. Create New App → From scratch
3. Incoming Webhooks → Add New Webhook to Workspace
4. Seleccionar canal: `#incidents`
5. Copiar URL del webhook

```bash
# Agregar a .env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

---

#### D) SendGrid API (Email)

1. Ir a https://sendgrid.com (sign up for free tier)
2. Settings → API Keys → Create API Key
3. Copiar clave

```bash
# Agregar a .env
SENDGRID_API_KEY=SG.YOUR_KEY_HERE
REPORTER_EMAIL_FROM=sre-agent@YOUR_DOMAIN.com
```

---

### Paso 2: Cambiar a Modo REAL

```bash
# Editar .env
MOCK_INTEGRATIONS=false
MOCK_EMAIL=false
```

### Paso 3: Reiniciar Sistema

```bash
# Recrear .env volume y reiniciar
docker compose down
docker compose up --build

# Verificar health
curl http://localhost:8000/api/health
# Debe mostrar: "mock_mode": false
```

### Paso 4: Test E2E con APIs Reales

```bash
# Crear incident
TRACE=$(curl -s -X POST http://localhost:8000/api/incidents \
  -F "title=Real Integration Test" \
  -F "description=Testing real Trello, Slack, SendGrid" \
  -F "reporter_email=oncall@company.com" | jq -r '.trace_id')

sleep 10

# Verificar resultado
curl -s "http://localhost:8000/api/incidents/$TRACE" | jq '
  {
    status: .status,
    severity: .severity,
    ticket_id: .ticket_id,
    ticket_url: .ticket_url
  }
'

# Esperado:
# - Ticket REAL en tu Trello board
# - Mensaje REAL en #incidents Slack
# - Email REAL recibido
```

---

## 🔄 Cambiar Entre Modos

### Quick Script: Mock → Real

```bash
#!/bin/bash

# Backup actual
cp .env .env.mock

# Cambiar a real
sed -i '' 's/MOCK_INTEGRATIONS=true/MOCK_INTEGRATIONS=false/' .env
sed -i '' 's/MOCK_EMAIL=true/MOCK_EMAIL=false/' .env

# Pedir credenciales
echo "Ingresa ANTHROPIC_API_KEY:"
read ANTHROPIC_KEY
sed -i '' "s|ANTHROPIC_API_KEY=.*|ANTHROPIC_API_KEY=$ANTHROPIC_KEY|" .env

# Similar para TRELLO, SLACK, SENDGRID...

# Reiniciar
docker compose restart backend
```

### Quick Script: Real → Mock

```bash
#!/bin/bash

# Restaurar mock
cp .env.mock .env

# Reiniciar
docker compose restart backend
```

---

## ⚠️ Consideraciones de Seguridad

### 🔒 Nunca Commitear Credenciales

```bash
# .env debe estar en .gitignore
cat .gitignore | grep "^\.env"  # Debe tener:  .env

# Verificar que no está trackeado
git status | grep ".env"  # No debe aparecer

# Si accidentalmente fue commiteado:
git rm --cached .env
git commit -m "Remove .env from git history"
git push
```

### 🔐 Rotar Credenciales en Producción

```bash
# Si una credencial se expone:
1. Invalidar en el servicio original (Trello, Slack, etc.)
2. Generar nueva credencial
3. Actualizar en .env
4. Reiniciar containers
5. Deploying en prod
```

---

## 📊 Matriz de Prueba

### Modo MOCK - Test Unitario

```bash
docker compose up --build
# En .env: MOCK_INTEGRATIONS=true

# Test pipeline simulado
for i in {1..5}; do
  curl -s -X POST http://localhost:8000/api/incidents \
    -F "title=Mock Test $i" \
    -F "description=Testing iteration $i" \
    -F "reporter_email=test$i@company.com"
  sleep 3
done

# Todos deben retornar: "status": "notified", "severity": "P2"
```

### Modo REAL - Integrated Test

```bash
docker compose up --build
# En .env: MOCK_INTEGRATIONS=false

# Test con credenciales reales
curl -s -X POST http://localhost:8000/api/incidents \
  -F "title=Real Integration Test" \
  -F "description=This creates real Trello card + Slack message" \
  -F "reporter_email=oncall@company.com"

# Verificar manualmente:
# ✅ Trello board tiene nuevo card
# ✅ #incidents channel tiene mensaje
# ✅ Email recibido en REPORTER_EMAIL_FROM
```

---

## 🐛 Troubleshooting

| Problema | Síntoma | Solución |
|----------|---------|----------|
| LLM fails (mock on) | `triage_summary: "Triage analysis failed"` | Verificar `MOCK_INTEGRATIONS=true` en container |
| Trello fails | Ticket no se crea | Verificar `TRELLO_API_KEY`, `TRELLO_TOKEN`, `TRELLO_LIST_ID` |
| Slack fails | No llega notificación | Verificar URL webhook `SLACK_WEBHOOK_URL` y canal correcto |
| Email fails | No llega correo | Verificar `SENDGRID_API_KEY`, dominio verificado en SendGrid |
| Config no aplica | Cambios en .env no reflejados | Hacer `docker compose down && up --build` |

**Ver logs en vivo:**

```bash
docker logs qa-multiagent-backend -f --tail=50
```

---

## 📋 Checklist: Implementación Real

Antes de deployed a producción:

- [ ] `MOCK_INTEGRATIONS=false` en .env
- [ ] Todos los 4 API keys válidos
- [ ] Test E2E exitoso (ticket + Slack + email)
- [ ] `.env` en `.gitignore` y NO commiteado
- [ ] Logs muestran "Real LLM call" (no mock)
- [ ] Credenciales rotadas si fueron expuestas
- [ ] Rate limits configurados en cada servicio
- [ ] Error handling validado para fallos de API

---

## 🎓 Ejemplo Completo: De Mock a Real

```bash
# 1. Comenzar con mock (demo)
cp .env.example .env
sed -i '' 's/MOCK_INTEGRATIONS=false/MOCK_INTEGRATIONS=true/' .env
docker compose up --build

# Test mock
curl -X POST http://localhost:8000/api/incidents \
  -F "title=Testing" \
  -F "description=Mock mode" \
  -F "reporter_email=test@company.com" \
  | jq .

# 2. Cambiar a real (producción)
# Obtener y agregar credenciales a .env
ANTHROPIC_API_KEY=sk-ant-XXXXX
TRELLO_API_KEY=XXXX
TRELLO_API_TOKEN=XXXX
...

# Editar .env
sed -i '' 's/MOCK_INTEGRATIONS=true/MOCK_INTEGRATIONS=false/' .env

# Reiniciar
docker compose down && docker compose up --build

# Test real
curl -X POST http://localhost:8000/api/incidents \
  -F "title=Real Test" \
  -F "description=With real integrations" \
  -F "reporter_email=oncall@company.com" \
  | jq .

# 3. Verificar en servicios reales
# Abrir Trello → nuevo card
# Abrir #incidents Slack → nuevo mensaje
# Revisar email → notificación recibida
```

---

## 🔗 Enlaces Rápidos

- 🤖 **Anthropic Console**: https://console.anthropic.com
- 📋 **Trello API**: https://trello.com/app-key
- 💬 **Slack API**: https://api.slack.com/apps
- 📧 **SendGrid**: https://sendgrid.com

---

**Última actualización**: 2026-04-08  
**Status**: ✅ Documentado y testeado  
**Contribuyentes**: AgentX Hackathon Team
