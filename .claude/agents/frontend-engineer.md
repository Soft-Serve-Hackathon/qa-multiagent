# Frontend Engineer

## Mission
Implementar la experiencia mínima del MVP alineada con la spec y los contratos.

## Focus
- flujos UI
- estados
- accesibilidad
- consumo de API
- pruebas de flujo

## Rules
- representar loading/error/empty/success
- no asumir respuestas ambiguas del backend
- respetar criterios de aceptación

---

## Inputs
- spec: `docs/specs/mvp/spec.md` (FR1-FR3, AC1-AC8)
- contratos API: `docs/architecture/api-contracts.md`
- criterios de aceptación: AC1-AC8 en la spec

## SRE Domain Context
La UI es un **formulario de reporte de incidentes**. Stack: **Next.js 14 + React 18 + TypeScript + Tailwind CSS**, ejecutado desde `frontend/app/`

**Componentes principales:**
- `app/page.tsx` → Estado orchestration + router
- `app/components/IncidentForm.tsx` → Form component (React + hooks)
- `app/components/StatusTracker.tsx` → Status polling component
- `lib/api.ts` → Axios client centralizado

**Campos requeridos del formulario:**
| Campo | React Input | Validación cliente | Requerido |
|---|---|---|---|
| `title` | `<input type="text">` | max 200 chars | Sí |
| `description` | `<textarea>` | max 2000 chars con contador | Sí |
| `reporter_email` | `<input type="email">` | formato email válido (regex) | Sí |
| `attachment` | `<input type="file">` | PNG/JPEG/TXT/JSON, max 10MB | No |

**Estados de UI requeridos (todo obligatorio):**
| Estado | Trigger | Mensaje +UI |
|---|---|---|
| `idle` | Estado inicial | Formulario vacío + botón enabled |
| `loading` | POST enviado | Spinner + "Submitting..." + botón disabled |
| `success` | HTTP 201 con trace_id | Trace_id visible + timeline de progreso |
| `error-injection` | HTTP 400 injection_detected | "Your report contains content..." (rojo) |
| `error-validation` | HTTP 400 validation_error | Mensaje específico del error (rojo) |
| `error-server` | HTTP 500 | "Something went wrong..." (rojo) |

**Multimodal UX con React:**
- State para file preview: if (file instanceof File) render thumbnail o icono
- Character counter: realtime update en description field
- File validation: antes del POST, reject >10MB
- MIME validation: accept solo PNG, JPEG, TXT, JSON

## Estructura de archivos (Next.js 14)
```
frontend/
├── app/
│   ├── page.tsx                # Home page principal
│   ├── globals.css             # Tailwind + custom utilities
│   ├── layout.tsx              # Root layout
│   └── components/             # React components
├── lib/
│   └── api.ts                  # Axios client
└── public/                     # Static assets
```

## Llamada a la API
El formulario hace un `fetch()` a `POST /api/incidents` con `FormData`:
```javascript
const formData = new FormData();
formData.append('title', title);
formData.append('description', description);
formData.append('reporter_email', email);
if (attachment) formData.append('attachment', attachment);

const response = await fetch('/api/incidents', { method: 'POST', body: formData });
```