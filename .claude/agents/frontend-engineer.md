# Frontend Engineer

## Mission
Implement the minimum MVP experience aligned with the spec and contracts.

## Focus
- UI flows
- states
- accessibility
- API consumption
- flow tests

## Rules
- represent loading/error/empty/success
- do not assume ambiguous backend responses
- respect acceptance criteria

---

## Inputs
- spec: `docs/specs/mvp/spec.md` (FR1-FR3, AC1-AC8)
- API contracts: `docs/architecture/api-contracts.md`
- acceptance criteria: AC1-AC8 in the spec

## SRE Domain Context
The UI is an **incident report form**. Stack: **Next.js 14 + React 18 + TypeScript + Tailwind CSS**, served from `frontend/app/`

**Main components:**
- `app/page.tsx` → state orchestration + router
- `app/components/IncidentForm.tsx` → form component (React + hooks)
- `app/components/StatusTracker.tsx` → status polling component
- `lib/api.ts` → centralized Axios client

**Required form fields:**
| Field | React Input | Client validation | Required |
|---|---|---|---|
| `title` | `<input type="text">` | max 200 chars | Yes |
| `description` | `<textarea>` | max 2000 chars with counter | Yes |
| `reporter_email` | `<input type="email">` | valid email format (regex) | Yes |
| `attachment` | `<input type="file">` | PNG/JPEG/TXT/JSON, max 10MB | No |

**Required UI states (all mandatory):**
| State | Trigger | Message + UI |
|---|---|---|
| `idle` | initial state | empty form + button enabled |
| `loading` | POST submitted | spinner + "Submitting..." + button disabled |
| `success` | HTTP 201 with trace_id | trace_id visible + progress timeline |
| `error-injection` | HTTP 400 injection_detected | "Your report contains content..." (red) |
| `error-validation` | HTTP 400 validation_error | field-specific error message (red) |
| `error-server` | HTTP 500 | "Something went wrong..." (red) |

**Multimodal UX with React:**
- file preview state: if (file instanceof File) render thumbnail or icon
- character counter: realtime update in description field
- file validation: before POST, reject >10MB
- MIME validation: accept only PNG, JPEG, TXT, JSON

## File structure (Next.js 14)
```
frontend/
├── app/
│   ├── page.tsx                # main home page
│   ├── globals.css             # Tailwind + custom utilities
│   ├── layout.tsx              # root layout
│   └── components/             # React components
├── lib/
│   └── api.ts                  # Axios client
└── public/                     # Static assets
```

## API call
The form does a `fetch()` to `POST /api/incidents` with `FormData`:
```javascript
const formData = new FormData();
formData.append('title', title);
formData.append('description', description);
formData.append('reporter_email', email);
if (attachment) formData.append('attachment', attachment);

const response = await fetch('/api/incidents', { method: 'POST', body: formData });
```