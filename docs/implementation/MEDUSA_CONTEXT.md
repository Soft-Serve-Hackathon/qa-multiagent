# Medusa.js Context en el Proyecto SRE

## ¿Qué es Medusa.js y por qué está en el proyecto?

**Medusa.js** es un framework de e-commerce headless de código abierto (TypeScript) que proporciona backends scalables para plataformas de comercio electrónico.

**Link oficial:** https://medusajs.com

### Rol en el Sistema SRE

El proyecto está diseñado para automatizar la triage de incidentes en equipos de SRE que operan plataformas de e-commerce. En particular:

1. **Contexto técnico especializado:** El TriageAgent está entrenado para entender módulos específicos de Medusa.js:
   - `cart` - Carrito de compras
   - `order` - Pedidos
   - `payment` - Procesamiento de pagos
   - `inventory` - Gestión de inventario
   - `product` - Catálogo de productos
   - `customer` - Gestión de clientes
   - `shipping` - Cálculo y gestión de envíos
   - `discount` - Descuentos y promociones

2. **Análisis de código fuente:** Durante la triage, el LLM (Claude) puede usar la herramienta `read_ecommerce_file` para:
   - Inspeccionar archivos del repositorio de Medusa.js
   - Correlacionar el reporte de incidente con el código fuente
   - Sugerir archivos específicos que podrían estar afectados
   - Recomendaciones técnicas contextualizadas

### Flujo de Integración

```
1. Incidente ingresa con descripción + screenshot/log
   ↓
2. TriageAgent analiza con Claude (multimodal)
   ↓
3. Claude puede usar `read_ecommerce_file` para inspeccionel código
   ↓
4. Se determina:
   - Severidad (P1-P4)
   - Módulo afectado (cart, order, payment, etc.)
   - Resumen técnico con referencias a archivos
   - Confianza en el análisis
   ↓
5. Ticket se crea con contexto técnico enriquecido
```

### Configuración

**Variable de entorno:**
```bash
MEDUSA_REPO_PATH=./medusa-repo
```

**Estructura esperada:**
```
medusa-repo/
  packages/
    medusa/
      src/
        services/
          cart.ts
          order.ts
          payment.ts
          ...
        routes/
          ...
        api/
          ...
```

## Para Desarrollo Local

### Modo Con Repo Real
Si tienes una copia del repositorio Medusa.js clonado:
```bash
git clone https://github.com/medusajs/medusa.git medusa-repo
export MEDUSA_REPO_PATH=./medusa-repo
```

### Modo Mock (feature/mocks)
Para desarrollo y testing sin dependencia de un repo externo:
```bash
export MEDUSA_REPO_PATH=./mock-medusa-repo
export MOCK_INTEGRATIONS=true
```

El mock-repo contiene estructura mínima pero realista para que Claude pueda analizar:
- Archivos de servicios con comentarios
- Estructura de módulos típicos
- Ejemplos realistas de patrones de Medusa.js

## Ejemplo de Uso en Triage

**Entrada:**
```
Título: "Carrito rechaza agregar items premium a clientes nuevos"
Descripción: "Los nuevos clientes no pueden agregar items con variantes premium al carrito. El sistema retorna error 400."
Log: "Error en POST /carts/cart-123/line-items - status 400"
```

**Proceso Claude:**
1. Lee el log y descripción
2. Identifica módulo: `cart`
3. Llama `read_ecommerce_file("packages/medusa/src/services/cart-service.ts")`
4. Analiza el código y la lógica de validación
5. Retorna: `severity: P2, affected_module: cart, files: ["packages/medusa/src/services/cart-service.ts"]`

**Resultado Ticket Trello:**
```
Título: [P2] Cart service rejects premium variants for new customers
Descripción:
  Module: cart
  Severity: P2
  Summary: Line item validation in cart service doesn't properly handle new customer + premium variant combinations
  Relevant files:
    - packages/medusa/src/services/cart-service.ts
    - packages/medusa/src/rules/cart-validation.ts
```

## Casos de Uso Reales

1. **Bug en payment connector** → Analiza cómo se procesan pagos
2. **Stock desincronizado** → Revisa inventory service
3. **Error en checkout** → Examina order workflow
4. **Descuentos aplicados incorrectamente** → Inspecciona discount engine

## Seguridad

- El LLM **no tiene acceso real** a código privado/sensible
- Solo lee archivos del Medusa.js repo (código abierto)
- Hay protección contra path traversal (`..` patterns bloqueados)
- Máximo 3000 caracteres por lectura (evita llenar context window)

## En el Contexto de E-commerce

Para un equipo que opera **cualquier plataforma de e-commerce** (no solo Medusa.js):
- El proyecto está generalizado pero fue diseñado con Medusa.js como caso de uso
- Puedes adaptar `affected_module` y `tools.py` para otros frameworks (Shopify, WooCommerce, etc.)
- El mismo sistema de triage funciona con cualquier base de e-commerce

## Roadmap: Vector Search (Fase 2)

**Escalabilidad actual:** File-by-file reading es lento para repos grandes (30K+ archivos).

**Solución propuesta:** Embeddings vectoriales con ChromaDB
- Pre-procesar Medusa.js repo: embeddings de cada función/clase/servicio
- En triage: búsqueda semántica devuelve top-K snippets más relevantes
- Mucho más rápido y eficiente para repos complejos

---

**Conclusión:** Medusa.js no es "solo datos" — es el **contexto de dominio** que hace posible que Claude dé recomendaciones SRE profesionales para equipos de e-commerce.
