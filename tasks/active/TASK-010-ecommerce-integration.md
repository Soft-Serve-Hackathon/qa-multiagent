# Task: TASK-010 — E-commerce Integration (Medusa.js)

## Goal
Integrar Medusa.js como fuente de verdad del codebase e-commerce. El TriageAgent debe poder acceder a archivos reales de Medusa.js para generar análisis técnico coherente con la arquitectura real.

## Source
- spec: `docs/specs/mvp/spec.md` (FR5, AC2)
- architecture: `docs/architecture/adr/ADR-001-ecommerce-repo.md`
- acceptance criteria: AC2 — `Log con stack trace de PaymentService → agente cita archivo correcto de Medusa.js`

## Scope
- Clonar repositorio medusajs/medusa en `ecommerce/medusa/` durante Docker build (via Dockerfile build stage)
- Crear `src/ecommerce_tools.py` con function `read_ecommerce_file(relative_path: str) -> str`
- Crear índice de servicios principales: `src/ecommerce_index.py` que lista `packages/medusa/src/services/**/*.ts` con metadata (qué hace cada servicio)
- Registrar `ecommerce_tools.read_ecommerce_file` como tool en `src/agents/triage_agent.py`
- Crear `GET /api/ecommerce/services` endpoint para que el frontend pueda mostrar hints de archivos
- Documentar estructura de Medusa.js en comentarios (dónde están los servicios, plugins, workflows)
- Cache simple en memoria de índice de servicios (limpieza cada 24h o por request explícito)

## Out of Scope
- Ejecutar comandos en el repo de Medusa.js (solo lectura)
- Clonar node_modules o instalar dependencias
- Análisis estático avanzado (AST parsing)
- Integración con Medusa.js CLI

## Files Likely Affected
- `Dockerfile` (agregar `git clone medusajs/medusa` en build stage)
- `docker-compose.yml` (volumen read-only para `ecommerce/medusa/`)
- `src/ecommerce_tools.py` (nuevo)
- `src/ecommerce_index.py` (nuevo)
- `src/agents/triage_agent.py` (registrar tool)
- `src/main.py` (inicializar índice en startup)
- `.env.example` (ECOMMERCE_REPO_PATH=/ecommerce/medusa)
- `.dockerignore` (excluir node_modules si es clonado)

## Constraints
- Medusa.js debe ser clonado de rama `main` del repositorio oficial
- Ruta base en container: `/ecommerce/medusa` (montado como bind volume read-only)
- Índice pre-calculado al startup: lista de servicios con path + 1-liner descripción
- rate limit: máximo 100 reads por minuto desde TriageAgent (acumulado)
- Cache de índice: en memoria (dict), TTL 24 horas
- Timeout de read_ecommerce_file: 2 segundos máximo, retornar primeras 8KB si archivo > 8KB
- Validar path para evitar `../../../etc/passwd` (path traversal)

## Validation Commands
```bash
# 1. Verificar que Medusa.js fue clonado en Docker build
docker compose up --build
docker compose exec backend ls -la /ecommerce/medusa/packages/medusa/src/services/

# 2. Verificar función read_ecommerce_file
docker compose exec backend python -c "
from src.ecommerce_tools import read_ecommerce_file
content = read_ecommerce_file('packages/medusa/src/services/cart.ts')
print(f'Read {len(content)} bytes from cart.ts')
"

# 3. GET /api/ecommerce/services debería retornar lista de servicios
curl http://localhost:3000/api/ecommerce/services | jq '.services | length'
# Expected: >20

# 4. Prueba con AC2: simular un triage con stack trace de PaymentService
curl -X POST http://localhost:3000/api/incidents \
  -F "title=Payment failed" \
  -F "description=Stack trace: PaymentService.authorize() failed" \
  -F "reporter_email=test@example.com"

# Esperar respuesta y verificar que el trace JSON incluye:
# "suggested_files": ["packages/medusa/src/services/payment.ts", ...]
```

## Done Criteria
- [ ] Clone de medusajs/medusa existe en `ecommerce/medusa/` (dentro de container)
- [ ] `src/ecommerce_tools.py` implementa `read_ecommerce_file(path: str) -> str`
- [ ] Validación de path evita traversal attacks (verificar `../` rechazados)
- [ ] `src/ecommerce_index.py` indexa servicios principales al startup
- [ ] `GET /api/ecommerce/services` retorna JSON con lista de servicios (name, path, description)
- [ ] TriageAgent tiene tool `ecommerce_tools.read_ecommerce_file` registrada
- [ ] AC2 validado: un incidente con stack trace de un servicio real cita el archivo correcto
- [ ] Logs muestran tiempo de lectura y bytes leídos
- [ ] Cache de índice implementado con TTL (validar que rehashes después de 24h)
- [ ] Rate limiting: máximo 100 reads por minuto, retorna 429 Too Many Requests si se excede
- [ ] Logs estructurados con stage="ecommerce_read", service, num_bytes, duration_ms

## Risks
- **Clone time:** Clonar Medusa.js puede tomar 2-5 minutos. Mitigación: usar `git clone --depth 1 --branch main` para shallow clone más rápido.
- **Disk space:** Medusa.js + node_modules puede ser >2GB. Mitigación: clonar sin node_modules (`git clone --filter=blob:none` si Git v2.19+), o usar `rm -rf .git packages/*/node_modules` después del clone.
- **Index staleness:** Si el repo es clonable dinámicamente, el índice puede quedar stale. Mitigación: documentar que post-MVP puede añadirse refresh vía webhook.

## Handoff
Next recommended role: Backend Engineer (para TriageAgent) → QA Engineer (validar AC2)
Notes: Este task puede ejecutarse en paralelo con TASK-002 a TASK-007, pero TASK-003 (TriageAgent) depende de que `read_ecommerce_file` esté disponible. Considerar hacer esta tarea primero (TASK-010) para desbloquear TASK-003.
