# Problem Statement

## Idea inicial
Un agente SRE que convierte reportes de incidentes multimodales (texto + imagen de error + archivo de log) en tickets de Trello enriquecidos con análisis automático del codebase de la aplicación e-commerce, notifica al equipo técnico vía Slack y al reporter vía email, y cierra el ciclo cuando el incidente se resuelve.

## Problema principal
En equipos de ingeniería que operan aplicaciones e-commerce, el triage manual de incidentes consume entre **15 y 45 minutos por incidente**. El ingeniero on-call debe:

1. Leer y entender el reporte del usuario (que puede ser ambiguo o incompleto)
2. Correlacionar el error con los logs del sistema
3. Buscar en el codebase qué módulo o servicio podría estar afectado
4. Crear un ticket con suficiente contexto técnico para que otro ingeniero pueda actuar
5. Notificar manualmente al canal correcto del equipo
6. Recordar actualizar al reporter cuando el problema se resuelve

Cada uno de estos pasos es manual, repetitivo y propenso a errores de clasificación. En e-commerce, **cada minuto de downtime tiene un costo directo en ventas perdidas y daño a la reputación de la marca**.

## A quién le duele

### SRE on-call engineer
El más afectado. Recibe alertas a cualquier hora, muchas veces con información incompleta. Tiene que reconstruir el contexto del problema antes de poder actuar. En incidentes de alta severidad (P1/P2), este tiempo de triage es crítico.

### Reporter del incidente
Puede ser un usuario final, un developer interno o un monitor automatizado. No sabe si su reporte fue recibido, quién lo está atendiendo, ni cuándo esperar una resolución. La falta de confirmación genera ruido: reportes duplicados, escaladas innecesarias, tickets incompletos.

### Engineering manager / Tech lead
No tiene visibilidad en tiempo real del estado de incidentes activos. Los tickets en Trello suelen crearse tarde, con contexto insuficiente, o directamente no se crean si el ingeniero on-call resuelve el problema rápido pero no documenta.

## Impacto
Sin una solución:
- **MTTR elevado**: el tiempo promedio de resolución se extiende por el overhead de triage manual
- **Fatiga del equipo on-call**: tareas repetitivas de bajo valor que consumen energía cognitiva en momentos de alta presión
- **Tickets incompletos**: sin contexto técnico suficiente, los tickets bloquean la investigación posterior
- **Ciclo abierto**: el reporter nunca sabe que su incidente fue resuelto a menos que alguien recuerde notificarle
- **Sin trazabilidad**: sin logs estructurados del proceso de triage, es imposible auditar qué pasó y cuándo

## Señales de valor
Sabremos que la solución vale la pena cuando:
- El tiempo de triage se reduce de ~30 minutos a ~2 minutos (el agente genera el análisis y el ticket en segundos)
- El reporter recibe confirmación automática con número de ticket dentro de los primeros 60 segundos de submitear el reporte
- El ticket en Trello tiene suficiente contexto técnico (módulo afectado, severidad, archivos relevantes del codebase) para que un ingeniero pueda actuar sin ir y volver con el reporter
- Los logs de observability permiten reconstruir exactamente qué hizo el agente en cada etapa del pipeline
- El equipo on-call puede operar con MOCK_INTEGRATIONS=true en entornos sin credenciales configuradas y el sistema sigue funcionando
