# ADR-002: Estrategia de observability — Logging estructurado JSON

## Status
Accepted

## Context
El hackathon requiere "logs/trazas/métricas cubriendo las etapas principales del pipeline (ingest → triage → ticket → notify → resolved)". La learning session del 8 de abril fue sobre "AI Observability in Production Platforms" y el tema del 9 de abril es "From Vibes to Verifiable" — ambos señalan que los evaluadores van a buscar evidencia de observability real, no print statements.

Los evaluadores NO ejecutan el código (mentores solo leen el repo y el video demo). Por tanto, la observability debe ser:
1. **Visible en el video demo** — los logs deben aparecer en pantalla durante la demostración
2. **Consultable via API** — un endpoint que muestre los eventos permite demostrarla sin necesidad de acceder al servidor
3. **Estructurada** — JSON con campos estándar para que sea parseada por herramientas modernas

## Decision
Implementar logging estructurado JSON con un módulo centralizado `src/observability.py`.

Cada agente llama a `emit_event(trace_id, stage, incident_id, status, duration_ms, **metadata)` al completar su proceso. El módulo escribe a:
1. **stdout** (visible en `docker compose logs` y en la terminal del demo)
2. **`logs/agent.log`** (archivo persistente montado como volumen Docker: `./logs:/app/logs`)
3. **SQLite tabla `observability_events`** (consultable via GET /api/observability/events)

El `trace_id` (UUID v4) es asignado por IngestAgent y fluye sin modificación a través de todos los agentes, permitiendo reconstruir el pipeline completo de un incidente con un solo filtro.

Para el demo, el endpoint `GET /api/observability/events?trace_id=XXX` retorna todos los eventos del pipeline en orden cronológico, mostrando la trazabilidad end-to-end.

## Consequences

**Positivos:**
- Observability completamente demostrable sin infraestructura externa
- trace_id permite correlación de todos los eventos de un incidente
- Visible en el video demo (terminal + endpoint API)
- `docker compose logs` muestra los eventos en tiempo real
- El endpoint GET /api/observability/events permite mostrar la evidencia a los evaluadores en el README con un screenshot

**Negativos / Trade-offs:**
- No persiste los logs entre reinicios del contenedor si el volumen no está montado. Se mitiga documentando el volumen en `docker-compose.yml`.
- No es un sistema de observability enterprise (sin Jaeger, sin dashboards, sin alertas). Se documenta como limitación conocida en `AGENTS_USE.md`.

## Alternatives Considered

**OpenTelemetry + Jaeger:**
- Descartado: requiere servicios adicionales en Docker Compose (Jaeger UI, collector), aumenta complejidad del setup y puede fallar en el entorno de evaluación. El valor demostrativo no justifica la complejidad extra dado el tiempo disponible.

**Print statements:**
- Descartado explícitamente. La learning session "From Vibes to Verifiable" penaliza este enfoque. Print statements no son consultables, no tienen estructura, y no permiten filtrado por trace_id.

**Prometheus + Grafana:**
- Descartado: overhead de configuración demasiado alto para el tiempo disponible. Adecuado para la fase de producción (documentado en SCALING.md).
