# QUICKGUIDE.md — Quick Start Guide

Get the SRE Incident Intake & Triage Agent running in under 5 minutes.

---

## Prerequisites

- Docker + Docker Compose v2.0+
- Git
- API credentials (or use mock mode — no credentials needed)

---

## Step-by-Step Setup

### 1. Clone the repository
```bash
git clone <repo-url>
cd qa-multiagent
```

### 2. Configure environment
```bash
cp .env.example .env
```

Open `.env` and fill in your credentials:

```bash
# Required for LLM triage
ANTHROPIC_API_KEY=sk-ant-...

# Required for Trello ticketing
TRELLO_API_KEY=your-trello-api-key
TRELLO_API_TOKEN=your-trello-api-token
TRELLO_BOARD_ID=your-board-id
TRELLO_LIST_ID=your-todo-list-id
TRELLO_DONE_LIST_ID=your-done-list-id

# Required for Slack notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Optional — leave MOCK_EMAIL=true if no SendGrid account
SENDGRID_API_KEY=SG...
MOCK_EMAIL=false
```

> **No credentials?** Set `MOCK_INTEGRATIONS=true` to run the full pipeline without real API calls. All external calls return realistic simulated responses — perfect for the demo.

### 3. Build and start
```bash
docker compose up --build
```

> First run clones Medusa.js (e-commerce reference repo) — may take 2-3 minutes.

### 4. Open the application

| URL | What |
|---|---|
| `http://localhost:3000` | Incident submission form |
| `http://localhost:3000/dashboard` | Live observability dashboard |
| `http://localhost:8000/docs` | Backend API (FastAPI Swagger) |

### 5. Submit a test incident

Fill in the form at `http://localhost:3000`:
- **Title:** `Checkout fails with 500 error`
- **Description:** `Users cannot complete purchase. Error appears after adding items to cart and clicking "Proceed to checkout".`
- **Your email:** `your@email.com`
- **Attachment:** Upload any error screenshot (PNG) or a `.log` file

Click **Submit Report**.

---

## Expected Result

Within ~30 seconds of submitting:

| What | Where |
|---|---|
| Immediate response in UI | Trace ID displayed + "You will be notified by email" |
| AI reasoning visible | Chain-of-thought steps in triage result |
| Trello card created | Board → "To Do" column with `[P2] Checkout fails...` |
| Slack notification | #incidents channel with severity + card link |
| Email confirmation | Reporter's inbox with card reference |
| Dashboard updated | `http://localhost:3000/dashboard` — new incident visible |
| Observability trace | `http://localhost:8000/api/observability/events` |

---

## Running in Mock Mode (no credentials needed)

Set in `.env`:
```bash
MOCK_INTEGRATIONS=true
```

The pipeline runs completely end-to-end. All external calls (Trello, Slack, Email) return realistic simulated responses. Logs clearly show `"mock": true` in each event. Perfect for testing without credentials or in CI.

---

## Testing Deduplication

Submit two similar incidents (same module, similar title):

```bash
# First incident
curl -X POST http://localhost:8000/api/incidents \
  -F "title=Database connection pool exhausted" \
  -F "description=DB pool at capacity, new connections timing out" \
  -F "reporter_email=engineer@company.com"

# Wait a few seconds, then submit a similar one
curl -X POST http://localhost:8000/api/incidents \
  -F "title=DB pool full, connections failing" \
  -F "description=Cannot open new DB connections, pool exhausted" \
  -F "reporter_email=engineer2@company.com"
```

The second incident will appear as `status=deduplicated` in the dashboard and API — linked to the first ticket, no duplicate Trello card created.

---

## Verifying Observability

After submitting an incident, check the full trace:

```bash
# Get the trace_id from the UI, then:
curl "http://localhost:8000/api/observability/events?trace_id=YOUR_TRACE_ID"

# View all recent events (last 20):
curl "http://localhost:8000/api/observability/events?limit=20"

# Filter by pipeline stage:
curl "http://localhost:8000/api/observability/events?stage=triage"
```

Expected: 4–5 events (`ingest → triage → ticket → notify → resolved`) all sharing the same `trace_id`.

Or open the live dashboard: `http://localhost:3000/dashboard`

---

## Running the Load Test (50 concurrent incidents)

```bash
# Install dependencies (once):
pip install httpx click

# Run with mock mode (no credentials needed):
python scripts/load_test_50_incidents.py --mock --incidents 50

# Expected output:
# ✅ Submitted: 50/50
# 📊 Throughput: ~242 incidents/sec
# ✅ All tickets created in ~2s
```

See [scripts/README.md](scripts/README.md) for full usage.

---

## Checking Logs

```bash
# All agent logs in real time:
docker compose logs -f backend

# Or read the persistent log file:
cat logs/agent.log
```

Each log line is structured JSON: `timestamp`, `level`, `logger`, `message`.

---

## Health Check

```bash
curl http://localhost:8000/api/health
```

Expected:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "uptime_seconds": 42,
  "database": "connected",
  "mock_mode": true
}
```

---

## Troubleshooting

| Problem | Likely cause | Solution |
|---|---|---|
| `docker compose up` fails on Medusa.js clone | No internet or git not available in Docker | Check network, ensure Docker has internet access |
| `ANTHROPIC_API_KEY` error | Key not set or invalid | Verify key in `.env` — get one at console.anthropic.com |
| Trello card not created | Wrong `TRELLO_LIST_ID` or invalid token | Get IDs from Trello board URL, regenerate token at trello.com/app-key |
| Slack message not sent | Invalid webhook URL | Create a new webhook at api.slack.com/apps |
| Port 3000 or 8000 in use | Another service on that port | Change `APP_PORT` in `.env` and update `docker-compose.yml` |
| Database column error on startup | Old DB from previous version | Run: `docker compose down -v && docker compose up --build` |

---

## How to get Trello credentials

1. Go to https://trello.com/app-key → copy your **API Key**
2. Click "Token" on the same page → authorize → copy your **Token**
3. Open your Trello board → the URL contains the board ID: `trello.com/b/{BOARD_ID}/...`
4. Use the Trello API to get list IDs:
   ```bash
   curl "https://api.trello.com/1/boards/{BOARD_ID}/lists?key={API_KEY}&token={TOKEN}"
   ```
