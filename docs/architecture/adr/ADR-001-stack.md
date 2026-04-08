# ADR-001: Stack tecnológico del sistema

## Status
Accepted

## Context
El sistema necesita un stack que permita:
- Ejecutarse dentro de GitHub Actions (ambiente Linux, sin servidor permanente)
- Llamar a múltiples APIs externas (Anthropic, OpenAI, GitHub, Jira)
- Ser mantenido fácilmente por un equipo pequeño
- Iterar rápido en el MVP sin overhead de compilación o configuración compleja

Las opciones evaluadas fueron Python y TypeScript/Node.js, los dos lenguajes con mejor soporte de SDKs para las APIs relevantes (Anthropic, OpenAI).

## Decision
**Python 3.11+** como lenguaje principal del proyecto.

- Runtime de GitHub Actions: `actions/setup-python`
- SDKs oficiales: `anthropic`, `openai`, `PyGithub` o `httpx` para GitHub API, `jira` (atlassian-python-api)
- Testing: `pytest` + `pytest-mock`
- Gestión de dependencias: `pip` + `requirements.txt` (sin Poetry en el MVP para reducir complejidad)
- Variables de entorno: `python-dotenv` para desarrollo local

## Consequences
**Positivo:**
- Python tiene SDKs oficiales de primera clase para Anthropic y OpenAI
- Ecosistema maduro para scripting, procesamiento de texto y APIs
- Equipo con experiencia previa en el lenguaje
- Fácil de ejecutar en GitHub Actions sin build step

**Negativo:**
- Sin tipado estático estricto por defecto — mitigar con type hints y `mypy` si se incorpora
- Gestión de dependencias más frágil que Poetry o uv — aceptable para el MVP

**Trade-offs:**
- Se prefiere simplicidad sobre robustez de toolchain en esta fase

## Alternatives Considered
- **TypeScript/Node.js**: buen soporte de SDKs, pero más overhead de configuración (tsconfig, compilación) para un proyecto de scripting/agentes
- **Go**: muy eficiente pero SDKs de IA menos maduros y curva de aprendizaje mayor para agentes
