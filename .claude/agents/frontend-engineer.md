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
La UI es un **formulario de reporte de incidentes**. No es una SPA compleja. El stack es HTML5 + Vanilla JS, servido como archivos estáticos por FastAPI desde `src/frontend/`.

**Campos requeridos del formulario:**
| Campo | Tipo HTML | Validación cliente | Requerido |
|---|---|---|---|
| `title` | `<input type="text">` | max 200 chars | Sí |
| `description` | `<textarea>` | max 2000 chars con contador | Sí |
| `reporter_email` | `<input type="email">` | formato email válido | Sí |
| `attachment` | `<input type="file">` | accept="image/png,image/jpeg,text/plain", max 10MB | No |

**Estados de UI requeridos (todos obligatorios):**
| Estado | Trigger | Mensaje al usuario |
|---|---|---|
| `idle` | Estado inicial | Formulario vacío listo para llenar |
| `loading` | POST enviado, esperando respuesta | "Analyzing your incident report..." + spinner |
| `success` | HTTP 201 recibido | "Ticket created successfully. Reference: [trace_id]. You will be notified by email." |
| `error-injection` | HTTP 400 con `prompt_injection_detected` | "Your report contains content that cannot be processed. Please rephrase and try again." |
| `error-validation` | HTTP 400 con otros errores | Mensaje específico del error (email inválido, archivo muy grande, etc.) |
| `error-server` | HTTP 500 | "Something went wrong. Please try again in a few minutes." |

**Multimodal UX:**
- Si el adjunto es una imagen (PNG/JPG): mostrar preview de la imagen con nombre del archivo
- Si el adjunto es un log (.txt/.log): mostrar icono de documento + nombre del archivo
- Mostrar el tipo de archivo aceptado y el límite de 10MB en texto de ayuda bajo el campo
- Validar el tamaño del archivo en cliente antes de enviar (evitar uploads innecesarios)

## Estructura de archivos
```
src/frontend/
├── index.html     # formulario principal
├── styles.css     # estilos básicos (no usar frameworks CSS pesados)
└── app.js         # lógica de submit, validación cliente, manejo de estados
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