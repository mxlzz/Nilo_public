# E09.02g.2 — preregistro de circuito mínimo C1 de cinco neuronas en aprendizaje continuo

**21/11/2026. Registrado antes de implementar/probar.** Se pretende contrastar si la estructura genética y aritmética del motor C1 de 1997, ya reconstruida en el banco de NeuroLab, permite aprendizaje/reversión en una red de **cinco unidades** sin cuerpo, mundo, LLM ni recompensas insertadas como respuestas correctas dentro de la red.

## 1. Alcance y fuente

Es **un modelo de laboratorio deliberadamente reducido**, no un Norn de 952 neuronas ni réplica exacta del ejecutable. Parámetros numéricos de genes de Decision y Concept y operaciones neuronales/sinápticas provienen de `dad1.gen` y `Creatures.exe`, contrastados en E09.02f.1–f.6 y E09.02g.1.

**Abstracciones externas declaradas:**
- Cada ensayo presenta P0=P1=255. Concept tiene un detector fijo de dos dendritas STW=128, atenuación255 y SVRule `ANDTYPE0`: su salida efectiva en este cálculo es **253**. Sus dos sinapsis se dejan constantes por ahora, para aislar aprendizaje de decisiones.
- Dos neuronas de Decision (D0,D1), cada una con **una dendrita excitatoria** y **una inhibitoria**, las cuatro provenientes del único concepto, en lugar de las 128+128 dendritas por neurona del genoma original. Los cuatro pesos comienzan `sus=0,stw=0,ltw=0,strength=2`, dentro de rangos genéticos.
- Decision utiliza estado basal80 y regla `STATE+TYPE0-TYPE1` con saturación por operación; atenuación neuronal128. Por ensayo el estado se restablece a80 y no se integra todavía la relajación del estado entre ensayos. La red es **episódica**, no reloj biológico C1 completo.
- Tras actuar, el **evaluador externo** genera un pulso abstracto CHEM0=255 Reward o CHEM1=255 Punishment para **todo el lóbulo de decisión**. El cerebro no recibe la etiqueta correcta, sino solo concentraciones químicas. No se reproducen aún reacciones metabólicas ni la latencia real de generación de químicos.
- Cuatro sinapsis se actualizan con la implementación genética `update_c1_synapse`: susceptibilidad, STW/LTW y fortaleza, en pasos tick1..180. CHEM2/3 son cero: **no se dispara migración de decisiones**.

## 2. Incertidumbre explícita: orden WTA y causalidad

El ejecutable evalúa las neuronas y sus dendritas y aplica winner-takes-all al final del lóbulo. El valor de OUTPUT disponible a cada SVRule puede provenir de la instantánea previa del estado y del orden de evaluación. **No se ha demostrado aún el acoplamiento completo para un circuito de cinco neuronas simplificado**.

Se fijan por separado **dos políticas de actualización de susceptibilidad**, sin elegir la que funcione mejor a posteriori:
- `post_wta_gated` (control de elegibilidad): solo la neurona elegida ofrece output no nulo a sus dendritas; las demás reciben output0.
- `pre_wta_all` (control de competencia): ambas neuronas presentan su score positivo antes de aplicar WTA; se mide si un mismo refuerzo global modifica por igual acciones que no se ejecutaron.

También dos reglas de desempate:
- `first_index`: D0 si ambos scores son idénticos, consistente con el ganador de índice más bajo detectado en el recorrido WTA de este ejecutable.
- `random_tie`: `random.Random(seed*1_000_000+trial).choice((D0,D1))`, control experimental anterior E09e (no PRNG de Creatures).

Se ejecutan **las cuatro combinaciones del diseño 2×2** en las mismas 20 semillas; no se elige mejor combinación después. La exploración forzada ε es cero.

## 3. Datos, controles y métrica preregistrados

- 20 semillas `0..19`.
- Fase A: 60 ensayos en los que D0 provoca Reward y D1 Punishment, evaluación sin aprendizaje de80 elecciones.
- Fase B, inversión: 120 ensayos en que D1 provoca Reward y D0 Punishment, evaluación sin aprendizaje de80 elecciones.
- Control congelado para cada combinación: misma topología, entradas, esquema de selección y pulso externo, pero **no** se modifican sinapsis.
- Comparación externa con resultados previos de E09e (STW/LTW experimental) registrada, **no** recalibrar sus reglas/coeficientes.
- Medir exactitud por semilla en ambas fases, ventaja sobre congelado, valores STW/LTW/suscept/strength de cuatro conexiones, igualdad/diferencia entre D0 y D1, pasos de WTA y porcentaje de elecciones sin ganador positivo.
- Criterio **por condición**: ≥18/20 semillas con precisión≥0.90 tanto tras A como tras B; ventaja media inicial≥0.30 sobre control congelado.
- **No preregistrar una selección ganadora entre las cuatro variantes.** Un éxito de `post_wta_gated` solo demuestra un escenario condicionado; si falla `pre_wta_all`, es información sobre la importancia de elegibilidad/orden temporal, no «fallo del ejecutable original».
- Reportar alcance temporal: se reinicia estado basal de Decision entre ensayos, por lo que aun un éxito no demuestra continuidad autónoma ni función completa de largo plazo.

## 4. Oráculos previos al código

- Con P0=P1=255 y dendritas de Concept STW128, C=**253**.
- Antes de reforzar, todas las conexiones Decision tienen STW0 y ambas neuronas obtienen score80.
- Primera recompensa en tick1, con Output elegido80, fuente253, químico255: susceptibilidad sube4 y STW sube3 únicamente en la clase excitatoria (para la neurona que tenga OUTPUT habilitada); LTW queda0.
- Con `post_wta_gated` y D0 elegida, las conexiones D1 no ganan susceptibilidad en tick1.
- Con `pre_wta_all`, ambas neuronas pueden modificar simultáneamente la susceptibilidad, pese a que solo una fue elegida.
- Sin feedback y sin actualización no cambia ningún peso/fortaleza durante holdout.
- Checkpoint reproducible de las cuatro sinapsis y contador.
- Reproducibilidad de 20 semillas; no acceso dentro del cerebro a `correct_action` o recompensa objetivo.
- La fase no modifica módulos de generaciones anteriores ni sus resultados.

**Gate G09.02g.2:** informar todas las condiciones, incluidos resultados negativos, y aprobar solo las que cumplan los umbrales. El objetivo de fase es detectar si la red mínima puede aprender **bajo convenciones temporales explícitas**, no proclamar emulación histórica.

**Próximo camino:** evaluar si la real causalidad de C1 requiere mantener el OUTPUT del tick anterior, incorporar la relajación neuronal y reacciones bioquímicas; o si una mente mínima propia puede aprovechar estos mecanismos sin replicar las limitaciones de C1.
