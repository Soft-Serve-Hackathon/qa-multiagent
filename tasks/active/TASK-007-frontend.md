# Task: TASK-007 — Frontend (Formulario de reporte de incidentes)

## Goal
Implementar el formulario web HTML para reportar incidentes. Debe ser simple, funcional y demostrable en el video demo.

## Source
- spec: `docs/specs/mvp/spec.md` (FR1-FR3, AC1)
- architecture: `docs/architecture/api-contracts.md` (POST /api/incidents)
- agent: `.claude/agents/frontend-engineer.md` (campos, estados UI, multimodal UX)

## Scope
- `src/frontend/index.html`: formulario principal
- `src/frontend/styles.css`: estilos básicos (sin frameworks CSS pesados)
- `src/frontend/app.js`: lógica de submit, validación cliente, estados UI
- FastAPI sirve los archivos estáticos: `app.mount("/", StaticFiles(directory="src/frontend"))`

## Campos del formulario
| Campo | Tipo | Validación | Requerido |
|---|---|---|---|
| title | text input | max 200 chars | Sí |
| description | textarea | max 2000 chars + contador | Sí |
| reporter_email | email input | formato email | Sí |
| attachment | file input | PNG/JPG/TXT/LOG, max 10MB | No |

## Estados UI requeridos (todos obligatorios)
| Estado | Qué mostrar |
|---|---|
| idle | Formulario vacío listo |
| loading | "Analyzing your incident report..." + spinner, botón deshabilitado |
| success | "✓ Ticket created. Reference: {trace_id}. You will be notified by email." |
| error-injection | "Your report contains content that cannot be processed. Please rephrase and try again." |
| error-validation | Mensaje específico del error (email inválido, archivo muy grande, etc.) |
| error-server | "Something went wrong. Please try again in a few minutes." |

## Multimodal UX
- Si se adjunta imagen: mostrar preview thumbnail + nombre del archivo
- Si se adjunta log: mostrar icono de documento + nombre del archivo
- Texto de ayuda: "Supported: PNG, JPG, TXT, LOG — max 10MB"
- Validar tamaño en cliente antes de enviar
- Actualizar contador de caracteres en tiempo real para description
- Bloquear submit si description está vacía o contiene solo espacios

## Flujo técnico esperado

### Request (FormData)
```
POST /api/incidents HTTP/1.1
Content-Type: multipart/form-data

Fields:
- title (string, max 200)
- description (string, max 2000)
- reporter_email (string, valid email)
- attachment (file, optional, <10MB)
```

### Response (Success)
```json
{
  "trace_id": "uuid-v4",
  "status": "processing",
  "message": "Incident received. You will be notified when triage is complete.",
  "estimated_time_seconds": 30
}
```

### Response (Validation Error)
```json
{
  "error": "validation_error",
  "field": "reporter_email",
  "message": "Invalid email format"
}
```

### Response (Injection Detected)
```json
{
  "error": "injection_detected",
  "message": "Your report contains content that cannot be processed. Please rephrase and try again."
}
```

### Response (Server Error)
```json
{
  "error": "internal_error",
  "message": "Something went wrong. Please try again in a few minutes."
}
HTTP 500
```

## Out of Scope
- Dashboard de incidentes
- Página de estado en tiempo real (polling)
- Login / autenticación

## Files Likely Affected
- `src/frontend/index.html` (nuevo)
- `src/frontend/styles.css` (nuevo)
- `src/frontend/app.js` (nuevo)
- `src/main.py` (modificar — agregar mount de StaticFiles)

## Constraints
- HTML5 + Vanilla JS — sin React, Vue, ni frameworks SPA
- El formulario usa `fetch()` con `FormData` para el submit
- Código limpio y legible — los mentores pueden leer el HTML durante la evaluación
- CSS responsivo para desktop + tablet (mobile no es requerido pero es un plus)
- Validación cliente-side ANTES de enviar:
  - title: no vacío, max 200 chars
  - description: no vacío, max 2000 chars, no contiene <guardrail_patterns>
  - reporter_email: validar con regex /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  - attachment (si existe): MIME type en (image/png, image/jpeg, text/plain) + size <10MB
