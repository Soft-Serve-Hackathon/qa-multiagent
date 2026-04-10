# Demo Video - Instrucciones Completas

**Objetivo:** Demostrar el flujo completo de un incidente desde su reporte hasta la creación de un ticket en Trello con asignación automática de owner y notificación en Slack.

**Tiempo estimado:** 10-15 minutos (incluyendo setup)

---

## PARTE 1: SETUP PREVIO

### 1.1 Verificar que el ambiente virtual está activo

```bash
cd /Users/lilianestefaniamaradiagocorrea/Desktop/Hackathons/qa-multiagent
source .venv/bin/activate
```

**Expected output:** Línea de prompt debe mostrar `(.venv)` al inicio.

### 1.2 Verificar que estamos en la rama correcta

```bash
git branch
```

**Expected output:** Debe mostrar `* feature/mocks` (rama activa).

### 1.3 Verificar estructura de carpetas clave

```bash
ls -la backend/src/agents/
ls -la backend/src/infrastructure/
ls -la frontend/
```

**Expected:** 
- `backend/src/agents/` debe contener: `ingest_agent.py`, `triage_agent.py`, `ticket_agent.py`, `notify_agent.py`, `qa_agent.py`, `fix_recommendation_agent.py`, `resolution_watcher.py`
- `backend/src/infrastructure/` debe contener: `external/`, `llm/`, `routing/` (con `owner_router.py`)
- `frontend/` debe contener: `package.json`, `app/`, `lib/`

---

## PARTE 2: VERIFICAR CREDENCIALES

### 2.1 Verificar archivo .env

```bash
cat .env | grep -E "TRELLO|SLACK|CLAUDE|MOCK"
```

**Requisitos:**
- `ANTHROPIC_API_KEY` debe tener valor (API key válida de Claude)
- `TRELLO_API_KEY` y `TRELLO_TOKEN` deben tener valores
- `SLACK_WEBHOOK_URL` debe tener valor
- `MOCK_INTEGRATIONS=false` (o no estar presente para usar real)
- `OWNER_ROUTING_JSON` debe contener mapeo de módulos a owners

**Si falta algo:**

```bash
# Copiar template y llenar manualmente
cp .env.example .env
# Editar .env con credenciales reales
```

### 2.2 Verificar Trello API Key

Para obtener credenciales de Trello:
1. Ir a https://trello.com/app-key
2. Generar nueva key si es necesario
3. Ir a "Token" y generar un token permanente con permisos de lectura/escritura/eliminación
4. Copiar Key y Token al .env

**Test rápido:**
```bash
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

from src.infrastructure.external.trello_client import TrelloClient
client = TrelloClient()
boards = client.get_boards()
print(f'✓ Trello conectado. Boards encontrados: {len(boards)}')
for board in boards:
    print(f'  - {board[\"name\"]}')
"
```

### 2.3 Verificar Slack Webhook

