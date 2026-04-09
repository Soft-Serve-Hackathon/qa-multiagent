# Mock Medusa.js Repository

Este directorio contiene una **estructura mock del repositorio Medusa.js** usado para desarrollo en `feature/mocks`.

## Propósito

- Proporcionar un repositorio "falso" pero realista de Medusa.js
- Permitir que Claude lea archivos y dé análisis técnicos sin dependencia externa
- Acelerar desarrollo local sin clonar todo el repo real (~2GB)

## Estructura

```
mock-medusa-repo/
└── packages/
    └── medusa/
        └── src/
            ├── services/          # Core e-commerce logic
            │   ├── cart-service.ts
            │   ├── order-service.ts
            │   ├── payment-service.ts
            │   └── inventory-service.ts
            ├── models/            # Type definitions
            │   └── index.ts
            └── controllers/       # Route handlers (stub)
```

## Cómo se Usa

### En TriageAgent (LLM Tool Call)
```python
# El LLM hace:
read_ecommerce_file("packages/medusa/src/services/cart-service.ts")

#
Se resuelve a:
/mock-medusa-repo/packages/medusa/src/services/cart-service.ts
```

### Ejemplo Real
Si un incidente dice "Cart rechaza premium variants", Claude puede:
1. Identificar módulo: `cart`
2. Leer `cart-service.ts`
3. Ver la lógica de validación
4. Correlacionar con el error reportado
5. Dar recomendaciones precisas

## Para Agregar Archivos

Copia archivos realistas de Medusa.js o crea stubs que representen el código típico:
- Incluir comentarios de docstring
- Usar errores y validaciones realistas
- Mantener estructura TypeScript/Medusa.js patterns

## En Producción

Para usar el repo real:
```bash
# Clonar Medusa.js completo
git clone https://github.com/medusajs/medusa.git medusa-repo

# Cambiar variable en .env
MEDUSA_REPO_PATH=./medusa-repo
```

Luego Claude tendrá acceso a 30K+ archivos del repo real.

## Notas

- Archivos limitados a 3000 caracteres en lectura (protección de context window)
- Protección contra path traversal (`..` bloqueado)
- Modo **READ-ONLY** — LLM nunca escribe en repo
