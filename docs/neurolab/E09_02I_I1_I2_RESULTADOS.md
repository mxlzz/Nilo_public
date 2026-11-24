# E09.02i — resultados I1 e I2: acoplamiento temporal parcial

**Fecha:** 2026-11-21. **Preguntas originales:** [preregistro I1–I3](E09_02I_INTEGRACION_QUIMICA_PRE_REGISTRO.md). **Estado:** I1 e I2 completadas en sus criterios técnicos, **I3 / G05 / G09 abiertas**. Esta es línea experimental N, no emulación completa de C1.

## Resultado I1 (química)

- [Código](../../experiments/neurolab/e09_chemical_bridge.py) que reutiliza, sin cambiar, módulos históricos de emisión, recepción, asignación de loci y reacciones.
- Estado inmutable con pool256, fuentes tipadas por lóbulo/locus, cuatro CHEM Decision y cuatro Concept, tick lógico. Se traza emisor→receptor→reacción; no hay decaimiento en este módulo inicial.
- [Tests](../../experiments/neurolab/tests/test_e09_chemical_bridge.py) con genes previamente verificados del GEN CD: gen111 consume Reward49 para generar Reinforcement51+Echo54; la concentración nueva **no llega a los receptores en ese mismo tick**. Gen124 Decision, con fuente80, emite 79 a DecASH1=53 y consume la fuente. Lóbulos 6 y 8 independientes.
- Ensayo falsable: si se invierte artificialmente el orden a reacción→receptor, Concept CHEM0 recibe 11 en el tick inicial; con el orden original recibe 0, recién 11 en el siguiente. No hay un agente aprendiendo, solo una diferencia causal en el flujo.
- [CI I1](https://github.com/mxlzz/Nilo_public/actions/runs/44951342148): **success 383 tests + 2 expectedFailure históricos**. Las pruebas tienen fixtures derivados del genoma previo, no bytes propietarios originales en CI.
- **Gate I1 validada en su alcance técnico**. No cierre de G05/G09.

## Resultado I2 (microred de seis unidades + química)

- [Adaptador](../../experiments/neurolab/e09_coupled_brain.py) reutiliza íntegro C1ContextBrain: Decision usa los CHEM almacenados **antes** de que la química del tick actual procese el pool; la química produce CHEM que leerá el cerebro en el próximo tick.
- Estado conjunto incluye cerebro, pool, fuentes emisoras, canales y reloj lógico. Checkpoint integral guardable/restaurable, con esquema estricto. Se comparó una continuación desde estado vivo y otra desde estado restaurado: idénticas en la secuencia de prueba.
- Controles de [test I2](../../experiments/neurolab/tests/test_e09_coupled_brain.py): 6 neuronas y 8 sinapsis sin cambios, no se fuerza una respuesta correcta, aprendizaje congelado no altera pesos aunque química siga avanzando, puertos emisores NO se rellenan mágicamente desde winner outputs.
- [CI I2](https://github.com/mxlzz/Nilo_public/actions/runs/44951467547): **success 391 tests + 2 expectedFailure históricos**.
- **Gate I2 validada en su alcance de acoplamiento temporal parcial**; Concept CHEM se registra pero la microred actual no implementa su plasticidad estructural, y tampoco se ha verificado la conexión automática de winner-output a los loci emisores.

## Lo que todavía impide un ensayo conductual concluyente

- El estado químico inicial de laboratorio es un pool cero o explícito; no es el metabolismo completo de una criatura.
- El primer puente no aplica el decaimiento global del pool256. Antes de someterlo a feedback repetido, debe incorporarse [I1b](E09_02I_1B_POOL_DECAY_PRE_REGISTRO.md) con **tasas declaradas y su procedencia**. Para la línea histórica H faltan los valores originales de los 256 químicos.
- El evaluador sigue siendo externo; el cerebro no fabrica su propia señal de recompensa y G05 continúa fallando en distractores según g.10b.
- No hay ventajas observadas sobre un baseline tabular ni corrección de errores de crédito causal en esta intervención: no se ejecutó el experimento I3.

**Siguiente:** I1b decaimiento del pool con tasas explícitas; después evaluar si se puede ensayar aprendizaje sin confundir un parámetro sintético con el C1 original. PR #103 draft; Nilo0.7/main intactos.
