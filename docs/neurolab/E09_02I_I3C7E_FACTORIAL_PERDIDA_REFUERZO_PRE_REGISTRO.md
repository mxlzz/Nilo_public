# NeuroLab E09.02i–I3c.7e — preregistro: vía de refuerzo × régimen de atrofia con memoria activa

**21/11/2026 · NL-EXP-I3c7e-v1 · DOCUMENTO CREADO ANTES DE CÓDIGO Y NUEVOS DATOS.** Continúa [I3c.7d](E09_02I_I3C7D_RESULTADO_COMPARABILIDAD_ATROFIA.md). **Estudio de desarrollo experimental, no confirmación G05/G09.** La intervención nominal≠cero es una configuración de laboratorio; ninguna equivale a Norn histórico completo.

## Pregunta falsable

¿La ausencia de aprendizaje químico frente al fuerte benchmark directo de E09g.5 se debe, al menos en parte, a que los ensayos previos tenían **diferentes CHEM2/CHEM3 basales** y a que el holdout congelaba dendritas? Medir **interacciones** de dos factores:
1. **Vía de refuerzo:** pulso neural directo `(255,0,0,0)/(0,255,0,0)` frente al precursor metabólico80 de I3 vía reacciones y receptores originales, con receptor/decay de tasa40 sintética. Ambos responden al resultado de la **propia** elección (on-policy), sin token causal privilegiado.
2. **Régimen de pérdida:** `loss0` con CHEM2/CHEM3 del *input neural* desactivados como **ablación sintética explícita**, versus `loss16` conservando la salida nominal del receptor Decision original, normalmente16 sin emisores53/70.

No confundir una **ablación experimental CHEM2/3=0** con una corrección fiel a *Creatures 1*. La vía directa y química tienen distinta amplitud y retardo: **no se declaran dosis equiparadas**; dentro de cada vía comparar el efecto de la atrofia, con conteos de feedback y exposición informados.

## Cohorte y estímulos congelados

- **Semillas nuevas sólo de desarrollo 1600..1619, 20 semillas.** Las 1400..1419 permanecen sin consumir, reservadas para confirmación futura si existe hipótesis prometedora.
- Reusar exactamente `C1ContextBrain` (6 unidades/8 dendritas), `blocks` y `train_brain/evaluate_brain` de E09g.5 para el calendario de estímulos **32 bloques×8 ticks de entrenamiento por fase y 16 bloques×8 de holdout por fase**, con `blocks(seed,10000,32)`, `blocks(seed,20000,32)`, `blocks(seed,30000,16)`, `blocks(seed,40000,16)`. Mapping A, luego B invertido, **sin reset neural entre fases**.
- **4 brazos plásticos (factorial):** `D0` directo loss0, `D16` directo loss16, `M0` precursor loss0, `M16` precursor loss16. **2 controles congelados `FD` y `FM`** (un control por vía, con input nominal16 pero `learn=False` durante entrenamiento; no variar pérdida porque el congelamiento ya la bloquea). Todos parten de un mismo estado tipado y comparten estímulos/tiempos; después sus acciones y resultados pueden divergir.
- Cada tick de entrenamiento: el cerebro decide leyendo **solo contexto actual, estado anterior y químico del brazo**. El evaluador externo decide después si hubo acierto; para D el signo se entrega como pulso neural **en el tick siguiente**, exactamente el calendario `train_brain` E09g.5, con `pending` que continúa entre fases. Para M el evaluador agrega al pool, **después de la decisión y de avanzar la química de ese tick**, precursor `(33+1)` si acierto o `17` si error, dosis80; la química de receptor/bridge se lee por el cerebro en ticks posteriores. No inyectar etiqueta al cerebro.
- Ecuación de input por vía: D toma `REWARD/PUNISHMENT/ZERO` de `pending`; M toma `state.chemistry.decision_chem`; entonces aplicar al **solo input del cerebro** CHEM2/CHEM3=0 en brazos `loss0`, o conservar CHEM2/CHEM3 nominales en `loss16`. Los puertos/emisores del laboratorio siguen vacíos, la química global conserva originales `selected_genes`, `chemical_bridge_tick`, `decay_pool` con tasa40. **No modificar ningún helper ni gen**.
- **Control de paridad:** la rama `D0` **debe reproducir exactamente** la trayectoria neuronal y las precisiones de `e09_context_protocol.train_brain/evaluate_brain` para la misma semilla y secuencias, fase A y B (si difiere abortar). `D16` difiere de D0 solamente en CHEM2/3 del input y sus consecuencias on-policy. `M0` y `M16` conservan idénticas tasas/precursor, y difieren por pérdida/feedback on-policy posterior; no exigirles química idéntica una vez divergen las decisiones.
- **Instrumentación obligatoria:** por cada rama y fase registrar número de precursores/pulsos, acierto/error, AUC CHEM0/1 real leído, count `strength>0`, `STW>=5` en enlaces vivos, LTW positiva en enlaces vivos, pérdida y ganancia de strength según testigo sináptico original; checkpoints por seed y SHA de configuración/resultados. Si se altera el núcleo C1, abortar.

