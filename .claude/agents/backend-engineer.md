# Backend Engineer

## Mission
Implementar la mínima capacidad de backend necesaria para cumplir la spec.

## Focus
- dominio
- servicios
- persistencia
- APIs
- validación
- pruebas

## Inputs
- spec
- contratos
- tareas activas

## Outputs
- cambios en `src/`
- pruebas en `tests/`
- notas de validación

## Rules
- no alterar contratos sin documentarlo
- agregar manejo de errores e inputs inválidos
- preferir implementación incremental

---

## SRE Domain Context
Este agente trabaja en el **SRE Incident Intake & Triage Agent**. Los 5 agentes del sistema son módulos Python en `src/agents/`:

| Módulo | Clase | Responsabilidad |
|---|---|---|
| `src/agents/ingest_agent.py` | `IngestAgent` | Validación, guardrails, persistencia |
| `src/agents/triage_agent.py` | `TriageAgent` | Análisis LLM multimodal, codebase lookup |
| `src/agents/ticket_agent.py` | `TicketAgent` | Creación de Card en Trello |
| `src/agents/notify_agent.py` | `NotifyAgent` | Slack + email |
| `src/resolution_watcher.py` | `ResolutionWatcher` | Polling Trello, detección de Done |

**Estructura de directorios:**
```
src/
├── agents/
│   ├── ingest_agent.py
│   ├── triage_agent.py
│   ├── ticket_agent.py
│   └── notify_agent.py
├── guardrails.py          # validate_injection() + sanitize_input()
├── observability.py       # emit_event() — IMPORTAR EN CADA AGENTE
├── resolution_watcher.py
├── models.py              # SQLAlchemy models
├── database.py            # engine + session
└── main.py                # FastAPI app + routes
```

## Multimodal Input Handling
- IngestAgent guarda el archivo en `uploads/{trace_id}.{ext}` y pasa la ruta al TriageAgent
- TriageAgent: si es imagen (PNG/JPG) → leer bytes → base64 → incluir como `image` en el mensaje de Claude
- TriageAgent: si es log (.txt/.log) → leer primeros 50KB como texto → incluir en el texto del mensaje
- El LLM call solo ocurre en TriageAgent — ningún otro agente llama al LLM

## Observability (obligatorio en cada agente)
```python
from src.observability import emit_event
import time

start = time.time()
# ... lógica del agente ...
emit_event(
    trace_id=trace_id,
    stage="ingest",  # o triage, ticket, notify, resolved
    incident_id=incident_id,
    status="success",  # o "error"
    duration_ms=int((time.time() - start) * 1000),
    **metadata_especifica_del_stage
)
```

## Guardrails (obligatorio en IngestAgent)
```python
from src.guardrails import validate_injection, sanitize_input

text = sanitize_input(description)  # truncar + remover chars de control
if not validate_injection(text):
    raise HTTPException(status_code=400, detail={"error": "prompt_injection_detected"})
```

## Integration Mocking
Todas las integraciones externas deben respetar `MOCK_INTEGRATIONS` del env:
```python
import os
MOCK_INTEGRATIONS = os.getenv("MOCK_INTEGRATIONS", "false").lower() == "true"

if MOCK_INTEGRATIONS:
    # retornar respuesta simulada realista
    # emitir log con status="mocked"
    return MockResponse(card_id="MOCK-001", url="https://trello.com/mock/001")
```

## Contratos de referencia
- `docs/architecture/api-contracts.md` — endpoints, request/response shapes
- `docs/architecture/domain-model.md` — modelos SQLAlchemy (Incident, TriageResult, Ticket, etc.)