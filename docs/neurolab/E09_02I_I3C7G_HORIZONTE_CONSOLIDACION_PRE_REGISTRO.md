# NeuroLab E09.02i–I3c.7g — preregistro de horizonte de consolidación de LTW, corto versus largo

**21-11-2026 · NL-EXP-I3c7g-v1 · PREREGISTRO ANTES DEL CÓDIGO Y NUEVOS DATOS.** Continúa [I3c.7e](E09_02I_I3C7E_RESULTADO_FACTORIAL_ATROFIA.md) y [I3c.7f](E09_02I_I3C7F_RESULTADO_PERSISTENCIA.md), ambos cerrados técnicamente, G05 abierta. **No se autoriza cambiar el cerebro, genes, dosis, tasa química o ganancia.**

## Hipótesis y alcance falsable

El cerebro `C1ContextBrain` inicia **LTW=0** y el gen Decision original cambia LTW a razón de como máximo **una unidad en ticks múltiplos de128**. Después de primera fase A de256 ticks y reversión B de256 ticks, sólo hay cuatro ticks habilitados globales (128,256,384,512); durante la inversión B **dos** (384,512), de modo que ningún enlace puede comenzar la lectura invertida con LTW≥5. Con Concept-output126 y atenuación Decision128, ya se verificó que se requiere **STW≥5** para contribución positiva; la LTW sola no puede sostener esa contribución en ninguna decisión del holdout invertido de ticks513..640.

**Pregunta:** ¿incrementar EXCLUSIVAMENTE el **presupuesto de entrenamiento después de la inversión** hasta ofrecer cinco oportunidades naturales de consolidación durante B (`ticks384,512,640,768,896`) produce pesos LTW funcionales y mejora la retención **ACTIVE-NOREWARD** de la misma microred y química?

**Distinción científica obligatoria:** la duración larga también añade48 bloques×8=384 decisiones y oportunidades de refuerzo. **No es una manipulación aislada de LTW**: compara **horizonte/experiencia disponible**, no permite atribuir una mejoría a LTW sin otros mecanismos. Es un ensayo de **viabilidad del presupuesto**, no confirmación histórica C1 ni prueba G05 por sí mismo.

## Cohorte/secuencias precomprometidas

- **20 nuevas semillas de desarrollo: 1700..1719**, nunca usadas en E09g/I3c.7; cohortes1400..1419 permanecen **reservadas y sin evaluar** para confirmación futura.
- Emplear `C1ContextBrain`, `ArmState`, `run_phase` y química de [I3c.7e](../../experiments/neurolab/e09_i3c7e_loss_factorial.py) con **idénticos genes, REWARD/PUNISHMENT directo255, precursor metabólico80, rate sintética40, sin emisores nuevos ni migración**. Reusar `blocks` del E09g.5, no inventar un generador.
- Fase **A original**: `blocks(seed,10000,32)`, 32 bloques×8=256 ticks de aprendizaje y `blocks(seed,30000,16)` de evaluación, mismo mapping A, **una sola ejecución por brazo**; clon exacto después de A para iniciar ambas ramas de fase B. Fase A no se usa para elegir caminos.
- Fase B, mapping invertido: prefijo `short = blocks(seed,20000,32)` (32 bloques, 16 por contexto), extensión `ext = blocks(seed,24000,48)` (48 bloques, 24 por contexto); `long = short+ext` (80 bloques, 40 por contexto). **Para cada modo el estado de entrenamiento, la química y el pending después de las primeras32 unidades de long deben coincidir byte a byte con el checkpoint short de tick512.** Si no, abortar; no recostear otras fuentes ni rerandomizar prefix.
- **4 brazos originales, todos sobre dos horizontes B**: `M0` químico80 con pérdida suprimida sintéticamente (sin confundir con GEN fiel), `M16` químico80 con pérdida nominal, `D0` directo255 sin pérdida como control positivo de fuerza de señal, `FM` química nominal con aprendizaje congelado como control negativo. 4×2 subramas B por seed, con estados iniciales idénticos para las dos duraciones de **cada modo**. No incluir modelos Q con token causal privilegiado ni buscar nuevos valores de dosis.
- Después de B corta o larga, usar **el MISMO holdout** `blocks(seed,40000,16)` y dos CLONES readout de128 ticks: `frozen (learn=False)` y `active_no_new_reward (learn=True)`, sin nuevos pulsos y conservando pool residual legítimo. La rama corta lee en ticks513..640, larga en897..1024, ambas finalizan en un tick múltiplo128. No usar lectura activa como entrenamiento posterior de la otra rama.
- Para D0-short, exigir de nuevo **identidad exacta** con `E09g.5 train_brain/evaluate_brain` para ambas fases, y para todos los modos B-short exigir reproducción de `I3c.7e.run_phase` con la secuencia idéntica por seed, incluyendo la fase A. La identidad de E09g5 no garantiza aprendizaje ni debe reemplazar el control negativo FM.

