# Local Development Setup — SRE Incident Intake & Triage Agent

## ✅ Quick Start (5 minutes)

### Step 1: Configure Environment (✅ ALREADY DONE)

The `.env` file has been configured with **MOCK_INTEGRATIONS=true** for local testing without external credentials.

**Key settings:**
```bash
MOCK_INTEGRATIONS=true          # ✅ All external calls are mocked
MOCK_EMAIL=true                 # ✅ Email is logged instead of sent
ANTHROPIC_API_KEY=mock          # ✅ Mock key
TRELLO_API_*=mock               # ✅ Mock credentials
SLACK_WEBHOOK_URL=mock          # ✅ Mock webhook
SENDGRID_API_KEY=mock           # ✅ Mock SendGrid
```

**Verify:**
```bash
cat .env | grep "MOCK_INTEGRATIONS\|MOCK_EMAIL"
# Expected output:
# MOCK_INTEGRATIONS=true
# MOCK_EMAIL=true
```

### Step 2: Start Docker Compose

```bash
# Build and start all services
docker compose up --build

# Expected output after ~2-3 minutes:
# qa-multiagent-backend   | INFO:     Application startup complete.
# qa-multiagent-frontend  | ready - started server on 0.0.0.0:3000
```

**Services running:**
- Backend API: `http://localhost:8000` (FastAPI)
- Frontend: `http://localhost:3000` (Next.js)
- Database: SQLite at `./data/incidents.db`

### Step 3: Validate E2E Pipeline

In a **new terminal tab** (while Docker is running):

#### Health Check
```bash
curl http://localhost:8000/api/health

# Expected response (HTTP 200):
# {
#   "status": "ok",
#   "version": "1.0.0",
#   "database": "connected",
#   "mock_mode": true
# }
```

#### Submit Incident (POST /api/incidents)
```bash
curl -X POST http://localhost:8000/api/incidents \
  -F "title=Payment Timeout in Checkout" \
  -F "description=Users see 500 error when attempting payment. Issue affects 15% of checkout attempts." \
  -F "reporter_email=oncall@company.com"

# Expected response (HTTP 201):
# {
#   "incident_id": 1,
#   "trace_id": "550e8400-e29b-41d4-a716-446655440000",
#   "status": "received",
#   "message": "Your incident report has been received..."
# }
```

**Save the `trace_id` from the response — you'll use it in the next step.**

#### Wait for Pipeline (3-5 seconds)
```bash
# Give backend time to process:
# - IngestAgent: validate + persist
# - TriageAgent: LLM analysis (mocked)
# - TicketAgent: create Trello card (mocked)
# - NotifyAgent: send Slack + email (mocked)
sleep 5
```

#### Fetch Incident Status (GET /api/incidents/{trace_id})
```bash
curl http://localhost:8000/api/incidents/{trace_id}

# Replace {trace_id} with the actual ID from Step 3.2
# Example: curl http://localhost:8000/api/incidents/550e8400-e29b-41d4-a716-446655440000

# Expected response (HTTP 200):
# {
#   "incident_id": 1,
#   "trace_id": "550e8400-e29b-41d4-a716-446655440000",
#   "title": "Payment Timeout in Checkout",
#   "status": "notified",
#   "severity": "P2",
#   "affected_module": "cart",
#   "triage_summary": "...",
#   "confidence_score": 0.87,
#   "ticket_id": "mocked-trello-card-id",
#   "ticket_url": "https://trello.com/c/mocked-card",
#   "created_at": "2026-04-08T...",
#   "updated_at": "2026-04-08T..."
# }
```

**🎉 If you see all fields populated, the pipeline is working!**

#### Check Observability Trace
```bash
curl "http://localhost:8000/api/observability/events?trace_id={trace_id}"

# Expected: Events for stages: ingest, triage, ticket, notify
# Each event shows: duration, status, severity, module, confidence
```

#### Frontend UI Test
Open `http://localhost:3000` in your browser:
1. Fill the form: Title, Description, Email
2. Click "Report Incident"
3. Watch the status update in real-time as the pipeline progresses
4. Verify links to Trello card (mocked)

---

## 🔧 Alternative: Running Without Docker

If you prefer local development without Docker:

### Backend Only

```bash
# Terminal 1: Backend
cd /Users/lilianestefaniamaradiagocorrea/Desktop/Hackathons/qa-multiagent
source .venv/bin/activate
export $(cat .env | xargs)
cd backend
python -m uvicorn src.main:app --reload --port 8000

# Backend runs on http://localhost:8000
```

### Frontend Only

```bash
# Terminal 2: Frontend
cd /Users/lilianestefaniamaradiagocorrea/Desktop/Hackathons/qa-multiagent/frontend
npm install  # if not already done
npm run dev

# Frontend runs on http://localhost:3002 or http://localhost:3000
```

---

## 🎛️ Configuration Options

### Enable Real Integrations (Production)

For Trello, Slack, and SendGrid integration, edit `.env`:

```env
# Disable mocking
MOCK_INTEGRATIONS=false
MOCK_EMAIL=false

# Add real credentials
ANTHROPIC_API_KEY=sk-ant-...
TRELLO_API_KEY=...
TRELLO_API_TOKEN=...
TRELLO_BOARD_ID=...
TRELLO_LIST_ID=...
TRELLO_DONE_LIST_ID=...
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SENDGRID_API_KEY=SG....
```

