# SRE Incident Intake & Triage Agent

> Submitted for **AgentX Hackathon** by SoftServe — April 2026  
> Tag: **#AgentXHackathon**

---

## What it does

A multi-agent system that converts incident reports (text + screenshot or log file) into enriched Trello cards with automatic analysis of the Medusa.js e-commerce codebase. The system notifies the engineering team via Slack and the original reporter via email — and closes the loop when the incident is resolved.

**Key features beyond the minimum requirements:**
- 🧠 **Chain-of-thought reasoning** — Claude explains *why* it assigned each severity, not just what
- 🔗 **Incident deduplication** — similar incidents are linked to the existing ticket, preventing noise
- 📊 **Live observability dashboard** — real-time metrics at `/dashboard`
- ⚡ **50 concurrent incidents** — validated at 242 submissions/sec with 100% success rate

**Core pipeline:**
```
[Reporter submits incident] → [AI Triage by Claude claude-sonnet-4-6] → [Trello card created]
                           → [Slack #incidents notified]
                           → [Reporter confirmed by email]
                           → [Reporter notified on resolution]

Deduplication path:
[Similar incident] → [TicketAgent detects duplicate (≥75% similarity)] → [Linked, no duplicate card]
```

---

## Problem it solves

In e-commerce engineering teams, manual incident triage takes **15–45 minutes per incident**. The on-call engineer must read the report, correlate it with logs, search the codebase for the affected module, create a ticket with enough context, notify the right team channel, and remember to update the reporter on resolution.

Every minute of downtime in e-commerce has a direct cost in lost revenue. This system reduces triage time from ~30 minutes to ~2 minutes, produces technically enriched tickets, and closes the notification loop automatically.

---

## Architecture Overview

```
┌─────────────────┐     POST /api/incidents
│   Web UI Form   │ ──────────────────────────────────────────┐
│  + Dashboard    │                                            │
└─────────────────┘                                            ▼
                                                    ┌─────────────────┐
                                                    │  IngestAgent    │
                                                    │  • Guardrails   │
                                                    │  • Sanitization │
                                                    │  • trace_id     │
                                                    └────────┬────────┘
                                                             │
                                                             ▼
                                        ┌────────────────────────────────┐
                                        │        TriageAgent             │
                                        │  • Claude claude-sonnet-4-6    │
                                        │  • Multimodal (image + log)    │
                                        │  • Chain-of-thought reasoning  │
                                        │  • Medusa.js codebase lookup   │
                                        │  • severity / module / files   │
                                        └────────────┬───────────────────┘
                                                     │
                                                     ▼
                                        ┌────────────────────────────────┐
                                        │        TicketAgent             │
                                        │  • Deduplication (75% thresh.) │
                                        │  • Trello REST API             │
                                        │  • Severity labels + module    │
                                        └────────────┬───────────────────┘
                                                     │
                                                     ▼
                                        ┌────────────────────────────────┐
                                        │        NotifyAgent             │
                                        │  • Slack Incoming Webhook      │
                                        │  • Email via SendGrid          │
                                        └────────────────────────────────┘

                    (background job)
                    ┌─────────────────────────────┐
                    │      ResolutionWatcher       │
                    │  • Polls Trello every 60s   │
                    │  • Detects "Done" cards      │
                    │  • Triggers NotifyAgent      │
                    └─────────────────────────────┘
```

**Each agent has a single, non-overlapping responsibility. State lives in SQLite — agents are stateless and horizontally scalable.**

---

## Key Technical Decisions

| Decision | Choice | Reason |
|---|---|---|
| LLM | Claude claude-sonnet-4-6 | Multimodal native (image + text in one request), chain-of-thought reasoning |
| E-commerce base | Medusa.js (medusajs/medusa) | TypeScript, real production complexity, excellent open-source docs |
| Ticketing | Trello REST API | Simple key+token auth, mock-friendly, real integration available |
| Communicator | Slack Incoming Webhooks | No OAuth required, instant setup, real channel alerts |
| Observability | Structured JSON logging + SQLite events + `/dashboard` | "From Vibes to Verifiable" — fully traceable end-to-end |
| Guardrails | Prompt injection detection in IngestAgent | Input validated before reaching the LLM — zero wasted tokens |
| Responsible AI | `reporter_email` excluded from LLM prompt | Privacy + transparency by design |
| Deduplication | SequenceMatcher weighted similarity (60% title + 40% desc) | Prevents ticket noise without requiring a vector DB |

---

## Demo

> 🎬 **Video demo:** [YouTube link — add before submission] (max 3 min, English, #AgentXHackathon)

**What the demo shows:**
1. Submitting an incident report with a screenshot of a 500 error in checkout
2. Chain-of-thought reasoning from Claude (step-by-step: symptom → severity → module → files)
3. Trello card created with enriched technical context (severity P2, module: cart)
4. Slack notification in #incidents + email confirmation to reporter
5. Submitting a similar incident → deduplication detected → linked to existing ticket
6. Live dashboard at `http://localhost:3000/dashboard` — KPIs, severity distribution, recent incidents
7. Observability trace at `http://localhost:8000/api/observability/events` — same `trace_id` across all stages

---

## Quick Start

See [QUICKGUIDE.md](QUICKGUIDE.md) for full instructions.

**TL;DR:**
```bash
git clone <repo-url>
cd qa-multiagent
cp .env.example .env
# Fill in: ANTHROPIC_API_KEY, TRELLO_API_KEY, TRELLO_API_TOKEN, SLACK_WEBHOOK_URL
# OR: set MOCK_INTEGRATIONS=true for demo without real credentials
docker compose up --build
# Incident form:  http://localhost:3000
# Dashboard:      http://localhost:3000/dashboard
# API docs:       http://localhost:8000/docs
```

---

## Scalability Validation

Load tested with 50 concurrent incidents (mock mode):

```
Throughput:   242.5 incidents/sec (submission)
Success rate: 100% (50/50 tickets created)
P95 latency:  196ms
```

See [SCALING.md](SCALING.md) for full Phase 1→3 architecture roadmap.

---

## Documentation

| File | Contents |
|---|---|
| [AGENTS_USE.md](AGENTS_USE.md) | Agent architecture, reasoning chain, deduplication, observability evidence, safety measures |
| [SCALING.md](SCALING.md) | How the system scales — Phase 1 to 3, cost analysis, bottleneck analysis |
| [QUICKGUIDE.md](QUICKGUIDE.md) | Step-by-step setup, testing, troubleshooting |
| [scripts/README.md](scripts/README.md) | Load test script usage |
| [docs/context/](docs/context/) | Hackathon context, assignment, technical requirements |

---

## License

MIT — see [LICENSE](LICENSE)
