# 👁️ OBSERVABILITY: Complete Instrumentation Guide

Este documento describe la **estrategia completa de observability** del sistema QA-MultiAgent.

---

## 📊 3 Pilares de Observability

```
┌─────────────────────────────────────────────────────────┐
│           OBSERVABILITY = Logs + Traces + Metrics      │
├──────────────────┬──────────────────┬──────────────────┤
│     LOGS         │     TRACES       │     METRICS      │
├──────────────────┼──────────────────┼──────────────────┤
│ ✅ Implemented   │ ✅ Implemented   │ 🟡 Basic         │
│ JSON structured  │ trace_id         │ Health endpoint  │
│ Per-stage        │ Queryable API    │ No Prometheus    │
│ File + stdout    │ Full audit trail │ No Grafana       │
└──────────────────┴──────────────────┴──────────────────┘
```

---

## ✅ LOGS: JSON Structured Logging

### Architecture

```
┌────────┐   ┌──────────────┐   ┌──────────────┐   ┌────────┐
│ Agent  │──>│ JSON Logger  │──>│ File Output  │   │ 📁 logs/
│        │   │ Formatter    │   │              │   │ agent.log
└────────┘   └──────────────┘   └──────────────┘   └────────┘
                  ↓
              stdout (docker logs)
```

### Log Format

```json
{
  "timestamp": "2026-04-08T22:50:00.123456+00:00",
  "level": "INFO",
  "logger": "src.agents.ticket_agent",
  "message": "Trello card created: MOCK-024F17C3",
  "trace_id": "cd8ad4f8-6746-450b-9eba-0696a309d8ea",
  "incident_id": 42,
  "context": {
    "card_id": "MOCK-024F17C3",
    "card_url": "https://trello.com/c/...",
    "severity": "P2",
    "module": "backend"
  }
}
```

### Implementation

```python
# infrastructure/observability/logger.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": getattr(record, 'trace_id', None),
            "incident_id": getattr(record, 'incident_id', None),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

# Usage in agents:
logger = logging.getLogger(__name__)
logger.info(f"Ticket created: {ticket_id}", extra={
    "trace_id": trace_id,
    "incident_id": incident_id,
})
```

### Access Logs

**Via Docker:**
```bash
docker compose logs backend -f --tail=100
```

**Via File:**
```bash
tail -f /data/logs/agent.log | jq .
```

---

## ✅ TRACES: Distributed Tracing with trace_id

### Flow

```
Incident Created (trace_id=UUID-1234)
  ↓ (propagated through all stages)
IngestAgent [trace_id=UUID-1234]
  ↓
TriageAgent [trace_id=UUID-1234]
  ↓
TicketAgent [trace_id=UUID-1234]
  ↓
NotifyAgent [trace_id=UUID-1234]
  ↓
ResolutionWatcher [trace_id=UUID-1234]
```

### Queryable via API

```bash
# Get all events for a single incident
curl http://localhost:8000/api/observability/events?trace_id=cd8ad4f8-6746-450b-9eba

# Response:
{
  "trace_id": "cd8ad4f8-6746-450b-9eba",
  "events": [
    {
      "stage": "ingest",
      "status": "success",
      "duration_ms": 45,
      "timestamp": "2026-04-08T22:50:00Z"
    },
    {
      "stage": "triage",
      "status": "success",
      "duration_ms": 2340,
      "metadata": {"severity": "P2", "confidence": 0.8}
    },
    {
      "stage": "ticket",
      "status": "success",
      "duration_ms": 890,
      "metadata": {"card_id": "MOCK-024F17C3"}
    },
    {
      "stage": "notify",
      "status": "success",
      "duration_ms": 450,
      "metadata": {"channels": ["slack", "email"]}
    }
  ]
}
```

### Implementation (Database)

