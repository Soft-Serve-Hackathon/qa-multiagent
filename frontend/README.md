# Frontend — Next.js

Frontend application for the SRE Incident Triage Agent.

## 📦 Tech Stack

- **Framework:** Next.js 14
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **HTTP Client:** Axios
- **Node Version:** 20+

## 🚀 Quick Start

### Development

```bash
npm install
npm run dev
```

Access at `http://localhost:3000`

### Production Build

```bash
npm run build
npm start
```

## 📁 Project Structure

```
app/
├── page.tsx              # Home page
├── layout.tsx            # Root layout
├── globals.css           # Global Tailwind styles
└── components/
    ├── IncidentForm.tsx  # Incident report form
    ├── StatusTracker.tsx # Real-time status polling
    └── ui/
        └── FormInput.tsx # Reusable input component

lib/
├── api.ts                # Centralized API client

public/
├── favicon.ico           # App icon
└── ...                   # Other static assets

Configuration files:
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── postcss.config.js
├── next.config.js
├── .eslintrc.json
└── .gitignore
```

## 🔌 API Integration

The frontend communicates with the backend via REST API:

### Environment Variables

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

### API Endpoints Used

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/incidents` | Submit incident report |
| GET | `/api/incidents/{trace_id}` | Get incident status |
| GET | `/api/health` | Backend health check |

## 🎨 Components

### IncidentForm
- Form validation (client-side)
- File upload (max 10MB, PNG/JPEG/TXT/JSON)
- Error handling & display

### StatusTracker
- Real-time polling (5-second intervals)
- Timeline visualization
- Trace ID display

## 🧪 Type Safety

Full TypeScript support with:
- Component prop types
- API response types
- Form state types

## 📝 Development Guidelines

- Use TypeScript for all components
- Follow Tailwind utility-first approach
- Keep components small and focused
- Use React hooks for state management
- Add proper error boundaries

## 🐳 Docker

Build and run with Docker:

```bash
docker build -t qa-multiagent-frontend:latest ./frontend
docker run -p 3000:3000 qa-multiagent-frontend:latest
```

## 🔗 Related

- Backend: [../backend/](../backend/)
- Architecture: [../MONOREPO.md](../MONOREPO.md)
- Structure: [../STRUCTURE.md](../STRUCTURE.md)
