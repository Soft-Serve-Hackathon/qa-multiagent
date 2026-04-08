# Frontend Instructions — Next.js 14 + TypeScript + Tailwind CSS

## Contexto
Frontend del SRE Incident Intake & Triage Agent. App Router de Next.js 14.
Dos flujos principales:
1. **Formulario de ingesta** (`IncidentForm.tsx`) — multimodal: título, descripción, email, adjunto (imagen o log)
2. **Status tracker** (`StatusTracker.tsx`) — polling cada 5s a `GET /api/incidents/{trace_id}` hasta resolución

Comunicación con backend: Axios via `lib/api.ts` → proxy en `next.config.js` → `http://backend:8000`.

## Reglas

- Implementa flujos alineados con `docs/specs/mvp/spec.md` (AC1-AC8).
- Muestra estados explícitos en todo componente: `loading`, `error`, `success`, `empty`.
- El `trace_id` devuelto por `POST /api/incidents` es el identificador que el usuario ve para tracking.
- No acoples componentes a shapes de respuesta del backend que no estén en `docs/architecture/api-contracts.md`.
- Validación de formulario en cliente: título requerido, email válido, archivo ≤ 10MB (PNG/JPG/log).
- Mantén Tailwind CSS para estilos — no introduzcas otras librerías de UI sin documentarlo.
- Tests o validación manual documentada para los dos flujos críticos (submit + status polling).
