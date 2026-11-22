# E09.02i–I3c.6c — resultado: cambiar CHEM no equivale a inhibir la pérdida de fuerza

**21/11/2026 · Resultado numérico preregistrado, sin entrenamiento neuronal nuevo.** [Preregistro anterior a código](E09_02I_I3C6C_UMBRAL_ATROFIA_PRE_REGISTRO.md) · [runner](../../experiments/neurolab/e09_i3c6c_functional_loss_threshold.py) · [CI #44966668042](https://github.com/mxlzz/Nilo_public/actions/runs/44966668042) **SUCCESS 4/4 tests**, archivo íntegro `neurolab-i3c6c-functional-atrophy-gate`, ID **14731529325**, retención90 días. Código original `emitter_tick`, `receptor_value`, `update_c1_synapse` y genes Decision no modificados.

## Método

33 valores exhaustivos de origen `locus0..32`, dos parejas originales:
- Emisor124 químico53→receptor127 CHEM2, clase excitatoria Decision.
- Emisor125 químico70→receptor128 CHEM3, clase inhibitoria Decision.

En cada valor: pool inicialmente cero, muestra de emisión tick0 y transferencia del receptor; luego se aplica el químico resultante a una dendrita artificial con `strength=4`, STW/LTW/susceptibilidad0, `source_output=0`, `owner_state=80` y tick sináptico5 (gene loss-rate5). Se inspeccionó directamente `lose_strength_rule_output`, valor CHEM, fuerza final y si hubo pérdida, sin tunear dosis/ganancia ni inventar una nueva regla. Los oráculos fueron idénticos para ambas clases.

## Resultado

- **Locus0–2:** receptor permanece CHEM16; fuerza `4→3` en tick5.
- **Locus3:** emisor entrega2, receptor reduce CHEM16→15; **la fuerza aún cambia4→3**. Una modificación analógica de CHEM no cambia la regla de atrofia.
- **Locus17:** receptor CHEM1, la pérdida continúa `4→3`.
- **Locus18:** receptor CHEM0, por primera vez `lose_strength_rule_output=0` y fuerza permanece **4**.
- **Locus18–32:** también inhiben la pérdida en el testigo aislado.

La SVRule de pérdida original simplemente devuelve CHEM2/CHEM3 y `update_strength` reduce fuerza si la salida es **no cero**, de modo que el **umbral funcional es 18**, y no3. Éste es un resultado matemático del mecanismo existente, no una suposición sobre el juego vivo.

El origen Type1 histórico es el mínimo de conexiones agotadas por clase/neuron recorrida. **Capacidad necesaria** para que esa ruta aislada pueda alcanzar18: al menos18 conexiones por clase/neurona implicada, **además** de suficientes fuentes candidatas para cumplir la restricción original de no duplicar orígenes. La versión fija tiene2 y la dinámica1; ambas son insuficientes. **Capacidad18 no garantiza que se agoten18 ni que la realimentación sea eficaz**, y tampoco que haya aprendizaje. El original tiene128 por clase/Decision y puede soportar esa magnitud, sujeto al resto de dinámica química/actividad.

## Consecuencia científica

**G-I3c6c-LOSS y G-I3c6c-SCALE validada para la prueba aislada. G05/G09/G00-H ABIERTAS.** No tiene fundamento «corregir» la red añadiendo un tercer contacto a cada clase o inyectando directamente químico53/70: el primer cambio de concentración no altera el comportamiento de `lose_strength`.

Antes de programar una variante nueva comparar opciones del [análisis I3c.7](E09_02I_I3C7_OPCIONES_AUTORREGULACION.md): (A) recuperar suficiente estructura/candidatos conforme a GEN y Type1 con controles, (B) separar adaptación N explícita de fidelidad C1 y someterla a ablación, o (C) conservar la ausencia de feedback y documentar su límite. Cada opción tiene costes y divergencias distintos; no interpretar un éxito de CI como aprobación de diseño.
