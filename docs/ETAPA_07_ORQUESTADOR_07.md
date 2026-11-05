# Nilo 0.7 · Etapa 07 — Núcleo orquestador y adaptadores

**Fecha:** 4 de noviembre de 2026 · **Rama:** `refactor/0.7` · **Estado: COMPLETADA.** [CI final #41897149049](https://github.com/mxlzz/Nilo/actions/runs/41897149049): **success, 727 pruebas (1 omitida) + 9 pruebas focalizadas, auditorías, escenarios físicos, replay exacto, ZIP portable**. [CI de seis partidas históricas #41895886906](https://github.com/mxlzz/Nilo/actions/runs/41895886906): **success**. [Plan de 25 etapas](PLAN_REESTRUCTURACION_NILO_07.md) · [Etapa 06](ETAPA_06_OPERACIONES_07.md) · [PR draft #155](https://github.com/mxlzz/Nilo/pull/155).

## 1. Auditoría del coordinador original

En la etapa 06, `nilo.py` tenía **2.141 líneas** (~142 KB) y concentraba la fachada ejecutable, `Simulation` (36 métodos), ciclo del mundo, sesiones SQLite, disparadores LLM, diagnósticos, exportación del estado para la interfaz y un `BaseHTTPRequestHandler` de más de 100 líneas. Un cambio de servidor podía requerir importar las mismas dependencias del motor, incluso cuando solo se necesitaba avanzar un minuto. Además, la traza del laboratorio buscaba métodos de `Simulation` por nombre de archivo `nilo.py`, por lo que extraerlos sin actualizar el trazador produciría diagnósticos incompletos.

Se confirmó que las regresiones antiguas usan una API de hecho que debe preservarse: `nilo.Simulation()`, `nilo.DB` reasignable en pruebas, `nilo.Handler.sim` para pruebas HTTP, `initial_state`, `ACTION_DURATIONS`, las funciones `typing_*` y `is_newsworthy`, y `nilo.config`, `nilo.available`, `nilo.route` reemplazables con mocks. La reproducción física histórica usa la misma clase pública. Hacer desaparecer estos puntos de extensión cambiaría el resultado de cientos de fixtures sin aportar una mejora al motor.

También se encontró una dependencia inversa: `historical_lab.py` importa `laboratorio_casos`, que importa `nilo.py`; el nuevo motor no puede importar directamente `historical_lab.TimelineStore` sin crear un ciclo entre dominio, laboratorio y aplicación.

## 2. Estructura después de la extracción

| Archivo / capa | Propiedad exclusiva |
| --- | --- |
| `nilo.py` (fachada pública y entrada CLI) | Reexportación de contratos históricos y subclase adaptadora `Simulation`. Conecta `nilo.DB`, `config`, `available` y `route` mediante callbacks que reflejan las modificaciones del cliente; inicia web únicamente desde `main()` |
| `nilo_runtime/application/deps.py` | Dependencias de caso de uso, rutas base `HERE/DB`, utilidades temporales de tipiado y texto. **No importa HTTP, HTML, `webbrowser` ni `nilo.py`.** `RuntimeServices` define puertos inyectables para configuración y proveedor |
| `nilo_runtime/application/engine.py` | **`Simulation` headless**, clase de composición pequeña de casos de uso. Se puede importar y ejecutar con `db_path` y puertos propios sin siquiera importar la fachada `nilo.py` |
| `nilo_runtime/application/session.py` | Vida de la sesión, migración de estructura/saves, escritura transaccional, snapshot y sello temporal |
| `nilo_runtime/application/records.py` | Cuaderno, noticias, eventos, lectura/revisiones, QMP, diagnóstico, archivo y proyección observable |
| `nilo_runtime/application/decisions.py` | Validación de plan delegada al entorno, proyectos, deliberación LLM/demo, agenda, reintentos y chat |
| `nilo_runtime/application/clockwork.py` | Avance de tiempo, acción pendiente, fases, aplicación de resultado y medición, colapso, regulación de velocidad y bucle autónomo |
| `nilo_runtime/application/operation_dispatch.py` | Acción documental tipada de etapa 06, sin fabricar ni modificar materia |
| `nilo_runtime/storage/timeline.py` | `TimelineStore` y codec JSON comprimido del checkpoint, sin importar un simulador ni el laboratorio; **misma tabla y bytes contractuales** que el almacenamiento anterior |
| `historical_lab.py` | Inspector/replayer de checkpoints anteriores; **reexporta** `TimelineStore` del storage, sin segunda implementación |
| `nilo_runtime/web/http.py` | `Handler`, rutas `/api/*`, lectura de `interfaz.html`, servidor de loopback, ciclo de apertura/cierre y arranque por inyección de un factory de simulación |
| `laboratorio_casos.py` | Traza métodos reales de los casos de uso por ruta relativa dentro del repositorio, sin pretender que siguen definidos en `nilo.py` |

La extracción conserva **los 36 métodos existentes**, su orden interno de operaciones físicas, el contrato `ActionResult` y las reglas de navegación/tiempo de las etapas anteriores. Las clases de caso de uso se componen en `engine.Simulation` sin otro scheduler ni otro `world.execute_action`. El módulo principal pasa de 2.141 líneas a una fachada pequeña; el servidor mantiene el mismo contrato HTTP, pero deja de pertenecer al runtime de aplicación.

La auditoría de equivalencia sobre el commit anterior confirmó que **los 36 métodos trasladados coinciden literalmente** después de deshacer las únicas adaptaciones intencionales: reemplazo de `config/available/route` por los puertos inyectados, parámetro `services` del constructor y nuevo import de `TimelineStore`. El bloque completo de `Handler` también coincide **byte a byte** con el original (6.307 bytes); solo la firma de `main()` admite ahora una fábrica de simulación. No se añadieron temporizadores, rutas físicas ni comportamientos nuevos. Se corrigieron pruebas que inspeccionaban el archivo monolítico para que comprueben los propietarios nuevos, y se hizo obligatorio que las trazas del laboratorio incluyan llamadas efectivas en `decisions.py` y `clockwork.py`.

## 3. Puertos y puntos de acceso

Uso headless en un proceso o programa externo, sin UI:

```python
from pathlib import Path
from nilo_runtime.application.engine import Simulation
from nilo_runtime.application.deps import RuntimeServices

# Puede sustituirse config, available y route para pruebas o un proveedor distinto.
sim = Simulation(db_path=Path("partida_de_prueba.sqlite3"))
try:
    sim.s["paused"] = False
    sim.s["speed"] = 60
    sim.s["person"]["plan"] = [{"op": "wait", "minutes": 5}]
    sim.think = lambda: None     # evitar red en el ejemplo
    sim.tick(0)                  # preparar acción pendiente
    sim.tick(5)                  # consumir 5 minutos del mundo a ×60
    sim.write()                  # mismo snapshot que la aplicación de escritorio
finally:
    sim.conn.close()
```

La API de la fachada sigue siendo `from nilo import Simulation`, `Handler`, `DB`, `initial_state`. Una prueba que asigna `nilo.DB` o aplica `patch.object(nilo,"route",...)` mantiene el comportamiento previo por medio de `RuntimeServices`. El import directo de `engine.Simulation` usa puertos estándar del core sin depender de esos globales de compatibilidad.

Las rutas web y su política de request size, endpoint y validez permanecen en `nilo_runtime/web/http.py`; `Handler.sim` sigue siendo el mismo objeto público para las pruebas HTTP heredadas. El laboratorio de escenarios `laboratorio_casos.run` sigue utilizando `nilo.Simulation` y ahora puede trazar de nuevo `tick`, `plan_ready`, `write` y `event` en sus rutas nuevas.

## 4. Estabilidad de partidas y laboratorio histórico

El codec de `TimelineStore` fue trasladado literalmente a `nilo_runtime/storage/timeline.py`, y `historical_lab.TimelineStore` es un alias de esa clase. Esto corta el ciclo `historical_lab → laboratorio_casos → nilo → engine/session → historical_lab`. Se mantienen idénticos `timeline_checkpoints`, `format`, estado de RNG, timestamp, SHA-256 del blob y método de compresión; ni el agente ni la UI ven las claves privadas. El esquema principal de la partida sigue siendo **v5**, y los replays 0.6.4 utilizan su ruta de reglas históricas.

## 5. Puertas de validación

- [`tests/test_orquestador_07.py`](https://github.com/mxlzz/Nilo/blob/refactor/0.7/tests/test_orquestador_07.py) levanta una simulación desde un **subproceso Python limpio** importando únicamente `nilo_runtime.application.engine`, verifica ausencia de imports `nilo`/`http.server`/`nilo_runtime.web.http`, procesa una acción `wait` y guarda en SQLite; inspecciona el origen de los métodos y la composición en cuatro casos de uso; comprueba reexportación de `TimelineStore`; prueba los viejos hooks `nilo.DB`, `config`, `available`, `route` y un plan idéntico desde ambos entrypoints; comprueba la traza de escenarios.
- [`tools/auditar_orquestador_07.py`](https://github.com/mxlzz/Nilo/blob/refactor/0.7/tools/auditar_orquestador_07.py) busca imports inversos hacia HTTP/UI/fachada desde `application` y `storage`, evita duplicar métodos entre mixins y exige una fachada `nilo.py` pequeña.
- La puerta de `validacion.yml` incluye auditores de arquitectura/ID/operaciones/orquestador, toda la suite, escenarios físicos, ZIP portable **extraído**, cinco procesos con semillas distintas y replay bit a bit de la huella original `9c4d43a5815fb042e06e32789b7dc6606023c3eb0634fe08dd7ad90616dc5c24`.
- La puerta `baseline_07.yml` importa en copias seis partidas sintéticas de 0.5.9.4.2, 0.6.0 y 0.6.4 sin modificar las originales.

**Puerta de salida superada.** La ejecución [#41897149049](https://github.com/mxlzz/Nilo/actions/runs/41897149049) terminó **success** con **727 tests (1 omitido)** y **9 regresiones headless focalizadas**, auditorías de dependencias, identidad, operaciones y orquestador, escenarios físicos, continuidad RNG/IDs en cinco procesos, ZIP portable importable y los dos replays con la huella exacta de referencia `9c4d43a5815fb042e06e32789b7dc6606023c3eb0634fe08dd7ad90616dc5c24`. La ejecución histórica [#41895886906](https://github.com/mxlzz/Nilo/actions/runs/41895886906) terminó **success**, verificando **6/6** SQLite sintéticas de 0.5.9.4.2, 0.6.0 y 0.6.4, intactos los originales, y el auditor de operaciones. Ninguna puerta queda pendiente.

## 6. Límites y deuda transitoria

El motor es **importable y ejecutable sin HTTP/UI**, pero todavía hay partes de `Simulation` que operan sobre `self.s` heredado y servicios de raíz. La extracción por casos de uso preserva esa superficie para migrar las reglas físicas de forma incremental (etapas 08–12), sin forzar una nueva DB ni una API paralela. El `tick` continúa siendo extenso: más adelante sus subrutas físicas se delegarán a módulos de mundo/navegación/recursos, ya preparados por `ActionResult`, `TimePlan` y el registro de operaciones.

La separación de archivos no demuestra por sí sola mejora de autonomía del personaje. Las pruebas longitudinales LLM y de memoria aún corresponden a la etapa 23. Los saves personales privados, `main`, `VERSION` y el release público 0.6.4 siguen fuera de esta rama.

**Etapa 07 cerrada. Siguiente: 08 · Mundo y generación, habilitada y aún no iniciada.**