**To get real Trello credentials:**
1. Go to https://trello.com/app-key
2. Copy `API Key`
3. Click `Token` to generate a token
4. Get board/list IDs via: `curl "https://api.trello.com/1/boards/{BOARD_ID}/lists?key={API_KEY}&token={TOKEN}"`

### Logs & Debugging

**Backend logs** (in Docker):
```bash
docker compose logs backend -f
```

**Database access** (SQLite):
```bash
sqlite3 ./data/incidents.db ".tables"
sqlite3 ./data/incidents.db "SELECT * FROM incidents LIMIT 5;"
```

**Observability events** (view full trace):
```bash
curl "http://localhost:8000/api/observability/events" | python3 -m json.tool
```

---

## 🆘 Troubleshooting

| Issue | Solution |
|---|---|
| `docker compose: command not found` | Install Docker Desktop or Docker CLI |
| `Port 8000/3000 already in use` | `lsof -i :8000` to find process, then `kill -9 PID` |
| `Backend not connecting to DB` | Check `./data/` directory exists and has perms: `mkdir -p data logs uploads` |
| `Frontend won't load at localhost:3000` | Check frontend Dockerfile uses port 3000, not 3002 |
| `Mock API calls not working` | Verify `MOCK_INTEGRATIONS=true` in .env: `grep MOCK_INTEGRATIONS .env` |
| `Triage result is empty` | ANTHROPIC_API_KEY must be set (even if mock), or Claude fallback returns P3/unknown |

---

## ✅ Full E2E Test Script

Save as `test-e2e.sh`:

```bash
#!/bin/bash

echo "🚀 SRE Incident Intake & Triage Agent — E2E Test"
echo ""

BACKEND_URL="http://localhost:8000"

# 1. Health check
echo "1️⃣ Health Check..."
HEALTH=$(curl -s $BACKEND_URL/api/health)
STATUS=$(echo $HEALTH | grep -o '"status":"[^"]*' | cut -d'"' -f4)
[ "$STATUS" == "ok" ] && echo "✅ Backend healthy" || echo "❌ Backend not responding"

# 2. Create incident
echo ""
echo "2️⃣ Creating test incident..."
RESPONSE=$(curl -s -X POST $BACKEND_URL/api/incidents \
  -F "title=Test Incident E2E" \
  -F "description=Testing full pipeline functionality" \
  -F "reporter_email=test@example.com")

TRACE_ID=$(echo $RESPONSE | grep -o '"trace_id":"[^"]*' | head -1 | cut -d'"' -f4)
if [ -z "$TRACE_ID" ]; then
  echo "❌ Failed to create incident"
  echo "Response: $RESPONSE"
  exit 1
fi
echo "✅ Incident created: $TRACE_ID"

# 3. Wait for processing
echo ""
echo "3️⃣ Processing pipeline..."
sleep 5

# 4. Check status
echo ""
echo "4️⃣ Checking incident status..."
STATUS_RESPONSE=$(curl -s $BACKEND_URL/api/incidents/$TRACE_ID)
INCIDENT_STATUS=$(echo $STATUS_RESPONSE | grep -o '"status":"[^"]*' | cut -d'"' -f4)
SEVERITY=$(echo $STATUS_RESPONSE | grep -o '"severity":"[^"]*' | cut -d'"' -f4)

if [ -n "$SEVERITY" ]; then
  echo "✅ Triage completed: Severity=$SEVERITY, Status=$INCIDENT_STATUS"
else
  echo "⚠️  Triage not completed yet"
  echo "Response: $STATUS_RESPONSE"
fi

# 5. Check observability
echo ""
echo "5️⃣ Checking observability events..."
EVENTS=$(curl -s "$BACKEND_URL/api/observability/events?trace_id=$TRACE_ID")
EVENT_COUNT=$(echo $EVENTS | grep -o '"stage"' | wc -l)
echo "✅ Events recorded: $EVENT_COUNT stages"

echo ""
echo "🎉 E2E Test Complete"
```

**Run:**
```bash
chmod +x test-e2e.sh
./test-e2e.sh
```

---

## 📦 Deployment Options After Testing

### Option 1: Docker Compose (Local)
```bash
docker compose up -d
# Runs in background, auto-restart on reboot
```

### Option 2: AWS ECS (Production)
```bash
# Push images to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com
docker tag qa-multiagent-backend:latest $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com/qa-multiagent-backend:latest
docker push $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com/qa-multiagent-backend:latest

# Deploy via ECS/Fargate
```

---

## 🎯 Next Steps

1. ✅ **Verify Setup**: Run `test-e2e.sh` to validate end-to-end
2. 📹 **Record Demo**: Show incident submission → triage → Trello card (3 min video)
3. 🚀 **Deploy**: Push to AWS or similar for production
4. 📊 **Monitor**: Check logs and observability events in production

---

**Need help?** Check `/Users/lilianestefaniamaradiagocorrea/Desktop/Hackathons/qa-multiagent/docs/` for detailed architecture and spec documents.
