# E09.02d — preregistro: exploración ocasional sin cambiar la plasticidad

**Fecha 2026-11-21. Documento redactado antes de código y ejecución de la variante.**
Antecedente: E09.02c negativo: 20/20 semillas aprenden, 6/20 invierten, exactitud media reversión 0.30.

## Hipótesis falsable

H1: la incapacidad de invertir una preferencia de los cinco nodos se debe en parte a una política de acción exclusivamente codiciosa, que explora SOLO si hay empate. Una política epsilon-greedy con probabilidad fija **epsilon=0.10** de elegir una de las dos acciones al azar por ensayo debería permitir adquirir la nueva preferencia sin alterar los pesos ni sus reglas.

H0: aun con epsilon fijo la inversión no supera el umbral o sigue dependiendo de una semilla favorable.

No atribuir esta política a Creatures 1: **es un mecanismo experimental de control**, no una SVRule genética.

## Diseño congelado

- Modelo idéntico al E09.02c: 2 entradas, 1 concepto AND, 2 decisiones, pesos D0Exc/D0Inh/D1Exc/D1Inh, valores iniciales cero, tasa +16 a excit del elegido cuando reward=+1, +16 a inhib del elegido cuando reward=-1.
- Sin modificar MiniLearner de la versión E09.02c ni su resultado. Implementar EpsilonLearner(MiniLearner) con exactamente UNA diferencia: respond puede forzar acción exploratoria con epsilon=0.10 aun sin empate.
- Reproducibilidad estricta: generador determinista por seed*1_000_000+state.trials; primero sortear rng.random()<0.10, si se cumple tomar elección rng.choice(D0,D1); si no, acción ganadora; si hay empate, rng.choice(D0,D1). Sin estado de PRNG oculto.
- Experimento **pareado** con E09.02c: semillas 0–19, 60 ensayos fase inicial D0 premiada, test80, baseline pesos congelados, 120 ensayos reversión D1 premiada, test80. En evaluación sigue epsilon=0.10, ya que esa política forma parte del cerebro; reportar coste de errores provocados por exploración.
- Criterio G09.02d: >=18/20 semillas con precisión >=0.90 inicial y revertida, y ventaja media >=0.30 ante control congelado. Además, invertir >6/20 semillas que alcanzaban el umbral en el experimento anterior, reportar coste de exploración (errores de acción a pesar de score ganador). Si falla, registrar sin alterar epsilon/semillas/entrenamiento ni escoger otros datos post hoc.
- Test de no-reescritura: el learner E09.02c continúa dando el mismo resultado negativo (1.0 original, 0.3 reversión) en 20 semillas. No reemplazar datos de E09.02c.
- Controles: mismos parámetros sin feedback, baseline epsilon=0.0 E09.02c; sin estímulo de concepto no hay modificación de sinapsis. Checkpoint/resume con misma semilla+contador devuelve idéntica trayectoria.

## Limitaciones

Las entradas carecen de significado y siempre activan el mismo concepto. La acción correcta está en el evaluador. La política epsilon puede producir errores innecesarios tras aprender. Este ensayo prueba una causa del bloqueo de reversión; no demuestra comprensión causal, aprendizaje de conceptos, autonomía ni emulación C1.

## Artefactos

experiments/neurolab/c1_microlearning_exploration.py, experiments/neurolab/e09_exploration_protocol.py, tests E09.02d, CI con archivos JSON de resultados. **No editar la especificación de E09.02c**.
