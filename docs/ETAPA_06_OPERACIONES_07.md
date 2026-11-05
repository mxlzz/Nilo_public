# Nilo 0.7 · Etapa 06 — Registro y validación de acciones

**Fecha:** 4/11/2026 · **Rama:** `refactor/0.7` · **Estado: COMPLETADA.** CI integral `referencia privada #41892936356` (`referencia-historica-privada-actions-runs-41892936356`): **success, 718 tests (1 omitida), replay exacto, auditor y ZIP**. CI de compatibilidad `referencia privada #41893382694` (`referencia-historica-privada-actions-runs-41893382694`): **success, seis partidas sintéticas históricas abiertas sobre copias**. [Plan maestro](PLAN_REESTRUCTURACION_NILO_07.md) · [Etapa 05](ETAPA_05_TIEMPO_07.md) · PR draft `referencia privada #155` (`referencia-historica-privada-pull-155`).

## 1. Auditoría de fuentes operativas (0.6.4–etapa 05)

El sistema reconocía los nombres de las operaciones a través de **cuatro contratos desconectados**:

| Fuente original | Responsabilidad | Riesgo |
| --- | --- | --- |
| `action_contracts.ACTION_GUIDE` / `COMMON_RULES` | Manual visible para el LLM y descripción de capacidades | Un texto podía documentar una acción inexistente o con forma no soportada |
| `brain.normalize_decision` | Lista de operaciones aceptadas y transformación específica de `go`, `explore`, `rest`/ `wait`, predicciones | La normalización podía admitir estructuras que otro módulo intentaría interpretar sin contrato |
| `IslandPlanner.validate_plan` | Precondiciones dependientes del estado físico: conocimiento, materiales, recorrido, forma y herramientas futuras | Se mezcla validación estructural con disponibilidad física; los filtros no compartían un único punto de consulta |
| `nilo.ACTION_DURATIONS` | Tabla local de tiempos estimados | Cualquier operación nueva podía aparecer en manual sin duración o en ejecución sin descripción |
| `Simulation._tick_slice` | Ramas `design`, `propose`, `report_issue`, `compare`, `conclude`, `perform_result` | Un segundo árbol de ejecución dentro del coordinador, además del dispatcher físico del mundo |
| `world.execute_action` / `capabilities.dispatch` | Acciones materiales en el mundo y métodos concretos de `interact` | Los casos de uso documentales/éticos y físicos podían recibir rutas distintas por duplicación |
| `laboratorio_casos` / `action_contracts.spec_for` | Lista de escenarios, contratos y diagnóstico | Pruebas escritas a partir de la guía antigua, no del contrato tipado |

Esta auditoría **no** presupone que las reglas físicas de cada operación son duplicadas: `world.execute_action` es el handler físico histórico que aún debe descomponerse en las etapas 08–12. La corrección de esta etapa remueve los registros superpuestos de **qué operación existe y qué ejecutor le corresponde**, sin inventar otro conjunto de leyes materiales.

## 2. Registro canónico

