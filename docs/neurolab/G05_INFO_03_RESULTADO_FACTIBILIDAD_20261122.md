# G05-INFO.03 — informe de verificación de factibilidad (22/11/2026)

**Dictamen de esta unidad: PASS TÉCNICO, NO G05 científico.** [Contrato previo](G05_INFO_03_CONTRATO_VERIFICACION_20261122.md) → [código ejecutado](../../experiments/neurolab/g05_info_feasibility.py) → [resultado toy permanente](resultados/g05_info03_toy_20261122.json). [GitHub Actions #45058669648](https://github.com/mxlzz/Nilo_public/actions/runs/45058669648) SUCCESS, commit de workflow `2ae5bd99eb5a5107a728e28977aaa5b0fc3c4a81`, Python 3.13.18, [artefacto #14767624707](https://github.com/mxlzz/Nilo_public/actions/runs/45058669648/artifacts/14767624707).

**Integridad:** script SHA256 `fa00ba120439a35250f5f2dafd1ddbaca802fa02a4b4565dc868d4bd0f02bc0c`; JSON generado SHA256 `51a334cb8860cd15ad2d1443547c73dc099f7ce98372a44249db45ae5028beda`. **Ambos digest idénticos entre ejecución local (Python3.13.5) y CI (Python3.13.18).** Archivo JSON permanente versionado recoge los valores, no pretende ser un duplicado de bytes idéntico a la salida de `json.dumps(sort_keys=True)`; el artefacto CI y el script reproducen la salida exacta.

## 1. Observaciones y oráculos ejecutados

1. El generador g.10b original permite recuperar el origen por el último cambio de contexto: **648/648 pulsos** en 216 secuencias de 3 ensayos cada una. La afirmación de [G05-INFO.01](G05_INFO_01_RESULTADO_IDENTIFICABILIDAD_20261122.md) queda ahora respaldada por **script ejecutado** (no solo demostración algebraica).
2. El generador candidato **no identifica unívocamente la acción causal**: dos historias latentes distintas —causa en t0 con L4 y en t2 con L2— producen el mismo flujo de contextos, decisiones y pulsos hasta t4. Esto demuestra ambigüedad **individual**, no ausencia de señal estadística.
3. Colisiones: fixture de tres eventos debidos al mismo tick, dos signos distintos, prioridades .7/.1/.6 → ganador de prioridad .1, signo negativo, **2 descartes**; un solo químico emitido. Los pulsos programados llegan exactamente tras 2/4/7 ticks y no se filtran IDs ni marcas de ensayo. `None` elimina el evento causal correspondiente.
4. Con 20.000 ticks y semillas técnicas **0, 1 y 42**, el estimador descriptivo `mean(reward_t·quality_{t-lag})` produce en demoras causales2/4/7 **~0.060–0.064**, y en demoras no causales1/3/5/6/8 magnitudes como máximo **0.0076**; pasan el gate de sanity del contrato `causal >.025`, `no causal |corr|<.025`. Al permutar signos entre tiempos con premio, los valores 2/4/7 quedan entre **−0.0105 y +0.0035**. Esto muestra **señal agregada detectable bajo política de exploración aleatoria**, no que la microred C1 o un aprendiz propio puedan explotarla.
5. El calendario exógeno tiene la **misma huella** si se invierten todas las acciones o se sustituyen sistemáticamente algunas por `None`, sin alterar oportunidades/demoras/prioridades. Ante `None` se agendan menos eventos. Reejecutar con la misma semilla produce resultados idénticos y semillas distintas producen huellas diferentes.
6. Eventos programados por semilla: 3957/4031/4023; entregados 3707/3741/3760; perdidos por colisión **250/290/263** (aprox. 6–7% de programados). Las colisiones son una pérdida de señal observable **solo al evaluador**; no se descartan a escondidas de las métricas.

**Limite:** todas las mediciones se hicieron con acciones aleatorias, un único mapping fijo, **sin entrenamiento de ningún modelo neuronal ni de baselines** y sin pruebas de reversión. No permiten inferir potencia estadística, tasa de aprendizaje ni que el problema deje de tener otras correlaciones explotables cuando la política aprende.

## 2. Semántica de colisiones y ventajas de alternativas existentes

La regla de **prioridad exógena y descarte sin diferimiento** conserva el API de cuatro bytes del microcerebro, impide informar por accidente múltiples IDs de recompensas y evita un backlog visible por su reloj. Pierde parte de la señal (~6–7% en toys), pero el mecanismo de pérdida es independiente del signo/acción condicionado a la agenda exógena. Su costo conceptual es inferior a inventar una cinética química mezclada no derivada de C1.

La formulación pertenece a la familia de feedback **demorado anónimo**, no un algoritmo nuevo. [Pike-Burke et al., ICML2018](https://proceedings.mlr.press/v80/pike-burke18a.html) estudian atribución con recompensa anónima/agregada y [Cesa-Bianchi et al., JMLR2022](https://www.jmlr.org/papers/v23/21-1443.html) generalizan feedback compuesto. Estos trabajos no prueban automáticamente comportamiento en nuestro microC1. [MushroomRL](https://mushroomrl.readthedocs.io/en/dev/source/api/algorithms/index.html) tiene TrueOnlineSARSA(λ), pero requiere interfaz de transición/MDP; [Brian2](https://brian2.readthedocs.io/en/2.11.0/examples/frompapers.Izhikevich_2007.html) da ejemplos de dopamina-STDP, no una sustitución directa. Es razonable **reutilizar la microred existente y controles tabulares transparentes** primero.

## 3. Invariante de comparación y problema aún abierto

**Advertencia metodológica:** `C1ContextBrain.step()` calcula la acción a partir de `previous_contexts`: tiene **un tick de latencia perceptiva**, mientras una tabla que lea el contexto actual puede decidir más rápido. No atribuir esa diferencia a crédito temporal. Requisito de próxima cohorte: reportar rendimiento en ticks estables vs inmediatamente posteriores a cambio de contexto, política simple con contexto instantáneo y con retardo, tasa de `None`, y no declarar G05 alcanzada solo por diferencia entre arquitecturas.

El contrato operativo debe imponer **elección pre-recompensa** para todos: el pulso `t` se presenta junto a `x_t`, pero el efecto de aprendizaje asociado al químico no debe cambiar la elección de ese mismo tick en tabla si la red C1 tampoco lo hace. Se puede aplicar update después de elegir con las trazas anteriores; no se entrega etiqueta de evento a ningún control.

## 4. Resultado y siguiente puerta

**PASS** de G05-INFO.03 conforme a requisitos pretest; queda demostrado que el banco candidato es distinto del anterior, que no hay reconstrucción causal perfecta en el testigo adversario y que existe señal ideal bajo exploración. **No está demostrado que carezca de TODOS los atajos, ni que garantice aprendizaje ni superioridad neuronal.**

**Siguiente unidad:** redactar preregistro científico autónomo `G05-NX01` con métrica primaria y stop gate explícitos, particiones nuevas, control reactivo, control con elegibilidad tabular, C1 nativa y frozen, y análisis causal por recompensa de controles sin privilegio. Antes de correr modelos validar con tests la semántica de igualdad de inputs, recompensa después de elección, fuga de mapping, entrega sin ID, reversiones, latencia y restauración. Si no se pueden satisfacer, STOP sin consumir semillas nuevas.

`main`/Nilo0.7 intactos; PR#103 draft; NR01 cierre vigente; semillas 1400..1419 y 24000..24019 siguen reservadas.
