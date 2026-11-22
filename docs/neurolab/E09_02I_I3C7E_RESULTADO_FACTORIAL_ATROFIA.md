# NeuroLab I3c.7e — resultado factorial: el refuerzo químico aprende bajo exposición repetida, pero la retención activa es frágil

**21/11/2026 · estudio exploratorio preregistrado, G05 NO SUPERADA.** [Preregistro previo al código](E09_02I_I3C7E_FACTORIAL_PERDIDA_REFUERZO_PRE_REGISTRO.md) · [runner](../../experiments/neurolab/e09_i3c7e_loss_factorial.py) · [CI original #44969153930](https://github.com/mxlzz/Nilo_public/actions/runs/44969153930) **SUCCESS, siete tests, 20/20 semillas1600..1619, seis brazos y dos fases**, artefacto `neurolab-i3c7e-factorial-reward-loss-active-retention` **ID14733290218**. Se descargó el ZIP y se inspeccionó el JSON original de **39.359.911 bytes** SHA256 **`193ef109e214d33b9779611f1757d3bf23781755d38a0212778ed4269748752c`**; el subconjunto `per_seed` (trayectorias sin resumen estadístico) tiene SHA256 canónico **`311b387817b4f0d645cf191df99ae701641c11e9329758fe64f1f71701af8f8e`**.

**Nota sobre versión de análisis:** la primera CI incluyó medias de comparación FROZEN−ACTIVE pero omitió los **IC95 seed-cluster por brazo**, que el preregistro requería. Se corrigió **sólo la agregación estadística** en [código](../../experiments/neurolab/e09_i3c7e_loss_factorial.py), sin tocar `run_seed`, red, genes, estímulos, dosis o reglas. La [CI corregida #44969437429](https://github.com/mxlzz/Nilo_public/actions/runs/44969437429) **SUCCESS: siete tests**, artefacto **14732389870**, verificó SHA exacta de las 20 trayectorias neuronales originales `311b387817b4f0d645cf191df99ae701641c11e9329758fe64f1f71701af8f8e` y los IC95 de las seis comparaciones dentro de brazo. Es **la misma cohorte y las mismas trayectorias**, no una segunda prueba de hipótesis; conservar ambas versiones y artefactos.

## Diseño, control positivo y límites de comparabilidad

Misma red de 6 unidades y 8 dendritas, tarea exacta E09g.5 (32 bloques×8 ticks train y16×8 holdout por fase, A→B invertido), 20 nuevas semillas:
- **D0** pulso directo255, CHEM2/3 a0 como ablación nominal de pérdida (identidad exacta con E09g.5). **D16** mismo camino directo y CHEM2/3 del receptor nominal16.
- **M0** precursor químico80, CHEM2/3 del input neural forzados0 como **ablación N sintética, no original C1**. **M16** mismo precursor y CHEM2/3 nominal16 del genoma original, sin emisor endógeno53/70.
- **FD/FM** control `learn=False` en entrenamiento para cada vía. En todos los modos, recompensas generadas por la propia acción *después* de decidir; signos y cargas químicas posteriores pueden divergir on-policy.

Dos **readouts CLONADOS** después de cada entrenamiento: FROZEN (`learn=False`, como E09g.5, congela también atrofia), y ACTIVE (`learn=True`, **sin nuevos pulsos/precursor**, pero permite degradación y químicos residuales). Ninguno contamina el estado que continúa a la inversión. **El modo D0 reproduce exactamente** `train_brain` y `evaluate_brain` de E09g.5 en las dos fases (comparación de estados y métricas, no solo promedios): test exitoso.

Las dos vías NO igualan intensidad/tiempo: directo255 en un tick, precursor80 puede acumularse y tarda al menos la fase química; no usar comparación directa D−M como atribución causal exclusivamente bioquímica.

## Resultados, lectura más importante: segunda fase invertida

**Precisión steady media en 20 semillas**:
- **D0:** FROZEN **0,9760**, ACTIVE **0,9417**. **D16:** FROZEN **0,9776**, ACTIVE **0,9406**.
- **M0:** FROZEN **0,9521**, ACTIVE **0,8177**.
- **M16:** FROZEN **0,9276**, ACTIVE **0,6500**.
- **FD/FM:** alrededor de **0,4995** congelado y **0,4953** activo. La tarea no se resuelve simplemente por sesgo fijo de elección.

**Primera fase:** D0 frozen0,9724/active0,9260; D16 frozen0,9344/active0,8250; M0 frozen0,9557/active0,8344; M16 frozen0,8849/active0,6177. El patrón cualitativo se repite, con magnitudes no idénticas.

**Contrastes pareados por 20 semillas, bootstrap2000 RNG60518 (ACTIVE, fase invertida):**
- **M0−M16 = +0,1677** (IC95 **[+0,1391,+0,1990]**). Es la comparación principal del régimen de atrofia *dentro de la misma vía química*, aunque el feedback sea on-policy y diverja después de decisiones distintas.
- **D0−D16 = +0,0010** (IC95 **[−0,0234,+0,0250]**): no se observa diferencia media bajo el mismo contraste de atrofia, después de entrenar repetidamente con premio directo. En la primera fase D0−D16=+0,1010 IC95 [+0,0510,+0,1635].
- **D0−M0 = +0,1240** (IC95 **[+0,0802,+0,1682]**) incluso con pérdida química desactivada, pero **no** atribuir únicamente a vía directa: amplitud/retardo/exposición siguen distintos.
- **M16−FM = +0,1547** (IC95 **[+0,1146,+0,1958]**) en ACTIVE: hay cierta mejora química frente al control congelado en entrenamiento, aunque no haya robustez suficiente.

**FROZEN vs ACTIVE dentro del mismo brazo (segunda fase, per-seed bootstrap pareado):**
- D0 diferencia **+0,0344**, IC95 calculado desde el artefacto original [0,0182,0,0516].
- D16 +0,0370 [0,0177,0,0620].
- M0 +0,1344 [0,0901,0,1802].
- **M16 +0,2776 [0,2047,0,3417]**: la diferencia de lectura es sustancial. Los intervalos se recalculan en la CI de revisión, preservando la traza original.

## Persistencia sináptica y resultados negativos

Al finalizar el holdout ACTIVE de la fase invertida, **D0 y M0 conservan 8/8 enlaces activos en las20 semillas**. D16 conserva de6 a8 (media7,55). En **M16, 19/20 semillas terminaron con 0/8 y la restante con 1/8** (media0,05). Estas diferencias de conexión explican parte de la fragilidad de las asociaciones en este circuito, sin demostrar por sí solas la única causa de cada elección.

**Lectura temporal POST HOC del ZIP completo, no endpoint preregistrado:** para M16 ACTIVE invertido, el primer tick sin ninguna conexión ocurre entre los índices47 y117 del holdout para 19 semillas; la última todavía tiene una conexión en el tick127. En los cuatro cuartos sucesivos del holdout, la precisión total media (no sólo steady) fue **0,642 / 0,713 / 0,637 / 0,494**. M0 sin atrofia conserva8 links, pero su precisión también decae **0,836 / 0,828 / 0,747 / 0,572**. Por lo tanto **no atribuir todo el deterioro a fuerza0**: también interviene la relajación de STW, la magnitud de LTW, arrastre de químicos y cambios de contexto. Esta partición posterior no es análisis confirmatorio; el balance de contextos por cuarto no está garantizado.

**Robustez necesaria para G05:** con ACTIVE y criterio steady≥0,90 en **AMBAS fases**, D0 **13/20**, D16 **7/20**, M0 **1/20**, M16 **0/20**, FD/FM **0/20**. No alcanza la meta de ≥18/20 en esta exploración. El efecto positivo de M16 sobre el frozen control no equivale a un aprendizaje químico robusto, mucho menos a la mente autónoma original.

**Precaución bioquímica:** con pulsos por tick la exposición CHEM acumulada es mucho mayor que en un único evento I3c.7b. Se observó `pool_saturation_ticks=0` **solo en las muestras pos-paso** del auditor, con picos de refuerzo51/precursor1 hasta230 (menor255); no descarta saturación momentánea entre el agregado de precursor y el siguiente paso químico. No afirmar fidelidad metabólica a un Norn vivo.

## Conclusión y decisión de método

**G-I3c7e-SOFTWARE y revisión de IC95 validadas en CI original y CI de revisión. G05/G09/G00-H ABIERTAS.** La química con refuerzo repetido sí puede inducir discriminación del contexto en el modelo experimental, incluso bajo nominal16, pero la retención es inestable cuando siguen corriendo las reglas de fuerza y peso. El experimento factorial muestra un efecto importante de pérdida sobre M; **no permite separar a su vez amplitud, retardo y crédito causal** por vía. Mantener la elección de arquitectura abierta.

No gastar inmediatamente las semillas **1400..1419 reservadas** en confirmar un sistema que no alcanzó los criterios de robustez. Priorizar una auditoría mecanística de **STW/LTW funcional** con el mismo artefacto y de la trayectoria química completa: distinguir pérdida de conectividad de pesos vivos menores al umbral STW5, y verificar posibles picos pos-inyección. Solo después diseñar un ensayo independiente más discriminante, no optimizar precisión mirando estas semillas.
