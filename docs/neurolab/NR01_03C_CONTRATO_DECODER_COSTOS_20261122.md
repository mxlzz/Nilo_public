# NR01.03-C — contrato previo a ensayos: decoder, exposición y coste

**22/11/2026 · ESPECIFICACIÓN PRE-CÓDIGO, NO RESULTADO EXPERIMENTAL.** Depende de NR01.02/02a y NR01.03-B. Esta unidad no consume semillas 23000..23019 ni 24000..24019, ni valida transferencia. Es una propuesta técnica congelable mediante tests toy antes de correr ciencia. Los cambios posteriores requieren adenda explícita anterior al ensayo afectado.

## Pregunta y límites

Comparar **ARTlib FuzzyART** y **MiniBatchKMeans** contra controles no privilegiados, sin entregar clases latentes ni un decoder desproporcionadamente potente. El aprendizaje no supervisado ocurre solo en 1200 observaciones; las fases con recompensa actualizan exclusivamente el decoder, nunca encoder. El evaluador entrega al agente exclusivamente `tuple[float, ...]` (16D), no `EvaluatorCase`, semilla, fase, contexto o acción correcta.

## Interfaz exacta propuesta

- `observe_unlabelled(x: tuple[float, ...]) -> None`: modifica solo estado encoder; prohibido consultar premios.
- `freeze_encoder() -> None`: congela normalizadores y prototipos, retiene el estado reproducible.
- `encode_read_only(x) -> tuple[float, ...] | None`: no modifica ni crea categorías ni contadores; `None` significa representación no asignable, nunca etiqueta verdadera.
- `choose(x) -> ("D0"|"D1")`: lee encoder y decoder; empate determinista D0, sin semilla privilegiada.
- `apply_reward(x, chosen_action, reward: int) -> None`: solo después de elegir, y solo con `reward in {-1,+1}`; en dos acciones, el objetivo binario puede inferirse de (acción,premio), **idénticamente para todos**.
- `snapshot() -> bytes` y `restore(bytes)`: mismo resultado y trayectoria tras reanudar, incluyendo estado de RNG y preprocesamiento.

**Fases:** cada modelo nuevo reinicia su estado al cambiar de mundo; en una familia conserva encoder durante feedback y reversión/tarea B2. A: un mismo decoder para original y reversión, sin aviso de cambio. B: decoder independiente para B1 y B2, mismo encoder congelado, para probar reutilización; B2 no recibe parámetros del decoder B1. En cada presupuesto 8/16/32/64 se evalúa el prefijo de la misma cinta desde un estado inicial equivalente; nunca continuar de 8 a 16 duplicando ejemplos.

## Encoder y categoría

- **Raw lineal:** `phi=(x[0],...,x[15],1)`, 17 coordenadas; no usa adquisición no supervisada. Es un baseline competitivo, no una versión deliberadamente debilitada.
- **ART:** entrada16D fija en [0,1]; complemento16→32 tal como ARTlib; `rho={.60,.80,.90}`, `alpha=.001`, `beta=1`. Identificador de categoría para decoder **one-hot de 16 posiciones + bias 1**; observar y memorizar el mapeo categoría→slot en orden de creación, sin usar factores ocultos. Categorías >16: estado `over_budget` persistente, **no recortar ni fusionar por cuenta propia**. Reportar brazo inviable para ese mundo y su proporción; no excluirlo silenciosamente al promediar. La API debe demostrar en tests que una categoría desconocida durante lectura no dispara creación ni actualización.
- **MiniBatchKMeans:** `K={4,8,16}`, centros aprendidos solo sobre 1200 observaciones; `predict` devuelve un índice0..K-1; decoder one-hot K + bias. Fijar `batch_size=32`, `n_init=1`, `random_state=42`, recorrido secuencial de bloques32 (1200=37 bloques completos + uno16), sin barajar una segunda vez. Probar inicialización y read-only en tests toy antes de usar mundos.
- **Memoria de casos:** conservar **hasta 16** pares (x, acción correcta inferida tras premio), FIFO sin acceso a etiquetas del evaluador; vecino por distancia euclídea cuadrada en 16D, empate por el caso más antiguo; ningún caso => D0. Cada ejemplo, etiqueta, contador y normalizador integra el coste.
- **Ablación de encoder:** mismo decoder y presupuesto pero sin adquisición; si el método no admite `predict` sin ajuste, registrar `no_defined`, no inventar clusters ni interpretar la ablación como fracaso del algoritmo. Control adicional factible: categorías con asignación fija aleatoria independiente de etiquetas, con semilla toy o de mundo ya permitida en desarrollo, y coste contabilizado.

