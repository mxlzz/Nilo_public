# E09.02i–I3c.6b — umbral químico y límite estructural del cerebro reducido

**21/11/2026. Resultado determinista preregistrado, SIN nuevo entrenamiento.** [Preregistro](E09_02I_I3C6B_UMBRAL_QUIMICO_PRE_REGISTRO.md) anterior al código, [módulo matemático](../../experiments/neurolab/e09_i3c6b_feedback_threshold.py) que llama **las funciones C1 ya existentes**, [CI #44966495426](https://github.com/mxlzz/Nilo_public/actions/runs/44966495426) **SUCCESS 4/4 pruebas**, artefacto **`neurolab-i3c6b-genetic-chemical-threshold`, ID14731344539** con ambas curvas completas para locus0..16. Ningún cambio a genes, tasa, química, red, método de aprendizaje ni `main`.

## Resultado que determina la viabilidad

Se reutilizó `Emitter/emitter_tick` (emisor124 locus1→químico53; emisor125 locus2→químico70, gain255 y flag1), junto a `Receptor/receptor_value` (genes127/128, CHEM2/CHEM3 nominal16 con inversión, gain255). Se verificó el fixture GEN original de SHA `e2bb4ccf6a4081a128c6c9ffc6eb233452d416717ceef47e78820ca3a152ddd4`. Con pool inicialmente cero, un único paso químico y sin otras fuentes:

- **Locus0:** emisión0; CHEM2/3 permanecen16.
- **Locus1:** emisión0 por truncamiento de `(1×255)>>8`; CHEM16.
- **Locus2:** emisión1, pero el receptor calcula una disminución0 de `(1×255)>>8`; CHEM16.
- **Locus3:** emisión2, reducción de receptor1; CHEM pasa a **15**.
- Para ambos pares de genes el **primer efecto receptor requiere locus3**. No basta producir químico con locus2.

El agregador histórico Type1, confirmado estáticamente en [I3c.6a](E09_02I_I3C6A_RESULTADO_REALIMENTACION_ATROFIA.md), envía al locus el **mínimo** de conexiones agotadas en la clase para registros neuronales recorridos. La topología de **C1ContextBrain** tiene sólo **2 dendritas por clase y neurona** (2 decisiones×2 clases=8), por lo que su mínimo nunca puede superar2. La de **DynamicContextBrain** tiene **1 por clase y neurona** (4 dendritas), cuyo mínimo no supera1.

**Resultado lógico:** el circuito original *aislado* emisor→receptor53/70 **no puede reducir CHEM2/CHEM3 por sí mismo en estas topologías**. Es imposible alcanzar el umbral3 aun si todas sus conexiones se agotan. El GEN original tiene hasta 128 dendritas por clase Decision, por lo que la imposibilidad corresponde a la reducción del laboratorio, no al C1 completo.

## Consecuencia y decisión

- **G-I3c6b-FUNCTION y G-I3c6b-TOPOLOGY verificadas** mediante las funciones existentes y tests; **G05/G09/G00-H ABIERTAS**.
- **No implementar conexión ciega de emisores** en las variantes actuales: activaría nuevas rutas de código pero, en estas condiciones de pool0 y sólo esos dos emisores, no cambiaría el locus receptor ni la atrofia. Un aumento de dosis para fingir el mismo resultado también divergiría de la bioquímica estudiada.
- La elección de diseño permanece ABIERTA entre (A) recuperar una **clase con ≥3 contactos** y comparar control estructural igualado, (B) introducir un **adaptador N explícito de señal** que conserve el mecanismo matemático pero remapee el conteo bajo una hipótesis, o (C) mantener el circuito acotado sin feedback y estudiar otra fuente histórica efectiva. Las tres requieren análisis de antecedentes y preregistro separados; **NO se eligió ni implementó arquitectura nueva**.
- No inferir que otros químicos o reacciones del metabolismo original no pudieran alterar CHEM2/3; el resultado se aplica estrictamente al trayecto aislado con pool inicial cero y sin emisores externos.

**Siguiente unidad recomendada:** comparar **sin codificar** las tres opciones y seleccionar el experimento de menor complejidad que pueda falsar una hipótesis sobre autorregulación/retención, con control de capacidad y cohorte nueva. No repetir I3c.5d ni aumentar gain/dosis por ajuste.
