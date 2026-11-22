# NeuroLab — control de alineación antes de abrir nueva etapa (22/11/2026)

**Clase:** auditoría de continuidad, no experimento ni aprobación de nueva línea. **Jerarquía:** [issue #102](https://github.com/mxlzz/Nilo_public/issues/102) → [README maestro](README.md) → [puertas reconciliadas](E09_00R_RECONCILIACION_GATES_20261122.md) → [cierre E09](E09_CIERRE_FORMAL_RESULTADO_20261122.md) → [plan NR01](NR01_PLAN_INVESTIGACION_REPRESENTACIONES.md) → [cierre NR01](NR01_04_06_RESULTADO_Y_CIERRE_20261122.md).

## 1. Objetivo que no debe perderse

Estudiar **cuáles son los mecanismos mínimos inspirados en Creatures 1** para que un cerebro aislado adquiera, conserve, modifique, transfiera y reorganice asociaciones a partir de experiencia. En la línea histórica H, reconstruir lo que efectivamente hizo C1; en la línea experimental N, contrastar mecanismos con controles y medir su necesidad. **No** añadir cuerpo, mundo, LLM ni integrar en Nilo 0.7 por inercia.

## 2. Veredicto sobre trabajo realizado

- **Método y continuidad: alineación positiva.** E09 se cerró honestamente sin superar G09, tras equivalencias E03/E06 con controles tabulares, E07 sin ventaja sobre LRU y fallos de crédito temporal/retención. NR01 era **una nueva pregunta justificada y diferenciada**, formalizada en plan separado y con alternativas existentes, no una alteración retroactiva de G09.
- **Ejecución de NR01: alineación positiva con su plan.** Generador/decoders/controles y preregistros anteriores a datos, 20 mundos desarrollo × 2 familias × 8 brazos, observaciones comparables, diagnóstico de costo y stop gate. [CI #45049703202](https://github.com/mxlzz/Nilo_public/actions/runs/45049703202) SUCCESS: 320 condiciones, 0 errores, 104 ART fuera de presupuesto. KMeans4 vs mejor baseline FIFO 1NN: +3.53pp, menos que umbral5pp; reversión A de KMeans4=.4875 vs 1NN=1.0. **NR01.05 no habilitada; no usar confirmación24000..24019.**
- **Objetivo científico principal: INCOMPLETO.** Ni E09 ni NR01 acreditan una misma mente neuronal mínima que integre aprendizaje, memoria, reversión, generalización, crédito causal y reorganización. NR01 prueba una capacidad representacional particular, no resuelve crédito G05, retención R-ACT-I3c ni síntesis G09. No interpretar el stop de una arquitectura concreta como refutación universal de redes neuronales ni como cierre de NeuroLab.
- **Riesgo documental específico:** el [issue #102](https://github.com/mxlzz/Nilo_public/issues/102) y apartados históricos del [README](README.md) conservan descripciones iniciales/pasos obsoletos; el [marcador canónico](ESTADO_Y_CONTINUIDAD.md) contiene secciones cronológicas con estados contradictorios si se leen fuera de contexto. Respetar encabezado vigente y fecha; no ejecutar próximos pasos de secciones antiguas.

## 3. Dictamen y puerta previa a cualquier etapa nueva

**No hay justificación para reanudar tuning miniC1, elevar presupuesto ART, reabrir NR01.05 o inventar NR02 automáticamente.** El plan permite resultados negativos y detener una línea sin acabar la investigación.

**Próxima unidad recomendada (DOCUMENTAL, no aprobada como nueva campaña):** reevaluar explícitamente 2–3 preguntas pendientes contra el objetivo original, sin ejecutar modelos ni consumir semillas: (a) G05, atribución del refuerzo retrasado bajo distractores y baselines causales simples; (b) memoria y estabilidad tras reversión/intervalos sin premio frente a caches y memoria no neuronal; (c) aprendizaje representacional composicional solo si existe un caso de uso con déficit demostrable respecto a controles simples. La arqueología H se mantiene en línea separada; abordar una laguna de C1 solo si cambia el diseño o la interpretación.

Cada opción tendrá: pregunta falsable, evidencia ya obtenida, alternativas existentes, control más simple, qué resultado cambiaría una decisión, recursos, condición de detención y dependencia con G09. **Si ninguna promete información decisiva, pausa del programa N sin desarrollar**. Propuesta no equivale a permiso para iniciar una nueva etapa experimental.

## 4. Estado de conservación

Todo NeuroLab permanece en [PR #103](https://github.com/mxlzz/Nilo_public/pull/103) **draft**; `main` y Nilo 0.7 sin cambios. No se tocan semillas confirmatorias ni archivos originales de C1. Este documento no modifica resultados históricos ni reabre gates.

**Próximo paso concreto:** antes de pedir nuevas corridas, presentar una elección justificada entre preguntas pendientes o una pausa. La decisión deberá registrarse en el protocolo, no improvisarse durante desarrollo.
