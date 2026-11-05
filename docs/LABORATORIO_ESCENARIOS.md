# Laboratorio de escenarios de Nilo 0.6.2

## Propósito

Inspeccionar el funcionamiento del motor por comportamiento **sin leer archivo por archivo**. A diferencia del laboratorio de acciones 0.6.1, los escenarios entran al orquestador original `Simulation`: `brain.normalize_decision → Simulation.plan_ready → IslandPlanner.validate_plan/improve_plan → Simulation.tick → Environment → ActionResult → measure/diagnostics → archivo SQLite`.

La decisión de entrada se prepara en el escenario, simulando **la salida estructurada del LLM**. No se llama a Gemini ni a Groq, no se afirma que una IA real habría tomado esa decisión, y no se asignan intereses nuevos a Nilo.

## Abrir

En Windows: doble clic en **`ABRIR_LABORATORIO.bat`** y abrir `http://127.0.0.1:8766` si no se abre automáticamente. En Python instalado: `python laboratorio_motor.py`. No hacen falta credenciales.

La página principal muestra el banco de casos. El laboratorio físico anterior sigue disponible en `http://127.0.0.1:8766/sandbox`, identificado como el ejecutor físico **legado**, sin ciclo completo.

## Modos

**1. Escenarios (principal).** Catálogo agrupado en acciones elementales; navegación y exploración; recursos y necesidades; fabricación; interacción de objetos; investigación; planes y proyectos; casos límite. Cada escenario tiene una descripción, los comandos de entrada, una lista explícita de condiciones preparadas, un resultado esperado y una semilla.

Pulsar **Ejecutar escenario** recorre las etapas reales del motor. Se muestran diferencias físicas, tiempo transcurrido, estado del personaje, diagnósticos, eventos, mediciones y traza resumida de funciones con líneas de código ejecutadas. Cada función permite desplegar fragmentos de código real. **Ejecutar todos** recorre el catálogo y señala casos que no cumplan su expectativa.

**2. Sandbox (secundario).** Panel de botones con todas las operaciones del catálogo. Al elegir una operación se ofrecen botones de destino, método, materiales, duración o forma según corresponda. Se pueden agregar hasta 12 pasos a un plan, seleccionar fixtures de mundo/materiales y ejecutar la deliberación por **el mismo Simulation real**. El JSON se ofrece solo como ajuste avanzado cuando las opciones de botones no alcanzan.

**3. Análisis cognitivo.** En la respuesta de cada escenario se registran las claves del contexto observado antes y después, y qué campos conservaría el constructor de payload Gemini. Se trata del **constructor de percepción y presupuesto real**, pero no una llamada a red ni una reproducción literal de las intervenciones que `Nilo.think` pudiera agregar en un ciclo autónomo.

## Cobertura y límites

- **68 casos de referencia** agrupados en ocho familias, con al menos un caso por cada una de las 26 operaciones. Incluyen aceptación, fallo esperado, rechazo de validación, navegación, cambios de nivel, extracción a distancia, herramientas, construcción, almacenamiento, ensayos, cierre de proyectos y procesos de varias deliberaciones.
- El caso `go → árbol` y `go → piedra` está deliberadamente marcado como **rechazado**: esas búsquedas por nombre todavía no están implementadas. Es un **caso de diseño pendiente**, no un éxito inventado.
- `gather piedra` ejecuta las **reglas actuales** (extracción sin herramienta). La tasa del 33 % manual, el pico para recolección y la nueva memoria 5×5 siguen pendientes. Un laboratorio no instala reglas nuevas.
- Los escenarios cubren **clases de condiciones**, nunca todas las permutaciones infinitas de estado, material, geometría, semilla y posición. La suite conserva expectativas observables y debe ampliarse cuando aparece una rama nueva.
- Se puede preparar expresamente un inventario, una roca, una cueva o una construcción para el ensayo. Esos **fixtures** no se atribuyen a acciones espontáneas de Nilo: el catálogo muestra cuándo se utilizaron y no los confunde con material creado por el motor.
- El orquestador se ejecuta sobre **SQLite temporal**; la partida original `nilo_mundo.sqlite3` no se lee ni se escribe. No se requieren APIs.
- Las trazas están deliberadamente resumidas: registran funciones seleccionadas, sus líneas ejecutadas y hasta 14 líneas de código por aparición. No equivalen a un perfil de todas las sentencias ni a una depuración del proceso por cada instrucción Python.
- La percepción mostrada en la vista cognitiva no equivale a una deliberación real en red con historial completo; las opciones de fallback/proveedor se analizan separadamente.
- El reloj de Nilo se ejecuta por ticks reales bajo el motor original. Si el laboratorio encuentra una discrepancia del propio motor, no la corrige ni la oculta.