## Medidas, controles y umbrales predefinidos

**Primaria exploratoria:** precisión `steady` sin nuevos premios en fase B ACTIVE por modo y duración; contraste pareado por semilla `M0-long−M0-short` y `M16-long−M16-short`, y diferencia FROZEN−ACTIVE para cada horizonte. Informar también `overall` y exactitud por contexto sin elegir la mejor métrica.

**Mecanismo/práctica:** al terminar B (ANTES de holdout), contar dendritas vivas `strength>0`, dendritas vivas con **LTW≥5**, vivas con STW≥5, pesos LTW/STW completos y el tiempo desde la última actualización de LTW; contrastar la cota corta LTW≤4 contra valores reales largos. Reportar también número de decisiones, signos, recompensas, AUC química CHEM0/1, saturación pos-paso observada, pérdida/ganancia de fuerza y al finalizar ACTIVE, para que más práctica no sea ocultada como «consolidación mejor». Registrar intentos con `None`, no excluirlos.
 
**Análisis:** 20 clusters de semilla, bootstrap pareado **2000 réplicas RNG60519**; contraste primary con IC95 y números por seed en los cuatro brazos, no usar ticks individuales como independientes. Umbral exploratorio de efecto interesante: `M0 long−short ACTIVE steady >=0.10` con IC95 completamente>0 **y** evidencia de alguna LTW≥5 en un enlace funcional después de B largo. Si falla, no ajustar duración/tasa/dosis en esta cohorte; documentar posibilidad de que STW relajada/feedback on-policy o falta de estructura impidan retención.
 
**Puerta de aprendizaje G05 (NO reclamable aún con éxito):** criterio existente exige **≥18/20 semillas** con `steady≥.90` en ambas fases ACTIVE, ventaja sobre FM congelada en entrenamiento y evidencia de crédito causal sin privilegios; incluso si se cumple en esta exploración, debe confirmarse luego con cohorte independiente1400..1419 y controles de igual presupuesto. No convertir un contraste largo-versus-corto en prueba de que LTW fue la causa única.

**G-I3c7g-SOFTWARE:** E09g.5 D0-short paridad exacta, clones short prefix long idénticos, 20 seeds y4 modos×2 horizontes, control FM sin pesos aprendidos, no nuevos premios en evaluación, testigos de plasticidad intactos, trazas completas/hash por seed y CI con artefacto. G05/G09/G00-H ABIERTAS.

## Decisión posterior ya fijada

Si más tiempo B mejora M0 ACTIVE y aparecen LTW funcionales pero M16 sigue sin conectar, las causas se separan: insuficiencia de consolidación temporal y atrofia nominal. Después considerar un diseño de autorregulación **N explícito** sólo con ablation y control de costo, o bien mantener foco en C1 sin validar fidelidad global.

Si M0 largo permanece inestable **con LTW ya funcional**, la hipótesis limitada por calendario sola es insuficiente y hay que examinar crédito causal/representación antes de agregar tamaño. Si no alcanza LTW funcional pese a cinco oportunidades, observar por qué `ltw_toward` no converge con STW, no aumentar repeticiones por conveniencia.

No reusar seeds desarrollo para certificar G05, no merge PR#103, `main` y Nilo0.7 intactos.
