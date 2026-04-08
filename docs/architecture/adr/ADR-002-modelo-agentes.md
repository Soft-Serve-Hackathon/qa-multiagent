# ADR-002: Modelo de orquestación de agentes

## Status
Accepted

## Context
El sistema requiere coordinar múltiples agentes IA que ejecutan en secuencia o en paralelo, cada uno con un modelo y responsabilidad diferente. Hay dos enfoques principales:

1. **Orquestación via framework** (LangChain, LlamaIndex, CrewAI, etc.): abstracciones de alto nivel para cadenas de agentes.
2. **Orquestación manual directa**: cada agente es una función Python que llama al SDK del modelo correspondiente, y la coordinación la maneja el entrypoint del workflow.

El riesgo del enfoque con framework es el acoplamiento a una abstracción que puede cambiar de API, agregar overhead innecesario y dificultar el debugging en el MVP.

## Decision
**Orquestación manual directa** sin frameworks de agentes en el MVP.

Cada agente es un módulo Python con:
- Una función principal `run(input) -> output` con tipos explícitos
- Un cliente IA inyectado como dependencia (facilita testing con mocks)
- Sin estado interno persistente entre llamadas

La coordinación entre agentes la maneja el entrypoint del workflow (`pr_review.py`, `qa_trigger.py`), que llama a los agentes en el orden correcto y pasa los outputs como inputs del siguiente.

```python
# Ejemplo de orquestación en qa_trigger.py
findings = qa_agent.run(diff=pr.diff, files=pr.files_changed)
tech_report, biz_report = await asyncio.gather(
    technical_reporter.run(findings),
    business_reporter.run(findings)
)
ticket = ticket_creator.run(tech_report, biz_report, pr)
solution_proposer.run(findings, ticket)
```

## Consequences
**Positivo:**
- Sin dependencias externas de frameworks — el código es Python puro + SDKs oficiales
- Debugging directo: el flujo de datos es explícito y trazable
- Fácil de testear: cada agente se prueba de forma aislada con mocks del cliente IA
- Reemplazar un modelo (Claude → GPT o viceversa) solo requiere cambiar el cliente inyectado

**Negativo:**
- No hay retry automático, memoria ni herramientas de observabilidad que un framework daría gratis
- El manejo de errores y el estado parcial se implementa manualmente

**Trade-offs:**
- Se acepta más código boilerplate a cambio de control total y menor complejidad en el MVP

## Alternatives Considered
- **LangChain**: ecosistema amplio pero API inestable entre versiones, abstracción costosa para este caso de uso
- **CrewAI**: orientado a agentes con roles colaborativos — más expresivo pero over-engineering para el MVP
- **LlamaIndex**: enfocado en RAG y recuperación de documentos — no aplica bien al flujo de PR review
