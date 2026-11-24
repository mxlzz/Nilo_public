# NeuroLab E09.02i–I3c.7h — resultado: contingencia de premio temporal importa, sin probar crédito individual ni persistencia G05

**22/11/2026 · experimento de desarrollo PREREGISTRADO antes de código y datos**, [protocolo corregido](E09_02I_I3C7H_CONTINGENCIA_PERMUTADA_PRE_REGISTRO.md) · [fe de erratas conceptual pre-datos](E09_02I_I3C7H_DECISION_CONTINGENCIA_CAUSAL.md) · [CI #44986258314](https://github.com/mxlzz/Nilo_public/actions/runs/44986258314) **SUCCESS 7/7 tests y ejecución íntegra de 20 semillas** · artefacto `neurolab-i3c7h-contingency-shuffle-fixed-c1` ID **14739997041**.

**Proveniencia:** archivo íntegro `i3c7h.json` **39.394.817 bytes**, SHA256 **`d723c4a590c0428e13b175c39cd9028c69ed5b714d000f46ada61717eebe925e`**, verificado al descargar y leer ZIP; lista de20 trayectorias `per_seed` SHA256 canónica **`dfb26799e560d072234224fd3075980fdd7a0104b3fc1486200731e556a10d41`**. [Hashes de cada semilla](resultados/e09i3c7h_resumen_y_hashes.json). No publicar genoma/EXE original propietarios; los artefactos son resultados experimentales. Su conservación en Actions es temporal, por eso se retienen huellas e instrucciones de reproducción.

## Diseño exacto y controles superados

- Cohorte nueva **1800..1819**, nunca usada antes. Misma microred **C1ContextBrain**, ocho dendritas/6 unidades, mismos genes de química I3, precursor80, decay40 sintético y **atrofia cerebral CHEM2/3=0** como ablación N *no histórica*. Dos fases con inversión de mapping A→B, **32 bloques×8 ticks** de entrenamiento y **16 bloques×8** de lectura por fase. Ningún cambio en núcleo neuronal, receptor o migración.
- **B** químico contingente con evaluación de la propia acción. **Y** replay exacto de B: **20/20 semillas×2 fases×256 ticks** con acción, estado neuronal y estado químico B/Y **idénticos a cada tick**. B replay coincide exacto con `I3c7e.run_phase(M0)`; no se usa B−Y como hipótesis causal porque la igualdad es matemática.
- **P** signos del mismo B reordenados una única vez con PRNG fija, **dentro de cada contexto/fase**. Mantiene cada tick con evento/None y los totales de premios/castigos **por contexto**, pero los signos ya no son contingentes de la elección de P. No se recalcula feedback desde P. **F** recibe la misma cinta de B, pero pesos congelados durante entrenamiento. **B/Y/F química íntegra idéntica tick a tick**; P no, porque el orden importa.
- [CI44986258314](https://github.com/mxlzz/Nilo_public/actions/runs/44986258314) validó siete contratos que incluyen permutación adversarial, integridad de cohortes, igualdad neuronal y química, fuente C1 original, congelación F y readouts sin nuevas recompensas.

## Resultado principal: exactitud `steady` bajo dinámica ACTIVE sin nuevos premios

**20 seeds agrupadas por semilla, IC95 bootstrap pareado2000 veces RNG60520.**

- **Primera fase:** B **0,8375**, P **0,5667**, F **0,5292**; B−P **+0,2708** (IC95 **[+0,1979,+0,3474]**), B−F +0,3083 (IC95 [+.2807,+.3380]).
- **Fase invertida (PRIMARIA):** B **0,8781**, P **0,4917**, F **0,4927**; B−P **+0,3865** (IC95 **[+0,2964,+0,4823]**), B−F **+0,3854** (IC95 [+.3526,+.4182]).
- Y= B en todas las observaciones por diseño. **FROZEN** fase invertida B **0,9760**, P **0,4990**, F **0,4927**. **No usar frozen alto como memoria activa estable**: bloquea relajación y pérdida de fuerza durante lectura.
- **Manipulación efectiva:** en primera fase **20/20** semillas cumplen≥10% de cambios de signo y proporción media reordenada **0,3684**; invertida **20/20**, proporción media **0,3789**. Hubo divergencia real de decisiones B/P en promedio **91,3/256** ticks durante primera fase y **127,45/256** tras inversión. El criterio previo ≥16/20 semillas y el umbral de interés B−P≥.10/IC95>0/B≥.75/B−F≥.10 se superaron. Eso **no** equivale a G05.
- **Contingencia accidental de P:** en ticks de entrega el signo permutado coincidió con el resultado de la propia acción P en promedio **0,5336** (fase1) y **0,4779** (fase invertida), frente a1.0 del brazo B. P no recibe un reward anti-objetivo fijo: la contingencia propia queda aproximadamente al azar a pesar de cantidades similares.
- **Por contexto:** en segunda fase, exactitud **overall** B S0=.8219/S1=.7875, P S0=.5898/S1=.3977, F ~.498/.484. El efecto no se restringe a un único contexto; el resultado `steady` primario es diferente de overall, no mezclar denominadores.

## La química NO es un tercer factor apareado por tick

La permutación conserva las entregas y cantidades de sustratos positivos/negativos, no el orden cronológico de metabolitos y reacciones. En inversión, la **AUC neural CHEM0/1** media de entrenamiento fue B **8980,85/3373,40**, P **8967,90/3238,50**; la química exacta post-tick B/P coincidió **sólo1 de5120 instantes** (20 seeds×256) en esa fase y25 de5120 en la primera, frente a igualdad B/Y/F total. Esto confirma que, aunque las AUC agregadas se aproximen, la cinética temporal difiere ampliamente.

**Interpretación permitida:** *desalinear experimentalmente las recompensas con las decisiones empeora marcadamente el comportamiento bajo el mismo presupuesto marginal por contexto*. **No permitido:** afirmar que la variable aislada fue sólo contingencia sin cambios químicos; identificar sinapsis que causaron cada elección; atribuir a la microred consolidación duradera u originalidad fisiológica C1. Es un contraste operacional de reordenamiento de valencias, no un oráculo de crédito causal.

## Persistencia y criterio G05

Aunque B alcanza0,878 en inversión ACTIVE, **sólo 2/20 semillas** (1804,1819) obtuvieron `steady≥0,90` en **ambas fases bajo ACTIVE**. P0/20, F0/20. **La meta preexistente G05 de ≥18/20 NO se alcanzó.** Las precisiones B por cuartos sucesivos del holdout ACTIVE invertido fueron **.8344/.8844/.7969/.7031**, frente P **.5156/.4781/.4688/.5125**. La pérdida de respuesta B aún es significativa al final, sin nuevos premios; STW en vivo del B al final del entrenamiento promedió3,7 contactos≥5, P5,0, y ambos mantuvieron8/8 conexiones bajo atrofia desactivada, lo que impide explicar todo sólo por fuerza0.

No se demuestra una mente autónoma, un Norn histórico completo ni `G05/G09/G00-H`. El resultado informa qué parte del aprendizaje es genuinamente sensible a la relación temporal recompensa–elección, y cuál de sus limitaciones exige examinar el circuito por dentro.

## Decisión científica

**G-I3c7h-SOFTWARE VALIDADA, G-I3c7h-INFORMATIVO VALIDADA, señal de interés precomprometida POSITIVA; G05/G09/G00-H ABIERTAS.** No repetir permutaciones, ni cambiar dosis, tasa128, loss0 o topología para obtener más éxito en estas semillas. Cohorte 1800..1819 ahora de desarrollo consumido; conservar intacta 1400..1419 para futura confirmación.

**Siguiente unidad con más información marginal:** examinar sinapsis individuales mediante **intervenciones contrafactuales de readout** en clones del mismo estado de cerebro (con y sin fuerza/contribución de cada conexión), usando código original y controles *sham*, antes de incrementar potencia, tamaños o seleccionar una arquitectura. Estas ablaciones pueden probar necesidad local de una conexión para la decisión en ese estado, **no que el propio feedback asignó correctamente crédito ni que dicha sinapsis sea necesaria universalmente**. Auditar primero disponibilidad de controles/repositorios ya existentes y definir estimando, ventana, tamaño muestral/coste en preregistro. No consumir otra cohorte sólo por inercia.