## Decoder común con feedback posterior

Para entradas `phi=(feature,bias)`, acciones D0/D1, peso `w` inicializado en ceros, `score=w·phi`, elegir D1 si score>0, sino D0. Tras conocer recompensa, inferir `y=+1` si la decisión correcta era D1, `y=0` si era D0 (en tarea de dos acciones el reward revela si acertó). Actualizar **solo decoder**, con `p=sigmoid(clip(score,-30,30))` y `w <- w + 0.25*(y-p)*phi`. `float64` en todos; no weight decay, minibatches, warm-start del decoder ni selección posterior de learning rate. El mismo algoritmo usa raw16D y one-hot categórico, aunque **no implica misma expresividad**: informar las diferencias y sumar coeficientes al presupuesto. Para memoria de casos no hay decoder adicional.

Para no favorecer artefactos categóricos por tener claves enteras y más o menos parámetros, informar además precisión del raw lineal, KNN y costes totales. Ningún candidato se declara mejor por superar solamente un baseline débil; se compara con el **mejor baseline simple seleccionado exclusivamente en desarrollo**.

## Costo y bloqueo

Registrar separadamente: bytes de parámetros numéricos (`ndarray.nbytes`), serialización completa reconstruible (bytes), número de prototipos, pesos decoder, buffers, ejemplos cacheados, RNG, normalizadores y tiempo CPU monotónico por proceso. Informar memoria pico si puede medirse consistentemente; no equiparar tamaño de objeto Python y tamaño serializado. Comparar CPU sobre el mismo runner y versiones fijadas; reportar timing exploratorio si hay alta variabilidad. Un modelo que exceda tope16 ART permanece en informe con fallo de presupuesto; no se imputa artificialmente 0% de acierto sin distinguir inviabilidad de error.

**Igualdad de datos:** todos los brazos reciben exactamente el mismo orden y valores de las cintas x, misma serie de 1200 no etiquetadas, mismos 64 feedback por fase y mismo test. Guardar SHA256 de las observaciones por fase y logs sin datos latentes. El evaluador retiene los `EvaluatorCase`; el modelo solo ve `case.observation`. El reward se calcula después de decisión. No llamar a `target_for_evaluator` desde ningún módulo de modelos.

## Criterio de puerta de SOFTWARE NR01.03-C

Tests usando **solo semillas toy0/1/42 o vectores manuales**:
1. Igualdad exacta de observaciones/orden por brazo, y ausencia de latentes/objetivos en llamadas de modelo (spy/fake).
2. Reward entregado después de `choose`; actualización de decoder reproducible con ejemplo calculado independientemente.
3. `encode_read_only` no cambia pesos, centros, categorías, asignaciones, contadores o RNG; checkpoint roundtrip bit a bit para acción/decoder.
4. Prefijos 8/16/32/64 correctos; reversión A no reinicia decoder, tarea B2 sí; encoder nunca se actualiza en feedback/test.
5. Casos cero categoría, categorías desconocidas, 16 y 17 ART; 17 se registra `over_budget` sin recorte.
6. El conteo de coste incluye encoder, decoder y memoria de casos; rechazo explícito de semillas históricas y confirmatorias.
7. Verificación toy de versión/compatibilidad ARTlib0.1.12 y scikit-learn1.9.1 y regresión de generador.

**Estado actual de esta página:** contrato documental escrito; ningún test NR01.03-C implementado o ejecutado, ninguna cohorte científica ejecutada. La próxima acción es implementar adaptadores/harness y tests toy; al fallar cualquiera, conservar NR01.03-C en curso, corregir con adenda si se cambia un contrato. No fusionar PR103 ni modificar Nilo 0.7.

## Riesgos que deben conservarse en el informe

La etiqueta binaria se reconstruye del premio por la existencia de solo dos acciones; es realista para esta tarea, pero no un problema de crédito diferido. ART categoriza entradas por semejanza y puede crear categorías por contexto; el tope 16 puede descartar muchas corridas. KMeans usa prototipos entrenados por bloques y ART secuenciales: igualdad de observaciones no significa igualdad de optimización. Un decoder one-hot por cluster **no puede interpolar dentro de un cluster**; si esto lo perjudica, no ajustar decoder retrospectivamente: registrarlo como límite del contrato. La prueba no demuestra conciencia, una mente general ni equivalencia histórica con C1.
