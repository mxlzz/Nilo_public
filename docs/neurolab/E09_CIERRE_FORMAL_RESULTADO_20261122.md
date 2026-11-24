# NeuroLab — cierre formal de la fase E09: resultado parcial y puerta G09 no superada

**Fecha:** 22/11/2026. **Decisión aprobada:** el usuario autorizó cerrar E09 con las limitaciones reales, preservar evidencia y explorar una nueva pregunta de adquisición de representaciones **sin volver a tunear miniC1**. **Alcance:** cierre metodológico de la *campaña experimental N E00–E09*, no cierre definitivo de NeuroLab, no declaración de éxito global, no incorporación a Nilo 0.7. PR #103 permanece draft.

## 1. Pregunta original y distinción del alcance

[Issue #102](https://github.com/mxlzz/Nilo_public/issues/102): si una microred inspirada en Norns puede aprender, conservar, reaprender, generalizar y reorganizar asociaciones, sin una respuesta codificada por acción. [Etapas E00–E09](ETAPAS_00_09.md), [errata de puertas](E09_00R_RECONCILIACION_GATES_20261122.md).

- **H** reconstruye solo lo verificable de C1 histórico; GEN y EXE se inspeccionaron parcialmente pero H no tiene implementación integral; arqueología **continúa como línea separada bajo preguntas acotadas**.
- **N** examina un circuito mínimo experimental; las diferencias de las reglas C1 se documentan; no hay cuerpo, mundo, semántica de agente, conciencia ni LLM.
- **E09:** síntesis mínima reproducible para determinar qué mecanismos son esenciales, redundantes, no demostrados y si conviene crecer/revisar/detener. No supone construir un organismo autónomo.

## 2. Dictamen científico

**Logros reales por módulo:** motor neuronal verificable E01, selección E02; aprendizaje y reversión de E03; separación funcional aislada STW/LTW E04; detección conjuntiva con invariancia contextual E06; recableado con costo de olvido E07; dinámica recurrente elemental E08. En química/genoma C1 existen análisis parciales, efectos locales causales de recompensa y contacto STW, con evidencia mayormente experimental/forense controlada. [Auditoría](E09_01_AUDITORIA_CAPACIDADES_20261122.md).

**Resultados negativos/limitaciones decisivas:**
1. **E03 es exactamente tabular** bajo su prueba original de dos estímulos, reinicio por episodio de tres ticks y cuatro pesos [TAB2, CI45028560329](E09_05_TAB2_E03_RESULTADO.md). No implica que la plasticidad E03 sea falsa, solo que la topología neuronal no aporta función distintiva demostrada.
2. **E06 es exactamente tabular** bajo la conjunción A×B precodificada de cuatro pares, bit contextual irrelevante y ocho pesos [TAB1, CI45028224155](E09_05_TAB1_RESULTADO_EQUIVALENCIA.md). El sistema no aprendió sus detectores ni comparó originalmente una tabla con la misma extracción de features.
3. **E07 migra sinapsis, pero empata con LRU**, y olvida patrones previos; no hay ventaja sobre una gestión simple de memoria.
4. **G05 original (crédito temporal selectivo) NO se superó** con distractores; que exista elegibilidad no basta.
5. **R-ACT-I3c (retención activa sin nuevo premio) NO se superó** en miniC1. I3c7h verifica premio contingente y I3c7i causalidad local de STW; I3c7k no llega al umbral de suficiencia del oráculo de consolidación. No transformar los resultados negativos en inexistencia universal de aprendizaje neuronal.
6. La integración E09 `CoupledState` es **parcial real** entre neuronas y química, no un cerebro que exhiba simultáneamente todas las capacidades E03–E08; no hubo ablación de una arquitectura unificada ni mínimo de coste probado.

**Por tanto, puerta G09: NO SUPERADA.** Lo que sí queda cerrado es la decisión de **REVISAR / DETENER ESTA CAMPAÑA DE INGENIERÍA INCREMENTAL**, una salida contemplada por el plan. No se declara una «arquitectura neuronal mínima resultante» que no existe. E09.02/03/04/08 quedan explícitamente **sin validación integral**; la declaración formal de cierre administrativo no maquilla esas lagunas.

## 3. Reproducibilidad y conservación

- [Índice E01–E08](E09_EVIDENCE_INDEX.md), [síntesis E09.08–.10](E09_08_10_SINTESIS_DECISION_20261122.md), [auditoría archivística](E09_01_07_PRESERVACION_EVIDENCIAS_20261122.md).
- [Archivo adicional de ocho ZIP de resultados clave](E09_ARCHIVO_EVIDENCIAS_20261122.md) en Drive del usuario, SHA-256 y procedencia versionados en GitHub; los originales del juego no se incluyeron ni se hicieron públicos por GitHub.
- Persiste una laguna: algunas trazas secundarias de Actions no están preservadas fuera de su retención. La documentación puede apoyar resultados limitados y críticos, no una publicación que requiera trazas integrales de todas las corridas sin una nueva auditoría.
- Se conserva **sin borrar y sin alterar** tanto lo que falló como los casos de éxito; semillas confirmatorias 1400–1419 reservadas y no consumidas.

## 4. Continuidad autorizada — separada de E00–E09

Abrir una **línea exploratoria distinta `NR01` (representaciones adquiridas)**. No es E10 retroactivamente incorporada al plan y no altera G09. Antes de código: investigación comparativa de herramientas existentes; fijar tarea que no entregue conceptos precodificados, representaciones aprendidas *solo* de experiencia, control tabular con igual información, costo/retención/transferencia y gates previos.

**Gate para reabrir implementación:** [NR01 plan metodológico](NR01_PLAN_INVESTIGACION_REPRESENTACIONES.md) y revisión de alternativas; si falta pregunta discriminante, se suspende en fase documental. La libertad de escoger una solución tabular, simbólica o híbrida permanece: la meta no es «ganar con neuronas» sino aislar la capacidad mínima y útil.

## 5. Qué no está autorizado

- No introducir mundo/cuerpo, funciones de supervivencia, personalidad, autonomía general o LLM.
- No arreglar retroactivamente G05/G09; no modificar microC1 para lograr métricas.
- No consumir holdouts históricos ni elevar recursos/costos sin justificación.
- No fusionar PR #103 ni tocar `main`/Nilo0.7, ni publicar bytes propietarios `Creatures.exe`/`dad1.gen`.

**Estado formal:** **E09 terminada como campaña, con resultado parcial/negativo y G09 sin superar**. La decisión de una nueva rama/arquitectura depende de un gate de NR01, no de inercia del historial.
