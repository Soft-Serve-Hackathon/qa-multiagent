# SCALING.md — Scaling Architecture

---

## Current MVP Architecture (Phase 1)

The MVP runs as a single Docker container with FastAPI, SQLite, and a background thread for the ResolutionWatcher. Suitable for:
- Hackathon demo
- Small teams (<50 incidents/day)
- Single e-commerce application

**Deployment:** `docker compose up --build` — one command, no external services required.

---

## Scaling Bottlenecks Identified

### 1. Synchronous LLM calls in TriageAgent
**Current:** TriageAgent is called as a FastAPI BackgroundTask. Under load, multiple incidents queue in the same process.  
**Bottleneck at:** ~10 concurrent incidents  
**Phase 2 solution:** Message queue (RabbitMQ or AWS SQS). IngestAgent publishes to a queue. N TriageAgent workers consume in parallel. Workers are stateless — horizontal scaling is trivial.

### 2. SQLite as persistence layer
**Current:** SQLite file (`data/incidents.db`) with SQLAlchemy ORM.  
**Bottleneck at:** ~1,000 concurrent writes  
**Phase 2 solution:** PostgreSQL. The SQLAlchemy ORM is already configured with `DATABASE_URL` env var. Migration requires only changing the connection string — no code changes.

### 3. ResolutionWatcher polling
**Current:** Background thread polls Trello every 60 seconds.  
**Bottleneck at:** Latency (up to 60s) and Trello API rate limits at high volume  
**Phase 2 solution:** Trello Webhooks. The endpoint `POST /api/webhooks/trello` is already implemented. Only Trello webhook configuration is needed — zero code changes.

### 4. Single NotifyAgent instance
**Current:** Single thread sends all Slack and email notifications.  
**Bottleneck at:** ~20 notifications/minute (SendGrid rate limits)  
**Phase 2 solution:** NotifyAgent as a separate worker consuming from a notifications queue. N workers in parallel, each handling one channel.

### 5. Medusa.js file-based context
**Current:** TriageAgent reads specific files from the mounted Medusa.js repo.  
**Bottleneck at:** Latency per tool call, inaccuracy on ambiguous modules  
**Phase 2 solution:** ChromaDB (or similar) vector store with embeddings of the Medusa.js codebase. Semantic search returns the top-K most relevant code snippets in one fast query.

---

## Phase 2 Architecture (Production-Ready, 500-5,000 incidents/day)

```
[Web UI / API Gateway]
        │
        ▼
[FastAPI + Load Balancer]
        │
        ▼
[Message Queue: RabbitMQ / SQS]
   ├── incidents queue
   └── notifications queue
        │
        ├─── [TriageAgent Workers × N]  ──→ [PostgreSQL]
        │           │                         │
        │           └──→ [Vector Store]       │
        │                (ChromaDB / Pinecone) │
        │                                     │
        ├─── [TicketAgent Workers × N] ──→ [PostgreSQL]
        │           │
        │           └──→ [Trello API]
        │
        └─── [NotifyAgent Workers × N] ──→ [PostgreSQL]
                    ├──→ [Slack]
                    └──→ [Email]

[ResolutionWatcher] ──→ [Trello Webhooks] (push, no polling)
[Observability] ──→ [OpenTelemetry Collector] ──→ [Jaeger / Grafana]
```

---

## Phase 3 — Enterprise / Multi-tenant (5,000+ incidents/day)

- **Multi-tenant routing:** One deployment supports multiple teams. Each team has its own Trello board, Slack channel, and routing rules (configured via YAML or database).
- **Severity-based escalation:** P1 incidents trigger PagerDuty/OpsGenie in addition to Slack.
- **Custom triage rules per team:** Teams can define module-to-team mappings (e.g., cart incidents → payments team).
- **Audit trail:** Immutable event log (append-only) for compliance and post-incident reviews.
- **Rate limiting per tenant:** Prevents one team from exhausting LLM API quota.

---

## Cost Analysis

**Per incident (MVP, single call to Claude claude-sonnet-4-6):**
- Input tokens: ~2,000 (system prompt + incident text + codebase context) ≈ $0.006
- Output tokens: ~300 (triage result JSON) ≈ $0.006
- Total LLM cost per incident: **~$0.012**

**Daily cost projections:**
| Volume | LLM cost/day | Notes |
|---|---|---|
| 10 incidents/day | ~$0.12 | Demo / small team |
| 100 incidents/day | ~$1.20 | Growing startup |
| 1,000 incidents/day | ~$12.00 | Mid-size e-commerce |
| 10,000 incidents/day | ~$120.00 | Enterprise — consider caching frequent patterns |

**Cost optimization strategies:**
- Cache triage results for identical/near-identical incident texts (semantic deduplication)
- Use a lighter model (claude-haiku-4-5) for low-confidence initial triage, escalate to claude-sonnet-4-6 for P1/P2
- OpenRouter support: `LLM_PROVIDER=openrouter` env var allows switching to alternative models at lower cost

---

## OpenRouter Support

The LLM client abstraction in `src/llm_client.py` supports `LLM_PROVIDER` env var:
- `LLM_PROVIDER=anthropic` (default) → uses Anthropic SDK directly
- `LLM_PROVIDER=openrouter` → routes through OpenRouter API, enabling access to alternative models

This allows cost optimization in production without changing agent code.

---

## Operational Runbook (Phase 2)

**Scaling TriageAgent workers:**
```bash
docker compose up --scale triage-worker=5
```

**Migrating from SQLite to PostgreSQL:**
```bash
DATABASE_URL=postgresql://user:pass@host/db docker compose up --build
# Alembic migrations run automatically on startup
```

**Enabling Trello webhooks (eliminates polling):**
1. Set `TRELLO_WEBHOOK_URL=https://your-domain.com/api/webhooks/trello` in `.env`
2. Register webhook via Trello API: `POST https://api.trello.com/1/webhooks`
3. No code changes required — endpoint already implemented