## Arquitectura para extender

- `laboratorio_casos.py`: catálogo declarativo, preparación explícita de fixtures, motor temporal aislado, trazas, comparaciones antes/después, veredicto de expectativas y sandbox por plan.
- `laboratorio_escenarios.html`: interfaz práctica de casos y comandos por botones.
- `laboratorio_motor.py`: servidor localhost, rutas `/api/catalog`, `/api/scenario/<id>` y `/api/manual`; mantiene `/sandbox` para acceder al laboratorio anterior.
- `tests/test_laboratorio_casos.py`: recorre el catálogo completo y verifica que cada caso cumpla su resultado esperado, sin crear una segunda física.

Para añadir un caso, definir una entrada `case(...)` con la acción/plan, la condición explícita (fixture) y la clase de resultado esperada. Si el caso necesita una condición nueva, extender `fixture` sin alterar las reglas del mundo. No escribir cálculos físicos paralelos en el laboratorio.

Para auditorías longitudinales, todavía queda una extensión importante: cargar una secuencia histórica de una partida real y reconstruir las decisiones originales bajo la misma versión del motor, sin volver a llamar a un LLM.

## Extensión histórica 0.6.3

La vista `/historico` permite cargar SQLite, recorrer momentos por slider y reproducir en una copia temporal los puntos anteriores a deliberaciones y acciones capturados desde la versión 0.6.3. Las partidas antiguas son de consulta, sin reconstrucción exacta. Ver [Laboratorio histórico](LABORATORIO_HISTORICO.md).

## Vista de comprensión para observadores · v0.6.4

Se simplificó la pantalla a **dos columnas**: la izquierda contiene catálogo y condiciones, apilados verticalmente; la derecha incluye secciones desplegables, con **«Qué recibe el LLM»** abierta por defecto. El botón «Ejecutar todos» desaparece de la interfaz (las 68 pruebas siguen en CI). Cada bloque y etapa del recorrido incorpora un botón **?** con explicaciones, incluido «Normalizar decisión»: transforma la respuesta del LLM al contrato de acciones, sin ejecución física todavía.

### Exactamente qué recibe el proveedor

El laboratorio llama a **`brain.build_deliberation_request()`**, el mismo constructor que usa `request_llm()`. Reconstruye las entradas que prepara `Simulation.think()`: percepción, últimos **16 eventos**, hasta 8 conversaciones recientes y la regla sobre comentarios humanos. La vista permite alternar **Gemini/Groq** y **antes/después**. Expone:

- **Datos del mundo que recibe el LLM, con valores:** el JSON final después de proyección cognitiva y compresión, no una lista de claves.
- **Instrucciones del sistema** y **mensaje de usuario** textuales: Gemini separa sistema/usuario y entrega los contratos de acciones dentro del usuario; Groq incorpora contratos en sistema y el JSON en usuario.
- **Solicitud íntegra:** el cuerpo JSON serializado exactamente por el constructor, con roles, parámetros, modelos y valores. No incluye credenciales HTTP ni realiza llamadas a API.
- **Diferencias:** campos finales cuyo contenido cambió entre la percepción anterior y posterior; se muestran valores antes/después para comparar la consecuencia de la acción.
- **Campos descartados con sus valores originales:** representación previa del escenario que el filtro **no envía** al LLM.

El modelo real puede recibir otro modelo/proveedor al activar un fallback; la vista muestra la reconstrucción para la selección elegida **sin afirmar que se envió**. La simulación ejecuta decisiones prefijadas, no conversaciones espontáneas del LLM. Si el escenario no tiene chats, se envía la lista vacía, como ocurriría en una partida sin chats.

### Diferencia con los diagnósticos internos

«Diagnósticos y estado interno completo» muestra datos técnicos del laboratorio, incluyendo reservas numéricas del motor, para el observador. **No se envían como bloque al modelo.** Solo los valores que sobreviven a `project_context` y a los presupuestos de `build_deliberation_request` forman parte del mensaje. Los resultados de mediciones documentadas pueden contener números y, cuando se incluyen, esos números sí aparecen exactamente en la vista LLM.
