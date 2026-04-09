# Open Questions

## Decisions already made (documented here for traceability)

| Question | Decision | Reason |
|---|---|---|
| Which e-commerce app should the agent use as its knowledge base? | **Medusa.js** (medusajs/medusa) | TypeScript, high real-world complexity, excellent documentation, actively maintained. The agent analyzes payments, orders, and inventory. |
| Which multimodal LLM should be used? | **Claude claude-sonnet-4-6** (Anthropic SDK) | Native multimodal support, available in the workspace, handles image + text in the same request. |
| What backend stack? | **Python + FastAPI** | Best integration with the Anthropic SDK, code analysis libraries, and observability. |
| What ticketing system? | **Trello** (real API) | The team has an account. The hackathon accepts "Jira / Linear / Other" — Trello is valid. Cards represent incidents. |
| What communicator? | **Slack** (Incoming Webhook) | The team has a workspace. Webhooks do not require complex OAuth. |
| What modalities should be supported? | **Text + image (PNG/JPG) + log (.txt/.log)** | Covers the most common incident report cases. Video is optional for the MVP. |
| Team size? | **2-3 people** | Tasks are divided in parallel by layer (frontend, backend, integrations). |
| Persistence? | **SQLite** (via SQLAlchemy) | Simplifies Docker setup. The schema is PostgreSQL-compatible for future scaling. |
| How does the agent access the Medusa.js codebase? | Cloned during Docker build, mounted as a read-only volume. Tool `read_ecommerce_file(path)` in TriageAgent. | No embedding complexity needed for the MVP. |

## Open questions

### MVP scope
- **Runbook suggestions in the MVP?** The hackathon mentions them as optional for extra points. Evaluate if there is time after the end-to-end flow works.
- **Incident deduplication?** Also optional. Add if time remains — requires semantic similarity comparison of reports.
- **Automatic severity scoring with additional business logic?** The TriageAgent already outputs P1-P4, but is an extra rule layer needed? For now, the LLM determines severity.

### Implementation
- **Trello webhook or polling to detect resolved cards?** Trello supports webhooks. If configuration is too complex for the available time, use 60-second polling as a fallback.
- **How does ResolutionWatcher access Trello credentials in Docker?** Via container environment variables — already defined in `.env.example`.
- **Should the web form be plain HTML or use a mini framework?** HTML5 + vanilla JS is sufficient for the demo. Do not over-engineer the frontend.
- **Real email or mock?** SendGrid if credentials are available, mock with detailed logs otherwise. Set `MOCK_EMAIL=true` in `.env`.

### Demo and submission
- **Who records the demo video?** It should be recorded once the end-to-end flow works. Maximum 3 minutes, in English, uploaded to YouTube with tag `#AgentXHackathon`.
- **Should the repo be public before or only at submission time?** Make it public just before submission to avoid others seeing the work early.
- **Which Trello account should be used for the demo board?** Use a dedicated board for the hackathon with columns: To Do / In Progress / Done.

## Known technical constraints
- Docker Compose is mandatory — the whole app must run with `docker compose up --build`
- You cannot fork existing projects — the code must be original
- The repo must have an MIT license
- The video must be in English
- Absolute deadline: April 9 at 10PM COT — no extensions