- Injection detection en cliente: detectar patrones de "ignore previous instructions", "system prompt", etc. → mostrar error-injection sin enviar
- No guardar credentials, tokens, ni API keys en el formulario

## Validación de Injection (Cliente)
Patrones a rechazar (case-insensitive):
```javascript
const INJECTION_PATTERNS = [
  /ignore\s+previous/i,
  /system\s+prompt/i,
  /jailbreak/i,
  /you\s+are\s+now/i,
  /as\s+an\s+ai/i,
  /forget\s+your\s+instructions/i
];
```
Si alguno coincide → estado error-injection, no enviar POST

## Validation Commands
```bash
# 1. Happy path: texto + imagen
- Abrir http://localhost:3000
- Llenar: title="Payment failed", description="..."
- Adjuntar screenshot PNG
- Click submit → loading → success con trace_id en pantalla

# 2. Validación cliente: email inválido
- Dejar reporter_email vacío o inválido
- Botón submit debe estar deshabilitado O error al hacer click

# 3. Validación cliente: archivo muy grande 
- Adjuntar archivo >10MB
- Mostrar error "File too large (max 10MB)" sin enviar

# 4. Injection detection
- Escribir "ignore previous instructions" en description
- Mostrar error-injection inmediatamente (sin POST a /api/incidents)

# 5. Multimodal preview
- Adjuntar imagen PNG/JPG → preview thumbnail visible
- Adjuntar archivo .log → icono de documento + nombre de archivo visible

# 6. Nombre de archivo en logs
- Si se adjunta "error_2024-04-08.log"
- Mostrar en preview: "📄 error_2024-04-08.log"

# 7. Contador de caracteres
- Escribir en description
- Ver contador actualizar en vivo: "X / 2000"
- Desabilitar submit cuando description > 2000 chars
```

## Done Criteria
- [ ] Formulario carga en http://localhost:3000 sin errores de consola
- [ ] HTML5 válido, sin warnings en DevTools
- [ ] Submit con imagen adjunta → estado loading (spinner visible) → estado success con trace_id en pantalla
- [ ] Preview de imagen visible ANTES de submit (thumbnail)
- [ ] Preview de archivo log visible (icono + nombre de archivo)
- [ ] Validación cliente: email inválido → submit deshabilitado O error al click
- [ ] Validación cliente: archivo >10MB → error "File too large" sin POST
- [ ] Contador de caracteres en description actualiza en tiempo real
- [ ] Estado error-injection activado cuando se detecta "ignore previous instructions" → NO se hace POST
- [ ] Todos los 6 estados UI funcionan en el navegador (idle, loading, success, error-injection, error-validation, error-server)
- [ ] Botón submit deshabilitado mientras está en estado loading
- [ ] Respuesta de éxito muestra `trace_id` proporcionado por la API
- [ ] Mensaje de error-injection no expone detalles técnicos (mensaje genérico, user-friendly)
- [ ] FormData contiene todos los campos esperados (title, description, reporter_email, attachment)
- [ ] MIME type validation: solo acepta PNG, JPG, TXT, LOG (rechaza otros tipos)
- [ ] Logs browser no contienen credenciales ni información sensible

## Implementación de estados UI
```javascript
// Estados que debe soportar:
const STATES = {
  idle: { buttonText: "Submit Report", buttonDisabled: false, showForm: true },
  loading: { buttonText: "Analyzing...", buttonDisabled: true, showSpinner: true },
  success: { showSuccess: true, showTrace: true, showButton: "Submit Another" },
  errorInjection: { showError: true, errorMsg: "Your report contains...", errorType: "injection" },
  errorValidation: { showError: true, errorMsg: "<specific field>", errorType: "validation" },
  errorServer: { showError: true, errorMsg: "Something went wrong...", errorType: "server" }
};
```

