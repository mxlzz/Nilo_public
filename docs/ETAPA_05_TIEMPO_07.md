# Nilo 0.7 · Etapa 05 — Reloj y ejecución temporal

**Fecha:** 4/11/2026 · **Rama:** `refactor/0.7` · **Estado: COMPLETADA.** [CI integral #41888419832](https://github.com/mxlzz/Nilo/actions/runs/41888419832), commit `ae11f74b2e256aa1dbe1fb3c0e96094a108f032a`: **success**. [Compatibilidad histórica #41888419813](https://github.com/mxlzz/Nilo/actions/runs/41888419813): **success**, seis partidas sintéticas abiertas. [Plan maestro](PLAN_REESTRUCTURACION_NILO_07.md) · [Issues #141](https://github.com/mxlzz/Nilo/issues/141) y [#142](https://github.com/mxlzz/Nilo/issues/142).

## 1. Auditoría de 0.6.4 y anomalías concretas

Nilo maneja cuatro escalas diferentes: segundos reales de `time.monotonic()` para el loop; minutos simulados en `person.clock_minutes`; segundos base restantes de escritura (`remaining_real`) y minutos previstos de acciones físicas (`pending.total/remaining`). Un cooldown de proveedor, la cuota real y la hora de guardado son **tiempo de pared**, no eventos del mundo.

| Magnitud | Unidad y fuente anterior | Hallazgo |
| --- | --- | --- |
| Velocidad | `timing.effective_speed` con ×1, ×10, ×60 y ×80; escritura como máximo ×2; consulta LLM ×1 sin acción pendiente | La escala del reloj funciona, pero carecía de un contrato de fases reutilizable |
| Inicio de acción | `_tick_slice` crea `pending` con `total` y `remaining` a partir de `ACTION_DURATIONS`, descanso solicitado y fatiga | `total` es una **estimación de trabajo**, no la duración declarada por el handler |
| Navegación | `start_navigation` reemplaza `pending.total` por `len(route)*travel_minutes_per_tile` | Para `go/explore` equivale al viaje; para `gather` **pierde el trabajo de extracción** (#142) |
| Acreditación de efectos | `environment.perform_result` ocurre cuando `remaining<=0` | En `gather` remoto el inventario aumenta en cuanto llega, sin que transcurra el trabajo |
| Resultados | `action_result.duration_minutes`, `measurement.duration_minutes`, `pending.total` | No miden el mismo intervalo y el archivo anterior no especificaba sus distintas responsabilidades (#141) |
| Interrupción | Colapso borra `pending` y `plan` | Guardaba operación/minutos parciales pero no fase de viaje/trabajo ni duración prevista desagregada |
| Guardado | `snapshot` JSON en SQLite | `pending.remaining` y `clock_minutes` sobreviven a reinicios; no deben recalcularse con `time.time()` salvo migraciones especiales de escritura |
| Espera sin tareas | `auto_wait_frozen` detiene el mundo cuando no hay acciones y el proveedor no responde | El cooldown externo debe continuar en reloj real; no se acelera con el mundo |

**Consecuencia:** el dato «`action_result.duration_minutes=22`» de una extracción puede coexistir legítimamente con `pending.total=20` como estimación de trabajo, o `measurement.duration_minutes=35` si se caminó 15 minutos. Nunca corresponde sumar «duración del handler» a la medición otra vez ni describirla como duración efectivamente observada.

## 2. Contrato de dominio implementado

[`nilo_runtime/core/clock.py`](https://github.com/mxlzz/Nilo/blob/refactor/0.7/nilo_runtime/core/clock.py) define funciones puras:

- `clamp_real_elapsed`: avanza hasta 20 segundos reales por iteración para evitar que una suspensión del proceso «pague» trabajo futuro al reanudar. Rechaza tiempos negativos, infinitos y NaN en ejecuciones modernas.
- `TimePlan` / `plan_time`: separa `planned_travel_minutes` y `planned_work_minutes`; `planned_total_minutes=travel+work`. `go`, `explore` y otras navegaciones son viajes sin trabajo agregado artificialmente.
- `phase_progress`: calcula progreso desde `pending.total`, `pending.remaining` y tiempos previstos **guardados**, sin consultar reloj real, nombres de acciones ni narración de Nilo.
- `completion_contract`: emite `status=completed|blocked|interrupted`, duración total/travel/work prevista y transcurrida, duración **medida** del reloj y duración **declarada** por el handler. Son campos independientes. `work_phase_completed` indica cumplimiento del tiempo de trabajo, **no** si la operación obtuvo éxito físico.

No se crea un nuevo reloj, un segundo sistema de acciones ni un planificador autónomo paralelo. `Simulation` mantiene la autoridad sobre el avance físico. Los helpers solo hacen explícitos los cálculos y registros.

## 3. Cambios de ejecución

- [`nilo.py`](https://github.com/mxlzz/Nilo/blob/refactor/0.7/nilo.py) agrega `pending.timing` **solo para acciones nuevas** con versión interna 1 y fase actual. No altera el esquema principal de save v5 ni los formatos de acciones ya existentes.
- **`gather` con navegación:** el estado inicial programa `viaje + trabajo de extracción`. Al alcanzar la fuente solo se completa la fase `travel`; durante `work` no se consume depósito ni aumenta inventario. `perform_result(gather)` se ejecuta al concluir ambas fases. La fatiga sigue aplicando a viaje y trabajo. Una ruta bloqueada cancela la ejecución y no concede materiales.
- **`gather` adyacente:** mantiene un solo bloque de trabajo; no existe viaje fantasma. El trabajo previsto es `ACTION_DURATIONS['gather']*fatigue_multiplier`. La duración que declare el handler tras extraer puede diferir del estimado; queda etiquetada como `handler_declared_minutes`.
- **`go` / `explore` / otras navegaciones:** conservan el total de viaje y sus efectos por casillas vencidas. No se agrega una segunda fase ficticia. `due` se calcula solo con `elapsed_travel_minutes`, sin mover posiciones al consumir trabajo posterior de `gather`.
- **Acciones estacionarias:** `build`, `craft`, `rest`, `interact`, `wait` y demás mantienen los minutajes previos, ahora marcados como trabajo planificado; sus resultados siguen ocurriendo únicamente al terminar.
- **Colapso por energía:** en ruta moderna se registra `interrupted_by_collapse.time_contract` con fase y tiempo consumido, sin invocar handler ni conceder materiales. El descenso de necesidades hasta el colapso es una consecuencia real del tiempo transcurrido.
- **Mediciones y outcomes:** nuevas `measurement.time_contract` y `action_outcomes.time_contract` identifican la relación entre duraciones. El campo `physical_result.duration_minutes` y `ActionResult.to_record()` **no cambian de significado** para no reinterpretar registros anteriores.
- **Observador:** `public_state.activity_timing` expone la fase y tiempo restante para la actividad en curso; no se inyecta en forma de regla al LLM. `pending.total/remaining` permanecen utilizables por la interfaz anterior.
- **Tiempo externo:** no se acelera el cooldown LLM, `MAX_LLM_CALLS_PER_DAY`, llamadas de proveedores, tiempo de chat ni duración real del programa. La escritura mantiene máximo ×2. El tiempo apagado no cuenta como trabajo transcurrido, salvo reglas legadas de migración.

## 4. Preservación explícita de replays y saves

Los replays `historical_replay` y `legacy_replay_rules` mantienen el algoritmo original de `tick` y la programación original de `gather`: **no se reescriben los históricos para hacerlos parecer correctos**. Las partidas anteriores que se encuentren con un `pending` sin `timing` conservan los minutos restantes antiguos; las fases nuevas solo rigen acciones iniciadas en 0.7. Las partidas largas que hayan ejecutado recolectas anteriores conservan sus mediciones y evidencias.

## 5. Ensayos y criterios de cierre

[`tests/test_tiempo_07.py`](https://github.com/mxlzz/Nilo/blob/refactor/0.7/tests/test_tiempo_07.py) incorpora pruebas puras de planificación y duración, recolección distante y adyacente, viaje `go` sin trabajo adicional, ruta bloqueada, colapso a mitad de extracción, reanudación SQLite en fase `work`, trabajos múltiples que no acreditan construcciones anticipadas, pausa real y cambio a ×80 sin saltar trabajo, límites de velocidad y selección ×2 de escritura.

La puerta de salida exige: suite completa + escenarios físicos + auditor de arquitectura + ZIP portable + dos replays históricos con huella `9c4d43a5815fb042e06e32789b7dc6606023c3eb0634fe08dd7ad90616dc5c24`, y reimportación sin alterar originales de seis saves sintéticos de 0.5.9.4.2/0.6.0/0.6.4.

**Comprobado:** [CI #41888419832](https://github.com/mxlzz/Nilo/actions/runs/41888419832) completó **709 tests (1 omitido)**, con auditor de arquitectura e identidad, cinco procesos con RNG independiente, escenarios físicos, arranque desde ZIP extraído y dos replays que conservaron exactamente la huella `9c4d43a5815fb042e06e32789b7dc6606023c3eb0634fe08dd7ad90616dc5c24`. [CI #41888419813](https://github.com/mxlzz/Nilo/actions/runs/41888419813) importó **6/6 partidas sintéticas históricas** desde copias sin alterar originales. Las regresiones temporales de pruebas de itinerarios iniciales se corrigieron antes del cierre: corredor efectivamente transitable, selección controlada de fuente de madera y propagación de la duración del handler por el coordinador.

## 6. Deuda relacionada, fuera de esta etapa

El tiempo de ejecución declarado por `world.execute_action` deriva de las reglas internas de cada operación. En muchos casos es diferente del **estimado previo**, sin que eso por sí mismo indique un reloj averiado. Esas discrepancias quedan explícitas en el contrato; la ejecución por fases de cada handler físico se revisará con la descomposición de operaciones/dispatcher (etapas 06–12). La historia física posterior no se puede reconstruir desde textos antiguos, y el reinicio del programa no puede hacer transcurrir una fase de trabajo no ejecutada.

No se declara mejora de comportamiento LLM por estos tests deterministas; la evaluación de autonomía corresponde a la etapa 23.

## 7. Cierre y próximos límites

La etapa 05 **superó su puerta de salida**. El tiempo de trabajo de una extracción remota se contabiliza junto al viaje y se puede interrumpir sin acreditar material futuro; los registros nuevos informan fase y duración medida sin sobrescribir la historia previa. Los IDs, física y términos del catálogo no se modificaron más allá de la propagación de la duración que ya declaraba el handler en recolección/ascenso modernos. El reloj en reposo, la pausa, el guardado intermedio y los cooldowns reales conservan sus roles distintos. No se promete que una **estimación** de trabajo sea igual a lo que luego declare el handler: ambas cifras son deliberadamente etiquetadas y distintas.

**Etapa 06 — Contratos y registro de acciones — habilitada; aún no iniciada.** `main`, `VERSION` y partidas personales intactos.
