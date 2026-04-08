# Copilot Repository Instructions

Este repositorio sigue una metodología basada en especificaciones y agentes especializados.

## Antes de sugerir código

1. revisa `README.md`
2. revisa `AGENTS.md`
3. revisa la spec relevante en `docs/specs/`
4. revisa contratos y decisiones en `docs/architecture/`
5. revisa la tarea activa si existe en `tasks/active/`

## Reglas

- genera cambios pequeños y consistentes con la spec
- no inventes alcance de producto
- evita lógica no validada por criterios de aceptación
- cuando el cambio afecte diseño, sugiere documentarlo
- incluye pruebas o estrategia de validación cuando corresponda
- respeta separación de responsabilidades entre frontend, backend, QA y seguridad

## Prioridades

1. claridad
2. corrección
3. mantenibilidad
4. validabilidad
5. velocidad

## Formato esperado de ayuda

Cuando sea posible, estructura la ayuda así:

- entendimiento del problema
- propuesta de cambio
- archivos a tocar
- validación sugerida
- riesgos