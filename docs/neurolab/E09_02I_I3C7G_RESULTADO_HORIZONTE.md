# NeuroLab I3c.7g — resultado: LTW≥5 aparece con mayor entrenamiento, pero NO mejora retención activa

**21/11/2026 · EXPERIMENTO EXPLORATORIO PREREGISTRADO, G05 NO VALIDADA.** [Preregistro](E09_02I_I3C7G_HORIZONTE_CONSOLIDACION_PRE_REGISTRO.md) **anterior al código y resultados**, [runner reutilizando código E09g.5/I3c.7e](../../experiments/neurolab/e09_i3c7g_consolidation_horizon.py), [CI #44970705424](https://github.com/mxlzz/Nilo_public/actions/runs/44970705424) **SUCCESS 6/6 tests**, artefacto ZIP `neurolab-i3c7g-short-long-original-ltw-gates` **ID14733194016**. JSON íntegro **49.164.278 bytes, SHA256 `128e92df48b749c046fb9e1b02fce3beb54f4c8b82ed814b067a7c8d0c215d78`**; las20 trayectorias `per_seed` SHA256 canónica **`9343414af0f29260a0080dd950fbf3dab493633e2550669b999ec1f88e9783fb`**. Se descargó y analizó el artefacto completo después de CI, sin descartar casos.

## Diseño efectivamente verificado

- **20 semillas nuevas1700..1719** (cohorte de desarrollo, ahora consumida), cuatro brazos `M0` químico80 con pérdida anulada sintéticamente, `M16` químico80 con pérdida nominal16, `D0` directo255 sin pérdida (control positivo), `FM` química con entrenamiento congelado (control negativo). Todos con el **mismo** `C1ContextBrain` de ocho dendritas, GEN, receptor, reacciones, tasa química40, sin migración ni nuevos emisores.
- Fase A idéntica a E09g.5, 32 bloques×8 ticks, hasta tick256, con identidad exacta de D0 frente a `train_brain/evaluate_brain`.
- Fase B invertida **SHORT32 bloques×8=256 ticks** versus **LONG80 bloques×8=640 ticks**; **los primeros32 bloques son idénticos**, estado neuronal + químico + `pending` de refuerzo en tick512 exacto; LONG continúa SHORT con48 bloques balanceados extra (24 de cada contexto), no vuelve a sortear ni reinicia.
- Decisiones por fase B: SHORT256, LONG640; por eso LONG recibe mucha más práctica y refuerzos. Los holdouts de128 ticks usan idéntica secuencia por seed, con clones `FROZEN` y `ACTIVE sin nueva recompensa`; en ACTIVE sigue evolucionando el pool químico residual. Sin label/acción causal privilegiados en el cerebro.
- Original LTW por genoma `ltw_rate=128`: fase B corta habilita ticks384/512 (2 consolidaciones post-reversión), larga ticks384/512/640/768/896 (5); el máximo teórico global al final de B corta es LTW4 y al final de larga LTW7, desde0.

## Resultado primario: LONG contra SHORT, fase B ACTIVE sin premios nuevos

**Exactitud steady media sobre20 semillas (no seleccionar subgrupo):**

- **M0:** SHORT **0,8599**; LONG **0,8370**; LONG−SHORT **−0,0229** (IC95 seed-bootstrap **[−0,0828,+0,0297]**). No mejora consistente.
- **M16:** SHORT **0,6490**; LONG **0,6729**; diferencia **+0,0240** (IC95 **[−0,0307,+0,0792]**). Tampoco mejora consistente.
- **D0:** SHORT **0,9214**; LONG **0,8568**; diferencia **−0,0646** (IC95 **[−0,1266,−0,0005]**). Caída exploratoria tras más práctica; el resultado es compatible con interferencia/actividad, no prueba que el entrenamiento largo sea nocivo en general.
- **FM control sin aprendizaje:** SHORT **0,4688**; LONG **0,5156**; diferencia **+0,0469** (IC95 **[+0,0172,+0,0760]**). **Advertencia metodológica**: hasta sin plasticidad las trayectorias neuronales/contexto/tiempo pueden cambiar la precisión; por eso LONG vs SHORT no aísla LTW. No interpretar el desplazamiento de FM como aprendizaje.

## Gate molecular verificada, pero insuficiente

Antes del holdout invertido, cantidad total de sinapsis VIVAS con **LTW≥5** (20 seeds×8 slots = máximo160 por modo):
- **SHORT:** 0 en todos los modos, como exige la cota matemática previa.
- **LONG M0:** **75/160**, presentes en **20/20 semillas**; las ocho sinapsis siguen vivas en todas.
- **LONG M16:** **35**, presentes en **18/20 semillas**; fuerza activa promedio al inicio del holdout **4,5 de8**, frente a **4,65 de8** SHORT.
- **LONG D0:** **160/160**, en20/20 semillas.
- **LONG FM:** **0**, como debe ocurrir con entrenamiento congelado.

La hipótesis de factibilidad **LTW≥5 después de cinco oportunidades** SÍ fue verificada para M0 y también para M16/D0. Pero el criterio preregistrado de mejora conductual química M0 LONG−SHORT≥0,10 con IC95>0 **NO** se cumplió: `exploratory_feasibility_M0=false`. El mecanismo de consolidación cruzó el umbral, pero **no se tradujo en mayor retención conductual bajo este calendario y tarea**.

**Más práctica no puede atribuirse a LTW sola:** M0/D0 LONG recibieron **640** eventos externos de feedback en fase B, contra **256** SHORT; M16 recibió en promedio **634,55** LONG y **254,2** SHORT por algunas acciones ausentes. El camino químico puede acumular o cambiar exposiciones, y el aprendizaje on-policy produce trayectorias distintas después de la divergencia temporal. No declarar igualdad química entre brazos LONG/SHORT.

## Robustez y fases

Tomando criterio `steady≥.90` en **ambas fases bajo ACTIVE**, sobre20 semillas:
- M0 SHORT **3/20**, M0 LONG **3/20**.
- M16 SHORT **0/20**, M16 LONG **0/20**.
- D0 SHORT **9/20**, D0 LONG **6/20**.
- FM **0/20** en ambas duraciones.

**Ninguna rama** supera el umbral preregistrado general de **≥18/20** para G05. Los controles congelados FROZEN pueden seguir siendo altos, pero no miden retención autónoma con plasticidad activa.

## Conclusión y decisión crítica

**G-I3c7g-SOFTWARE VALIDADA, gate molecular de LTW≥5 VALIDADA, mejora ACTIVE y G05 NO VALIDADAS. G09/G00-H ABIERTAS.** Ya no es defendible seguir atribuyendo el fracaso de retención *solo* a falta de oportunidad de consolidación. Dos limitaciones previas se mantienen (fuerza perdida bajo nominal16, STW que se relaja en M0), pero **ni suprimir pérdida ni aumentar el horizonte alcanza para robustez**. Puede haber interferencia on-policy, atribución de recompensa a distractores, representación pobre o una definición de estabilidad inadecuada para este tipo de agente; ninguna está probada causalmente por este ensayo.

**Siguiente unidad con mayor retorno científico:** antes de aumentar arquitectura, diseñar **un contraste de contingencia causal apareado** de refuerzo sobre la misma microred: con igual calendario y exposición química por tick, comparar recompensa vinculada a la propia elección contra recompensa desconectada de esa relación (control yoked), manteniendo pérdida y tiempo constantes. Ya existe una implementación parcial de yoking [I3c.4](E09_02I_I3C4_QUIMICA_APAREADA_PRE_REGISTRO.md), pero fracasó entonces con bajo refuerzo/atrofia; **revisar reutilización antes de crear código**. El contraste no puede suponer que igualar química haga idéntica la política on-policy, y debe registrar ese límite. No ajustar tasa/dosis ni asignar etiqueta de objetivo al cerebro.

Preservar `main`/Nilo0.7 intactos y PR#103 draft; no gastar semillas1400..1419 reservadas de confirmación hasta tener un mecanismo causal defendible. No promover LTW≥5 aislada como aprendizaje duradero.
