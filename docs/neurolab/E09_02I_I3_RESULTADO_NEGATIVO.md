# E09.02i-I3 — resultado conductual negativo, preregistrado y conservado

**Fecha:** 2026-11-21. **Resultado científico: G-I3 NO SUPERADA.** El proceso técnico de GitHub Actions **sí finalizó correctamente**, pero el rendimiento del brazo metabólico M no superó al control congelado F.

## Identidad y evidencia

- [Preregistro I3](E09_02I_I3_BENCHMARK_PRE_REGISTRO.md), creado **antes** del código y los resultados; cohorte fijada 200..219 (20 semillas), dos fases A/B con inversión, entrenamiento60 y holdout36 ensayos por fase y semilla, 4 ticks objetivo + 1–3 distractores + 1 tick de llegada.
- [Runner fijo](../../experiments/neurolab/e09_i3_metabolic_protocol.py), [tests](../../experiments/neurolab/tests/test_e09_i3_metabolic_protocol.py), [workflow independiente](../../.github/workflows/neurolab-i3.yml).
- [GitHub Actions run #44952276187](https://github.com/mxlzz/Nilo_public/actions/runs/44952276187) **success**; artefacto completo **neurolab-i3-metabolic-preregistered**, ID 14725468833, contiene e09i3.json y su duplicado stdout, **20 semillas**, retención hasta 2027-02-19. [Resumen JSON versionado](resultados/e09i3_resultado_resumen.json).
- **Parámetros de laboratorio, NO C1 histórico:** tasa de decaimiento química **40 para cada uno de los 256 químicos**, dosis externa precursor **80**; cuatro reacciones genéticas de C1 57,71,111,112; receptores cerebrales 88,89,126..129. Sin emisores neuronales conectados automáticamente.

## Resultado primario (exactitud del objetivo en holdout, media 20 semillas)

| Brazo | Primera fase | Inversión | ≥90 % en ambas |
|---|---:|---:|---:|
| **M**: química + plasticidad | **0.513889** | **0.534722** | **0/20** |
| **F**: misma química, sin plasticidad | 0.512500 | 0.534722 | 0/20 |
| **C**: refuerzo directo original, referencia no apareada | 0.890278 | 0.845833 | 8/20 |
| **Q**: tabla con información causal explícita, referencia privilegiada | 1.000000 | 1.000000 | 20/20 |

**Ventaja M−F** promediando ambas fases: **+0.0006944**, equivalente a **+0.06944 puntos porcentuales**. Gate preregistrada (18/20 semillas M ≥0.90 en ambas fases, medias≥0.85, cada demora≥0.70 y M−F≥0.15): **FALSE**. Se cumplió la regla de conservar el fracaso; no se ajustaron dosis, tasas, pesos, neuronas ni umbrales.

Por demora d=1/2/3, M primera: **0.441667 / 0.570833 / 0.529167**, M inversión: **0.550000 / 0.558333 / 0.495833**. La media C primera se mantiene ~0.89 pero no es comparador pareado porque recibe pulsos directos de magnitud y cronología distintas. Q dispone de token explícito de origen/acción; su 100 % no demuestra ventaja entre métodos con igual información.

## Controles e indicadores secundarios

- M: se contabilizaron **71 decisiones objetivo no emitidas** en entrenamiento de la primera fase y **75** en la fase invertida, agregadas entre 20 semillas (20×60 decisiones objetivo por fase). F no registró decisiones objetivo faltantes en esas fases. Observación, **no atribución causal**.
- Máximos de concentración al final de los ensayos registrados en M y F: Reward49≤**25**, Punishment50≤**25**, Reinforcement51≤**109**. **Ninguna saturación 255** en el punto final de ensayo según la métrica preregistrada. No descarta picos intermedios no muestreados.
- Las lecturas CHEM son una transformación del pool vía receptores, con retardo temporal adicional; el origen puede generar refuerzo sin que éste produzca cambios STW medibles. **Hipótesis abierta** a observar cuantitativamente, no afirmar sin medir.
- La comparación M/F es *on-policy*: las recompensas generadas por el evaluador dependen de las elecciones de cada brazo, de modo que sus trayectorias químicas pueden divergir. El test de software no demuestra crédito causal correcto.

## Interpretación y decisión

**Comprobado:** el enlace químico funciona matemáticamente y se mantiene reproducible, **pero no reproduce el aprendizaje robusto del brazo con refuerzo externo directo** en esta tarea y parámetros. Este resultado negativo ayuda a localizar una insuficiencia de la integración o del régimen de recompensa; **no permite determinar cuál sin análisis adicional**.

**No concluye:** que un Norn C1 real no aprenda, que la química histórica esté mal diseñada o que la plasticidad neuronal sea inviable. La línea N usa tasas sintéticas y carece de metabolismo, emisiones cerebrales automáticas y aprendizaje estructural de Concept.

**Próximo paso exacto:** **E09.02i-I3a, diagnóstico observacional post hoc** sobre las mismas semillas congeladas: auditar señales CHEM efectivamente presentes, susceptibilidad, efecto sináptico de refuerzo y cambios STW. Preservar código/modelo y resultados I3; **no tunear dosis ni tasas**. Solo después decidir si se debe recuperar el genoma/tasas o redefinir un experimento confirmatorio con nueva cohorte.

**Puertas:** I1/I2/I1b técnicas verificadas; **I3 negativa**, G-I1b-RATES, G05, G09 y G00-H ABIERTAS. PR #103 draft, main y Nilo0.7 intactos.
