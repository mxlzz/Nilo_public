# E09.02g.10b — preregistro: crédito diferido con distractor y control causal

**Fecha:** 2026-11-21. Registrado antes de escribir o ejecutar el runner.

## Pregunta

¿La microred C1-reducida discrimina y revierte dos asociaciones cuando recibe un único refuerzo después de 1–3 estímulos distractores? ¿La compuerta IG (g.10a) ayuda, pese a almacenar solo el Concept de la decisión previa?

Las eligibility traces son un mecanismo ya conocido de crédito temporal (Sutton y Barto, 2ª ed., cap. 12, https://web.stanford.edu/class/psych209/Readings/SuttonBartoIPRLBook2ndEd.pdf ; https://pmc.ncbi.nlm.nih.gov/articles/PMC3208325/). NO se presupone que C1 lo implemente ni se introduce TD(lambda).

## Cohorte, secuencias y estímulos congelados

- 40 semillas nuevas: **120..159**. Fase A S0→D0 y S1→D1; fase B ambas invertidas. Persisten estados y pesos entre fases.
- Fase de entrenamiento: **60 ensayos** por fase, diez por cada combinación de objetivo S0/S1 y demora d=1/2/3. Barajar con Random(seed+50000) A y Random(seed+60000) B.
- Holdout por fase: **36 ensayos** sin aprendizaje ni químicos, seis por combinación, con Random(seed+70000) A y Random(seed+80000) B. Evaluar desde copia del estado para no modificar la trayectoria de entrenamiento.
- Ensayo: 4 ticks del contexto objetivo, **solo la cuarta decisión** cuenta; después d ticks del **contexto opuesto** (distractor), sin refuerzo por esas decisiones; por último 1 tick adicional con contexto distractor durante el cual llega Reward/Punishment por la acción objetivo. El refuerzo llega tras **d ticks de distractor y en el tick siguiente**: d indica distractores intermedios, NO demora total. El evaluador calcula signo sobre la acción efectivamente elegida por cada brazo en el cuarto tick; el mapping no ingresa a la red.
- Cada brazo ve la misma secuencia y dispone como máximo de **un pulso no nulo por ensayo**, únicamente en el último tick. No hay resets neuronales entre ensayos o fases. Durante holdout se presentan exactamente los mismos tipos de estímulo, pero siempre sin química y con plasticidad desactivada.

## Brazos sin cambio de parámetros

1. **C:** clase C1ContextBrain g.5 original, con plasticidad.
2. **IG:** wrapper step_intrinsic g.10a original, con su memoria del Concept previo y sin acceso a límites/posiciones de ensayos.
3. **F:** el mismo cerebro C1, con learn=False incluso durante entrenamiento, control congelado.
4. **Q:** tabla 2×2, alpha0.2 y epsilon0.10 en entrenamiento, greedy en holdout, algoritmo de selección tabular del g.5. Cola de UNA pareja causal (contexto objetivo, acción elegida) hasta que llega el refuerzo. Q conoce esa procedencia; el circuito C1 e IG NO. Q elige solo en el cuarto tick del objetivo, no implementa los estados sensoriales intermedios: **baseline informacionalmente privilegiado y estructuralmente distinto**.

## Variables, aceptación e interpretación congeladas

- Reportar exactitud de la **cuarta decisión objetivo** por modelo, fase y d, promedios, todas las 40 semillas y cantidad que alcanza exactitud ≥0.90 **en ambas fases**. Reportar IG-C y ventaja relativa a F y Q, incluida reversión.
- Puerta de robustez de un brazo neural: **≥36/40 semillas** deben obtener ≥0.90 en ambas fases, con media A y B ≥0.85 y **ningún grupo de demora** por debajo de 0.70. Resultado negativo conservado sin ajustar puertas ni cambiar red.
- Si C e IG fallan y Q aventaja en precisión total por ≥0.15, detener ampliaciones de red y ajustes de tasas para este banco; evaluar mecanismos existentes y reloj histórico. Si Q también falla, diagnosticar antes la validez del control.
- Pruebas de oráculos: conteo balanceado de combinaciones, 4 objetivos + d distractores + 1 tick de feedback; un solo pulso por ensayo; nada de feedback durante distractores previos; Q actualiza objetivo/acción causales; F nunca altera dendritas; determinismo; holdout sin aprendizaje y continuidad A→B.
- CI verde significa integridad del experimento, **no** gate científica superada. Fallas científicas se documentan. IG puede filtrar una recompensa equivocada sin saber reasignarla, por lo que incluso IG>C no demuestra atribución causal.

## Límites

No es emulación íntegra de Creatures 1: red mínima de seis unidades, ocho sinapsis y Concept predefinidos. No introducir LLM, cuerpo, mundo ni cambios en Nilo. G00-H, G05 y G09 permanecen abiertas.
