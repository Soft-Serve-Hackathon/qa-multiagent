# Task

## Title
T03 — Implementar cliente de GitHub API

## Goal
Crear un módulo reutilizable que encapsule las operaciones necesarias con GitHub API: leer el diff de un PR, obtener metadatos del PR y publicar comentarios. Este cliente es usado por múltiples agentes del sistema.

## Source
- spec: `docs/specs/mvp/spec.md` — FR2, FR3, FR4, AC2, AC3
- architecture: `docs/architecture/system-overview.md` (T01)
- acceptance criteria: AC2 — comentario en formato markdown estructurado; AC3 — verificar aprobación manual

## Scope
- Función `get_pr_diff(pr_number)` → retorna el diff como texto
- Función `get_pr_metadata(pr_number)` → retorna título, autor, rama base, archivos cambiados
- Función `post_pr_comment(pr_number, body)` → publica comentario en el PR
- Función `is_pr_approved(pr_number)` → retorna bool según reviews aprobadas
- Manejo de paginación para PRs con muchos archivos
- Manejo de PR gigante (EC5): truncar diff con advertencia si supera límite de tokens configurable

## Out of Scope
- Autenticación OAuth (usar solo token estático via secret)
- Webhooks (GitHub Actions maneja el trigger)

## Files Likely Affected
- `src/clients/github_client.py` (nuevo)
- `tests/clients/test_github_client.py` (nuevo)

## Constraints
- Usar `GITHUB_TOKEN` de GitHub Actions (no PAT personal) cuando sea posible
- El cliente debe ser mockeable para tests sin llamadas reales a la API
- Manejar rate limiting de GitHub API (429) con retry básico

## Validation Commands
- `pytest tests/clients/test_github_client.py`
- Test manual: llamar `get_pr_diff` con un PR real y verificar que retorna diff válido
- Test de EC5: pasar un diff de +3000 líneas y verificar que se trunca con advertencia

## Done Criteria
- Las 4 funciones implementadas y con tests unitarios (mocks de GitHub API)
- EC5 manejado: diff truncado con advertencia si supera límite configurable
- El cliente lanza excepciones tipadas (no genéricas) para errores de API

## Risks
- El `GITHUB_TOKEN` nativo de Actions tiene permisos limitados — verificar que puede comentar en PRs del repo

## Handoff
Next recommended role: Backend Engineer
Notes: Prerequisito de T04. Puede desarrollarse en paralelo con T02.
