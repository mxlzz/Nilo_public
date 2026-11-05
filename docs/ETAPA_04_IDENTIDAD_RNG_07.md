# Nilo 0.7 · Etapa 04 — Identidades y aleatoriedad

**Fecha:** 4/11/2026. **Rama:** `refactor/0.7`. **Estado: COMPLETADA.** [CI integral #41884761716](https://github.com/mxlzz/Nilo/actions/runs/41884761716) sobre commit `e6baaff096a7d00620c06e7acf6e329efd4202d5`: **success**. [CI histórico #41883891361](https://github.com/mxlzz/Nilo/actions/runs/41883891361): **success**, seis partidas sintéticas reabiertas. [Plan maestro](PLAN_REESTRUCTURACION_NILO_07.md) · [Etapa 03](ETAPA_03_EVENTOS_07.md) · [#143 — defecto de identidad global](https://github.com/mxlzz/Nilo/issues/143).

## 1. Diagnóstico del motor 0.6.4

En la versión de partida auditada:

- `Simulation.__init__` **resembraba** `self.rng` en cada reapertura mediante `9821+int(clock_minutes)`, en vez de restaurar su secuencia. Aunque conservara la misma semilla del mundo, el siguiente `explore/go` no partía necesariamente del mismo estado PRNG que un run continuo.
- `world.make_item` generaba `obj-<numero>` con `random.getrandbits(52)` **global**; `world.execute_action` generaba `obra-N-<numero>` con `random.getrandbits(16)` **global**, ignorando el objeto `rng` explícito que recibía la acción. El defecto está documentado en [#143](https://github.com/mxlzz/Nilo/issues/143): mismo mundo/acción/RNG local, ID de obra diferente si cambia `random.seed()`.
- **31 llamadas a `uuid.uuid4()`** en `nilo.py` (13) y 11 módulos relacionados (18), para proyectos, cuaderno, mediciones, diseños, conclusiones, resultados, piezas, predicciones y archivo.
- `world.new_world(seed)` ya creaba un `random.Random(seed)` **local** para la topología: se conserva; sus mapas no deben depender de otros RNG.
- `historical_lab.TimelineStore` ya guardaba `rng.getstate()` y `random.getstate()` en checkpoints, pero `Simulation` no restablecía un registro persistente de ambas secuencias desde el snapshot ordinario.
- `reproducir.py` reemplazaba explícitamente `uuid.uuid4()` y controlaba `random.seed` para reproducir huellas históricas; no debe alterarse esa semántica en los rulesets ya publicados.
- `providers.py` utiliza `random.random()` exclusivamente para introducir jitter en reintentos HTTP; **no** pertenece al RNG físico ni a la identidad del mundo. Se deja deliberadamente fuera de la secuencia simulada.

## 2. Arquitectura implementada

| Lugar | Contrato nuevo | Consecuencia |
| --- | --- | --- |
| `nilo_runtime/core/identity.py` | `EntropySession`: dos generadores independientes (`agent_rng`, `id_rng`) y contadores serializables para UUID y objetos físicos; funciones `new_uuid`, `id_bits`, `physical_suffix`, `entropy_scoped` | Ninguna dependencia de física, prompts, SQLite o del tiempo; IDs de un mundo no consumen el RNG de exploración |
| `nilo_runtime/storage/entropy.py` | Tabla SQLite `runtime_entropy` con el estado de los dos RNG, contadores, semillas y SHA-256 del JSON del snapshot | Se escribe **en la misma transacción** del snapshot. Se rechaza un checkpoint dañado o un snapshot moderno reescrito sin su estado de RNG |
| `Simulation` | Inicializa/restaura la sesión RNG antes de migraciones; `self.rng` usa ese estado; `write()` guarda entropía y snapshot juntos; `tick`, `plan_ready`, `journal`, `event`, `observer_summary`, `migrate`, `start_chat` operan vinculadas a su mundo | Reanudar una partida 0.7 desde un save íntegro continúa la secuencia de valores e IDs exactamente desde donde se guardó |
| Hilos de deliberación y chat | `_run_entropy_worker` vincula la identidad a cada thread (un `ContextVar` no se hereda automáticamente) | Las decisiones y el chat consumen la secuencia correcta de la partida, sin un generador mutable global compartido entre sesiones |
| 11 módulos heredados de registros y mediciones | Importan `new_uuid` en lugar de llamar directamente a `uuid.uuid4()` | Mantienen el formato de IDs conocido, pero los IDs nuevos vienen del generador propio del mundo; fuera de una sesión usan fallback de compatibilidad |
| `world.py` | `make_item(..., rng=None)` y `execute_action(..., rng)` usan `physical_suffix`; los IDs modernos tienen sufijo numérico monotónico en un namespace `>= 2**96`; las llamadas directas usan el RNG explícito | La identidad de build/craft deja de depender de `random.seed()` global. El contador evita repetir IDs después de retirar o desmontar obras y no colisiona con sufijos oficiales antiguos (16/52 bits) |
| `historical_lab.py` | Un checkpoint de la nueva rama incluye también `entropy_state` y lo restaura durante una reproducción local; checkpoints antiguos mantienen la ruta global anterior | Mayor repetibilidad de pruebas nuevas, sin inventar UUID históricos anteriores que nunca quedaron registrados |
| `tools/auditar_identidad_07.py` | Revisa llamadas a RNG global/UUID4 en módulos del dominio; se ejecuta en CI | No permite que un parche posterior reintroduzca `random.getrandbits` o `uuid.uuid4` global en rutas del motor |

La serie `uuid4` moderna conserva el tipo `UUID` y el aspecto de los registros. Los primeros ocho caracteres siguen una permutación biyectiva del contador; son distintos entre sí durante las primeras `2**32-1` asignaciones del mismo mundo. El contador, el estado de RNG del agente y la serie de identificadores se guardan junto con el snapshot. La numeración física moderna ocupa un namespace distinto del histórico y avanza monotónicamente por partida.

**Sin cambios en** `VERSION` ni en el esquema JSON del save v5; el nuevo metadato está en la misma SQLite, pero fuera de `person` y `world`, sin inyectarse al LLM. La creación de un mundo con `world_seed` fijo sigue usando el mismo generador topológico anterior.

## 3. Casos especiales y seguridad de datos

1. **Partidas existentes anteriores a 0.7:** no hay estado RNG reproducible en sus snapshots. Se aplica la semilla de reapertura histórica y se identifica expresamente como `legacy_seeded_without_history`; desde el primer guardado en esta rama, las futuras reanudaciones podrán ser exactas. No se promete recuperar la secuencia anterior.
2. **Saves antiguos reimportados en la misma SQLite:** si el snapshot se sustituyó por datos con **marcas de migración antiguas ausentes**, se considera una reimportación histórica y se inicia una nueva secuencia `legacy_reimported_without_history`, sin afirmar que es continuidad exacta. Es el caso cubierto por las pruebas de migración de 0.5.2.
3. **Mundo vacío con semilla editada:** se permite resembrar *únicamente* si todavía no hay tiempo ni objetos, proyectos, mediciones o eventos históricos; de lo contrario se rechaza para no falsificar una continuidad física.
4. **Corrupción o cambio de un save moderno:** si el `snapshot_sha256` y el checkpoint RNG no coinciden, no se resembrará silenciosamente. Se conserva el archivo y se informa la discrepancia. Un motor 0.6.4 que vuelva a guardar un snapshot modernizado dejaría la secuencia anterior fuera de sincronía; se debe trabajar siempre sobre copia/backup compatible, no alternar motores sobre el mismo archivo.
5. **Replays de referencia:** `historical_replay` y `legacy_replay_rules` evitan activar los generadores nuevos y permiten los `uuid4` y `random.getrandbits` antiguos; esto se controla con dos huellas históricas independientes del hash de Python.
6. **Resultados de modelos externos:** una secuencia RNG de mundo exacta **no** permite declarar reproducible una corrida LLM real si varían respuestas, latencias, proveedor o entradas externas.

## 4. Puertas de validación

[`tests/test_identidad_07.py`](https://github.com/mxlzz/Nilo/blob/refactor/0.7/tests/test_identidad_07.py) cubre: IDs diferentes tras miles de asignaciones, restauración exacta de `Random.getstate/setstate`, semilla estable, separación de IDs y RNG de exploración, concurrencia aislada por hilo, rechazos de estado corrupto, colisión por desmontaje, reanudación desde SQLite, edición de semilla, importación histórica reconocida, checksum obsoleto rechazado, replay con UUID parcheado, checkpoint nuevo con identidad, y el caso #143 de RNG global diferente frente a `build` con RNG explícito.

[Workflow `validacion.yml`](https://github.com/mxlzz/Nilo/actions/workflows/validacion.yml): suite unitaria y escenarios físicos, auditor de dependencias, nuevo auditor de RNG global, ZIP distribuible extraído, replays con fingerprint `9c4d43a5815fb042e06e32789b7dc6606023c3eb0634fe08dd7ad90616dc5c24`. [Workflow `baseline_07.yml`](https://github.com/mxlzz/Nilo/actions/workflows/baseline_07.yml): importación sin alterar seis SQLite sintéticas de 0.5.9.4.2, 0.6.0 y 0.6.4, replays y respaldo.

**Validación aprobada:** [run #41884761716](https://github.com/mxlzz/Nilo/actions/runs/41884761716) terminó **success** con **696 tests, 1 omitido**, auditor de arquitectura e identidad, escenarios físicos, reproducción desde un checkpoint con formato 0.6.3, ZIP extraído, dos fingerprints históricos idénticos y ensayo en **5 procesos independientes** con `random.seed` y `PYTHONHASHSEED` distintos. El reporte confirmó `global_seed_independent=true`, `python_hashseed_independent=true`, `resumed_equals_continuous=true`. [Run de compatibilidad #41883891361](https://github.com/mxlzz/Nilo/actions/runs/41883891361): **success**, las seis partidas históricas sintéticas se abrieron en copias y se conservó el original. Las fallas transitorias de CI durante el desarrollo (migración de fixtures y checksum sincronizado) fueron corregidas; no se consideran la línea base aprobada.

## 5. Límites de esta etapa

- Los métodos llamados directamente fuera del contexto de una `Simulation` conservan APIs históricas: `world.execute_action` utiliza su RNG explícito para ID físico; `make_item` sin RNG y funciones de archivo sin sesión pueden usar generación aleatoria heredada.
- Los checkpoints anteriores no incluían estados de `uuid.uuid4` de `os.urandom`. La reejecución exacta de sus UUID **no es recuperable**; el laboratorio puede comparar efectos físicos.
- No se cambian leyes físicas, chances, geometría, estados de ánimo ni tiempos de acciones; solo la procedencia de sus secuencias y IDs.
- La migración modular del mundo, el orquestador y el respaldo de partidas largas continúan en pasos 06–12 y 18. Las pruebas actuales no sustituyen corridas longitudinales de LLM de etapa 23.

**Puerta de cierre superada.** Ambos workflows de CI verdes, fingerprint del replay `9c4d43a5815fb042e06e32789b7dc6606023c3eb0634fe08dd7ad90616dc5c24` íntegro, importación histórica sintética sin pérdida, ejecución física desde un checkpoint de formato 0.6.3 verificada, reanudación RNG/IDs igual al proceso ininterrumpido, sin cambiar `main`, `VERSION` ni partidas privadas. **Etapa 05 (reloj y tiempo) habilitada; no iniciada.**
