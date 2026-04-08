# Testing Instructions — SRE Incident Triage Agent

## Contexto
Tests en `backend/tests/unit/` y `backend/tests/integration/`.
Framework: `pytest` + `pytest-mock`. Los clientes externos (Anthropic, Trello, Slack, SendGrid) se mockean siempre.

## Estructura esperada

```
backend/tests/
├── unit/
│   ├── test_ingest_agent.py       # Validación, injection detection, tipos de adjunto
│   ├── test_triage_agent.py       # Lógica de triage, tool calls mockeados
│   ├── test_ticket_agent.py       # Creación de card (Trello mock)
│   ├── test_notify_agent.py       # Slack + SendGrid mocks
│   └── test_resolution_watcher.py # Lógica de polling
└── integration/
    ├── test_api_incidents.py       # POST /api/incidents end-to-end
    └── test_pipeline.py            # Flujo completo ingest→triage→ticket→notify
```

## Reglas

- Deriva pruebas desde los criterios de aceptación de `docs/specs/mvp/spec.md` (AC1-AC8).
- Cubre: happy path, edge cases (archivo inválido, injection detectada, API externa caída) y errores relevantes.
- Todo test de agente debe usar mock del cliente LLM — nunca llamadas reales a Anthropic.
- Verifica que `trace_id` se propague correctamente a través de todo el pipeline.
- Tests de guardrails: valida que los patrones de injection detection en `shared/security.py` rechacen inputs maliciosos.
- Documenta en el handoff si la cobertura queda parcial y por qué.
