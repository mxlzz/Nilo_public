# NeuroLab E09.02i–I3c.7k — preregistro POST HOC: suficiencia de transferir STW aprendida a LTW

**22-11-2026 · NL-AUDIT-I3c7k-v1 · ANTES DE CODIFICAR ESTA INTERVENCIÓN.** **La cohorte y su resultado original I3c7g YA se conocen**, incluso se analizaron retrospectivamente sus márgenes LTW en [I3c7j](E09_02I_I3C7J_MEMORIA_DIAGNOSTICO_ESTRATEGIA.md). Éste es un contrafactual de **capacidad de almacenamiento**, no nueva prueba ciega/independiente, no confirmación G05. **NO** cambiar reglas de `C1ContextBrain`, GEN, dosis, `ltw_rate128`, entrenamiento, número de sinapsis ni scheduler.

## Problema y falsación

I3c7g M0 LONG, pese a 75/160 LTW vivas≥5, **0/20** microredes tenían un margen LTW-only positivo en ambos contextos; su margen STW real sí era positivo en ambas en **18/20**. La pregunta es: si en el instante posterior al entrenamiento invertido se conservara exactamente la **información diferencial de STW** como LTW, ¿esa información bastaría para retener mejor las decisiones en el holdout ACTIVE de128 ticks cuando la plasticidad/relajación continúan y no hay más premios?

**Hipótesis operacional:** `C (copy)` obtiene `steady ACTIVE` superior a `S (sham)` y `X (swap)`; alternativa es que no mejore, lo que pondría en duda que la sola transferencia de contenido sea una solución suficiente. Ni un resultado positivo demuestra que el circuito pueda realizar por sí mismo esta transferencia: es una **intervención microscópica oráculo** sin etiqueta de respuesta, explícitamente **N artificial**.

## Cohorte/estado inmutable

- **No usar nuevas semillas**: las20 **1700..1719** de I3c7g, ya consumidas. `1400..1419` sigue intacta para confirmación futura. Sólo `M0`, química original con pérdida `CHEM2/3=0` sintética, sin atrofia, por ser el brazo donde quedó aislado el problema de peso funcional.
- Reutilizar exactamente `sequences(seed)` de [I3c7g](../../experiments/neurolab/e09_i3c7g_consolidation_horizon.py): fase A `blocks(seed,10000,32)` y B invertida LONG `blocks(seed,20000,32)+blocks(seed,24000,48)`. Entrenamiento termina en **tick896**. Reutilizar `run_phase(M0)`, `ArmState`, `C1ContextBrain`, receptores/reacciones; **NO** filtrar mapping ni `correct` dentro del cerebro.
- Guardar el manifest de **SHA256 por semilla del resultado original `I3c7g.run_seed(seed)`** (fuente íntegra original artefacto14733194016 / CI44970705424, 49.164.278 bytes SHA256 `128e92df48b749c046fb9e1b02fce3beb54f4c8b82ed814b067a7c8d0c215d78`). La matriz `per_seed` tiene SHA256 canónica `9343414af0f29260a0080dd950fbf3dab493633e2550669b999ec1f88e9783fb`. **Abortar** si un seed/manifest difiere.
- Reconstruir el `ArmState` en tick896 con las **funciones existentes** y cotejar exactamente (a) el vector `strength/STW/LTW` `end_weights` y (b) los 640 frames de entrenamiento B SHORT+ext con el registro original `I3c7g.run_seed`, antes de intervenir. En lectura `SHAM ACTIVE`, exigir igualdad total de métricas/frames con el `I3c7g` de esa semilla/horizonte. No mutar el checkpoint entre readouts.

## Intervenciones predefinidas, UNA vez justo antes del holdout

- **S (sham):** no modificar ningún estado, leer ACTIVE sin refuerzo.
- **C (copy):** para cada uno de los8 contactos `LTW_i := STW_i` tomados de la copia original en tick896. **Sólo LTW cambia**; STW inicial, susceptibilidad, fuerza, estado de neuronas, química y pool quedan *idénticos a S*. No inyectar valor correcto/contexto/owner/dosis; éste es un ideal de *transferencia instantánea de la memoria ya codificada en STW*, no aprendizaje de la regla.
- **X (owner-swapped control):** misma lista de ocho valores STW copiados, pero **`LTW_i := STW_{(i+4) mod 8}`**. Intercambia *los dos propietarios Decision* sin alterar el multiconjunto exacto de valores, su procedencia Concept/clase y la magnitud total de LTW. Mismo checkpoint y química; puede provocar interferencia mayor que S, que debe reportarse como cambio experimental legítimo y no como efecto específico sin control.
- **F (frozen):** lectura `learn=False` del estado S original, sin modificación, como límite alto de capacidad. No confundir su rendimiento con retención activa.
- En **S/C/X** utilizar la misma `blocks(seed,40000,16)` de128 ticks, **`active_no_new_reward`** del E09g.5/I3c7e, sin ningún feedback nuevo; el pool químico previo puede permanecer. En **F** usar idéntica secuencia y `learn=False`. Los tres activos deben cumplir `new_feedback_events=0` y partir de checkpoint químico IDÉNTICO. Los tres readouts son clones separados; no modificar el entrenamiento que continuaría a otra fase.
- **Control causal de entrada:** como el `C1ContextBrain.step` lee STW y no LTW directamente, las lecturas **FROZEN** de S/C/X deben dar **exactamente las mismas 128 acciones/scores**, aunque sus LTW sean diferentes (con `learn=False` no se actualiza peso). Si no, abortar: la intervención produjo una fuga/cambio de input indebido.

## Métricas y decisión sin tuning

**Primaria, exploratoria:** `steady ACTIVE` de fase B invertida por seed, diferencia pareada `C−S`; secundaria `C−X`, `S−X`, `overall`, precisión por contexto, precisión por cuarto fijo32ticks, enlaces vivos, STW≥5, LTW≥5 al final de128 ticks, feedback nuevo, química AUC. **20 clusters seed**, bootstrap pareado2000 réplicas PRNG **60522**, IC95. No tratar los 128 ticks como observaciones independientes.

**Puerta informativa de prueba de suficiencia**: al menos **+0,10** de diferencia `C−S` steady ACTIVE, **IC95 inferior>0**, `C−X ≥+0,10` con IC95 inferior>0, y FROZEN de los tres modos idéntico. Si se supera, se justifica **investigar** una regla local de consolidación diferencial; no demuestra que esa regla ya exista. Si falla, **NO** ajustar el valor copiado, timing, slots o duración por resultados de estas20 seeds; volver a pregunta de representación/estado de neurona/scheduler o reconsiderar propósito de G05.

**Robustez G05:** se reporta conteo de seeds `steady≥0,90` en ambas fases ACTIVE sólo como diagnóstico compatible con preexistente, pero **C es un oráculo artificial** y no puede superar G05 aunque ese conteo sea18/20. Los estados fase A no se reentrenan, no permitir usar el holdout como entrenamiento.

**G-I3c7k-SOFTWARE:** fuente original hash exacta, reconstrucción B LONG idéntica, per-checkpoint identidad, única alteración LTW, control X conserva multiconjunto de pesos, FROZEN S/C/X idénticos, readouts sin premios, estadística por seed, datos íntegros/erratas en CI. **G05/G09/G00-H ABIERTAS** independientemente del resultado. PR#103 draft, main/Nilo0.7 y GEN intactos.
