# NeuroLab — E09.08–.10: síntesis científica y decisión de continuidad (22/11/2026)

**Tipo:** síntesis documentada tras [E09.00R](E09_00R_RECONCILIACION_GATES_20261122.md), [auditoría E00–E08](E09_01_AUDITORIA_CAPACIDADES_20261122.md), [evaluación de integración](E09_02_EVALUACION_INTEGRACION_MINIMA_20261122.md), [TAB1 E06](E09_05_TAB1_RESULTADO_EQUIVALENCIA.md) y [TAB2 E03](E09_05_TAB2_E03_RESULTADO.md). **No es una aprobación de G09** ni una nueva arquitectura. Respeta [etapas y puertas originales](ETAPAS_00_09.md).

## 1. Pregunta general y hallazgos

**Meta original** ([issue #102](https://github.com/mxlzz/Nilo_public/issues/102)): identificar mecanismos mínimos inspirados en *Creatures 1* que, en una mente neuronal aislada, posibiliten asociación, conservación, reversión, transferencia y reorganización, antes de imaginar cuerpo/mundo/LLM. La reconstrucción H y la experimentación N son vías independientes; no se confunde exactitud en test con organismo inteligente.

**Resultado discriminante de E09.05:**
- [E03](E09_05_TAB2_E03_RESULTADO.md) aprendizaje y reversión episódicos, originalmente 20/20 semillas, **idénticos** bajo el contrato E03 a una tabla simple de **2 entradas×2 acciones, cuatro pesos**. El WTA y la actualización neuronal se reducen a selección y cambio de la fila, gracias al reset de tres ticks.
- [E06](E09_05_TAB1_RESULTADO_EQUIVALENCIA.md) detector conjuntivo fijo frente a señales contextuales irrelevantes, originalmente20/20, **idéntico** bajo entrada legal E06 a tabla de **cuatro pares×dos acciones, ocho pesos**, con la misma representación precodificada. La ventaja contra memorizar 5 bits completos se debe a descartar `C` por diseño de features, no a un mecanismo neuronal exclusivo.
- [E07](E09_EVIDENCE_INDEX.md) migración bajo dos slots empata con LRU en nuevos patrones y olvida parte del pasado. Recableado útil frente a conexiones fijas, **no** valor distintivo frente a caché de igual capacidad.
- [E04](E04_PRE_REGISTRO.md) STW/LTW responde localmente en dos escalas, pero [I3c7k](E09_02I_I3C7K_RESULTADO_TRANSFERENCIA.md) no consigue el criterio propio de retención en un cerebro activo; un peso LTW alto no equivale a asociación funcional consolidada.
- [E05](E09_02G_10B_RESULTADO_DEMORA_DISTRACTORES.md) susceptibilidad temporal existe pero puede reforzar distractores; **G05 de atribución correcta sigue sin lograrse**. [g.10c](E09_02G_10C_RESULTADO_ELEGIBILIDAD.md) confirma pérdida de selectividad, no ausencia de traza.
- [E08](E08_PRE_REGISTRO.md) recurrencia produce oscilación de diseño, sin contribución demostrada a aprendizaje, memoria o decisión.
- **H/C1:** GEN y EXE originales se inspeccionaron parcialmente. [E09 C1ContextBrain](../../experiments/neurolab/c1_context_brain.py) más química [CoupledState](../../experiments/neurolab/e09_coupled_brain.py) integran una parte real, pero no tienen fidelidad de organismo ni retención R-ACT robusta. [I3c7l](E09_02I_I3C7L_CIERRE_ESTRATEGICO_LINEAS_H_N.md) detiene ajuste incremental del prototipo de ocho dendritas.

## 2. Mecanismos esenciales, redundantes o no demostrados en el alcance probado

- **Necesarios para los tests E03/E06:** capacidad de representar cada clase de estímulo pertinente, **estado adaptable por acción** y actualización por feedback. La conectividad neuronal concreta de esas implementaciones no es esencial: TAB1/TAB2 reproducen exactamente acción y evolución de parámetros, no solo porcentaje de aciertos.
- **Capacidad de ignorar contexto irrelevante en E06:** es imprescindible alguna forma de invariancia al bit contextual; su implementador puede ser detector neuronal fijo **o** extractor de pares en una tabla. No se ha demostrado que el sistema *aprenda* qué ignorar.
- **Migración E07:** ayuda cuando los slots fijos no representan las señales nuevas, pero no aporta una ventaja medida sobre LRU. **No seleccionada** como necesidad de la arquitectura mínima.
- **STW/LTW, elegibilidad, recurrencia:** propiedades o fallos parciales verificados; **necesidad y suficiencia conjunta no demostradas**. Ni descartarlas universalmente ni incorporarlas como adorno.
- **No probado:** memoria activa sin premio robusta, asignación causal fiable con retraso/distractores, conceptos aprendidos desde experiencia, elección con dinámica endógena funcional y comportamiento general bajo un mismo cerebro.
- **No determinar tamaño mínimo universal:** 4/8 pesos tabulares son construcciones **suficientes** para los dominios E03/E06 con features conocidas, no teoremas de cardinalidad mínima para cualquier algoritmo.

## 3. Estado contra E09.01–.10, sin falsificar progreso

**Cumplidas documentalmente:** reconciliación de criterios; revisión de evidencia E00–E08; comparación de componentes y costes de integración; controles TAB1/TAB2 con preregistro anterior a código y CI SUCCESS; informes de límites y negativos.

**Parciales:** E09.01 congelación de evidencia completa (resultados JSON E03/E06/E07/E08 versionados, trazas grandes posteriores en Actions temporales); E09.03 ablaciones locales (no matriz conjunta); E09.05 baselines simples (E03/E06 exactos, E07 LRU, pero no todos sobre mismo cerebro); E09.06 sensibilidad e incertidumbre (por ensayos, no globales); E09.07 informe global reproducible (referencias verificables, pero módulos no comparten un ensayo y quedan artefactos temporales).

**Abiertas:** E09.02 evaluación de *un cerebro* con capacidades combinadas; E09.04 minimización bajo un banco común; E09.08 selección de arquitectura mínima integrada defendible. **No aprobar G09** sin esas demostraciones ni sustituirla por integración con mundo.

## 4. Decisión con coste de oportunidad explícito

**Decisión técnica ahora — REVISAR / PAUSAR INGENIERÍA INCREMENTAL DE N:** no construir una unión artificial E03+E06 ni seguir afinando miniC1 de ocho dendritas, porque las capacidades positivas más fuertes de N hasta ahora se reproducen exactamente por tablas comparables y las funciones no tabulares más prometedoras aún no aprueban las pruebas decisivas. El trabajo restante de integración necesita una pregunta nueva que *cambie la decisión*; desarrollar para «llenar etapas» no es aceptable.

**Mantener y preservar:** (1) motores, tests, resultados y preregistros como laboratorio histórico verificable, (2) código TAB1/TAB2 como controles de complejidad, (3) análisis H como arqueología de C1 sin confundirlo con capacidad mínima N, (4) semillas confirmatorias1400..1419 y PR#103 draft sin merge. No borrar experimentos fallidos.

**Condición para retomar construcción N:** demostrar antes de programar una hipótesis que las tablas con misma información/recursos **no** resuelvan y cuya prueba permita aceptar o rechazar un beneficio relevante —p.ej. representación aprendida no precodificada, selectividad de premio realmente tardío o retención+reversión bajo tiempo continuo—. Las tres son **áreas de investigación, no diseños ni experimentos aprobados**. Revisar primero literatura y componentes existentes y evitar objetivos de entorno o conciencia fuera de alcance.

**Condición para continuar H:** pregunta histórico-mecánica cerrada en GEN/EXE y su valor para decidir sobre N; no gastar recursos de ejecución del juego por costumbre ni intentar reconstruir 952 neuronas sin una hipótesis delimitada.

## 5. Estado final de esta unidad

**E09.08–.10: SÍNTESIS Y RECOMENDACIÓN DOCUMENTADAS.** No declarar toda G09 superada: falta un cerebro común, su ablación y selección mínima. Esta es una **decisión negativa provisional y una razón metodológica de detención**, no un fracaso por ausencia de resultados. Un trabajo futuro tiene dos opciones legítimas: (a) cerrar formalmente la investigación N actual con G09 no alcanzada y resumen de hallazgos, o (b) aprobar una nueva hipótesis con poder discriminante antes de reabrir implementación.

**Próximo paso exacto del plan:** auditoría final de suficiencia del informe E09 y de la conservación de datos (E09.01/E09.07) para decidir si se puede declarar la línea experimental N suspendida de forma publicable. NO abrir por defecto más cohortes, más neuronas o un motor nuevo.
