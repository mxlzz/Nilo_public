# Nilo 0.7 · Etapa 03 — Resultados, eventos y procedencia verificable

**Fecha:** 4/11/2026. **Rama:** `refactor/0.7`. **Estado: COMPLETADA.** [CI general #41875118726](https://github.com/mxlzz/Nilo/actions/runs/41875118726), commit `37df274b94a34bf0f3ef5c6823049874e43b5572`: success. [Compatibilidad histórica #41874894941](https://github.com/mxlzz/Nilo/actions/runs/41874894941): success. [Plan completo](PLAN_REESTRUCTURACION_NILO_07.md) · [Seguimiento](ESTADO_REESTRUCTURACION_07.md) · [PR draft #155](https://github.com/mxlzz/Nilo/pull/155).

## 1. Auditoría localizada

La referencia 0.6.4 ya contenía `action_results.ActionResult` (`op`, `status`, `success`, `notable`, `facts`, `duration_minutes`, `physical`), un adaptador de `world.execute_action` con tupla de cuatro campos, `experiment_log.measure` con medición numérica y `inventions.record_action_outcome` con identificador `act-...`. Por tanto, **no** se creó un segundo sistema de ejecución ni se atribuye a 0.7 la introducción original de la tipificación. Se auditó el camino:

`world.execute_action` (retorno heredado) → `environments.IslandEnvironment.perform_result` → `action_results.result_from_execution` → `Simulation._tick_slice` → medición `med-...` → resultado `act-...` → historia, contrato físico y experiencia → eventos de texto.

### Problemas concretos confirmados

- **E01 · Retorno heredado disperso.** El handler de mundo retorna `(minutos, mensajes, éxito, relevancia)`. La conversión ya se hacía al nivel del entorno, pero `nilo.py` volvía a utilizar `.as_legacy()` en ramas de ascenso, recolección y ejecución ordinaria: se perdía semántica tipada en pleno coordinador.
- **E02 · Pérdida de estado al combinar desplazamiento y acción.** Para `gather` remoto, después de caminar el código combinaba mensajes y reconstruía `ActionResult.from_legacy` sin arrastrar el `status` del resultado físico. Se preserva explícitamente. `ascend` también transporta ahora el resultado interno tipado, incluyendo evidencia física cuando existe.
- **E03 · Las mediciones y eventos se podían leer por separado sin causalidad explícita.** `measure` registra cambios `inventory_delta`, `needs_delta`, conteos y posiciones; `record_action_outcome` guarda un ID; `self.event` guarda texto. La relación entre los tres no aparecía como objeto causal reutilizable y verificable.
- **E04 · Aprendizaje moderno parcialmente dependiente del texto.** Aunque `gather` y `forage` ya verificaban incrementos reales, `habits.record_skill` reconocía `drink` por «bebí» y `craft` por «fabriqu» en `facts`. Esos verbos no demuestran acción material. El bootstrap de archivos históricos aún reconoce expresiones antiguas, caso distinto que no debe reinterpretarse retroactivamente.
- **E05 · `ActionResult` no pertenece a física ni al agente.** Su definición estaba en `action_results.py`, que también consulta funciones físicas de flotación/contención; esto impide importar el tipo desde `core` sin arrastrar dependencias.
- **E06 · Diferentes concepciones de éxito.** Una operación documentada, una acción física ejecutada y una hipótesis física verificada no son el mismo hecho. La etapa conserva los cuatro `status` compatibles existentes, **no** interpreta un texto favorable como una propiedad demostrada y adjunta únicamente diferencias observadas a un evento de medición.

## 2. Contratos y cambios implementados

| Fuente | Responsabilidad luego del cambio | Compatibilidad |
| --- | --- | --- |
| `nilo_runtime/core/outcomes.py` | `ActionResult` único; `LegacyExecution` valida la tupla al límite; `RecordedEffect` y `CausalActionEvent` con `action_id`, `measurement_id`, `unmodeled_attempt_id`, estado y variaciones medidas | Solo biblioteca estándar; no importa mundo, física, LLM ni SQLite. `ActionResult.to_record()` conserva **exactamente** su contrato histórico |
| `action_results.py` | Adaptador de física heredada y captura de evidencia específica del motor; reexporta la misma clase `ActionResult` | Consumidores anteriores pueden seguir usando `from action_results import ActionResult` |
| `nilo.py` | Consume propiedades tipadas del resultado sin desarmarlo; crea `causal_event` una vez que existen `act-...` y `med-...`; enlaza `action_id` y `measurement_id` a los eventos de resultado y, cuando proceda, novedades | Solo en ejecuciones modernas; en `historical_replay` o `legacy_replay_rules` la estructura anterior se mantiene **intacta** para conservar fingerprints |
| `habits.py` | En ejecuciones modernas, aprende `drink` desde `ActionResult.verified_success` y `craft` desde éxito más **objeto nuevo medido**, sin verbos; recolección ya se comprobaba por inventario | El camino histórico sin resultado tipado conserva la semántica previa para migración y replays, sin reinterpretar evidencias antiguas |
| `MANIFIESTO_SHA256.json` | Incluye `nilo_runtime/core/outcomes.py` | El smoke de ZIP comprueba que esté presente antes de abrir el paquete |

### Qué significa «evento causal» en esta etapa

`causal_event_from_measurement(action_id, resultado, medición)` solo se puede construir con un `ActionResult` consistente, un ID de acción real y, cuando existe, una medición cuyo `id`, `op` y `evaluation_status` corresponden a esa ejecución. Solo incorpora deltas del inventario, necesidades, cantidad de objetos/obras y posiciones **contenidos en la medición**. Si no hay medición, `effects=[]` y `measurement_id=null`; el texto nunca se transforma en un incremento material ficticio. Un fallo puede tener costo físico observado. `no_evaluable` puede enlazar el ID de un intento que el motor registró, sin convertirlo en un fracaso experimental. No se generan nuevos IDs para la relación.

Un `status=verified_success` informa que el handler completó su operación; **no** prueba una función de una construcción ni una ley general. Para ello continúan siendo necesarias mediciones, criterios y ensayos por ID. La pantalla puede mostrar `facts`, pero los diagnósticos deben usar `status`, `physical`, `causal_event` y `measurement`.

## 3. Contraste con la referencia e integridad

Pruebas de etapa [`tests/test_eventos_07.py`](https://github.com/mxlzz/Nilo/blob/refactor/0.7/tests/test_eventos_07.py):

- Solo una clase `ActionResult` para imports nuevos/legados; adaptador de cuatro campos estable.
- Contradicciones entre `success` y `status` rechazadas al convertir; duraciones inválidas rechazadas.
- El texto «FÍSICA NO IMPLEMENTADA» por sí solo **no** convierte un fallo en `no_evaluable`; exige marcador de estado.
- Evento con diferencias físicas y vínculo real; sin medida, no se inventa variación; rechazo de referencias incorrectas y números no finitos.
- Aprendizaje de beber/fabricar por resultado físico verificado, incluso con relatos que no contienen palabras clave.
- Integración con `Simulation`: `action_outcomes`, `measurements` y eventos narrativos comparten IDs coherentes al completar una acción.
- El auditor de imports y el verificador del paquete ZIP siguen siendo obligatorios.

**Verificación ejecutada:** [CI #41875118726](https://github.com/mxlzz/Nilo/actions/runs/41875118726) pasó **680 pruebas (1 omitida)**, auditor estructural, escenarios físicos, importación desde ZIP extraído y dos replays con fingerprint idéntico `9c4d43a5815fb042e06e32789b7dc6606023c3eb0634fe08dd7ad90616dc5c24`. [CI #41874894941](https://github.com/mxlzz/Nilo/actions/runs/41874894941) probó la apertura de seis SQLite sintéticos históricos desde tres versiones usando el runtime refactorizado. Estos ensayos no representan corridas reales prolongadas de LLM.

## 4. Límite explícito de migración

- Los handlers internos de `world.execute_action` siguen retornando tuplas para quienes los importan directamente. El núcleo nuevo rechaza tuplas malformadas y **el único puente recomendado** es `IslandEnvironment.perform_result`. Retirar retornos y consumidores internos de `world` requiere la etapa 06 (registro de operaciones), 07 (orquestador) y 12 (handlers de construcción). No crear un segundo dispatcher.
- `experiment_log.measure` conserva el fallback `laboratory.measured_physics`, que incluye comprobaciones de texto para llamadas sin `ActionResult`; la ruta normal de `Simulation` **siempre** le entrega el resultado tipado. Eliminar ese fallback exige migrar tests y consumidores heredados antes de descartarlo, sin modificar la línea base.
- `bootstrap_skills` extrae hechos de archivos muy antiguos escritos solo en texto, de forma **explícitamente histórica**. La nueva ejecución usa diferencias de inventario o resultado físico.
- Los hechos y la selección de evidencias para cierre de proyectos siguen en `goal_evidence` / `project_lifecycle` y se reestructurarán en etapas 16–17. La adición de `causal_event` no significa que un proyecto pueda cerrarse automáticamente por un texto.
- IDs nuevos reproducibles y la eliminación del RNG global pertenecen al paso 04; duraciones/fases y efecto anticipado de `gather` pertenecen al 05/10. Este paso no cambia tiempos ni física de acciones.
- Los registros causales nuevos se generan solo para ejecuciones modernas, sin reescribir de forma retrospectiva las partidas antiguas ni los replays.

## 5. Puerta de salida

**Puerta de salida superada**: CI general y de compatibilidad histórica exitosos, suite, replay y ZIP verificados. [Registro de avance](ESTADO_REESTRUCTURACION_07.md) e issue maestro #151 actualizados. El programa en `main`, el release 0.6.4 y las partidas privadas no se modifican. **La etapa 04 — Identidades y aleatoriedad — queda habilitada, todavía no iniciada.**
