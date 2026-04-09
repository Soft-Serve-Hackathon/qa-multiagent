# Open Questions

## Decisiones ya tomadas (documentadas aquí para trazabilidad)

| Pregunta | Decisión | Razón |
|---|---|---|
| ¿Qué app e-commerce usar como base de conocimiento del agente? | **Medusa.js** (medusajs/medusa) | TypeScript, alta complejidad real, excelente documentación, activo. El agente analiza payments, orders, inventory. |
| ¿Qué LLM multimodal usar? | **Claude claude-sonnet-4-6** (Anthropic SDK) | Multimodal nativo, disponible en el workspace, maneja imagen + texto en el mismo request. |
| ¿Qué stack de backend? | **Python + FastAPI** | Mejor integración con Anthropic SDK, librerías de análisis de código y observability. |
| ¿Qué sistema de ticketing? | **Trello** (API real) | El equipo tiene cuenta. El hackathon acepta "Jira / Linear / Other" — Trello es válido. Las Cards representan incidentes. |
| ¿Qué comunicador? | **Slack** (Incoming Webhook real) | El equipo tiene workspace. Webhooks no requieren OAuth complejo. |
| ¿Qué modalidades soportar? | **Texto + imagen (PNG/JPG) + log (.txt/.log)** | Cubre los casos más comunes de reporte de incidentes. Video es opcional para el MVP. |
| ¿Equipo de cuántas personas? | **2-3 personas** | Las tareas se dividen en paralelo por capa (frontend, backend, integraciones). |
| ¿Persistencia? | **SQLite** (vía SQLAlchemy) | Simplifica el setup Docker. El schema es compatible con PostgreSQL para escala futura. |
| ¿Cómo accede el agente al codebase de Medusa.js? | Clonado durante Docker build, montado como volumen read-only. Tool `read_ecommerce_file(path)` en el TriageAgent. | Sin complejidad de embeddings para el MVP. |

## Preguntas aún abiertas

### Scope del MVP
- **¿Runbook suggestions en el MVP?** El hackathon los menciona como opcional que suma puntos. Evaluar si hay tiempo después de tener el flujo e2e funcionando.
- **¿Deduplicación de incidentes?** También opcional. Agregar si queda tiempo — requiere comparación semántica de reportes similares.
- **¿Severity scoring automático con lógica adicional?** El TriageAgent ya produce P1-P4, pero ¿se necesita una capa de reglas de negocio adicional? Por ahora, el LLM determina la severidad.

### Implementación
- **¿Webhook de Trello o polling para detectar cards resueltas?** Trello tiene webhooks. Si la configuración es compleja en el tiempo disponible, usar polling cada 60 segundos como fallback.
- **¿Cómo accede el ResolutionWatcher a las credenciales de Trello en Docker?** Via variables de entorno del contenedor — ya definido en `.env.example`.
- **¿El formulario web es HTML puro o necesita un mini framework?** HTML5 + vanilla JS es suficiente para el demo. No sobrearquitectar el frontend.
- **¿Email real o mock?** SendGrid si hay credenciales disponibles, mock con log detallado si no. `MOCK_EMAIL=true` en `.env`.

### Demo y submission
- **¿Quién graba el video demo?** Debe grabarse cuando el flujo e2e funcione. Máximo 3 minutos, en inglés, subir a YouTube con tag `#AgentXHackathon`.
- **¿El repo debe estar público antes o solo al momento de submission?** Hacerlo público justo antes de submitear para evitar que otros vean el trabajo antes.
- **¿Qué cuenta de Trello usar para el board del demo?** Definir un board específico para el hackathon con columnas: To Do / In Progress / Done.

## Restricciones técnicas conocidas
- Docker Compose es obligatorio — toda la app debe correr con `docker compose up --build`
- No se puede hacer fork de proyectos existentes — el código debe ser original
- El repo debe tener licencia MIT
- El video debe ser en inglés
- Deadline absoluto: 9 de abril 10PM COT — sin extensiones
