# E09.02i-I3a — diagnóstico post hoc, refuerzo sináptico observado (sin tuning)

**Fecha:** 2026-11-21. **Tipo:** exploración retrospectiva, **NO confirma ni reabre la puerta I3**. Preregistro anterior al código: [I3a](E09_02I_I3A_DIAGNOSTICO_POSTHOC_PRE_REGISTRO.md).

## Verificación de procedencia y equivalencia

- [Workflow #44952704490](https://github.com/mxlzz/Nilo_public/actions/runs/44952704490): **success**. Artefacto íntegro *neurolab-i3a-mechanistic-witness* ID **14726098025** con archivo e09i3a.json, vencimiento de retención 2027-02-19. [Resumen versionado](resultados/e09i3a_resumen.json).
- [Código observacional](../../experiments/neurolab/e09_i3a_diagnostic.py) reutiliza exactamente el brazo **M** original I3, cohorte 200..219, dos fases de 60 ensayos, tasas sintéticas40 y dosis80. No modifica C1ContextBrain, C1SynapticInput, STW, LTW, decisiones, química ni datos.
- Para **cada uno de los ocho contactos en cada tick**, ejecuta la función sináptica existente update_c1_synapse sobre el estado ANTERIOR y compara su resultado con la dendrita producida realmente por C1ContextBrain. **Todas las comparaciones coincidieron**. El estado completo tras cada fase coincide con la ejecución I3 sin instrumentación: *observación sin interferencia*.

## Conteos reales por fase sobre las mismas 20 semillas

| Métrica acumulada | Primera fase | Inversión |
|---|---:|---:|
| Evaluaciones de sinapsis | 67.200 | 67.200 |
| CHEM pertinente positivo | 13.308 | 13.500 |
| Susceptibilidad previa positiva | 47.769 | 48.202 |
| Ambos positivos simultáneamente | 9.850 | 9.836 |
| Reinforcement effect mayor que cero | **2.820** | **2.981** |
| Aumentos de STW | 1.724 | 1.828 |
| Cualquier cambio de STW | 3.787 | 4.034 |
| Cambios de LTW | **94** | **96** |
| CHEM máximo del canal relevante | 24 | 24 |
| Susceptibilidad previa máxima | 59 | 57 |
| Reinforcement effect máximo | **4** | **4** |
| Decisiones objetivo no emitidas | 71 | 75 |
| Inyecciones de precursor entregadas | 1.129 | 1.125 |

El refuerzo numérico fue positivo en **4,20 %** (fase1) y **4,44 %** (inversión) de todas las evaluaciones sinápticas, o en **21,2 %** y **22,1 %** de las evaluaciones que ya tenían CHEM relevante positivo. La LTW cambió en solo **0,14 %** de los eventos sinápticos, aunque esto no mide por sí solo retención conductual.

**Interpretación limitada:** la señal química **sí llega** y en algunos ticks afecta STW y LTW, por lo que es incorrecto afirmar que existe un corte completo de señal. El tamaño de efecto por evento no superó **4**. Ese contraste con los pulsos directos de **255** constituye una explicación mecánica plausible de la escasa ventaja M−F, pero **no es una demostración de causa única**: intervienen el retardo, el momento del objetivo/distractor, la susceptibilidad, la relajación y las reglas de decisión.

## Decisión después de observar (sin cambiar I3)

- **G-I3 se mantiene NEGATIVA**, tal como [preregistró y midió I3](E09_02I_I3_RESULTADO_NEGATIVO.md); ningún criterio, semilla, tasa ni dosis se reajusta.
- **G-I3a-OBSERVACIÓN válida**, no validación de aprendizaje: reenactment exacto y conteos reproducibles.
- Antes de un nuevo ensayo confirmatorio, la investigación debe separar al menos dos hipótesis: (A) amplitud insuficiente de las señales traducidas a CHEM y efecto STW; (B) crédito asignado a sinapsis distractoras por retrasos. **Primero buscar/identificar la dosis/tasas reales de GEN C1 o mecanismos de generación** para no ajustar artificialmente los parámetros a lo que funciona.
- Si se proponen controles contrafactuales (por ejemplo química sin retraso y con igual exposición total), preregistrar nuevas cohortes independientes; no llamar confirmatorio a datos reusados 200..219.

**G00-H/G05/G09/G-I1b-RATES abiertas**. El motor Nilo y main permanecen intactos, PR #103 continúa draft.
