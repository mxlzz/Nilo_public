# Laboratorio histórico de Nilo · v0.6.3

**Propósito.** Elegir un momento real de una partida en una línea temporal, inspeccionar lo que Nilo decidió e hizo, y reproducir desde el estado anterior cuando la partida dispone de un punto de restauración. Es una herramienta del observador, no parte de la percepción ni de la memoria consciente del personaje.

## Cómo abrirlo

1. Ejecutar `ABRIR_LABORATORIO.bat`, como en 0.6.2.
2. En `http://127.0.0.1:8766`, elegir **Partidas históricas** o entrar en `http://127.0.0.1:8766/historico`.
3. Elegir **Usar partida actual** (si existe `nilo_mundo.sqlite3` en esa carpeta) o cargar una copia `.sqlite3` desde el navegador (máximo 200 MB por la interfaz). Conviene cerrar Nilo antes de copiar manualmente el archivo para no perder transacciones que estén en SQLite-WAL.
4. Usar el **slider** o las opciones de filtrado para elegir una deliberación o una acción. Examinar su registro de la partida.
5. Si tiene estado previo preservado: pulsar **Reproducir procesamiento**. El motor ejecuta el plan o acción real en una SQLite **temporal**, mostrando funciones/lineas, el resultado experimental y las diferencias con el original cuando éste se puede asociar sin ambigüedad.
6. Opcionalmente modificar el JSON del comando seleccionado y reproducir la variante **desde el mismo estado**. El resultado original permanece intacto.

## Qué se registra desde esta versión

La clase `TimelineStore` crea `timeline_checkpoints` en el SQLite de la partida. Sin intervenir sobre el LLM ni cambiar las leyes físicas, guarda un estado comprimido:

- Antes de procesar **cada decisión** en `Simulation.plan_ready`: estado integral del mundo/personaje, decisión recibida, reloj, versión del motor, estado RNG local y global.
- Justo antes de **iniciar cada acción** al tomarla de la cola en `Simulation._tick_slice`: estado integral, operación que se iniciará, versión, RNG y el índice del archivo histórico.

Cada checkpoint lleva SHA-256 para detectar daños del bloque comprimido. Se usa JSON comprimido, **no pickle**, evitando ejecutar estructuras deserializadas. La tabla de estados forma parte del SQLite y crecerá según los eventos. No se eliminan puntos históricos automáticamente.

Los checkpoints **no forman parte de la memoria de Nilo**, ni le aparecen como avisos. El simulador puede desactivarlos al reejecutar un estado para evitar capturas recursivas. Los archivos originales se leen **solo mediante SQLite en modo lectura**, y los archivos cargados desde el navegador se copian a una carpeta temporal local; no hay transferencia a servidores externos ni llamadas a proveedores.

## Delimitación de la exactitud

**Partidas anteriores a v0.6.3:** las tablas históricas de decisiones y diagnósticos permiten inspección y navegación temporal. No incluyen el estado físico completo anterior a cada acción, por lo que el botón de reproducción se desactiva. No se genera un estado histórico ficticio mediante extrapolación del snapshot final.

**Partidas posteriores:** `historical_lab.replay` restaura el estado y RNG capturados, prepara un `Simulation` aislado y procesa una deliberación mediante `plan_ready` o una acción mediante `tick`, sin LLM. Los estados comparados son el anterior y el nuevo; los diagnósticos originales se vinculan solamente en el intervalo hasta el siguiente checkpoint. Si no hay diagnóstico asociable, el panel lo explicita.

**No se garantiza identidad bit a bit**: los UUID, el reloj real y algunas circunstancias externas (por ejemplo intervenciones humanas, cambios de proveedor, eventos fuera del snapshot) no están completamente reproducidos. El replay ejecuta **la versión de motor instalada**, e informa la versión con la que se registró el estado. Comparar versiones diferentes sirve para detectar diferencias, pero no garantiza atribuir causalidad a una sola modificación. La comparación de resultados físicos debe interpretarse teniendo en cuenta estas condiciones.

Los checkpoints permiten recuperar el estado del personaje pero el archivo de evidencias de solo lectura no se copia íntegro al SQLite temporal. Algunas consultas a registros archivados fuera del snapshot pueden diferir. El laboratorio no reproduce la producción del texto del LLM ni la red.

## Cobertura y pruebas

`tests/test_historical_lab.py` verifica puntos previos a deliberación y acción, lectura de bases antiguas, integridad de origen, restauración de acciones, variantes de decisión y sintaxis de interfaz (Node, cuando está instalado). La suite existente de 68 escenarios sigue ejecutándose sin cambio en la física.

**Pendiente de investigación:** optimizar compresión/deduplicación incremental del registro para partidas muy grandes; capturar fuentes externas o el flujo de UUID solo si la comparación causal lo exige; replays de planes completos con medición más fina de cada subpaso; reproducción fiel entre ramas/instalaciones distintas del motor y navegación histórica paginada para partidas de muchos años. Ninguno de estos pendientes habilita acciones nuevas de Nilo por sí mismo.
