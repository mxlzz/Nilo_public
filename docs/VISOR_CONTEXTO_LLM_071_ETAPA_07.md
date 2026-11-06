# Etapa 07 · Validación real y corrección de procedencia

Fecha: 2026-11-06. Rama: `work/0.7.1-visor-contexto-llm`.
Estado: corrección técnica implementada; cierre de etapa pendiente de CI final y prueba nueva del usuario. La revisión visual se pospone por decisión del usuario. No se publica 0.7.1 ni se cambia VERSION.

## Evidencia y causa

Se revisaron en modo de solo lectura dos bases aportadas por el usuario. No se incorporan al repositorio ni sus textos, decisiones o capturas. Las 22 solicitudes superan SHA-256, longitud y reconstrucción literal de mensajes. Las primeras cinco guardan procedencia detallada; las siguientes 17 solo contienen `trace_status=excede_limite`.

`build_metadata` repetía etiquetas y JSON Pointer en un objeto JSON que se comparaba contra 400.000 bytes antes de cualquier compresión. Al superar ese tamaño, devolvía un marcador y eliminaba toda atribución. La captura HTTP permanecía completa. No era un fallo de segmentación ni de la interfaz.

## Corrección

- Codec compartido y sin dependencias externas: JSON UTF-8 → zlib → base64, con versión de codificación, tamaño decodificado y SHA-256. Se conserva JSON plano cuando ocupa menos. Se mantiene el límite de **400.000 bytes almacenados** y se limita la expansión a **8 MiB**. La lectura comprueba EOF, ausencia de cola, longitud y hash; rechaza corrupción y expansión excesiva.
- La estructura semántica de procedencia sigue en versión 1. Al leer, la API y `RequestTraceStore` entregan los mismos campos, orígenes, transiciones y roles. El BLOB del cuerpo HTTP no cambia.
- Si el detalle supera el límite de rutas (8.000 por captura acumulada) o el presupuesto comprimido/decodificado, se reevalúa por campos raíz. Se conservan referencias y cambios entre etapas; `trace_status=partial`, `coverage.max_depth=1` y `coverage.unexpanded_paths` delimitan el detalle ausente. Los cambios raíz comparan valores completos en memoria, sin archivarlos.
- La profundidad máxima previa (9) ahora declara los subárboles no expandidos. No se atribuye cobertura completa a un índice cortado por profundidad.
- Si ni siquiera puede generarse una traza acotada, se guarda `unavailable` con motivo genérico, sin texto de excepciones ni valores ocultos. El cuerpo literal se captura igualmente.
- Lectura compatible con registros JSON anteriores, incluidos marcadores `excede_limite`, que la API identifica como parciales. Las lecturas no migran ni escriben SQLite.
- Nuevo módulo incluido en el manifiesto del paquete. Sin cambios en física, prompts, decisiones ni presentación HTML.

## Verificación local

- 59 pruebas del visor (9 nuevas de etapa 07): tamaño realista, exceso de rutas, límite comprimido, profundidad, payload discordante, corrupción, truncamiento, datos adicionales, expansión excesiva, lectura heredada, API de solo lectura y fallo explícito de instrumentación.
- Reconstrucción **offline** de contextos de 19 checkpoints aportados: 82.997–579.904 bytes de metadatos JSON se almacenaron en 10.593–31.710 bytes; las 19 trazas reconstruidas conservaron detalle completo y roundtrip idéntico. Sin red, nuevas decisiones ni escritura sobre las bases aportadas.
- Estas reconstrucciones son pruebas de la implementación: **no recuperan ni reemplazan las 17 trazas históricas descartadas**, ni prueban que los estados reconstruidos sean idénticos al contexto de cada intento original.
- Las 22 capturas originales siguen verificando bytes y bloques. Hashes de ambas bases aportadas idénticos antes y después de la revisión.
- Arquitectura sin ciclos nuevos, paquete importable verificado y escenarios aprobados. Replay determinista conserva fingerprint `9c4d43a5815fb042e06e32789b7dc6606023c3eb0634fe08dd7ad90616dc5c24`.

## Los dos intentos finales

Las 19 decisiones archivadas tienen su solicitud aceptada identificada por `trace_call_id`. En la copia del mundo, la sesión registra su última persistencia antes de la aceptación adicional y del último intento HTTP de la sidecar. El snapshot aún indica deliberación en curso. Por eso no es posible exigir correspondencia temporal completa entre ambas copias ni concluir un fallo de enlace.

En código, `accepted` significa respuesta validada por el router; el archivo de la decisión se escribe después, en otra base y transacción. No significa acción ejecutada. Un `transport_attempted` sin final indica ausencia de resultado registrado, no un error confirmado ni una respuesta aceptada. Se conserva esa evidencia sin inventar estados terminales. La causa exacta del corte no puede determinarse a partir de estas copias.

## Pendientes para cerrar la etapa

1. CI Linux y Windows del commit final, con instalación/migración/rollback portable.
2. Prueba breve nueva con esta versión para comprobar la captura prospectiva completa en ejecución real. Se puede continuar un mundo importado; las trazas antiguas perdidas seguirán identificadas como parciales.
3. Decisión de integración/publicación posterior. Interfaz visual aplazada; correcciones conductuales del PR #78 independientes.
