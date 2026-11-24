# E09.02i–I3c.7a — auditoría de reutilización y diseño de contraste G05

**21/11/2026 · DISEÑO Y AUDITORÍA, no nuevo entrenamiento ni selección de algoritmo.** Se recuperaron directamente los runners existentes [E03](../../experiments/neurolab/e03_protocol.py), [E09g.5](../../experiments/neurolab/e09_context_protocol.py), [E09g.10b](../../experiments/neurolab/e09_delayed_distractors_protocol.py), [I3b.1](../../experiments/neurolab/e09_i3b1_forks.py) y [I3c.4](../../experiments/neurolab/e09_i3c4_yoked_metabolic.py). Objetivo es **evitar duplicar herramientas y distinguir controles honestos de oráculos privilegiados** antes de tocar G05. Continuidad con [opciones I3c.7](E09_02I_I3C7_OPCIONES_AUTORREGULACION.md).

## Qué ya existe y qué demuestra

- **E03**: `PlasticLearner` propio asocia entradas A/B y revierte con un refuerzo explícito ±1 y pesos adaptables; el evaluador conserva el mapping, no el cerebro. CI exitosa para criterios preregistrados de su línea N. **No usa genes ni dinámica química C1** y no puede convertirse en oráculo de refuerzo químico Norn sin cambio explícito de modelo.
- **E09g.5 `C1ContextBrain`**: circuito de seis unidades y ocho dendritas con premios directos `REWARD=(255,0,0,0)`, castigos `PUNISHMENT=(0,255,0,0)`, controles `frozen` y `blind`. `train_brain` actualiza pulso pendiente tras cada tick y `evaluate_brain` congela pesos para medir. **Reutilizable** como control positivo de disponibilidad de señal y como control congelado/blind, **no es equiparable en amplitud** a la dosis de precursor80 tras reacciones.
- **E09g.10b `C`, `IG`, `F`, `Q`**: alterna cuatro ticks de contexto objetivo, distractores1–3 y tick de recompensa tardía. `C` usa pulsos directos, `IG` memoria interna de origen de dos bytes que filtra refuerzo según una heurística, `F` red congelada, `Q` tabla que conoce explícitamente la pareja objetivo/acción previa. **Q está mejor informado**, así que su superioridad no es comparación justa de representación cerebral; `IG` añade mecanismo de crédito que debe aislarse, no tratarse como C1 histórico.
- **I3b.1** ya cuenta con bifurcaciones `N/E1/L1/E4/L4` de un estado clonado y observadores, con gain4 **artificial** que elevó lectura única ~65% frente50%, no retención ni G05. Reutilizar el patrón de **estado común y testigo de transición** en vez de construir otro runner general.
- **I3c.4** implementa químico **yoked** por tick B/Y/F y verifica igualdad exacta, pero el feedback Y procede de elecciones ajenas; una mayor precisión de Y no probaría autonomía on-policy, y el experimento original terminó negativo.

## Dos experimentos diferentes que NO se deben mezclar

**Fase de ingeniería/mecanismo M (exploratoria):** clonar exactamente una decisión y su estado, aplicar distinta modalidad química a un mismo evento ya fijado, observar los efectos STW/fortaleza/atribución por origen y comparar contra N sin precursor y F congelado. El mapeo de verdad sólo llega al evaluador y determina **un único signo idéntico en ramas**. Ventaja: temporalidad y contexto emparejados. Limitación: exposición química/efecto sináptico NO equiparados; debe reportarse desnuda, sin llamarlo causalidad aprendida.

**Fase conductual C (confirmatoria eventual):** ejecutar múltiples decisiones con recompensa **on-policy** en el mismo cerebro, tarea original e inversión, holdout sin plasticidad, control sin aprendizaje y al menos referencia directa C con el mismo calendario de entradas. Las trayectorias de feedback divergen tras primeras decisiones distintas: **no afirmar yoking causal perfecto entre brazos on-policy**. Reportar por brazo el número de recompensas y química acumulada, no comparar como si hubieran recibido la misma intervención. La ausencia de señal/retención de I3c.5d/e obliga a verificar una condición mínima de STW funcional antes de G05.

## Bloqueos efectivos de diseño

1. **Equivalencia de amplitud no garantizada:** el pulso directo255 de E09g.5 no es comparable a químicos derivados de precursor80. Igualar «dosis de precursor», AUC, o `reinforcement_effect` en muestras no iguala necesariamente los tres simultáneamente. No usar ganancia4 de I3b.1 como solución preaprobada.
2. **Crédito del evaluador no debe filtrarse:** Q memoriza explícitamente (contexto,acción) y funciona como oráculo superior, pero una red neural que reciba esa identidad por software dejaría de probar atribución de crédito. `IG` filtra con memoria endógena y requiere comparación como mecanismo **N** propio, no histórico.
3. **Señal funcional:** medir fuerza>0 y STW/entrada >0 por conexión/owner, no confundir alteración numérica en un slot agotado con decisión afectada. Con Concept output126 el mínimo STW5 ya quedó observado en I3c.5e.
4. **Tiempo/repetición:** un único pulso antes de tick128 no prueba LTW; calcular explícitamente gates128/256 y supervivencia/recambio de conexiones en el experimento multi-episodio. No aumentar episodios sólo hasta encontrar positivos.
5. **Grupos:** las semillas0..419,800..919,1200..1219,1300..1319 están consumidas por ensayos previos; **1400..1419 permanecen reservadas**, no abrirlas para diagnóstico sin preregistro. Todo ajuste exploratorio exige grupo de desarrollo nuevo y holdout independiente.

## Recomendación de ejecución

**No escribir un nuevo sistema de aprendizaje.** Reusar primero observadores existentes, `C1ContextBrain`, `witness_step`, `neural_phase`, `I3c.4` para identidad química, y controles frozen/blind; conservar el tabular con origen explícito sólo como **cota informativa con privilegios**, no baseline par. El siguiente artefacto puede ser **un preregistro I3c.7b de comparación de mecanismo y gate de señal (sin datos ni entrenamiento)**, con un máximo de factores necesarios; sólo entonces código/test/CI. No seleccionar dosis o tamaño por precisión vista.

**Puertas de salida I3c.7a:** funciones existentes identificadas, controles y sesgos declarados, propuesta de fases M/C separadas, impedimento de emparejamiento de magnitud explícito. **Diseño AUDITADO, no experimento validado; G05/G09/G00-H ABIERTAS**. Ningún cambio a red, `main`, Nilo0.7 o genoma.
