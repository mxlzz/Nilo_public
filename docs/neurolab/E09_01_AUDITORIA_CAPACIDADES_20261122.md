# NeuroLab — E09.01/07: auditoría de capacidades E00–E08 y resultados E09 (22/11/2026)

**Naturaleza:** auditoría documental y lectura de código/JSON versionados; **no** nuevo experimento ni reejecución de las 20 semillas. Versión base identificada: `ad4745dac437f309068ad830312d779ff286e9a3`. El contrato de puertas correcto es [E09.00R](E09_00R_RECONCILIACION_GATES_20261122.md). PR #103 permanece aislado.

## 1. Evidencia realmente inspeccionada

- [Plan E00–E09](ETAPAS_00_09.md), [protocolo de evaluación](PROTOCOLO_EVALUACION.md), [auditoría E09 inicial](E09_AUDITORIA_INTERMEDIA.md), [índice E01–E08](E09_EVIDENCE_INDEX.md), [GEN de CD](E00_GENOMA_ORIGINAL_COMPARACION.md), [EXE forense](E09_02F_INFORME_EJECUTABLE.md) y [cierre I3c7l](E09_02I_I3C7L_CIERRE_ESTRATEGICO_LINEAS_H_N.md).
- Código: [kernel](../../experiments/neurolab/kernel.py), [plasticity](../../experiments/neurolab/plasticity.py), [twin_weight](../../experiments/neurolab/twin_weight.py), [eligibility](../../experiments/neurolab/eligibility.py), [concepts](../../experiments/neurolab/concepts.py), [rewiring](../../experiments/neurolab/rewiring.py), [recurrent](../../experiments/neurolab/recurrent.py), [C1ContextBrain](../../experiments/neurolab/c1_context_brain.py), [e09_coupled_brain](../../experiments/neurolab/e09_coupled_brain.py).
- JSON **permanentes leídos y parseados desde GitHub**: [E03](resultados/run-44852299967/e03.json) (SHA blob `a57ba6e1b974905a0299ea65799cf2776604747f`), [E06](resultados/run-44852299967/e06.json) (`706b105175388ab8e771844b72e8585cce1e1848`), [E07](resultados/run-44852299967/e07.json) (`4055562413c5c77541c2bdadcebac136a97d6837`), [E08](resultados/run-44852299967/e08.json) (`d9a3fa299cfe3b58559f0c3d474aaebea171e2b6`). Proveniencia original: [CI #44852299967](https://github.com/mxlzz/Nilo_public/actions/runs/44852299967), commit ejecutado `56cb2e7456103eee7a65cdadc275da01a1869720`.
- E09 posterior: [g.9 replicación](E09_02G_09_RESULTADO_REPLICACION.md), [g.10b](E09_02G_10B_RESULTADO_DEMORA_DISTRACTORES.md), [g.10c](E09_02G_10C_RESULTADO_ELEGIBILIDAD.md), [I3c7h](E09_02I_I3C7H_RESULTADO_CONTINGENCIA.md), [I3c7i](E09_02I_I3C7I_RESULTADO_ABLACION_LOCAL.md), [I3c7j](E09_02I_I3C7J_MEMORIA_DIAGNOSTICO_ESTRATEGIA.md), [I3c7k](E09_02I_I3C7K_RESULTADO_TRANSFERENCIA.md), [I3c7l](E09_02I_I3C7L_CIERRE_ESTRATEGICO_LINEAS_H_N.md). Sus resultados se citan, **no** se combinan como si fueran evaluaciones independientes de un mismo sistema.
- La CI general del commit base terminó **SUCCESS** tanto [Validación Nilo #44988262562](https://github.com/mxlzz/Nilo_public/actions/runs/44988262562) como [NeuroLab #44988262552](https://github.com/mxlzz/Nilo_public/actions/runs/44988262552). Esto establece regresión técnica para **ese SHA**, no cierre de puertas científicas.

## 2. Capacidades y puertas (sin transferir evidencia entre tareas)

**E00 / G00:** existe estudio real de 9 genes de lóbulos en `dad1.gen` extraído del CD, ~952 posiciones nominales y múltiples reglas GEN/EXE identificadas. El primer motor N fue legítimamente construido con aproximaciones explícitas. **G00 para prototipo restringido: suficiencia operativa**; **reconstrucción histórica H: parcial/abierta** (scheduler y bioquímica completa no verificados extremo a extremo). Los originales no están publicados en GitHub.

**E01 / G01:** kernel determinista, números acotados, checkpoint/replay y fixtures verificados para su ecuación experimental. **Logro técnico delimitado**, no emulación del cerebro C1 completo.

**E02 / G02:** seis unidades de dos entradas/dos conceptos/dos decisiones y elección WTA reproducible. **Logro técnico delimitado**, no decisión autodirigida.

**E03 / G03:** en ensayo original de 20 semillas, aprendizaje y reversión alcanzan **1,0000** cada uno frente a control congelado **0,4250**; [JSON](resultados/run-44852299967/e03.json). **Superada en episodios de corta duración del modelo E03** (reinicio de actividad cada episodio); no prueba persistencia con neuronas continuamente activas, química ni refuerzo demorado.

**E04 / G04:** [twin_weight](../../experiments/neurolab/twin_weight.py) separa respuesta rápida, relajación y peso lento para una sinapsis experimental propia con tests y control de peso único. **Efecto local demostrado**; la generalización a conservación durable de conducta en una microred ACTIVE sigue **no demostrada**. En [I3c7k](E09_02I_I3C7K_RESULTADO_TRANSFERENCIA.md) copiar STW a LTW eleva precisión ACTIVE solo **+0,04896** y NO alcanza la puerta específica +0,10; no se debe tachar E04 aislada como falsa por ello, ni aprobar memoria integrada.

**E05 / G05:** la elegibilidad local reacciona matemáticamente al premio diferido; el distractor reciente puede llevarse más actualización que la conexión causal (ejemplo: B+23 vs A+13). En [g.10b](E09_02G_10B_RESULTADO_DEMORA_DISTRACTORES.md), C1 reducida obtiene **16/40** semillas en ambas fases≥.90 con distractores, IG **6/40**; [g.10c](E09_02G_10C_RESULTADO_ELEGIBILIDAD.md) identifica persistencia de susceptibilidad objetivo pero dispersión del efecto químico. **G05 original: no superada**. No confundir con `R-ACT-I3c` (retención sin feedback).

**E06 / G06:** [JSON](resultados/run-44852299967/e06.json) muestra detector de pares **1,0000**, entradas individuales **0,5375**, memoria exacta **0,5000** y congelado **0,4500**, 20 semillas. **Generalización restringida demostrada** a la señal irrelevante `C=1`, pero las cuatro conjunciones XOR ya se habían definido y entrenado; **NO se aprendieron los detectores de concepto**, no hay extrapolación a categorías nuevas. G06 válida únicamente con esta acotación.

**E07 / G07:** [JSON](resultados/run-44852299967/e07.json): 2 slots migratorios y control LRU tienen precisión **1,0000** en patrones nuevos; fijos **0,5000**; pérdida media en antiguos por migración **0,5000**. **Capacidad de recableado sí; superioridad respecto de caché simple NO**. Mantener G07 como **no demostrada** para beneficio neto distintivo; no elegir migración automáticamente.

**E08 / G08:** [JSON](resultados/run-44852299967/e08.json) y [runner](../../experiments/neurolab/recurrent.py): oscilación determinista de dos unidades con conexiones recurrentes, silencio sin conexiones y amortiguación con pesos menores. **Fenómeno dinámico demostrado**, deliberadamente producido por topología y condición inicial; nada sobre pensamiento autónomo.

**E09 / G09:** se crearon combinaciones parciales del cerebro de contexto con química y receptores en [e09_coupled_brain](../../experiments/neurolab/e09_coupled_brain.py); esto **sí es integración parcial real** (no decir que «no hay integración alguna»). Pero no demuestra conjuntamente las capacidades E03, E04, E05, E06, E07 y E08, ni un baseline tabular no privilegiado, ni mínima complejidad en un banco común. **G09 sigue abierta**.

## 3. Hallazgos transversales y límites de validez

1. **Dos familias incompatibles sin adaptación:** E01–E08 usan objetos y reglas distintas (`BrainState`, `PlasticState`, `TwinSynapse`, `EligibleSynapse`, `ConceptWeights`, `WiringState`); E09 C1 usa `ContextBrainState` y `CoupledState`, actualización GEN/EXE parcial y química. No se pueden sumar resultados de las primeras como capacidades de la segunda.
2. **No hay ventaja global cuantificada sobre un sistema elemental.** En E07 LRU empata; en g.10b la tabla Q 2×2 acierta 40/40 pero recibe procedencia causal privilegiada, por lo que **no es comparación justa** frente a C1. Debe existir control con la **misma información accesible** para emitir una preferencia arquitectónica.
3. **Retención ACTIVE es una cuestión distinta de crédito temporal.** En [I3c7h](E09_02I_I3C7H_RESULTADO_CONTINGENCIA.md), B supera permutación de valencias en fase invertida (+0,3865) pero solo **2/20** semillas satisfacen el criterio específico de ambas fases de `R-ACT-I3c`; la química por tick no está apareada entre B/P. [I3c7i](E09_02I_I3C7I_RESULTADO_ABLACION_LOCAL.md) apoya necesidad causal de STW para decisiones locales, no para atribución histórica precisa del premio.
4. **FROZEN no sustituye ACTIVE.** Impedir la plasticidad/relajación en lectura puede mantener aciertos artificialmente; comparar desempeño bajo el modo declarado.
5. **Riesgo de sobreajuste conceptual:** las múltiples pruebas de desarrollo y análisis post hoc con cohortes reutilizadas no constituyen nuevas replicaciones independientes. Las semillas 1400..1419 NO se han usado y deben reservarse.
6. **Evidencia incompleta para auditoría archivística exhaustiva:** parte de las trazas grandes permanece en artefactos Actions de retención limitada; algunos hashes y resúmenes sí están versionados. Para G09, un índice no puede sustituir un manifiesto de qué datos crudos quedan accesibles ni pruebas end-to-end de la versión elegida.
7. **Enunciados obsoletos en documentos antiguos:** la auditoría inicial afirma que falta `dad1.gen` y ejecutable; hoy están documentados e inspeccionados. Se corrige por [E09.00R](E09_00R_RECONCILIACION_GATES_20261122.md), sin alterar la fecha histórica del informe.

## 4. Resultado de esta auditoría

- **Demostrado en su banco original:** decisión determinista; asociación/reversión breve; doble escala sináptica aislada; detector conjuntivo fijo; cambio de topología con olvido; oscilación recurrente; señales STW contingentes/causales locales.
- **Sin demostrar para la mente mínima integrada:** retención duradera ACTIVE robusta, crédito temporal selectivo, conceptos autoconstruidos, superioridad sobre LRU/tabular con igual información, dinámica propia que contribuya a conducta y arquitectura mínima conjunta.
- **No corresponde:** modificar el protocolo o implementar una nueva regla de memoria para ocultar estas lagunas.

**Puerta de esta auditoría documental:** COMPLETADA como clasificación basada en archivos existentes, **no** como G09 ni como validación experimental. Siguiente: evaluación de compatibilidad y coste de integración E09.02–.05 sin programar por inercia.
