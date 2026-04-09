# QUICKGUIDE.md — Quick Start Guide

Get the SRE Incident Intake & Triage Agent running in under 5 minutes.

---

## Prerequisites

- Docker + Docker Compose v2.0+
- Git
- API credentials (or use mock mode — see below)

---

## Step-by-Step Setup

### 1. Clone the repository
```bash
git clone <repo-url>
cd sre-triage-agent
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

> **No credentials?** Set `MOCK_INTEGRATIONS=true` to run the full pipeline without real API calls. All external calls return realistic simulated responses.

### 3. Build and start
```bash
docker compose up --build
```

First run builds backend and frontend images — may take 2-3 minutes.

### 4. Open the application
```
http://localhost:3000
```

### 5. Submit a test incident

Fill in the form:
- **Title:** `Checkout fails with 500 error`
- **Description:** `Users cannot complete purchase. Error appears after adding items to cart and clicking "Proceed to checkout".`
- **Your email:** `your@email.com`
- **Attachment:** Upload any error screenshot (PNG) or a `.log` file

Click **Submit Report**.

---

## Expected Result

Within ~60 seconds of submitting:

| What | Where |
|---|---|
| Immediate response in UI | Trace ID displayed + "You will be notified by email" |
| Trello card created | Board → "To Do" column with `[P2] Checkout fails...` |
| Slack notification | #incidents channel with severity + card link |
| Email confirmation | reporter's inbox with card reference |
| Observability trace | `http://localhost:3000/api/observability/events` |

---

## Running in Mock Mode (no real credentials needed)

Set in `.env`:
```bash
MOCK_INTEGRATIONS=true
```

The pipeline runs completely. All external calls (Trello, Slack, Email) return simulated responses. Logs clearly show `"mock": true` in each event. Useful for testing the pipeline without credentials or in CI environments.

---

## Verifying Observability

After submitting an incident, check the trace:

```bash
# Get the trace_id from the UI response, then:
curl "http://localhost:3000/api/observability/events?trace_id=YOUR_TRACE_ID"
```

You should see 4-5 events: `ingest → triage → ticket → notify → (resolved)`

Or view all recent events:
```bash
curl "http://localhost:3000/api/observability/events?limit=20"
```

---

## Running the E2E Smoke Test

```bash
# With the app running:
docker compose exec app python tests/e2e_smoke.py
```

This script:
1. Submits a test incident via POST /api/incidents
2. Verifies HTTP 201 + trace_id
3. Verifies GET /api/observability/events returns ≥4 events with the same trace_id
4. Verifies GET /api/incidents/:id shows status=notified

---

## Checking Logs

```bash
# All agent logs in real time:
docker compose logs -f

# Or read the persistent log file:
cat logs/agent.log
```

---

## Health Check

```bash
curl http://localhost:3000/api/health
```

Expected:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "uptime_seconds": 42,
  "database": "connected",
  "mock_mode": false
}
```

---

## Troubleshooting

| Problem | Likely cause | Solution |
|---|---|---|
| `docker compose up` fails during build | No internet or missing dependencies | Check network connection and Docker daemon status |
| `ANTHROPIC_API_KEY` error | Key not set or invalid | Verify key in `.env` — get one at console.anthropic.com |
| Trello card not created | Wrong `TRELLO_LIST_ID` or invalid token | Get IDs from Trello board URL, regenerate token at trello.com/app-key |
| Slack message not sent | Invalid webhook URL | Create a new webhook at api.slack.com/apps |
| Port 3000 already in use | Another service on that port | Change `APP_PORT=3001` in `.env` |
| `/api/health` returns 500 | Database not initialized | `docker compose down -v && docker compose up --build` |

---

## How to get Trello credentials

1. Go to https://trello.com/app-key → copy your **API Key**
2. Click "Token" on the same page → authorize → copy your **Token**
3. Open your Trello board → the URL contains the board ID: `trello.com/b/{BOARD_ID}/...`
4. Use the Trello API to get list IDs:
   ```bash
   curl "https://api.trello.com/1/boards/{BOARD_ID}/lists?key={API_KEY}&token={TOKEN}"
   ```
