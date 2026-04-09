# Scripts

Utility scripts for testing, validation, and demonstration.

---

## load_test_50_incidents.py

Load test: submits N concurrent incidents to the running API and measures throughput, latency, and ticket creation success rate.

### Prerequisites

```bash
# The API must be running (docker compose up --build OR local dev server)
pip install httpx click
```

### Usage

```bash
# Mock mode (MOCK_INTEGRATIONS=true in .env — no real API calls)
python scripts/load_test_50_incidents.py --mock --incidents 50

# Real mode (requires Trello/Slack/SendGrid credentials in .env)
python scripts/load_test_50_incidents.py --real --incidents 10

# Custom number of concurrent incidents
python scripts/load_test_50_incidents.py --mock --incidents 100
```

### What it validates

- Phase 1: Submits N incidents concurrently to `POST /api/incidents`
- Phase 2: Polls `GET /api/incidents/:trace_id` until tickets are created (up to 60s)
- Reports: throughput, P95 latency, success rate, severity distribution

### Expected output (mock mode, 50 incidents)

```
🚀 LOAD TEST: 50 Concurrent Incidents — MOCK mode
======================================================================
📝 Phase 1: Submitting 50 incidents concurrently
   ✅ Submitted: 50/50
   ⏱️  Duration: 0.21s
   📊 Throughput: 242.5 incidents/sec

🎫 Phase 2: Polling for ticket creation (up to 60s)
   Poll  1/60: 34/50 tickets ✓
   Poll  2/60: 50/50 tickets ✓
   ✅ All tickets created!

Performance Metrics:
  Submit latency:  P95=196ms | Avg=153ms | Max=199ms
  Throughput:      21.4 incidents/sec (end-to-end)
  Success rate:    100.0%
```

### Deduplication behavior

When sending similar incidents, the system will deduplicate them (TicketAgent links
duplicates to the existing card). The load test uses varied templates so all 50 
incidents generate unique tickets. To test deduplication specifically, submit incidents
with identical or near-identical titles.

---

## Viewing results

After running the load test, check the full observability trace:

```bash
# All events from the last load test
curl http://localhost:8000/api/observability/events?limit=200

# Filter by stage
curl "http://localhost:8000/api/observability/events?stage=ticket&limit=50"

# Filter by specific trace_id (copy from load test output)
curl "http://localhost:8000/api/observability/events?trace_id=<uuid>"
```