```python
# infrastructure/database.py
class ObservabilityEventModel(Base):
    __tablename__ = "observability_events"
    
    id = Column(Integer, primary_key=True)
    trace_id = Column(String(36), nullable=False, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)
    stage = Column(String(20), nullable=False)  # ingest|triage|ticket|notify|resolved
    status = Column(String(20), nullable=False)  # success|error|deduplicated
    duration_ms = Column(Integer, nullable=False)
    metadata = Column(Text)  # JSON: {severity, module, confidence, card_id, etc.}
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
```

---

## 🟡 METRICS: Basic Instrumentation

### Current (Built-in)

```python
# 1. Health Endpoint
GET /api/health
{
  "status": "ok",
  "database": "connected",
  "uptime_seconds": 3600,
  "pending_incidents": 5,
  "mock_mode": true
}

# 2. Event Counts (queryable from DB)
SELECT COUNT(*) FROM observability_events WHERE stage = 'triage'
SELECT AVG(duration_ms) FROM observability_events WHERE stage = 'triage'
```

### Recommended (For Production)

```python
# infrastructure/observability/metrics.py (NEW)

from prometheus_client import Counter, Histogram, Gauge

# Counters
incidents_received = Counter(
    "incidents_received_total",
    "Total incidents submitted",
    ["status"],
)

tickets_created = Counter(
    "tickets_created_total",
    "Total tickets created",
    ["severity", "module"],
)

triages_completed = Counter(
    "triages_completed_total",
    "Total triages completed",
    ["severity"],
)

# Histograms (latency buckets)
triage_latency = Histogram(
    "triage_latency_ms",
    "Triage processing latency",
    buckets=(50, 100, 250, 500, 1000, 2000),
)

ticket_latency = Histogram(
    "ticket_creation_latency_ms",
    "Ticket creation latency",
    buckets=(100, 250, 500, 1000, 2000),
)

# Gauges
pending_incidents_gauge = Gauge(
    "pending_incidents",
    "Number of incidents awaiting triage",
)

active_tickets_gauge = Gauge(
    "active_tickets",
    "Number of active tickets in Trello",
)

# Usage:
@app.post("/api/incidents")
def submit_incident():
    incidents_received.labels(status="success").inc()
    # ...
```

### Prometheus Scrape Config

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'qa-multiagent'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/metrics'
```

---

## 📖 Event Types & Metadata

### Per-Stage Events

#### **1. INGEST Stage**

```json
{
  "stage": "ingest",
  "trace_id": "uuid",
  "status": "success",
  "duration_ms": 45,
  "metadata": {
    "incident_id": 42,
    "has_attachment": true,
    "attachment_type": "image/png",
    "injection_check": "passed",
    "message": "Incident received and validated"
  }
}
```

#### **2. TRIAGE Stage**

```json
{
  "stage": "triage",
  "trace_id": "uuid",
  "status": "success",
  "duration_ms": 2340,
  "metadata": {
    "severity_detected": "P2",
    "module_detected": "backend",
    "confidence_score": 0.88,
    "model": "claude-sonnet-4-6",
    "has_image": true,
    "has_log": false,
    "reasoning_steps": 4
  }
}
```

#### **3. TICKET Stage**

```json
{
  "stage": "ticket",
  "trace_id": "uuid",
  "status": "success",
  "duration_ms": 890,
  "metadata": {
    "card_id": "MOCK-024F17C3",
    "card_url": "https://trello.com/c/...",
    "severity": "P2",
    "module": "backend",
    "labels": ["P2-High", "module-backend"],
    "deduplicated": false
  }
}
```

#### **4. NOTIFY Stage**

```json
{
  "stage": "notify",
  "trace_id": "uuid",
  "status": "success",
  "duration_ms": 450,
  "metadata": {
    "channels_notified": ["slack", "email"],
    "slack_status": "sent",
    "email_status": "sent",
    "recipient": "oncall@company.com"
  }
}
```

#### **5. RESOLVED Stage**

```json
{
  "stage": "resolved",
  "trace_id": "uuid",
  "status": "success",
  "duration_ms": 120,
  "metadata": {
    "ticket_id": "TRELLO-ABC123",
    "days_to_resolution": 2,
    "resolution_notified": true,
    "final_status": "closed"
  }
}
```

---

## 🔍 Querying Observability

### Dashboard (Future: Grafana)

```
┌────────────────────────────────────────────────────────────┐
│ QA-MultiAgent Observability Dashboard                     │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  📊 Incidents: 247 submitted                               │
│  ✅ Success Rate: 99.6%                                    │
│  ⏱️  Avg Latency: 3.2s                                     │
│                                                             │
│  Severity Distribution: [P1: 12] [P2: 89] [P3: 120] [P4:26]
│                                                             │
│  Stage Latencies (p95):                                    │
│    Ingest:   50ms                                          │
│    Triage:   2.1s                                          │
│    Ticket:   950ms                                         │
│    Notify:   380ms                                         │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

