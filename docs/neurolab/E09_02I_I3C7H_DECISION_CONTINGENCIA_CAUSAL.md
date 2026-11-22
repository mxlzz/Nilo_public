# NeuroLab E09.02i–I3c.7h — evaluación previa de alternativas para crédito causal apareado

**21/11/2026 · DISEÑO DE PRÓXIMA UNIDAD, NO PREREGISTRO NI NUEVA IMPLEMENTACIÓN.** Contexto empírico: [I3c.7e](E09_02I_I3C7E_RESULTADO_FACTORIAL_ATROFIA.md), [I3c.7f](E09_02I_I3C7F_RESULTADO_PERSISTENCIA.md) y [I3c.7g](E09_02I_I3C7G_RESULTADO_HORIZONTE.md). En la última, incluso con LTW≥5 en20/20 semillas químicas M0 después de entrenamiento B largo, **ACTIVE LONG no mejoró sobre SHORT** (−0,0229, IC95 [−0,0828,+0,0297]); M16 también fue no concluyente. G05/G09/G00-H permanecen abiertas. No seguir aumentando entrenamiento/gain/nodos de manera incremental.

## Qué investigar ahora

**Pregunta con mayor valor:** ¿la vía química está asignando sus cambios sinápticos a conexiones relacionadas causalmente con la decisión, o sólo acumula señal general durante estímulos presentes? La sensibilidad C con recompensa directa I3c.7b afectó también fuentes distractoras (472/1196 unidades) y su mejora fue transitoria. Los resultados M0/M16 muestran adquisición de asociación con repetición pero retención frágil; no basta con LTW funcional.

El repositorio YA TIENE:
- `e09_i3c4_yoked_metabolic.py`: construcción de feedback desde un **brazo referencia** y copia del mismo calendario de precursores a brazos Y/F, con igualdad exacta de estado químico por tick, además de testigo de eventos None. **NO reusar el runner completo**: funciona con `DynamicContextBrain` de cuatro contactos, Type1 migration y ensayos objetivo/distractor con delay, y falló cerca de0.50 cuando conexiones se agotaban; copiarlo introduciría dos factores (migración/topología) además de contingencia.
- `e09_i3c7e_loss_factorial.py`: `C1ContextBrain` de ocho dendritas, 256 ticks train E09g5 por fase con el circuito químico original sintético, hooks para `CHEM2/3` y lectura ACTIVE/FROZEN, testigo sináptico exacto, estados/clones tipados. **Este es el núcleo a reutilizar**.
- `e09_i3c7b_paired_signal.py`: bifurcaciones del mismo estado y control positivo/neutro, testigos de fuerza/STW y química. Reutilizar sólo testigos/estructura, no necesariamente su protocolo de un pulso.
- `e09_delayed_distractors_protocol.py`: control Q con token explícito (contexto,acción) es **privilegiado**, no baseline equivalente; `IG` introduce mecanismo propio, no C1 original.

## Comparación justa que se debe preregistrar ANTES de código

Usar mismo `C1ContextBrain`, calendario de bloques/cambio de mapping y tasa/dosis de I3c.7e. Para **una sola** condición de pérdida explícita primero (propuesta `loss0` como control instrumental para evitar agotamiento antes de medir crédito, sin venderla como original C1):
- **B**: plasticidad, feedback químico generado por su propia decisión/resultado **después** de elegir, como M0.
- **Y**: plasticidad, estados iniciales idénticos, recibe *exactamente* los mismos eventos externos de B (incluyendo signos, None, tick y dosis), pero su recompensa NO se calcula desde la elección de Y. Química completa B/Y debe ser idéntica por tick aunque sus estados neurales diverjan.
- **F**: dendritas congeladas durante entrenamiento, recibe calendario químico B para separar aprendizaje de exposición/percepción. La química B/Y/F debe coincidir byte por byte en train; si no, abortar antes de interpretar score.
- **R (opcional si aporta contraste real)**: copia de los signos de B **permutada de forma balanceada antes del ensayo** dentro de un calendario que conserve números de positivos/negativos y retardo por fase. No puede tener química per-tick idéntica a B al permutar signos; representaría otro contraste y debe etiquetarse separado. **No sumar este brazo sin demostrar que añade discriminación**.

**Precaución causal fundamental:** Y puede tener diferente acción porque aprendió algo distinto; yoking iguala química pero hace que sus recompensas no sean contingentes. Por lo tanto B−Y mide utilidad de contingencia bajo la misma exposición química con trayectorias neurales potencialmente divergentes; **no identifica sinapsis causales individuales**. Además Y puede coincidir con B aun con aprendizaje legítimo si las decisiones apenas divergen; registrar acuerdo B/Y y número de eventos en que la acción Y difiere, con intervalos. Si las políticas nunca divergen, la comparación no tiene poder y no debe presentarse como éxito.

**Lectura primaria:** holdout ACTIVE sin nuevos premios, precisión por contexto/phase y ventaja B−Y; medir fuente causal/no causal de refuerzo y LTW/STW con fuerza positiva, acuerdos de elección durante train, proporción de recompensas Y «correctas» bajo su propia decisión aunque generadas en B, y diferencias por signo. Reportar test FROZEN como secundario, retención durante128 ticks, no sólo accuracy final. Semillas independientes nuevas (no usar 1400..1419 confirmación); predefinir gate de utilidad B−Y, costos y corte si no hay divergencia/si el control B cae cerca de azar.

**Recomendación:** **reutilizar** el núcleo E09g5/I3c.7e con la rutina de identidad química de I3c.4, sin añadir neuronas, algoritmo propio de memoria, agentes, migración ni ajuste de parámetros. Antes de programar un ensayo nuevo cerrar sólo dos elementos: (1) cómo congelar de forma exacta el calendario de eventos de B sin convertir a Y en predictor con información oculta, (2) qué calendario de práctica asegura señal funcional suficiente para medir crédito sin cambiar variables simultáneamente. Las semillas1700..1719 están ahora consumidas por I3c7g, y no son holdout.

**Estado:** evaluación de alternativas/próxima unidad definida, **no hay experimento I3c.7h ejecutado**; G05/G09/G00-H ABIERTAS. PR#103 sigue draft, `main` y Nilo0.7 intactos.
