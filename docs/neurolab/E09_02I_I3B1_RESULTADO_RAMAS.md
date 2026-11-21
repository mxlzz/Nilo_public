# E09.02i-I3b.1 — resultado de bifurcaciones químicas pareadas

**21/11/2026. Resultado:** G-I3b1-WIRING **SUPERADA**, G-I3b1-OBSERVACIÓN **SUPERADA** (datos positivos y nulos conservados). **G05/G09 NO EVALUADAS**, I3 del modelo completo continúa NEGATIVA. Esto es una microintervención controlada, no aprendizaje vitalicio ni emulación histórica C1.

## Procedencia y reproducibilidad

- [Preregistro previo](E09_02I_I3B1_RAMAS_QUIMICAS_PRE_REGISTRO.md), seguido por implementación [e09_i3b1_forks.py](../../experiments/neurolab/e09_i3b1_forks.py), [tests](../../experiments/neurolab/tests/test_e09_i3b1_forks.py), [GitHub Actions #44956959320](https://github.com/mxlzz/Nilo_public/actions/runs/44956959320) **success**; artefacto **neurolab-i3b1-paired-forks**, ID **14728625057**, contiene JSON por episodio, expira 2027-02-19.
- **Falló primero una aserción del test** en [run #44956919841](https://github.com/mxlzz/Nilo_public/actions/runs/44956919841): exigía igualdad de todo el brazo neutro entre mappings A/B, pero el atributo etiquetado de «acierto» cambia por definición aunque el estado y la acción sean idénticos. Se corrigió **solo el test** (commit d40136ab8946eb39d9c56bda74e051dd1230c9ca), separando resultado sin etiquetar de etiqueta del evaluador; test suite específica **7/7** tras corrección. No se alteró simulador, preregistro, parámetro ni umbral.
- 20 semillas **300..319**, objetivo0/1, demora1/2/3, mappings A/B, **240 episodios** de un pulso. Acciones originales presentes 240/240, signos 120 correctos y 120 incorrectos por mappings invertidos. Misma topología 6 unidades/8 dendritas, tasa química **40 sintética**, dosis **80**, genes de reacción57/71/111/112; 5 ramas N/E1/L1/E4/L4.
- Contrastes pareados por **semilla-cluster**, percentiles de bootstrap 95% sobre **20 semillas** y 2000 réplicas seed60513. Los 240 episodios NO se consideran independientes para incertidumbre.

## Principales diferencias preregistradas

| Contraste | Diferencia media | IC bootstrap95% |
|---|---:|---:|
| Ganancia4−1, inyección temprana: suma de efecto en sinapsis candidatas | **+7,575** | [6,375; 8,700] |
| Ganancia4−1, inyección tardía: suma de efecto en sinapsis candidatas | **+6,492** | [5,325; 7,559] |
| Temprana−tardía, ganancia1: fracción de refuerzo en sinapsis del contexto objetivo | **+0,17736** | [0,13720; 0,21459] |
| Temprana−tardía, ganancia4: misma fracción | **+0,11202** | [0,10361; 0,12062] |
| Temprana−tardía, ganancia1: efecto acumulado candidato | +0,2583 | [0,1167; 0,4083] |
| Temprana−tardía, ganancia4: efecto acumulado candidato | +1,3417 | [1,1917; 1,4919] |

Clasificación «sinapsis candidata»: recibe Concept del objetivo **y** pertenece a Decision de la cuarta acción; «sinapsis de distractor»: recibe Concept opuesto, con cualquier Decision. **No son sinapsis cuya causalidad individual haya sido identificada experimentalmente.** El contraste temporal cambia la concentración en cada tick por decaimiento (mismo precursor inicial, no misma exposición temporal).

## Respuesta conductual secundaria y mecanismo

- Promedio de acierto de la **cuarta acción de lectura después de un solo evento**, sin nuevas recompensas ni plasticidad durante los cuatro ticks de lectura: N **0,5000**; E1 **0,5000**; L1 **0,5000**; E4 **0,65417**; L4 **0,65000**.
- Contrastes E4−N +0,1542 (IC cluster post hoc [0,0208; 0,2750]) y L4−N +0,1500 ([0,0375; 0,2500]). Estos intervalos se calcularon después de ver el archivo para una **métrica secundaria preregistrada, no contraste primario**; no reinterpretar como validación autónoma.
- Ninguna rama tuvo cambio **LTW** respecto de N. **Limitación del DISEÑO, no dato de falta de capacidad:** tronco termina en tick36; intervención llega hasta tick46–48 y lectura hasta tick50–52. El gen Decision tiene **ltw_rate=128**, y el helper C1 solo actualiza LTW si tick módulo 128 = 0. Por tanto el ensayo **jamás atraviesa un tick elegible de consolidación**. No usar este cero para concluir «el cerebro no puede consolidar».
- E1/L1 con ganancia1 producen efecto químico positivo, pero no cambian el acierto agregado en lectura. Ganancia4 es una manipulación artificial **NO C1 histórica**: muestra que intensidad de señal y ubicación temporal influyen mecánicamente, no justifica subir permanentemente el gain a4.
- **G05 crédito causal sigue ABIERTA**: clasificación objetivo/distractor no identifica sinapsis realmente causantes de acción y un pulso no prueba aprendizaje con experiencia acumulada.

## Siguiente unidad y puerta

**I3b.2 ventana LTW de 128 ticks**: [preregistro de fase](E09_02I_I3B2_VENTANA_LTW_PRE_REGISTRO.md) antes de código, semilla nueva, mismas dosis/reacciones, medir LTW exactamente al cruzar tick128 con evento temprano vs tardío. La prueba no será histórico-C1 completo ni G09. No tocar main ni Nilo0.7, PR#103 draft.