### Queries (via API)

```python
# Python: Query observability
import httpx

client = httpx.Client()

# Get all events for trace
events = client.get(
    "http://localhost:8000/api/observability/events",
    params={"trace_id": "cd8ad4f8-6746-450b-9eba"}
).json()

# Analyze:
for event in events["events"]:
    print(f"{event['stage']:10s}: {event['duration_ms']:4d}ms ({event['status']})")

# Output:
# ingest    :   45ms (success)
# triage    : 2340ms (success)
# ticket    :  890ms (success)
# notify    :  450ms (success)
# Total: 3,725ms
```

---

## 📈 Observability Roadmap

### Phase 1 (MVP - Current) ✅
- ✅ JSON structured logging
- ✅ trace_id propagation
- ✅ Event persistence
- ✅ /api/observability/events endpoint

### Phase 2 (Production) 🟡
- ⬜ Prometheus metrics export
- ⬜ Grafana dashboard
- ⬜ Alerting rules (error rate >5%)
- ⬜ Performance dashboards (p95/p99 latencies)

### Phase 3 (Enterprise) 🟤
- ⬜ OpenTelemetry / Jaeger integration
- ⬜ Cross-service tracing
- ⬜ Distributed trace sampling
- ⬜ DataDog / New Relic integration

---

## 🧪 Testing Observability

```bash
# 1. Submit incident
TRACE=$(curl -s -X POST http://localhost:8000/api/incidents \
  -F "title=Test" \
  -F "description=Testing observability" \
  -F "reporter_email=test@company.com" \
  | jq -r '.trace_id')

echo "Trace ID: $TRACE"

# 2. Wait for processing
sleep 5

# 3. Query events
curl -s "http://localhost:8000/api/observability/events?trace_id=$TRACE" | jq '
  .events[] | {
    stage: .stage,
    duration: "\(.duration_ms)ms",
    status: .status,
    metadata_keys: (.metadata | keys)
  }
'

# Output:
# {
#   "stage": "ingest",
#   "duration": "45ms",
#   "status": "success",
#   "metadata_keys": ["incident_id", "injection_check", ...]
# }
# ...
```

---

## 🚨 Error Observability

When something fails, observability events capture it:

```json
{
  "stage": "ticket",
  "trace_id": "uuid",
  "status": "error",
  "duration_ms": 2500,
  "metadata": {
    "error_type": "trello_api_error",
    "error_message": "HTTP 401: Unauthorized - Invalid API key",
    "retry_count": 3,
    "fallback_applied": false
  }
}
```

**Action**: Alert team when error rate > 5% per stage

---

## 📚 References

- Event persistence: `backend/src/infrastructure/database.py::ObservabilityEventModel`
- Event emission: `backend/src/infrastructure/observability/events.py::emit_event()`
- API endpoint: `backend/src/api/routes.py::/api/observability/events`
- Logging setup: `backend/src/infrastructure/observability/logger.py`

---

**Status**: ✅ Basic observability complete. Production metrics roadmap prepared.
