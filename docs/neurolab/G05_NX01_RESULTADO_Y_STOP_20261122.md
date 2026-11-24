# G05-NX01 — cierre anticipado por saturación de baseline (22/11/2026)

**Decisión científica: STOP de esta configuración antes de ejecutar los brazos neuronales.** Se respeta la regla de mejora mínima del [preregistro G05-NX01](G05_NX01_PREREGISTRO_20261122.md). No se declara G05 superada ni se afirma que una red C1 fracasó en un ensayo que **no se ejecutó**.

## 1. Cadena de evidencia y reproducibilidad

- **Preregistro anterior a los modelos:** [G05-NX01](G05_NX01_PREREGISTRO_20261122.md), commit `ba305f5a1eab84f09ff505feb3b381049543ca43`, método, parámetros y criterio de ventaja de C frente al mejor control de al menos 0,05 puntos absolutos.
- **Software:** [runner limitado a baselines](../../experiments/neurolab/g05_nx01_baseline_gate.py). SHA256 de bytes `d45f550abde2fee73f464f5f42b748df27fe00133548cd2b58e08251fdd9b87c`; GitHub blob SHA `298b6141d04f46377c8629818989a9368879f3da`.
- **Ejecución:** [GitHub Actions #45059347950](https://github.com/mxlzz/Nilo_public/actions/runs/45059347950) **SUCCESS**, Python 3.13 y commit ensayado `f903517a1264932ffb35eb7f75ef4e20c47b171d`. Verificación independiente respecto del cálculo local: **mismo resumen y SHA256 de salida**.
- **Datos:** [resumen por cada una de las 20 semillas](resultados/g05_nx01_baselines_dev_summary_20261122.json), [artefacto Actions ID14768836126](https://github.com/mxlzz/Nilo_public/actions/runs/45059347950/artifacts/14768836126) con JSON completo 20 mundos × 3 controles × 2 fases, SHA256 de ese JSON `cf656497efa08e7510b21c63a65f0876ba657c08e45410f825d26c83d6b3bdc1`. **El ZIP temporal no es conservación indefinida:** se conserva código exacto y resultado por mundo versionados; el JSON completo se reproduce desde código y semillas. ZIP Actions SHA256 `2c8f6e0ea6c203c753c0dd7cbe26c0a767710760576fe031a30c6a629fde94ec`.
- **Solo desarrollo** `25000..25019`. **No se ejecutaron los brazos C, F ni P**, ningún nuevo mecanismo neuronal, ni semilla de confirmación `26000..26019`; anteriores `1400..1419` y `24000..24019` intactas. La cohorte desarrollo 25000..25019 ya está ABIERTA, y no debe tratarse nuevamente como nueva confirmación.

## 2. Resultados observados (20 mundos completos; ambas fases)

Métrica preregistrada `S=0.5*(accuracy_estable_A+accuracy_estable_B)` en holdouts sin recompensa, tras 2400 decisiones de aprendizaje por fase y drenaje de7 ticks.

- **T0 — tabla reactiva sin memoria de origen:** `S̄=0.9361207947`; 15/20 mundos perfectos en ambas fases.
- **Tλ — tabla con elegibilidad temporal:** `S̄=0.9346719231`; 15/20 mundos perfectos.
- **TK — tabla con buffer de siete acciones y soporte conocido de retardos {2,4,7}:** `S̄=1.000000`, **20/20 mundos perfectos en ambas fases**. No recibe `source_tick`, `target`, `mapping`, valor `delay` efectivo ni identificador de recompensa. Usa los retardos **posibles** como conocimiento estructural del diseñador, algo autorizado y declarado en el preregistro.
- T0/Tλ también se acercan al techo: el contexto persistente (probabilidad de cambio .10 por tick) permite correlación indirecta con recompensas antiguas incluso sin reconstruir su origen. El éxito de TK no demuestra que haya inferido la causa puntual de cada evento; solo que aprendió una política correcta y reversible bajo esta distribución.

## 3. Demostración lógica de STOP, no selección oportunista

El éxito obligatorio para habilitar confirmación incluía `S_C - S_mejor_simple ≥ 0.05` en desarrollo. Como `S_TK=1.0` y por definición `S_C≤1.0`, **`S_C-S_TK≤0` incluso si la microred C obtiene un resultado perfecto en cada mundo**. Por tanto, la puerta de avance **ya es matemáticamente imposible**, sin necesidad de correr C ni calcular significancia. Ejecutarla después consumiría presupuesto sin poder modificar la decisión preregistrada.

**Interpretación estricta:** este STOP no mide desempeño de C, ni descarta universalmente su elegibilidad, ni demuestra ausencia de crédito temporal. Detiene un desafío demasiado fácil para el mejor control simple. No modificar alpha, lambda, demoras, frecuencia de contextos ni límite de aceptación para rescatar la campaña.

El control TK usa un prior estructural de los retrasos posibles; aunque le retiráramos ese prior para facilitar la comparación, sería una **nueva pregunta y nuevo contrato**. No quitar retrospectivamente el baseline más fuerte solo porque saturó.

## 4. Auditoría de alineación y coste

- Objetivo central sigue siendo conocer una mente neuronal mínima con aprendizaje/memoria/adaptación; **una puntuación alta en una tabla no demuestra ese objetivo**, pero demuestra que este banco no permite elegir entre arquitecturas bajo su gate de superioridad.
- [E09](E09_CIERRE_FORMAL_RESULTADO_20261122.md) y [NR01](NR01_04_06_RESULTADO_Y_CIERRE_20261122.md) están cerrados parcial/negativamente. Añadir otra variación de mundo para intentar que la red supere a la tabla, sin hipótesis funcional independiente, arriesga diseñar pruebas a medida del modelo y repetir un esfuerzo sin información nueva.
- **Decisión para N experimental:** PAUSA de desarrollo neuronal incremental y de generación de nuevas cohortes. Conservar microC1 y las herramientas como **testigos negativos y oráculos técnicos**, no como arquitectura final.
- **Alternativa de continuidad de mayor valor con requisitos claros:** línea H histórica, especialmente determinar en el `Creatures.exe` original el orden de actualización neuronal/química, la semántica de recepción de refuerzo y las diferencias respecto de `C1ContextBrain`. Esto responde a la otra vía del objetivo original y puede fundamentar una nueva hipótesis N sin inventar mecánicas. **No afirmar que H está resuelta:** la documentación disponible es parcial y requiere evidencia primaria.
- **Nueva investigación N solo si** se identifica de forma independiente una capacidad no trivial que los controles más simples no resuelven, se preregistra antes de nuevas corridas y se explica por qué la información y el presupuesto son comparables. La pausa es la salida que autoriza el plan, no un fracaso de gestión.

## 5. Estado exacto de puertas

- `G05-INFO.01`: fuga del ensayo g.10b demostrada.
- `G05-INFO.02`: diseño de benchmark conceptual documentado.
- `G05-INFO.03`: factibilidad toy, PASS técnico CI.
- `G05-NX01`: **desarrollo parcial SOLO controles; STOP temprano justificado por saturación**; C/F/P no ejecutados; confirmación 26000..26019 BLOQUEADA; **no afirmación de G05 aprobado**.
- `G05`, `R-ACT-I3c`, `G09`, `G00-H`: **no superadas**. `main` y Nilo0.7 intactos; [PR#103](https://github.com/mxlzz/Nilo_public/pull/103) draft/no merge.

**Próxima unidad documental orientativa:** reconciliar hallazgos de H sobre reloj de actualización/recompensa e identificar una laguna forense concreta cuya resolución cambiaría la hipótesis; si depende de ejecutar o decompilar material original y el archivo no está accesible, detener en el límite de evidencia, no inventar reconstrucción.
