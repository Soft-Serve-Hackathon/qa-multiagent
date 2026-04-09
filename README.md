# SRE Incident Intake & Triage Agent

> Submitted for **AgentX Hackathon** by SoftServe — April 2026  
> Tag: [#AgentXHackathon](https://youtube.com)

---

## What it does

A multi-agent system that converts incident reports (text + screenshot or log file) into enriched Trello cards with automatic analysis of the Medusa.js e-commerce codebase. The system notifies the engineering team via Slack and the original reporter via email — and closes the loop when the incident is resolved.

**Core pipeline:**
```
[Reporter] → IngestAgent → TriageAgent → QAAgent → FixRecommendationAgent → TicketAgent → NotifyAgent
                            (Claude claude-sonnet-4-6 + Medusa.js codebase)
                                                          ↑ background
                                                   ResolutionWatcher → NotifyAgent (on resolve)
```

---

## Problem it solves

In e-commerce engineering teams, manual incident triage takes **15–45 minutes per incident**. The on-call engineer must read the report, correlate it with logs, search the codebase for the affected module, create a ticket with enough context, notify the right team channel, and remember to update the reporter on resolution.

Every minute of downtime in e-commerce has a direct cost in lost revenue. This system reduces triage time from ~30 minutes to ~2 minutes, produces technically enriched tickets, and closes the notification loop automatically.

→ Full problem statement: [docs/idea/problem-statement.md](docs/idea/problem-statement.md)

---

## Architecture Overview

```
┌─────────────────┐     POST /api/incidents
│   Web UI Form   │ ──────────────────────────────────────────┐
│  (Next.js)      │                                            │
└─────────────────┘                                            ▼
                                                    ┌─────────────────┐
                                                    │  IngestAgent    │
                                                    │  • Guardrails   │
                                                    │  • trace_id     │
                                                    │  • File upload  │
                                                    └────────┬────────┘
                                                             │
                                                             ▼
                                        ┌────────────────────────────────┐
                                        │        TriageAgent             │
                                        │  • Claude claude-sonnet-4-6    │
                                        │  • Multimodal (image + log)    │
                                        │  • Medusa.js codebase lookup   │
                                        │  • severity / module / files   │
                                        │  • reasoning_chain (5 steps)   │
                                        └────────────┬───────────────────┘
                                                     │
                                                     ▼
                                        ┌────────────────────────────────┐
                                        │          QAAgent               │
                                        │  • Finds existing tests        │
                                        │  • Proposes regression tests   │
                                        │  • Scans Medusa.js test suite  │
                                        └────────────┬───────────────────┘
                                                     │
                                                     ▼
                                        ┌────────────────────────────────┐
                                        │    FixRecommendationAgent      │
                                        │  • Reads affected source files │
                                        │  • Proposes concrete fix       │
                                        │  • Assesses risk level         │
                                        └────────────┬───────────────────┘
                                                     │
                                          ┌──────────┴──────────┐
                                          ▼                      ▼
                               ┌─────────────────┐   ┌──────────────────┐
                               │  TicketAgent    │   │   NotifyAgent    │
                               │  • Deduplication│   │  • Slack webhook │
                               │  • Trello card  │   │  • Email (SMTP)  │
                               │  • Owner routing│   │  • Reporter CC   │
                               └─────────────────┘   └──────────────────┘

                    (background thread)
                    ┌─────────────────────────────┐
                    │      ResolutionWatcher       │
                    │  • Polls Trello every 60s   │
                    │  • Detects "Done" cards      │
                    │  • Triggers NotifyAgent      │
                    └─────────────────────────────┘
```

**Each agent has a single, non-overlapping responsibility.** See [docs/architecture/system-overview.md](docs/architecture/system-overview.md) for the full design.

---

## Key Technical Decisions

| Decision | Choice | Reason |
|---|---|---|
| LLM | Claude claude-sonnet-4-6 | Multimodal native (image + text in one request) |
| E-commerce base | Medusa.js (medusajs/medusa) | TypeScript, high real complexity, excellent docs |
| Ticketing | Trello REST API | Team has credentials, simple key+token auth |
| Communicator | Slack Incoming Webhooks | No OAuth required, instant setup |
| Observability | Structured JSON logging + `/api/observability/events` | "From Vibes to Verifiable" — traceable end-to-end |
| Guardrails | Prompt injection detection in IngestAgent | Input validated before reaching the LLM |
| Responsible AI | reporter_email excluded from LLM prompt | Privacy + transparency by design |

→ Full decision log: [docs/architecture/adr/](docs/architecture/adr/)

---

## Demo

> 🎬 **Video demo:** [YouTube link — add before submission] (max 3 min, English, #AgentXHackathon)

**What the demo shows:**
1. Submitting an incident report with a screenshot of a 500 error in checkout
2. Real-time triage by Claude (severity P2, module: cart, files from Medusa.js)
3. Trello card created with enriched technical context
4. Slack notification in #incidents
5. Email confirmation to the reporter
6. Observability events visible at `/api/observability/events` — same `trace_id` across all stages

---

## Quick Start

See [QUICKGUIDE.md](QUICKGUIDE.md) for full instructions.

**TL;DR:**
```bash
git clone <repo-url>
cd qa-multiagent

# Clone Medusa.js codebase used by triage file lookups
git clone https://github.com/medusajs/medusa.git medusa-repo

cp .env.example .env
# Ensure triage reads from the local Medusa.js clone
export MEDUSA_REPO_PATH=./medusa-repo

# Fill in: ANTHROPIC_API_KEY, TRELLO_API_KEY, TRELLO_API_TOKEN, SLACK_WEBHOOK_URL
# OR: set MOCK_INTEGRATIONS=true for demo without real credentials
docker compose up --build
# Open http://localhost:3000
```

For real Trello card creation and Slack-based owner assignment, configure:

```bash
export MOCK_INTEGRATIONS=false
export OWNER_ROUTING_JSON='{"cart":{"trello_member_id":"<TRELLO_MEMBER_ID>","slack_user_id":"<SLACK_USER_ID>"},"payment":{"trello_member_id":"<TRELLO_MEMBER_ID>","slack_user_id":"<SLACK_USER_ID>"},"default":{"trello_member_id":"<ONCALL_TRELLO_MEMBER_ID>","slack_user_id":"<ONCALL_SLACK_USER_ID>"}}'
```

When an incident is created, the system will:
1. Create the Trello card in the configured list.
2. Assign the card to the routed Trello member.
3. Send Slack alert mentioning the routed owner (`<@SLACK_USER_ID>`).
4. Send a Slack resolution notice when the card moves to Done.

If you are using the mock-integration profile, keep `MOCK_INTEGRATIONS=true` and still point
`MEDUSA_REPO_PATH` to `./medusa-repo` so Claude can analyze real e-commerce code context.

---

## Documentation

| File | Contents |
|---|---|
| [AGENTS_USE.md](AGENTS_USE.md) | Agent architecture, observability evidence, safety measures |
| [SCALING.md](SCALING.md) | How the system scales and future roadmap |
| [QUICKGUIDE.md](QUICKGUIDE.md) | Step-by-step setup and testing guide |
| [docs/specs/mvp/spec.md](docs/specs/mvp/spec.md) | Full MVP specification (FR1-FR13, AC1-AC8) |
| [docs/architecture/system-overview.md](docs/architecture/system-overview.md) | System design and agent pipeline |
| [docs/architecture/adr/](docs/architecture/adr/) | Architecture Decision Records |
| [docs/context.md](docs/context.md) | Hackathon context and requirements |

---

## License

MIT — see [LICENSE](LICENSE)
