# ADR-005: Estrategia de guardrails — Protección contra prompt injection

## Status
Accepted

## Context
El sistema recibe texto libre de usuarios externos via formulario web. Este texto se envía como input a Claude claude-sonnet-4-6 para el análisis del incidente. Un atacante podría intentar manipular al agente inyectando instrucciones en el campo de descripción o en el archivo adjunto.

El assignment requiere explícitamente: "basic protection against prompt injection / malicious artifacts (safe tool use + input handling)". Esta es también una señal de Responsible AI (Security) que los evaluadores verificarán.

## Decision
Implementar una capa de validación en **IngestAgent**, ANTES de cualquier llamada al LLM.

### Capa 1: Detección de prompt injection
Función `validate_injection(text: str) -> bool` en `src/guardrails.py`:
- Regex pattern matching contra patrones conocidos de inyección
- Patrones detectados: `ignore previous`, `ignore all`, `disregard`, `forget your`, `new instructions`, `you are now`, `system prompt`, `jailbreak`, `DAN`, `act as`, `pretend you are`, `reveal your`, `bypass`
- Si cualquier patrón coincide (case-insensitive): retornar `False`, log del intento, HTTP 400

### Capa 2: Sanitización de input
- `description` truncado a 2000 caracteres antes de persistir
- `title` truncado a 200 caracteres
- Caracteres de control (`\x00`-`\x08`, `\x0b`, `\x0c`, `\x0e`-`\x1f`) removidos del texto

### Capa 3: Validación de archivos adjuntos
- Validar MIME type real usando `python-magic` (no confiar solo en la extensión)
- Tipos permitidos: `image/png`, `image/jpeg`, `text/plain`
- Límite de tamaño: 10MB
- Para archivos de log: leer solo los primeros 50KB para evitar context overflow en el LLM

### Separación de datos sensibles
- `reporter_email` NO se incluye en el prompt enviado al LLM
- Solo aparece en el payload del ticket de Trello y en el email de notificación
- Esto previene que el LLM exponga o manipule el email del reporter

## Consequences

**Positivos:**
- Protege contra ataques básicos de prompt injection (demostrable con AC7)
- `reporter_email` aislado del contexto del LLM
- Archivos maliciosos rechazados antes de procesarlos
- El intento de inyección queda registrado en los logs de observability

**Negativos / Trade-offs:**
- Protección de primer nivel, no defensa en profundidad. Un atacante sofisticado puede obfuscar los patrones con encoding, espacios o variaciones. Se documenta como limitación conocida en `AGENTS_USE.md`.
- El truncado de texto puede eliminar contexto relevante en incidentes con descripciones largas. Se mitiga indicando al reporter en la UI que la descripción tiene un límite de 2000 caracteres.

## Alternatives Considered

**LLM-as-judge para detectar inyecciones:**
- Descartado para el MVP: requiere una segunda llamada al LLM antes de la llamada principal, duplicando la latencia y el costo. Documentado como mejora post-MVP.

**Librería de guardrails (NeMo Guardrails, Guardrails AI):**
- Descartado: overhead de configuración demasiado alto para el tiempo disponible. La implementación con regex cubre los casos básicos requeridos por el assignment.

**Sin guardrails:**
- Descartado explícitamente. El assignment requiere guardrails y la evaluación de seguridad de los mentores los verificará.
