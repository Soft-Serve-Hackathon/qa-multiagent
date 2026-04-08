# Task

## Title
T05 — Implementar gate de aprobación manual

## Goal
Asegurar que el agente QA (Fase 2) solo se ejecuta después de que un humano haya aprobado el PR en GitHub. Este es el punto de control manual del flujo.

## Source
- spec: `docs/specs/mvp/spec.md` — FR4, AC3
- architecture: `docs/architecture/system-overview.md` (T01)
- acceptance criteria: AC3 — el sistema no continúa al paso 5 sin aprobación humana registrada

## Scope
- Crear un segundo workflow en GitHub Actions que se dispara en `pull_request_review: [submitted]` con estado `approved`
- Verificar con `github_client.is_pr_approved()` (T03) que la aprobación existe
- Si está aprobado: disparar el pipeline de QA (T06)
- Si no está aprobado: no hacer nada (o loggear que se esperará aprobación)

## Out of Scope
- Implementar el agente QA en sí (eso es T06)
- Configurar timeout automático de aprobación

## Files Likely Affected
- `.github/workflows/qa-trigger.yml` (nuevo)
- `src/entrypoints/qa_trigger.py` (nuevo)

## Constraints
- El gate debe ser robusto: nunca disparar QA si la revisión es `changes_requested` o `commented`
- Documentar claramente en README que la aprobación manual es intencional y requerida

## Validation Commands
- Test manual: aprobar un PR y verificar que el workflow `qa-trigger` se dispara
- Test manual: comentar en un PR (sin aprobar) y verificar que el workflow NO se dispara
- `pytest tests/entrypoints/test_qa_trigger.py`

## Done Criteria
- El workflow QA solo se ejecuta cuando el PR tiene al menos una review con estado `approved`
- AC3 cumplido: revisiones de tipo `commented` o `changes_requested` no disparan QA
- Existe test que valida la lógica de verificación de aprobación

## Risks
- Si el repo tiene branch protection rules, el `GITHUB_TOKEN` puede no tener permisos de lectura de reviews — verificar permisos

## Handoff
Next recommended role: Backend Engineer
Notes: Depende de T03. Prerequisito de T06. Completa el Flujo A paso 4.