Para obtener Slack Webhook:
1. Crear Slack App en https://api.slack.com/apps
2. Activar "Incoming Webhooks"
3. Crear nuevo webhook para un canal (ej: #incidents)
4. Copiar URL al .env en `SLACK_WEBHOOK_URL`

**Test rápido:**
```bash
python3 -c "
import os
import json
from dotenv import load_dotenv
load_dotenv()

from src.infrastructure.external.slack_client import SlackClient
client = SlackClient()
response = client.post_incident_alert(
    title='TEST',
    description='Slack webhook test',
    severity='P4',
    owner_slack_user_id='U12345'
)
print(f'✓ Slack conectado: {response}')
"
```

### 2.4 Verificar Claude API Key

```bash
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic
client = Anthropic()
msg = client.messages.create(
    model='claude-3-5-sonnet-20241022',
    max_tokens=100,
    messages=[{'role': 'user', 'content': 'Say hello'}]
)
print(f'✓ Claude API conectado. Response: {msg.content[0].text}')
"
```

---

## PARTE 3: INICIAR EL BACKEND

### 3.1 Terminal 1: Backend Server

```bash
cd /Users/lilianestefaniamaradiagocorrea/Desktop/Hackathons/qa-multiagent/backend
../.venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

**Endpoints disponibles:**
- `GET http://localhost:8000/docs` - Swagger UI (para test manual)
- `POST http://localhost:8000/api/incidents` - Crear incidente

---

## PARTE 4: INICIAR EL FRONTEND

### 4.1 Terminal 2: Frontend Server

```bash
cd /Users/lilianestefaniamaradiagocorrea/Desktop/Hackathons/qa-multiagent/frontend
npm install  # Solo primera vez
npm run dev
```

**Expected output:**
```
 ▲ Next.js 15.x
 - Local:        http://localhost:3000
 - Environments: .env.local
```

**Acceso:**
- Frontend: `http://localhost:3000`
- Formulario de incidente: `http://localhost:3000/` (página principal debe tener forma de reporte)

---

## PARTE 5: FLUJO DE DEMO (paso a paso)

### Flujo Visual en la Demo

```
┌─────────────────────────────────────────────────────────────────┐
│ SIMULACIÓN DE INCIDENTE EN PRODUCCIÓN                           │
│                                                                   │
│ Escenario: Carrito de compra rechaza pagos de tarjetas         │
│ Módulo afectado: payment (Medusa.js)                           │
│ Severidad esperada: P2                                          │
│ Owner esperado: Se asigna automáticamente basado en módulo     │
└─────────────────────────────────────────────────────────────────┘
```

### Step 1: Reportar Incidente via Formulario

**Acción en pantalla:** Abrir `http://localhost:3000` en navegador

**Llenar formulario con:**
```
Title:        "Payment processing failing for all card types"
Description:  "Users reporting failed transactions across all payment methods. 
              Started around 14:30 UTC. Last successful transaction was at 14:28. 
              Error message: 'Connection timeout to payment gateway'"

Reporter Email: your-email@example.com

Attachment:   Opcional - adjuntar screenshot de error o log file
```

**Recomendación:** Copiar/pegar para ser rápido y consistente.

### Step 2: Click "Report Incident"

**Backend log esperado:**
```
[INGEST] Incident received: id=inc_xxxxx, trace_id=trace_xxxxx
[INGEST] File validated and saved
[INGEST] Pipeline triggered in background
```

**Frontend feedback:**
- Modal muestra: "✓ Incidente reportado exitosamente"
- ID de incidente mostrado para referencia
- Redirecciona a dashboard o muestra status in real-time

### Step 3: Observar Pipeline en Tiempo Real (Backend)

**Backend logs mostrarán secuencialmente:**

```
[INGEST] trace_id=trace_xxxxx | Incident created: id=inc_12345
[INGEST] trace_id=trace_xxxxx | Status: RECEIVED

[TRIAGE] trace_id=trace_xxxxx | Starting triage...
[TRIAGE] trace_id=trace_xxxxx | Reading Medusa.js codebase from: /path/to/medusa-repo
[TRIAGE] trace_id=trace_xxxxx | Affected module: PAYMENT
[TRIAGE] trace_id=trace_xxxxx | Severity: P2
[TRIAGE] trace_id=trace_xxxxx | Status: TRIAGED

[QA_SCOPE] trace_id=trace_xxxxx | Searching for related tests...
[QA_SCOPE] trace_id=trace_xxxxx | Found tests: payment_processor_test.ts
[QA_SCOPE] trace_id=trace_xxxxx | Status: QA_SCOPED

[FIX_RECOMMENDATION] trace_id=trace_xxxxx | Analyzing root cause...
[FIX_RECOMMENDATION] trace_id=trace_xxxxx | Suggested files: payment.ts, gateway-client.ts
[FIX_RECOMMENDATION] trace_id=trace_xxxxx | Status: FIX_RECOMMENDED

[TICKET] trace_id=trace_xxxxx | Creating Trello card...
[TICKET] trace_id=trace_xxxxx | Owner resolved: {trello_member_id: "xxx", slack_user_id: "Uyyy"}
[TICKET] trace_id=trace_xxxxx | Card created: card_id=payment_card_xxx
[TICKET] trace_id=trace_xxxxx | Member assigned to card
[TICKET] trace_id=trace_xxxxx | Status: TICKET_CREATED

[NOTIFY] trace_id=trace_xxxxx | Posting Slack alert...
[NOTIFY] trace_id=trace_xxxxx | Alert mentioning owner: <@Uyyy>
[NOTIFY] trace_id=trace_xxxxx | Sending email to reporter...
[NOTIFY] trace_id=trace_xxxxx | Status: NOTIFIED

[RESOLVED] trace_id=trace_xxxxx | Incident pipeline complete
```

**Tiempo esperado:** 8-15 segundos para todo el pipeline.

### Step 4: Verificar Card Creada en Trello

**Acción:** Abrir Trello directamente o ir a `https://trello.com/board-name`

**Buscar la nueva card con:**
- Título: `[P2] Payment processing failing for all card types`
- Descripción: Incluye resumen técnico + archivos sugeridos
- Asignado a: Member automáticamente asignado basado en módulo PAYMENT
- Etiquetas: P2, payment, auto-created

**Validación checklist:**
- ✓ Card existe en columna "Backlog" o "Incoming"
- ✓ Card tiene descripción con contexto técnico (Medusa.js analysis)
- ✓ Card tiene miembro asignado (owner automático)
- ✓ Card tiene etiqueta de severidad (P2)
- ✓ Card tiene descripción con archivos sugeridos a revisar

### Step 5: Verificar Slack Alert

**Acción:** Abrir Slack en el canal configurado (ej: #incidents)

**Mensaje esperado:**
```
🚨 INCIDENT ALERT [P2]

Title: Payment processing failing for all card types
Description: Users reporting failed transactions...

Affected Module: payment
Recommended Files: 
  - src/payment-processor.ts
  - src/gateway-client.ts
  - tests/payment.test.ts

Assigned to: <@owner-slack-userid> (automáticamente mencionado)
Trello Card: [link]

Debug Info: trace_id=trace_xxxxx
```

**Validación checklist:**
- ✓ Mensaje llegó al canal correcto
- ✓ Owner está mencionado con <@userid>
- ✓ Severidad (P2) es clara
- ✓ Información técnica es relevante
- ✓ Link a Trello está presente

### Step 6: Verificar Email del Reporter

**Acción:** Revisar email reportado (check inbox/spam)

**Email esperado:**
```
Subject: Incident Confirmation - Your Report Has Been Logged [ID: inc_xxxxx]

Body:
Hello,

Thank you for reporting the incident. Your report has been received and is being triaged.

Incident Details:
- ID: inc_xxxxx
- Title: Payment processing failing...
- Status: TRIAGED → TICKET_CREATED → NOTIFIED
- Severity: P2
- Assigned Owner: [owner-name]

You will receive updates as the incident is resolved.

Dashboard: http://localhost:3000/
```

**Validación checklist:**
- ✓ Email llegó a la dirección reportada
- ✓ ID de incidente incluído
- ✓ Status actual mostrado
- ✓ Link a dashboard incluído (opcional)

---

## PARTE 6: DASHBOARD EN TIEMPO REAL

### 6.1 Abrir Dashboard

**URL:** `http://localhost:3000/dashboard`

**Elementos visibles:**
1. **Mock Mode Indicator** (esquina superior derecha)
   - Badge azul: "🔧 Mock Integrations ON" o verde: "✓ Real Integrations"
   
2. **Incidents List**
   - Tabla con columnas: ID, Title, Status, Severity, Owner, Actions
   - Status muestra: RECEIVED → TRIAGED → QA_SCOPED → FIX_RECOMMENDED → TICKET_CREATED → NOTIFIED
   - Cada row tiene color basado en severidad (P1=rojo, P2=naranja, P3=amarillo, P4=gris)
   
3. **Real-time Updates**
   - Status actualiza en tiempo real conforme el pipeline avanza
   - Si hay nuevo incidente reportado mientras ves el dashboard, aparece automáticamente

### 6.2 Interacciones en Dashboard

**Clic en una fila de incidente:**
- Abre detalle lateral o modal
- Muestra: descripción completa, adjuntos, triage results, Trello link, Slack history

**Clic en "See in Trello":**
- Abre el card en Trello
- Verifica que sigue sincronizado

**Clic en "Slack Thread":**
- Abre el mensaje en Slack
- Verifica conversación de equipo

---

## PARTE 7: VALIDACIONES TÉCNICAS (LADO DEL DESARROLLADOR)

### 7.1 Revisar Observabilidad

```bash
# Terminal 3: Follow observability logs
tail -f logs/observability.log | grep trace_id=trace_xxxxx
```

**Expected:**
```json
{
  "timestamp": "2026-04-09T14:35:22.123Z",
  "trace_id": "trace_xxxxx",
  "stage": "TRIAGE",
  "status": "SUCCESS",
  "metadata": {
    "affected_module": "payment",
    "severity": "P2",
    "confidence_score": 0.95
  }
}
```

### 7.2 Revisar Owner Routing

```bash
python3 << 'PY'
import os
import json
from dotenv import load_dotenv
load_dotenv()

from src.infrastructure.routing.owner_router import resolve_owner

# Test resolving owner para payment module
owner = resolve_owner('payment')
print(f"Owner para 'payment': {owner}")

# Test fallback
owner_unknown = resolve_owner('unknown_module')
print(f"Owner para 'unknown_module' (fallback): {owner_unknown}")
PY
```

**Expected output:**
```
Owner para 'payment': {'trello_member_id': 'trello-payment', 'slack_user_id': 'U_PAYMENT'}
Owner para 'unknown_module' (fallback): {'trello_member_id': 'trello-oncall', 'slack_user_id': 'U_ONCALL'}
```

### 7.3 Revisar Medusa.js Codebase Integration

```bash
python3 << 'PY'
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from src.config import MEDUSA_REPO_PATH

print(f"MEDUSA_REPO_PATH resolved to: {MEDUSA_REPO_PATH}")
print(f"Path exists: {Path(MEDUSA_REPO_PATH).exists()}")

# List available modules
medusa_packages = Path(MEDUSA_REPO_PATH) / "packages/medusa/src"
if medusa_packages.exists():
    modules = [d.name for d in medusa_packages.iterdir() if d.is_dir()]
    print(f"Available modules in Medusa: {modules}")
PY
```

**Expected:**
```
MEDUSA_REPO_PATH resolved to: /Users/.../qa-multiagent/medusa-repo
Path exists: True
Available modules in Medusa: ['services', 'models', 'errors', 'utils', ...]
```

---

## PARTE 8: TROUBLESHOOTING

### Problema: Backend no inicia

**Error típico:**
```
ImportError: No module named 'anthropic'
```

**Solución:**
```bash
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### Problema: Trello API falla

**Error típico:**
```
[TICKET] Error creating card: 401 Unauthorized
```

**Solución:**
- Verificar `TRELLO_API_KEY` y `TRELLO_TOKEN` en .env
- Verificar que el token no expiró
- Test nuevamente con: `python3 -c "from src.infrastructure.external.trello_client import TrelloClient; c = TrelloClient(); print(c.get_boards())"`

### Problema: Slack webhook falla

**Error típico:**
```
[NOTIFY] Error posting to Slack: 404 invalid_hooks
```

**Solución:**
- Verificar URL en `SLACK_WEBHOOK_URL`
- Copiar URL completa desde https://api.slack.com/apps/your-app-id/incoming-webhooks
- Asegurarse que el canal existe y el bot tiene permisos

### Problema: Frontend no carga

**Error típico:**
```
error - ENOENT: no such file or directory, open '.../node_modules/...'
```

**Solución:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Problema: Pipeline tarda mucho (>30s)

**Causa probable:** Claude API responde lentamente

**Solución:**
- Verificar que `ANTHROPIC_API_KEY` es válida
- Verificar conexión a internet
- Revisar rate limits de Anthropic (en https://console.anthropic.com)
- Aumentar timeout en `backend/src/config.py` si es necesario

### Problema: Owner no se asigna correctamente

**Error típico:**
```
[TICKET] Owner resolved: None
```

**Solución:**
- Verificar que `OWNER_ROUTING_JSON` tiene formato válido
- Verificar que módulo afectado existe en el mapping
- Test manualmente:
  ```bash
  python3 -c "
  import json, os
  from dotenv import load_dotenv
  load_dotenv()
  routing = json.loads(os.getenv('OWNER_ROUTING_JSON', '{}'))
  print(f'Owner routing config: {routing}')
  "
  ```

### Problema: Medusa.js no se lee correctamente

**Error típico:**
```
[TRIAGE] Warning: Could not read Medusa codebase from path
```

**Solución:**
- Verificar que carpeta `medusa-repo` existe en raíz del proyecto
- Si no existe, clonar:
  ```bash
  git clone https://github.com/medusajs/medusa.git medusa-repo
  ```
- Verificar que `MEDUSA_REPO_PATH` en config.py resuelve correctamente

---

## PARTE 9: CHECKLIST FINAL PARA DEMO

Antes de grabar video, validar:

- [ ] Backend corriendo sin errores en puerto 8000
- [ ] Frontend corriendo sin errores en puerto 3000
- [ ] .env tiene credenciales reales (Trello, Slack, Claude)
- [ ] Trello board tiene columnas: Backlog, In Progress, In Review, Done
- [ ] Slack workspace y canal están listos
- [ ] Email del reporter es válido y accesible
- [ ] OWNER_ROUTING_JSON está configurado
- [ ] medusa-repo existe en raíz del proyecto
- [ ] Network es estable (importante para APIs)

**Tiempo estimado para la demo:** 5 minutos de video

---

## PARTE 10: SCRIPT PARA DEMO

Si prefieres automatizar la demo:

```bash
#!/bin/bash

# Script: demo.sh
# Uso: ./scripts/demo.sh

set -e

BASE_DIR="/Users/lilianestefaniamaradiagocorrea/Desktop/Hackathons/qa-multiagent"
cd "$BASE_DIR"

echo "=== QA MultiAgent Demo ==="
echo ""

# Step 1: Activate venv
source .venv/bin/activate
echo "✓ Python environment activated"

# Step 2: Check git branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$BRANCH" != "feature/mocks" ]; then
  echo "⚠ Warning: Not on feature/mocks branch (current: $BRANCH)"
fi

# Step 3: Verify credentials
python3 << 'PY'
import os
from dotenv import load_dotenv

load_dotenv()

checks = {
    "ANTHROPIC_API_KEY": bool(os.getenv("ANTHROPIC_API_KEY")),
    "TRELLO_API_KEY": bool(os.getenv("TRELLO_API_KEY")),
    "TRELLO_TOKEN": bool(os.getenv("TRELLO_TOKEN")),
    "SLACK_WEBHOOK_URL": bool(os.getenv("SLACK_WEBHOOK_URL")),
    "OWNER_ROUTING_JSON": bool(os.getenv("OWNER_ROUTING_JSON")),
}

print("Environment Validation:")
for key, value in checks.items():
    status = "✓" if value else "✗"
    print(f"  {status} {key}")

if not all(checks.values()):
    print("\n⚠ Some environment variables are missing. Update .env and try again.")
    exit(1)
PY

echo ""
echo "=== Demo Ready ==="
echo ""
echo "Start these in separate terminals:"
echo ""
echo "Terminal 1 (Backend):"
echo "  cd backend && ../.venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "Terminal 2 (Frontend):"
echo "  cd frontend && npm run dev"
echo ""
echo "Then:"
echo "  1. Open http://localhost:3000"
echo "  2. Fill the incident form"
echo "  3. Click 'Report Incident'"
echo "  4. Watch the pipeline in backend logs"
echo "  5. Verify card in Trello"
echo "  6. Verify alert in Slack"
echo "  7. Check email from reporter"
echo ""
```

Ejecutar:
```bash
chmod +x scripts/demo.sh
./scripts/demo.sh
```

---

## Referencias

- **Full spec:** [docs/implementation/FORM_ACTIVATION_FLOW.md](FORM_ACTIVATION_FLOW.md)
- **Medusa context:** [docs/implementation/MEDUSA_CONTEXT.md](MEDUSA_CONTEXT.md)
- **Feature summary:** [docs/implementation/FEATURE_MOCKS_SUMMARY.md](FEATURE_MOCKS_SUMMARY.md)
- **Architecture:** [docs/architecture/system-overview.md](../architecture/system-overview.md)
- **API docs:** [docs/architecture/api-contracts.md](../architecture/api-contracts.md)

---

**Autor:** QA MultiAgent Team  
**Fecha:** Abril 2026  
**Branch:** feature/mocks  
**Video Demo:** [link a video cuando esté listo]
