# E09.02i-I3c.4 — preregistro de química apareada B/Y/P/F

**2026-11-21 — PRE-IMPLEMENTACIÓN Y PRE-RESULTADOS.** Relaciona [I3 químico negativo](E09_02I_I3_RESULTADO_NEGATIVO.md), [I3c.3 adaptador](E09_02I_I3C3_RESULTADO_ADAPTADOR.md) y [I3c.3a sin atrofia bajo estímulo fijo](E09_02I_I3C3A_RESULTADO_TRAYECTORIA.md). Nueva cohorte **900..919**, no reciclada para tuning. **Experimento N** con genes originales parciales y parámetros metabólicos sintéticos, NO simulación histórica completa.

## Objetivo

Evaluar si la migración tipo1 en cuatro contactos realmente se activa ante los precursores y reacciones de I3 y si produce una diferencia de decisiones. El control principal debe **igualar exposición química**, no repetir la comparación confusa on-policy de I3.

## Protocolo fijado

- **20 semillas** 900..919. Dos fases secuenciales de regla A=(D0,D1) y luego B=(D1,D0). Por fase: **60 trials de entrenamiento** y **36 holdout** (6 repeticiones por delay), generators existentes de I3: train salts50000/60000; test salts70000/80000. Cada ensayo: 4 ticks contexto objetivo, delay1–3 ticks de distractor contrario, inyección de precursor si corresponde, 1 tick llegada de distractor. **Holdout** sin nuevos precursores, sin plasticidad ni migración y no afecta el estado para la fase siguiente.
- Seis unidades, **cuatro conexiones dinámicas** por rama; inicialización de sinapsis del adaptador existente, mismos genes C1 Decision y SVRule. Wiring contrabalanceado por paridad de semilla, INDEPENDIENTE de mapping: pares (C0,C1,C1,C0); impares (C1,C0,C0,C1), slots D0exc,D0inh,D1exc,D1inh. Ningún Concept adicional.
- **B:** plasticidad y recompensa condicionada a su decisión, sin migración; es el brazo de referencia para el calendario de precursores.
- **Y (yoked):** plasticidad con migración, recibe los precursores de B en el MISMO trial y tick, independientemente de si Y eligió igual; **su química debe ser IDÉNTICA a B tras cada tick**. Y no demuestra aprendizaje autónomo de refuerzo porque el feedback depende de otro agente.
- **P (on-policy):** plasticidad con migración y recompensa de su propia elección. Puede divergir la exposición química; reportar sin usar P−B como efecto causal puro.
- **F:** mismas cuatro conexiones SIN plasticidad ni migración, recibe cronograma de precursores B. Su química debe ser idéntica a B e Y; B−F informa sobre plasticidad en esa exposición.
- Precursores de I3: tras delay, acción correcta→agregar dosis80 a químicos33 y1, incorrecta→80 a17, acción None→no inyectar. Y/F replican incluso los None de B. Evaluador externo solo modifica pool, nunca introduce target/action/correct/mapping como entrada neuronal.
- **Química:** e09_chemical_bridge + four original reactions 57/71/111/112, six cerebral receptors 88/89/126..129, orden brain anterior a chemistry, **decay de pool256 a tasa40 para todas** y dosis80. Estas tasas/dosis son sintéticas, no GEN histórico. Sin emisores neuronales automáticos.
- **RNG Type1:** para Y/P, RandStream precargado con 16384 draws raw creados por random.Random(910000+seed) local y fijo; **convención N, no rand() MS CRT**. B/F no consumen draws. Checkpoint del adaptador sigue vigente.

## Métricas, falsación y límites

- Primarias exploratorias: holdout target accuracy por fase y **Y−B emparejado por semilla**, además de conteo real de migraciones aceptadas y contactos agotados de Y/P. **NO umbral de aprendizaje para aprobar por tuning**: 20 semillas, resultado descriptivo y con intervalos.
- Secundarias: B−F, P−B (con caveat on-policy), demorad1/2/3, contexto0/1, acciones None, signo y cantidad de precursor, contadores Type1 por reason, cursor, STW/LTW/fortaleza final.
- Bootstrap: media de diferencias por 20 semillas con intervalo percentil95% de 2000 réplicas, PRNG60513, mantener pares sin pseudorreplicación. Aciertos None=0.
- **Invariante química:** B/Y/F deben producir EXACTAMENTE el mismo estado de química luego de cada tick de train y holdout; invalidar cualquier divergencia antes de reportar accuracy. En la fase siguiente conservar los estados entrenados; no continuar desde holdout.
- **Invariante causal local:** B/Y neuronas y sinapsis idénticas ANTES de la primera migración aceptada (salvo cursor RNG si Type1 rechaza duplicado). Si divergen sin haber migrado, invalidar. Y/P sólo se comparan con B bajo mismos eventos hasta su primera diferencia de recompensa.
- Cuatro contactos siempre, toda identidad modificada debe llevar evento Type1 accepted. B/F nunca migran ni consumen draws, F sin actualización de pesos durante entrenamiento. No manipular semillas o tasas al observar resultados.
- **G-I3c4-VALIDITY:** replay por semilla, cronograma químico B/Y/F coincidente, y ninguna transición fuente no atestiguada. **G-I3c4-OBSERVATION:** resultados por semilla preservados incluso si B=Y=F y hay 0 migraciones. **G05/G09/G00-H** siguen abiertas sin excepción.
- Si Y no migra o no supera B, no aumentar conexiones, subir dosis o corregir genética para provocar un efecto: siguiente paso es investigar criterios de pérdida/migración, o recuperar valores GEN antes de nuevo ensayo confirmatorio. No se reclama fidelidad C1 o tiempo físico.

PR#103 borrador, main y Nilo0.7 intactos.
