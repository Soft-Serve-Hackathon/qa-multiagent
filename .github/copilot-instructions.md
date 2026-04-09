# Copilot Repository Instructions

This repository follows a methodology based on specifications and specialized agents.

## Before suggesting code

1. review `README.md`
2. review `AGENTS.md`
3. review the relevant spec in `docs/specs/`
4. review contracts and decisions in `docs/architecture/`
5. review the active task if one exists in `tasks/active/`

## Preferred workflow

1. review idea and open questions
2. consolidate the spec
3. review architecture
4. break work into tasks
5. implement one task at a time
6. validate
7. document handoff

## Rules

- make small changes consistent with the spec
- do not invent product scope
- avoid logic not validated by acceptance criteria
- when a change affects design, suggest documenting it
- include tests or a validation strategy when applicable
- respect separation of responsibilities between frontend, backend, QA, and security

## Priorities

1. clarity
2. correctness
3. maintainability
4. verifiability
5. speed

## Expected help format

Preferably respond with this structure:

1. Understanding
2. Plan
3. Changes
4. Validation
5. Risks
6. Handoff

## Done Checklist

Before closing a task, confirm:

- context read
- impacted files identified
- acceptance criteria covered
- tests or validation executed
- risks documented
- handoff prepared

## Guardrails

- avoid unsolicited large refactors
- do not delete documentation without a clear replacement
- do not assume unwritten requirements
- if you find gaps, write them in `docs/idea/open-questions.md` or in the handoff