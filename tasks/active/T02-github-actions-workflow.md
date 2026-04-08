# Task

## Title
T02 — Configurar GitHub Actions workflow para eventos de PR

## Goal
Crear el workflow de GitHub Actions que detecta la apertura (y re-apertura) de un PR y dispara el agente de revisión. Es el punto de entrada del sistema.

## Source
- spec: `docs/specs/mvp/spec.md` — FR1, AC1
- architecture: `docs/architecture/system-overview.md` (T01)
- acceptance criteria: AC1 — comentario publicado en menos de 5 minutos desde apertura del PR

## Scope
- Crear `.github/workflows/pr-review.yml` que se dispara en `pull_request: [opened, reopened, synchronize]`
- El workflow debe obtener el diff del PR y pasarlo al agente de revisión
- El workflow debe manejar secrets: `ANTHROPIC_API_KEY`, `GITHUB_TOKEN`
- Incluir manejo de errores básico: si el agente falla, dejar log claro y no bloquear el PR

## Out of Scope
- Implementar el agente de revisión (eso es T03/T04)
- Configurar el workflow de QA post-aprobación (eso es T07)

## Files Likely Affected
- `.github/workflows/pr-review.yml` (nuevo)
- `src/entrypoints/pr_review.py` o equivalente (nuevo, llamado por el workflow)

## Constraints
- El workflow no debe fallar silenciosamente — cualquier error debe ser visible en GitHub Actions logs
- Tiempo de ejecución máximo: 10 minutos (evitar costos excesivos de Actions)
- Usar `GITHUB_TOKEN` nativo de Actions para comentar en el PR

## Validation Commands
- Abrir un PR de prueba en el repo y verificar que el workflow se dispara
- Verificar en la pestaña Actions que el job aparece y completa
- Verificar que el workflow maneja el caso de PR sin diff (EC1)

## Done Criteria
- El workflow se dispara automáticamente al abrir un PR
- Los secrets necesarios están documentados en README o en un `.env.example`
- El workflow falla con mensaje claro si falta algún secret
- Edge case EC1 (PR vacío) está manejado: el workflow termina con mensaje explicativo

## Risks
- Los secrets de API key pueden no estar configurados en el repo — documentar el setup claramente

## Handoff
Next recommended role: Backend Engineer
Notes: Depende de T01 para conocer el entrypoint a llamar. Prerequisito de T03 y T04.
