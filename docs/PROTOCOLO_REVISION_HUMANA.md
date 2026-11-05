# Nilo — Protocolo de revisión humana de propuestas

**Decisión del proyecto (27 de octubre de 2026).**
Este documento fija el proceso de ampliación de leyes físicas y corrección de errores. Se aplica a las versiones futuras de Nilo hasta que el observador decida modificarlo expresamente.

## Responsabilidades

| Participante | Responsabilidad | Límite |
| --- | --- | --- |
| **Nilo** | Experimenta, observa, recopila evidencias, propone ampliaciones de física (`propose`) y plantea posibles errores (`report_issue`). Puede volver a investigar sus sospechas. | No ve ni modifica el código. No aprueba leyes ni parches. |
| **Motor** | Ejecuta las reglas y verifica resultados; puede registrar alertas deterministas de integridad. | Una alerta no demuestra por sí sola un bug; no decide correcciones. |
| **Observador (usuario)** | Lee las propuestas, las discute con ChatGPT y decide aceptarlas, rechazarlas, pedir más pruebas o impulsar una implementación. | Es el único que autoriza cambios en el programa. |
| **ChatGPT** | Ayuda a analizar evidencias, explicar fenómenos, evaluar alternativas e implementar y probar **solo lo autorizado**. | No actúa como revisor autónomo permanente ni decide qué propuestas aprobar. |

## Circuito de decisión

1. Nilo identifica un resultado inesperado, una hipótesis o una capacidad que no puede evaluar. Distingue **fracaso físico**, **física no representada** y **posible inconsistencia**.
2. Nilo registra una solicitud `sol-...` o `bug-...`, con resultados y mediciones reales cuando existen. También puede realizar más experimentos antes de presentar o ampliar el informe.
3. El observador la ve en **Vínculo → Propuestas**. Si hace falta, descarga **Exportar informe JSON** y lo trae a la conversación con ChatGPT.
4. El observador y ChatGPT analizan el fundamento, los datos, las condiciones de reproducción y las implicancias. Una sospecha puede terminar clasificada como interpretación equivocada, límite legítimo, física faltante, bug confirmado o información insuficiente.
5. El observador decide qué hacer. Puede pedir más experimentos, aceptar la idea sin implementarla todavía, descartarla o autorizar un cambio concreto.
6. **Solo después de una autorización explícita**, ChatGPT ayuda a implementar el cambio acordado. El código se prueba en una rama separada mediante tests, escenarios físicos y replay; el observador decide si integrar la versión.

## Dos aprobaciones distintas

- **Evaluación conceptual:** los controles de la interfaz, como *Aprobar estudio* o *Confirmar error*, registran una clasificación en el historial de Nilo. No conceden efectos físicos ni autorizan automáticamente cambios de código.
- **Autorización de implementación:** surge de una instrucción explícita del observador dirigida a ChatGPT, una vez conversada la propuesta. Es independiente del estado guardado en la interfaz.

## Reglas que no se automatizan

- Ningún agente revisa ni aprueba propuestas en nombre del observador.
- Ninguna solicitud dispara por sí misma escritura de código, pull requests, merges o publicación.
- Una alerta automática del motor puede abrir una **solicitud de revisión**; no instala un parche ni incorpora una ley.
- Las herramientas de pruebas y GitHub se usan para las modificaciones concretas autorizadas por el observador, no como un ciclo autónomo de mantenimiento.

## Próximos desarrollos permitidos

Sí pueden mejorarse la **calidad de las propuestas** de Nilo: reproducibilidad de las acciones, mediciones estructuradas, contraste de hipótesis, detección de duplicados, seguimiento de informes y explicaciones legibles. El objetivo es que Nilo investigue más por su cuenta y el observador disponga de mejor evidencia para decidir. **No** se desarrollará un agente de autoprogramación o autoaprobación.

## Estado de implementación

En Nilo 0.5.9.0 ya existen `propose`, `report_issue`, detección parcial de invariantes, bandeja de propuestas, revisión manual e informes JSON. El replay exacto del instante de una anomalía y la investigación experimental más autónoma de Nilo siguen pendientes.

Esta aclaración es de **gobernanza/documentación**: no altera la simulación ni las reglas físicas existentes.
