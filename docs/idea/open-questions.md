# Open Questions

## Sobre el alcance del MVP
- ¿El MVP cubre el flujo completo (pasos 1-8) o empezamos por un subconjunto?
- ¿Qué paso tiene más dolor hoy y debería ir primero?
- ¿El formulario de evidencia de bugs (paso 5 alternativo) es una interfaz web propia o un formulario externo (Google Forms, Notion, etc.)?

## Sobre los usuarios
- ¿Quién es el usuario primario del MVP: el desarrollador, el QA engineer o el tech lead?
- ¿Quién hace la aprobación manual del paso 4? ¿Cualquier reviewer o un rol específico?

## Sobre integraciones
- ¿Trello o Jira? ¿Ya tienen uno configurado con proyectos/boards definidos?
- ¿El repositorio de GitHub ya existe o se crea nuevo?
- ¿Ya tienen acceso a la API de GPT y Gemini además de Claude?
- ¿El agente de QA (paso 5) evalúa código directamente del PR o necesita un ambiente desplegado para revisar UX/UI?

## Sobre el QA agent
- ¿La regresión automatizada (paso 5) asume que ya existen tests escritos en el repo, o el agente también los genera?
- ¿Qué criterios define "UX/UI revisado"? ¿Hay diseños de referencia (Figma, screenshots)?
- ¿Cómo se determina cuáles flujos previos revisar en la regresión? ¿Hay un mapeo de features?

## Sobre los reportes
- ¿El reporte técnico (Claude) y el de negocio (GPT/Gemini) van en el mismo ticket o en tickets separados?
- ¿El reporte de solución técnica (paso 8) también se adjunta al ticket o es un artefacto separado?

## Sobre restricciones
- ¿Hay restricción de costos por llamadas a múltiples APIs de IA?
- ¿Hay restricción de tiempo para el MVP?
- ¿El stack del proyecto que se va a QA-ear es conocido o la plataforma debe ser agnóstica?