[`nilo_runtime/core/operations.py`](https://github.com/mxlzz/Nilo_public/blob/refactor/0.7/nilo_runtime/core/operations.py) es la fuente única de:

- **Nombre y texto de manual**: `ACTION_GUIDE`, `COMMON_RULES` y `SUPPORTED_OPERATIONS` se trasladaron textualmente desde `action_contracts.py`, manteniendo su orden y las aclaraciones sobre conocimiento observable. `manual_lines()` alimenta directamente el prompt LLM. No se regeneró ni reescribió el contenido de instrucciones histórico.
- **Duración**: `ACTION_DURATIONS` se trasladó íntegra desde `nilo.py`, como estimación temporal (no se interpreta como tiempo realmente medido). Cada `OperationSpec` obtiene `planned_minutes` de esa única fuente. No cambian los tiempos ni velocidades definidos en la etapa 05.
- **Ruta de ejecución**: `OperationSpec.executor` toma `physical` o uno de `design`, `propose`, `report_issue`, `compare`, `conclude`. `OperationSpec.navigable` identifica `go`, `explore`, `gather` y `ascend`. Los métodos de `interact` siguen siendo capacidades físicas versionadas en `capabilities.py`, no operaciones LLM nuevas.
- **Contrato mecánico verificable**: `VERIFIABLE` aporta los campos `verified_preconditions` y `verified_postconditions`; **son expectativas observacionales, no pruebas automáticas**.
- **Requisitos de forma**: `REQUIRED_FIELDS` y `FIELD_TYPES` definen la validación estructural y `validate_operation`. Está separada de las precondiciones materiales, de las que continúan encargándose `IslandPlanner` y los handlers del entorno. La validación estructural no afirma que existan un recurso, un destino o una herramienta.
- **Proyección legible**: `get_spec(op)`, `registered_operations()` (mapeo de solo lectura), `OperationSpec.to_record()` y `manual_lines()` permiten al laboratorio y a la interfaz inspeccionar la misma definición.

Se comprueba en importación que las operaciones del manual y la tabla de duración coincidan, y que los requisitos verificables no apunten a operaciones inexistentes. `get_spec` rechaza un nombre no registrado. Los registros tipados no importan `world`, el LLM, SQLite ni providers.

## 3. Consumidores migrados

- `action_contracts.py` ya no define una segunda guía, sus reglas comunes ni el catálogo verificado. Reexporta los nombres históricos para clientes anteriores; `instructions()` usa `manual_lines()`, y `spec_for` agrega duración, ejecutor y requisitos, sin cambiar los campos del diagnóstico anterior.
- `brain.normalize_decision` toma el conjunto de operaciones de `registered_operations()` y valida la forma de las solicitudes modernas antes de procesarlas. Mantiene reglas especiales de normalización espacial y necesidades. `legacy_rest` conserva los criterios del parser previo para replays publicados.
- `IslandPlanner.validate_plan` consulta `validate_operation` al comienzo de cada paso y sigue comprobando **después** alcance, recursos, geometría y capacidad a partir de hechos del mundo. No convierte condiciones hipotéticas en efectos.
- `nilo.py` consulta `get_spec(op).planned_minutes` y `.executor` en vez de duplicar una tabla de tiempos y el árbol de acciones documentales. `ACTION_DURATIONS` sigue importable desde `nilo.py` como alias por compatibilidad.
- `environments.IslandEnvironment` consulta la familia registrada antes de preparar una navegación o ejecutar física. Rechaza enviar un `design` al handler físico, pero permite `interact` como operación física genérica.
- [`nilo_runtime/application/operation_dispatch.py`](https://github.com/mxlzz/Nilo_public/blob/refactor/0.7/nilo_runtime/application/operation_dispatch.py) concentra el despacho **documental**. Mantiene la semántica anterior: `design` registra ficha sin construir; `propose` solicita una capacidad sin instalarla; `report_issue` registra un posible error; `compare` y `conclude` solo documentan evidencia disponible mediante IDs. Los efectos secundarios de archivo y cierre de investigación se preservan; el dispatcher no genera recursos materiales.
- El laboratorio usa `ACTION_GUIDE` reexportada por `action_contracts`, ahora originada en el mismo registro. Ningún método `interact` se eleva a operación sin declararlo expresamente.

**Distinción crítica que motivó una regresión inicial:** para `design`, `prediction` es una **cadena descriptiva**; para un ensayo medible, `prediction` es un **objeto** con hipótesis, métrica y umbral. La validación acepta la cadena de diseño sin equipararla a evidencia física. Este cambio se verificó contra `laboratorio_casos`.

## 4. Tests y controles permanentes

[`tests/test_operaciones_07.py`](https://github.com/mxlzz/Nilo_public/blob/refactor/0.7/tests/test_operaciones_07.py) verifica:

- Paridad exacta de nombres y duraciones entre guía, normalizador, reloj, validación y registro; contratos pre/post, clases de ejecutor y navegación.
- El manual LLM tiene el mismo orden y texto que el registro; `spec_for` expone duración, ruta y requisitos; el mapa de especificaciones es inmutable.
- Rechazo estructural de operaciones desconocidas, listas convertidas en cadenas, coordenadas booleanas, geometrías inválidas, etc., sin exigir pruebas físicas adelantadas.
- `design.prediction` textual aceptada sin confundirse con una medición; las solicitudes normales de `build`/ `go` mantienen su tratamiento.
- `IslandPlanner` rechaza operaciones inexistentes sin anular otras válidas; `execute_document` no construye objetos y rechaza rutas físicas; compare/conclude sin mediciones no inventan evidencia.
- Las capacidades concretas `llenar`, `probar_carga`, etc. permanecen detrás de `interact`.

[`tools/auditar_operaciones_07.py`](https://github.com/mxlzz/Nilo_public/blob/refactor/0.7/tools/auditar_operaciones_07.py) se ejecuta desde `validacion.yml` en cada push de `refactor/**`: busca mediante AST nuevas definiciones de `ACTION_GUIDE`, `ACTION_DURATIONS` o `DOCUMENT_EXECUTORS` fuera del registro, verifica paridad guía/reloj/LLM, rutas físicas, manual y ausencia de colisiones de métodos de capacidades. El ZIP portable incluye el registro y el adaptador, comprobados al extraer.

**Puerta de cierre superada.** CI integral `referencia privada #41892936356` (`referencia-historica-privada-actions-runs-41892936356`): **success, 718 pruebas (1 omitida)**, banco de escenarios, auditoría de capas/identidades/operaciones, escenarios físicos, ZIP portable extraído y fingerprint histórico en dos procesos exactamente `9c4d43a5815fb042e06e32789b7dc6606023c3eb0634fe08dd7ad90616dc5c24`. CI histórica `referencia privada #41893382694` (`referencia-historica-privada-actions-runs-41893382694`): **success, 6/6 partidas sintéticas** de 0.5.9.4.2, 0.6.0 y 0.6.4 importadas a copias, sin modificar las originales; incluyó auditoría del registro de operaciones. Se verificó además una comparación literal del bloque completo de manual/instrucciones y de la tabla de duraciones frente al commit de etapa 05: **ambos coinciden exactamente**.

## 5. Deuda explícita, sin segundo motor

- `world.execute_action` conserva por ahora el `if/elif` de **ejecución física**, y `capabilities.dispatch` sigue resolviendo métodos versionados. Su extracción a handlers físicos especializados pertenece a las etapas 08–12. Eliminarlo ahora sería una reescritura prematura de geometría y conservación de inventario.
- El sistema aún contiene lógica de vida de sesión y avance de acciones dentro de `Simulation._tick_slice`; dividirla pertenece a la etapa **07 — Núcleo orquestador**. El contrato 06 permite hacerlo sin reintroducir catálogos duplicados.
- El registro valida la **forma** y las rutas; la comprobación física contextual debe seguir siendo dinámica. Las acciones incompletas deben recibir un rechazo legible y nunca convertirse en éxitos por la descripción de manual.
- Las partidas viejas no reescriben planes o historial para ajustarlos al nuevo contrato; los fixtures de replays conservan sus reglas y resultados.
- Cambios en el catálogo de acciones exigirán ajustar **una sola definición** en `nilo_runtime/core/operations.py` y agregar pruebas de capacidades físicas, no duplicar manual/duración/dispatcher.

**Etapa 06 cerrada. Próxima: 07 · Núcleo orquestador, todavía no iniciada.** `main`, `VERSION`, el release 0.6.4 y las partidas privadas permanecen sin cambios. El despachador físico histórico continúa pendiente de la migración de los handlers en etapas 08–12; no se ha creado un motor paralelo.
