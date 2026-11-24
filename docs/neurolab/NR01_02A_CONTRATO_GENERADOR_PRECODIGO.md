# NeuroLab NR01.02a — especificación exacta del generador para software de control

**22/11/2026, ANTES de implementar `nr01_worlds.py` y antes de observar datos de una cohorte.** Es una adenda de ingeniería que cierra semillas, secuencias y formatos del [preregistro principal](NR01_02_PREREGISTRO_DESAFIO_20261122.md); **no modifica ecuaciones, tamaño de cohorte ni criterio científico**.

## 1. Función determinista y particiones

- Serie de enteros para crear PRNG independiente: `seed_for(world_seed, family, phase, stage) = world_seed*1000003 + family_code*10007 + phase_code*1009 + stage*17`.
- `family_code(A)=1`, `family_code(B)=2`; `phase_code(parameters)=11`, `unsupervised=23`, `feedback=37`, `reversal=41`, `feedback_b2=43`, `test=47`; `stage` entero no negativo reservado para distintos lotes o presupuesto.
- `random.Random(seed_for(...))`; `random.choice((-1,+1))` para patrones ocultos `p,q,u,v,w` en el orden lexicográfico de factores e índice; para ruido `rng.uniform(-0.06,+0.06)` **16 llamadas por observación**; separado del RNG del orden.
- El orden de casos se hace con PRNG `seed_for(world_seed,family,phase,stage)`; el ruido se genera con PRNG `seed_for(world_seed,family,phase,stage+100000)` para que no haya dependencia entre permutación y ruido. Los patrones ocultos usan `seed_for(world_seed,family,parameters,0)`.
- Algoritmo de balanceo: enumerar las combinaciones admisibles en orden lexicográfico, repetir todas `floor(n/k)` veces, elegir para las posiciones remanentes `n mod k` combinaciones sin reemplazo usando `rng.sample`, y finalmente `rng.shuffle`. La diferencia entre frecuencias de cada combinación será como máximo una.
- Particiones: `(family=A, z,c)` train si `c != (z+3)%4`; test en caso contrario. `(family=B,a,b,c)` train si `a!=b`; test `a==b`.
- Fases con conteos: unsupervised n=1200; feedback n=64 (reutilizar prefijos8/16/32 sin regeneración), reversal n=64 solo A, feedback_b2 n=64 solo B, test n=160 para A y n=120 para B. Para comparar estados tras etapa de entrenamiento y reversión, usar prefijos comunes de entrenamiento y la **misma cinta test de lectura** congelada.
- Ningún código de pruebas puede generar `24000..24019` accidentalmente: `make_tape` rechazará estas semillas por defecto; requiere flag `allow_confirmation=True` solo para la futura unidad NR01.05 tras freeze. Semillas históricas `1400..1419` se rechazan siempre en NR01.
- Para tests matemáticos y software usar únicamente semillas artificiales `0,1,42`; **no son cohorte de desarrollo**. Las 23000..23019 solo se usarán cuando empiecen ensayos científicos.
- El dato que llega al modelo es exclusivamente `tuple(x[0..15])`; `latents` y función `target` permanecen en un objeto de caso **del evaluador**, no pasan en argumentos a encoder/decoder.

## 2. Invariantes a verificar antes del primer ensayo

- A unsupervised: 1200 casos, exactamente100 por cada una de las12 combinaciones; A test: 160, 40×4 combinaciones retenidas.
- B unsupervised: 1200 casos, exactamente50 por cada una de las24 combinaciones; B test:120, 10×12 retenidas.
- Todos los vectores 16 reales entre0 y1; deterministas para igual seed/phase/stage; dos fases/semillas distintas con cintas distintas; fronteras train/test disjuntas en factores sin exponerlos a modelos.
- Fijar una huella SHA256 de la serialización canónica de una cinta de prueba seed42, `json.dumps([...],sort_keys=True,separators=(",",":"))`; mantenerla como fixture cuando se haya generado por el código y confirmado además con un cálculo independiente.
- Dejar la tarea B1/B2 y A original/invertida implementadas únicamente en `target_for_evaluator`; no importar el evaluador desde la implementación de modelos.
- Tests sin ejecución de entrenamiento ni importación de `artlib`, `river` o `scikit-learn`; sus APIs/versiones se verificarán en una unidad posterior.

**Semáforo:** preregistro de generador **cerrado**, sin pretender validación empírica. Es legítimo implementar solo generador y tests ahora; NO entrenar modelos ni mirar holdouts confirmatorios.