## Estructura de archivos esperada
```
src/frontend/
├── index.html          # Markup, form fields, estado containers
├── styles.css          # Responsive, estados visuales (loading spinner, error colors)
├── app.js              # State machine, validación, fetch(), event handlers
└── assets/
    └── spinner.svg     # Spinner para estado loading (16x16 o 24x24)
```

## Funcionalidades de Java Script distribuidas por módulo

### app.js — Componentes principales
```javascript
// 1. FormManager — manejo del formulario
class FormManager {
  validateInput() {}  // Validar campos antes de submit
  collectFormData() {} // Recolectar en FormData
  reset() {}          // Resetear para siguiente reporte
}

// 2. UIStateManager — máquina de estados
class UIStateManager {
  setState(newState) {} // idle, loading, success, error-*
  render() {}           // Actualizar DOM según estado
}

// 3. APIClient — comunicación backend
class APIClient {
  async submitIncident(formData) {} // POST /api/incidents, maneja respuesta + errores
}

// 4. InjectionDetector — guardrails cliente
class InjectionDetector {
  detect(text) {}    // Buscar patrones maliciosos
  getErrorMessage() {} // Mensaje amigable para usuario
}

// 5. FileUploadManager — manejo de archivos
class FileUploadManager {
  validateFile(file) {}      // Check MIME type, size
  generatePreview(file) {}   // Thumbnail para imagen, icono para log
  sanitizeFileName(name) {}  // Remover caracteres peligrosos en display
}
```

## Ejemplos de validación cliente

### Email
```javascript
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
if (!emailRegex.test(email)) {
  setState('errorValidation', { field: 'reporter_email', message: 'Invalid email' });
  return;
}
```

### Injection
```javascript
const injectionPatterns = [
  /ignore\s+previous/i,
  /system\s+prompt/i,
  /you\s+are\s+now/i
];
if (injectionPatterns.some(p => p.test(description))) {
  setState('errorInjection');
  return;
}
```

### File Size
```javascript
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
if (file.size > MAX_FILE_SIZE) {
  setState('errorValidation', { field: 'attachment', message: 'File too large (max 10MB)' });
  return;
}
```



## Risks
- **FastAPI StaticFiles conflicto con API routes:** Si las rutas no están bien ordenadas, GET / puede resolver a /api/incidents. Mitigación: registrar endpoints `/api/*` ANTES de montear StaticFiles en main.py. Ejemplo:
  ```python
  @app.post("/api/incidents")
  async def create_incident(...): ...
  
  app.mount("/", StaticFiles(directory="src/frontend", html=True))
  ```
- **CORS issues:** Frontend en localhost:3000 + API en mismo host no debe tener problemas, pero si separados, CORS headers necesarios.
- **FormData boundary encoding:** En algunos navegadores viejos, FormData puede tener problemas con archivos binarios. Mitigación: testear en Chrome 90+ (no es relevante para MVP).
- **Validación de MIME type side-by-side con backend:** El backend debe validar también (no confiar solo en client-side). Frontend es primera línea de defensa por UX.
- **Inyección de JavaScript en error messages:** Si Backend devuelve error con input del usuario (ej. `/api/incidents?title=<script>alert(1)</script>`), puede ejecutarse. Mitigación: sanitizar con `textContent` en lugar de `innerHTML`.

## Handoff
Next recommended role: QA Engineer (validar AC1 + estados UI) → Backend Engineer (para endpoint POST /api/incidents)

Notes: 
- El formulario es el **primer punto de contacto visual en el demo**. Debe verse limpio, sin errores de consola, y responder rápido.
- Los estados de error (especialmente error-injection) son críticos para demostrar guardrails. El evaluador buscará que se rechace content malicioso **antes** de llegar al LLM.
- El trace_id en pantalla de éxito es importante para conectar visualmente con los logs (verificar observability end-to-end en el video).
- Si el backend no está listo, usar `MOCK_MODE=true` en el formulario para simular respuestas y demostrar UI sin dependencias externas.

