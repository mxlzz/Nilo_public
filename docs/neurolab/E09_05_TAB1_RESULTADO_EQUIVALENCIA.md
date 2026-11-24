# NeuroLab — E09.05-TAB1: resultado de equivalencia exacta E06 ↔ tabla asociativa

**22/11/2026 · control independiente implementado tras preregistro.** [Preregistro anterior al código](E09_05_TAB1_EQUIVALENCIA_PRE_REGISTRO.md) · [comparador tabular independiente](../../experiments/neurolab/e09_pair_tabular_equivalence.py) · [tests](../../experiments/neurolab/tests/test_e09_pair_tabular_equivalence.py) · [CI #45028224155](https://github.com/mxlzz/Nilo_public/actions/runs/45028224155) SUCCESS · artefacto [#14756368469](https://github.com/mxlzz/Nilo_public/actions/runs/45028224155/artifacts/14756368469) (`neurolab-e09-tab1-fair-tabular-exactness`, JSON+SHA256, retención de GitHub 90 días) · commit del runner **`81af65e81e2554cfc9533bef9e418d5c96b1140f`**. Los archivos fuente se conservan en GitHub para regenerar el JSON sin depender del artefacto temporal.

## Resultado verificado en logs de Actions

- **4/4 tests exitosos**: replay original+reversión, invariancia de bit contextual, empates/saturación, exclusión de entradas fuera de dominio.
- **20/20 semillas de desarrollo E06 (0..19)**, sin nuevas semillas de confirmación.
- **38.720 comparaciones** del dominio legal completo (4 pares×2 contextos por estado alcanzado); **1.600 decisiones holdout** adicionales del protocolo original.
- **4.800 actualizaciones** plásticas pareadas, incluyendo entrenamiento original y fase de reversión diagnóstica sin reset.
- **0 discrepancias** en decisión, puntuaciones, pesos por acción y contador; `all_equal=true`. El check de resumen JSON del workflow también pasó.
- Artefacto zip SHA256, declarado por GitHub: `01fee34891b2802b4fc5e55c9e27c04bf62c1e17ba97d14accaedf6bfedf3348` (hash del ZIP, NO confundir con el SHA256 del JSON interno).

**Alcance temporal:** 120 entrenamientos +80 decisiones holdout +120 reentrenamientos invertidos por semilla, con invariancia para todos los ocho estímulos legales después de cada actualización. Los 20 seeds **son reutilizados**, pero la afirmación primaria es igualdad estructural por inducción; las pruebas detectan errores de implementación, no constituyen validación estadística de la arquitectura en otro problema.

## Por qué es equivalencia matemática y no solo coincidencia de porcentajes

En E06 se activa **exactamente un detector** de los cuatro pares codificados; los puntajes de cada acción son literalmente los dos enteros STW/weight de esa conexión. El bit contextual se descarta por el diseño original del detector. Una tabla de cuatro filas×dos pesos por acción, con el **mismo extractor de pares y presupuesto de ocho pesos**, calcula el mismo `argmax` y recibe exactamente la misma actualización local (±16, saturada). Dada inicialización idéntica y mismo reward por ensayo, acciones, pesos y estados son idénticos para **cualquier secuencia legal** (inducción), no solo las probadas.

**No** se afirma equivalencia para entradas múltiples/sin par, conceptos aprendidos dinámicamente, redes recurrentes, C1 histórico, bioquímica o refuerzos retrasados: esos escenarios se excluyeron antes del código.

## Consecuencia científica y decisión

El hallazgo original E06 **1,0 frente a memorizador exacto de cinco bits 0,5** es válido para aquel control, pero **no demuestra una ventaja exclusiva del circuito neuronal**. Compara dos representaciones distintas: el memorista exacto separa contextos C=0 y C=1 mientras el detector de pares descarta C desde el diseño. Con la **misma representación fijada de antemano**, la tabla asociativa obtiene necesariamente desempeño idéntico. Una futura comparación E09.05 no debe usar solo el memorista de cinco bits para justificar mayor complejidad neuronal.

**E09.05-BL-E06: resuelto analíticamente y verificado** como equivalencia de funcionalidad en el dominio original. **G06 permanece éxito limitado de invariancia contextual**, no aprendizaje autónomo de conceptos. **G09 abierta**: no hay aún una arquitectura integrada mínima ni prueba de ventaja en memoria durable, crédito temporal o recableado.

**Ahorro de trabajo justificado:** se descarta implementar por ahora un adaptador E03+E06 cuyo único objetivo sea reproducir esta misma representación/actualización. Si surge una nueva hipótesis sobre estados continuos, interferencia o aprendizaje de nuevos detectores, requerirá otro protocolo con una predicción discriminante; no reabrir automáticamente este test. No modificar `C1ContextBrain`, `main`, Nilo0.7 ni consumir semillas1400..1419.
