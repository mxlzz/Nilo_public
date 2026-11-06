# Nilo 0.7 · Etapa 09 — Navegación y exploración

**Fecha:** 5 de noviembre de 2026.  
**Rama de implementación:** `refactor/0.7`.  
**Estado:** **COMPLETADA**, con CI integral pública verde, benchmark medido y partidas sintéticas compatibles.  
**Seguimiento:** [#74](https://github.com/mxlzz/Nilo_public/issues/74) y [PR #77](https://github.com/mxlzz/Nilo_public/pull/77).  
**Referencia:** Nilo 0.6.4, sin modificar `main`, `VERSION` ni bases de datos personales.

## 1. Reauditoría del alcance

En la etapa 08 se había extraído el generador y la topología de `isla_v1`; `world.py` seguía agrupando **navegación, exploración y acciones físicas**. Esta etapa revisó la geometría accesible, rutas de una capa, fronteras de revelado, costas, retornos por la cueva, movimiento progresivo, consumo aleatorio, integración de `go/explore/gather/ascend` con el planificador y observabilidad del laboratorio.

| Función heredada | Problema observado | Tratamiento |
| --- | --- | --- |
| `pathfind` | BFS correcto en su orden, pero consultaba `revealed` como lista por cada vecino; carecía de índice multiconsulta | `NavigationIndex`: BFS local por origen/nivel, con `set` de conocimiento, padres y distancias |
| `choose_frontier` | Reejecutaba BFS por cada frontera potencialmente alcanzable | Un índice de origen para todas las candidatas; mismo orden de revelado, puntuación y RNG |
| `exploration_frontier` | Repetía BFS de cada candidata y consulta de lista | Usa la misma información conocida y distancias precalculadas |
| `reachable_shores` | Repetía BFS para cada punto de desembarco alcanzable | Un índice caminable; las orillas ocultas e inaccesibles siguen excluidas |
| `nearest_known` | Ejecutaba BFS por cada vecino posible de cada depósito | Comparación de distancias desde un índice local; no cambia materiales ni extracción |
| `go/move/advance_navigation` | Posible desalineación entre intención, ruta calculada y pasos realmente acreditados | Rutas de un único propietario, validadas por casilla; sin atravesar terreno oculto o bloqueado |
| `ascend/descend` | Riesgo de interpretar un portal distante como acceso inmediato | `known_exit_route` requiere ruta conocida; el cambio de nivel sigue siendo una acción física en el portal |
| Exploración sin progreso | Puede elegirse una frontera sin desplazarse ni observar algo nuevo en ejecución instantánea | Ese caso se diagnostica como intento sin progreso y no como éxito |

El mapa mantiene sus **37 × 21 celdas en dos niveles**. No se introduce pathfinding intercapas genérico: la conexión superficie/subsuelo es un portal físico específico de `isla_v1`. La información topológica verdadera sigue disponible para el motor, pero **el agente no puede trazar rutas sobre celdas que no haya revelado**.

### Dependencias y límites de la migración

Las funciones espaciales migraron a `nilo_runtime/worlds/navigation.py`. `world.py` reexporta las firmas históricas para `IslandPlanner`, `IslandEnvironment`, ejecutores y pruebas existentes; no conserva implementaciones duplicadas de BFS. El nuevo módulo solo importa el catálogo de terrenos, las primitivas del mundo `nilo_runtime/worlds/island.py` y la biblioteca estándar. No importa `world.py`, `nilo.py`, contexto LLM, API ni laboratorio.

`prepare_navigation` y `navigation_result` permanecen temporalmente en `world.py` por su interacción con selección de operaciones, recursos, eventos y resultados físicos. Esta deuda queda explícita para etapas 10–12; extraerlas ahora exigiría intervenir reglas fuera del alcance. `execute_action` también sigue siendo el dispatcher físico de acciones, **sin motor duplicado**.

## 2. Nuevo contrato de navegación

`NavigationIndex(w, origin, allow_water=False, known_only=False, target=None)` calcula un árbol BFS determinista para una sola posición inicial y capa.

- `distance((x,y))`: distancia en casillas, o `None` si inaccesible.
- `path_to((x,y))`: secuencia exacta de coordenadas, `[]` si el destino es el origen, o `None` cuando no hay ruta.
- `pathfind(w,origin,target,...)` mantiene la **firma y el retorno histórico**: lista de pasos o `[]` si el destino está en origen o es inaccesible. Se conserva esa ambigüedad solo en la fachada histórica, no en el índice nuevo.
- El índice es **efímero**: no se incorpora a SQLite, no altera el mundo y se construye de nuevo luego de una excavación, bloqueo o revelado. No requiere invalidación de cachés.
- Se conservan `DIRS`, desempates, orden de candidatos, aleatoriedad y el modo `known_only` para comparabilidad con replays anteriores.

La selección de frontera no conoce la forma del terreno oculto: evalúa únicamente una **casilla ya revelada** que limita con terreno todavía no revelado y cuya ruta es conocida y transitable. En exploración dirigida también verifica la orientación y región solicitadas; si esa dirección no ofrece frontera accesible, devuelve un diagnóstico en vez de elegir silenciosamente otra.

La navegación progresiva continúa ejecutando cada paso al vencer su tramo temporal, con control de adyacencia, nivel y capacidad para cruzar agua. Los cambios de terreno durante la marcha pueden bloquear una ruta, registrando desplazamiento efectivamente realizado y motivo. La selección de destinos no se convierte en teletransporte ni acredita automáticamente extracción de recursos.

## 3. Auditoría de observabilidad

El laboratorio `laboratorio_motor.py` tenía referencias estáticas a funciones en `world.py`. Tras el traslado, su traza real dejó de reconocer `exploration_frontier`, lo que detectó un test de integración de la suite completa. Se actualizaron los nombres de los archivos trazados a `navigation.py` y `island.py`, y las URL de código apuntan a **`mxlzz/Nilo_public` / `refactor/0.7`** con líneas reales. Los tests verifican ahora el módulo propietario correcto y los enlaces trazables.

La traza usa funciones ejecutadas efectivamente mediante `sys.settrace`; no se reemplazó por una lista narrativa prefijada. No se alteró el laboratorio físico paralelo (revisión prevista en etapa 21).

## 4. Pruebas y diferenciación de comportamiento

Se incorporaron **10 pruebas focalizadas** en `tests/test_navegacion_09.py`, comparando BFS contra una implementación de referencia independiente equivalente a 0.6.4, sobre cuatro semillas y ambos niveles, en modos de tránsito conocidos/no conocidos y cruce de agua. Otras pruebas verifican:

- Selección de fronteras y **estado RNG final** exactamente igual a la referencia para 40 semillas de elección.
- Coordenadas y rutas de exploración dirigida siempre dentro de conocimiento revelado.
- Índice de consulta regenerado frente a cambios de terreno.
- Orillas conocidas, transitables y conectadas.
- Regreso por el portal de cueva sin teletransporte.
- Falta de frontera informada como fracaso, sin progreso ficticio.
- Solo **un BFS por selección de frontera**, en lugar de uno por candidata.
- Un único propietario de funciones espaciales y ausencia de dependencia circular o import invertido mediante `tools/auditar_navegacion_09.py`.

La integración CI incluye el auditor, los tests focalizados, el comparador de rendimiento `tools/benchmark_navegacion_09.py`, la suite completa sin claves LLM, escenarios físicos, replay entre procesos y verificación de ZIP portable. `nilo_runtime/worlds/navigation.py` figura en el manifiesto y debe existir en el ZIP extraído.

**Comparación de complejidad:** antes, para F fronteras, el algoritmo repetía hasta F búsquedas BFS y comprobaciones lineales de membresía sobre R casillas reveladas; ahora se construye una vez un grafo de hasta V casillas y E aristas y se resuelven F consultas a distancias. El [workflow público #41966671990](https://github.com/mxlzz/Nilo_public/actions/runs/41966671990) midió, sobre **180 casillas reveladas y cuatro selecciones independientes**, **52,897 ms** para la implementación anterior y **2,195 ms** para la indexada: **24,1 veces más rápida en ese ensayo**. Las fronteras elegidas y el estado RNG fueron idénticos. Es una medición de microbenchmark en el runner, no una estimación de aceleración global de Nilo ni prueba de mejor autonomía.

## 5. Pruebas históricas y límites de inferencia

La [validación pública histórica #41965941042](https://github.com/mxlzz/Nilo_public/actions/runs/41965941042) fue **exitosa** tras el traslado espacial: seis SQLite sintéticas de 0.5.9.4.2, 0.6.0 y 0.6.4 importadas en copias, originales intactos; comparativa topológica con seis semillas. Esta evidencia demuestra compatibilidad de carga, **no** rendimiento de Nilo con un LLM real. La evaluación de autonomía se reserva para la etapa 23.

**Pendientes fuera de alcance:** nueva física de excavación o recursos (10–12), nuevo sistema de percepción (14), eliminación integral de coordinadores legados (10–12/24), reducción de bucles cognitivos y evaluación de runs Gemini/Groq (17/23). No se introducen objetivos externos ni accesos privilegiados a mapa.

**Puerta de cierre superada.** CI de la implementación definitiva [#41966671990](https://github.com/mxlzz/Nilo_public/actions/runs/41966671990): **success, 745 tests (1 omitida)**; auditorías estructurales, 10 pruebas focalizadas de etapa 09, benchmarks comparativos, seis semillas de topología, motor headless, escenarios físicos, continuidad RNG/IDs, replay histórico y ZIP portable extraído. Fingerprint histórico idéntico entre dos procesos: `9c4d43a5815fb042e06e32789b7dc6606023c3eb0634fe08dd7ad90616dc5c24`. La compatibilidad pública de seis partidas sintéticas se confirmó en [#41965941042](https://github.com/mxlzz/Nilo_public/actions/runs/41965941042). **Etapa 09 cerrada; habilitada la 10 · Recursos e inventario**, sin iniciar. No se modificaron `main`, `VERSION` ni partidas privadas.
