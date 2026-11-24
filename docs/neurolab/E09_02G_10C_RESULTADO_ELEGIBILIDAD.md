# E09.02g.10c — resultado: persistencia de susceptibilidad y crédito que se dispersa

**Fecha:** 2026-11-21. **Tipo:** diagnóstico exploratorio post hoc de g.10b, preregistrado antes de instrumentar, no replicación fuera de muestra. [Protocolo](E09_02G_10C_SUSCEPTIBILIDAD_PRE_REGISTRO.md).

**Evidencia:** [GitHub Actions #44943178871](https://github.com/mxlzz/Nilo_public/actions/runs/44943178871), job `136964639554`, commit ensayado `7ec6fc0e0a8bef52886962dddad64350da0885a6`, **CI success, 313 tests con 2 expectedFailure históricos**. [Resumen JSON conservado](resultados/run-44943178871/e09g10c_summary.json); traza completa de 4.800 eventos en artefacto `neurolab-metrics/metrics/e09g10c_events.json` de Actions (retención temporal). Las 40 semillas y las fases g.10b se reprodujeron con **paridad exacta de estado final** respecto de `neural_phase`. No se cambió `C1ContextBrain`.

## Hallazgo central

La microred C1-reducida **ya tiene traza sináptica de coactividad**: cada dendrita Decision mantiene una variable `susceptibility` que aumenta según la regla genética `OUTPUT TRUE INPUT` y decae en el tiempo. La regla química modifica STW en función de susceptibilidad y concentración del pulso. No es una memoria explícita de identificadores de acción ni una prueba de que el Norn real maneje igual los distractores.

En el instante de aplicar la recompensa, después de 1, 2 o 3 distractores intermedios, la susceptibilidad de la conexión entre el **concepto objetivo** y la **decisión originalmente seleccionada** seguía siendo **positiva en 100 % de los 4.800 eventos**. Esto refuta la explicación de que la red ya había perdido completamente toda elegibilidad del contexto original. El efecto no implica que cada actualización posterior sea beneficiosa.

## Efecto químico del mismo tick (pulse vs ZERO)

Se evaluó el **mismo estado previo** dos veces, cambiando únicamente químico Reward/Punishment por ZERO en una rama contrafactual desechada. La diferencia de STW posterior mide el efecto inmediato del pulso, no la causa del éxito futuro.

En la primera fase A:
- Con **1 distractor**, el pulso cambió STW de la sinapsis del objetivo en **73 %** de los eventos, y la sinapsis del distractor en **33 %**; efecto medio de +8.32 STW objetivo frente a +3.28 distractor.
- Con **3 distractores**, el objetivo recibió efecto en **54.1 %**, el distractor en **53.4 %**; efecto medio de +4.63 objetivo frente a +5.76 distractor.

En la fase invertida B se repite la dirección del fenómeno:
- Con 1 distractor: cambio en STW del objetivo **67.4 %**, del distractor **17.6 %**; efectos medios +6.74/+1.98.
- Con 3 distractores: objetivo **49.4 %**, distractor **41.4 %**; efectos medios +3.62/+4.02.

También hubo cambios por pulso en conexiones del propietario no seleccionado; no se debe hablar de atribución exclusiva a una única sinapsis. En cada fase y duración hay 800 eventos, sin pulsos ausentes, para 40 semillas y dos contextos balanceados.

## Revisión de la hipótesis previa

- **Se confirma memoria temporal local:** el genoma C1 y la microred reducida codifican una forma de elegibilidad por susceptibilidad. Por ello sería redundante agregar ciegamente nuevas eligibility traces.
- **Se confirma pérdida de selectividad con interferencia** en esta prueba: el efecto de la recompensa deja de concentrarse en la sinapsis objetivo y crece también sobre conexiones del distractor a medida que hay más demora.
- **La compuerta IG de g.10a/g.10b no era un mecanismo de atribución:** en g.10b eliminaba un tercio de los pulsos; g.10c demuestra que en los momentos con distractor de un tick la red C tenía aún susceptibilidad objetivo y a menudo una actualización química positiva en esa conexión. IG podría por tanto suprimir refuerzo potencialmente útil, pero **no** se compararon estados IG/C idénticos a lo largo de todo el entrenamiento para cuantificar la contribución conductual exacta.
- **G05/G09 NO cerradas:** hay memoria de corto plazo, no prueba de atribución correcta y reversible en condiciones generales. El reloj cerebral y bioquímica exactos del ejecutable histórico siguen siendo parcialmente desconocidos.

## Decisión de continuidad y costo de oportunidad

**No seguir añadiendo neuronas, compuertas o hiperparámetros** a este clasificador de dos contextos. La tarea g.10b ya fue resuelta a 100 % por la memoria tabular 2×2 con procedencia explícita; C1 reducida tiene susceptibilidad real pero carece de selectividad suficiente con distractores largos. Probar variaciones arbitrarias sería poco informativo.

**Siguiente prioridad recomendada:** estudiar el reloj y la procedencia química originales de Creatures 1 y cómo determinan la elegibilidad y las consecuencias en una situación natural. Antes de crear un nuevo mecanismo, comparar **costo y capacidades** de (a) susceptibilidad C1 ya existente, (b) un buffer causal de eventos, y (c) trazas de elegibilidad TD(λ) documentadas en la literatura. Solo desarrollar una variante si surge una pregunta claramente discriminante, con un preregistro nuevo y baseline de menor complejidad.

**Integración:** ninguna con Nilo; PR #103 sigue draft, no se fusionó a main ni se redistribuyeron archivos originales.