## Readouts: la parte que evita otro confusor

Después de cada fase de entrenamiento guardar el estado y ejecutar **dos evaluaciones independientes desde clones del mismo checkpoint**, sin ningún feedback nuevo:
- `FROZEN`: durante holdout usar `learn=False`; reproduce el estilo de E09g.5 y no debe modificar dendritas (incluida fuerza).
- `ACTIVE-NOREWARD`: durante holdout usar `learn=True` con entrada externa sin nuevos pulsos/precursor. Permite relajación, cambios de susceptibilidad y atrofia según CHEM2/3. La rama M retiene cualquier residuo químico legítimo anterior hasta su consumo/decaimiento; **registrar AUC** y no llamar esto «química cero». No reemplazar estado de entrenamiento con ninguno de los dos readouts.

En ambos casos precisión `overall` y `steady` (posiciones2–7), por contexto y fase. Además comparar **fuerza/STW/LTW y decay** al final del holdout. FROZEN y ACTIVE-NOREWARD no son equivalentes dinámicamente: su diferencia cuantifica efecto de permitir que continúen las reglas naturales de la microred sintética.

## Métricas, análisis, reglas de interpretación

**Primarias exploratorias:**
1. Exactitud steady y overall por fase A/B, brazo y tipo de readout; contraste pareado por semilla `D0−D16` y `M0−M16` en ACTIVE-NOREWARD y FROZEN, más dentro de cada brazo `FROZEN−ACTIVE`.
2. Integridad: trayectorias D0 idénticas al E09g.5 en ticks y readout congelado, con dos fases (no sólo media final). Controles FD/FM sin plasticidad en entrenamiento, sin atribución causal privilegiada.
3. Durabilidad: número de conexiones positivas en fin de entrenamiento y fin del holdout activo, STW≥5 y LTW positiva; ticks de pérdida/gain y saturación química observadas, evitando afirmar mismo feedback on-policy.

**Estadística:** 20 clusters de semilla con 2000 bootstrap pareadas y RNG60518. Reportar media y CI95 de contraste, ambos mappings/contextos, casos sin acción y sinápticos fuerza0. Un contraste descriptivo `abs(Δ)>=0,10` y CI95 excluyendo0 puede motivar una **confirmación posterior** con semillas1400..1419, **NO** superar G05 por sí solo. No seleccionar modo según éxito post hoc; no ajustar dosis/tiempo/genética tras resultados.

**Interpretación previa:**
- Si loss0 funciona y loss16 falla para igual vía, el régimen basal de atrofia limita el aprendizaje en este diseño, pero no prueba que la intervención original C1 esté mal.
- Si ambos modos difieren pese a igual pérdida, el feedback/retardo/exposición puede contribuir; la comparación D vs M sigue sin igualar amplitudes.
- Si FROZEN parece alto pero ACTIVE-NOREWARD se desploma, el benchmark anterior sobreestimó **persistencia funcional dinámica** al congelar la sinapsis; no afirmar que carezca de memoria en un modelo con otro metabolismo.
- Si hay aprendizaje robusto incluso en ACTIVE, planificar después estudio independiente de crédito y reversión; **no marcar G05 aprobada todavía**.

**G-I3c7e-SOFTWARE:** paridad D0 con E09g.5, controles/oráculos, 20 seeds×6 brazos×2 fases×dos readouts, JSON íntegro en Actions. **G05/G09/G00-H ABIERTAS en todos los resultados de esta cohorte.** No tocar `main`, Nilo0.7, GEN, EXE ni fusionar PR103.
