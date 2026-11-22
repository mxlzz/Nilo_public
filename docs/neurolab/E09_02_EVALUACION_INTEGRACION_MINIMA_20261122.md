# NeuroLab — E09.02–.05: evaluación previa de integración, controles y coste (22/11/2026)

> **Adenda posterior a esta evaluación (22/11/2026):** [E09.05-TAB1](E09_05_TAB1_RESULTADO_EQUIVALENCIA.md) encontró y comprobó equivalencia matemática y operacional exacta de `ConceptLearner` en E06 con una tabla de cuatro pares×dos pesos. La propuesta exploratoria del apartado 4 de construir un adaptador E03+E06 **queda despriorizada** mientras no exista otra predicción discriminante; no reinterpretemos una tabla como prueba de mente neuronal. Esta anotación preserva el análisis previo y documenta el cambio de decisión.

**Tipo:** decisión de diseño experimental sin implementación. Basada en [contrato reconciliado](E09_00R_RECONCILIACION_GATES_20261122.md), [auditoría E00–E08](E09_01_AUDITORIA_CAPACIDADES_20261122.md) y [plan E09](ETAPAS_00_09.md). No cambia C1, dosis, topología, semillas ni `main`.

## 1. Pregunta de decisión original

**¿Qué combinación mínima de mecanismos existentes conserva capacidades verificadas con un mismo estado, tick, presupuesto de información y evaluación, y añade algo que un baseline simple no logre?**

G09 exige síntesis y arquitectura mínima **si la evidencia la respalda**. No exige añadir ocho módulos ni construir un organismo. La síntesis puede terminar en **revisar/detener** si controles simples son suficientes o la integración aún no es defendible.

## 2. Arquitecturas realmente disponibles

**A. Familia N elemental (E01–E08).** `kernel.Brain/BrainState` es solo cómputo; `PlasticLearner/PlasticState` asocia elección/refuerzo en episodios; `ConceptLearner/ConceptWeights` ya incluye conceptos **fijos** y plasticidad de enlaces de decisión; `TwinSynapse` tiene dos velocidades sin decisiones; `EligibleSynapse` solo registra susceptibilidad; `WiringModel/WiringState` administra 2 slots, con LRU equivalente; `recurrent` usa `kernel` para oscilación aislada. **Incompatibilidad concreta:** el estado y reloj no son compartidos, las reglas de entrenamiento y entornos difieren. Concatenar los porcentajes no produce una arquitectura validada; un adaptador que altere plasticidad/episodios constituye un **modelo nuevo** y requiere hipótesis.

**B. Familia C1 reducida E09 (NO histórica completa).** [`C1ContextBrain`](../../experiments/neurolab/c1_context_brain.py): entrada contextual 0/1, conceptos ANDTYPE0 preconfigurados, dos decisiones WTA y ocho dendritas GEN; [`CoupledState/coupled_tick`](../../experiments/neurolab/e09_coupled_brain.py) acopla estado cerebral y [puente químico](../../experiments/neurolab/e09_chemical_bridge.py). **Sí integra parcialmente** reglas neuronales y químicas. Pero el puerto de emisores queda externo, no existe feedback endógeno de mundo, la lectura Concept CHEM no gobierna conceptos, no hay circuito E07 de recableado ni recurrencia conductual E08 y la implementación no reproduce el scheduler entero C1. [I3c7h](E09_02I_I3C7H_RESULTADO_CONTINGENCIA.md) y [I3c7k](E09_02I_I3C7K_RESULTADO_TRANSFERENCIA.md) aportan controles de aprendizaje, pero `R-ACT-I3c` fracasa. **Decisión existente:** conservar A/B como material auditable, no optimizar el mini-C1 de ocho contactos.

**C. Alternativas simples preexistentes.** Decisor congelado/azar, memoria asociativa tabular, detector conjuntivo fijo, caché LRU y `ConceptLearner` ya implementado son **baselines**, no proponer librería nueva. La tabla Q de [g.10b](E09_02G_10B_RESULTADO_DEMORA_DISTRACTORES.md) recibe procedencia causal externa: es **techo con información privilegiada**, NO control tabular justo para juzgar a N.

## 3. Qué preguntas ya están contestadas, sin más código

- **¿Reutilizar dos slots permite aprender nuevos patrones?** Sí; E07, pero **no supera LRU**. No hay motivo actual para agregar atrofia genética de mayor complejidad a N.
- **¿Una recurrente puede oscilar por sí sola?** Sí, E08; **no hay evidencia de mejora en decisión**. No integrar recurrencia por estética de «actividad mental».
- **¿Tres factores/eligibilidad solucionan el crédito diferido?** No con la atribución observada. C1 ya tiene susceptibilidad; agregar otra traza por nombre duplicaría función sin abordar selectividad.
- **¿Copiar STW a LTW salva la memoria?** No alcanza umbral de suficiencia I3c7k; no crear una regla de transferencia mecánica para repetir ese experimento.
- **¿La familia E01–E08 ya es un cerebro integrado?** No: sus reglas de estado/tiempo difieren. **¿Existe alguna integración parcial?** Sí, `CoupledState` en familia E09, y `ConceptLearner` combina dos funciones restringidas.

## 4. Dependencias mínimas para un posible ensayo nuevo E09.02

**Antes de codificar**, elegir una sola pregunta que pueda cambiar la decisión, registrando una matriz de compatibilidad de entrada/salida por cada modelo candidato. Propuesta limitada, sin aprobarla por inercia:

1. **Pregunta discriminante:** ¿el mismo sistema N simple que resuelve asociación/reversión E03 puede mantener generalización E06 cuando se evalúan ambas capacidades en una secuencia de estado continuo, sin reinicio entre pruebas, y supera al control tabular con las mismas observaciones disponibles? No es legítimo afirmar «sí» a partir de dos éxitos aislados.
2. **Primera alternativa de menor esfuerzo:** no escribir otro motor neuronal: **instrumentar una única evaluación adaptadora de `ConceptLearner` existente** (la única familia ya funcional con conceptos fijos y aprendizaje) frente a un mapeo tabular que observe las mismas entradas de cinco canales, acciones y premio. La adaptación no puede convertir los conceptos en etiquetas del evaluador ni dar al tabular información ausente. Conservar el esquema original de estados y declarar cualquier cambio de tick como nuevo modelo.
3. **Hipótesis falsable para preregistro futuro:** bajo secuencia continua de asociación, inversión y contexto irrelevante, el detector conjuntivo + decisión plástica tendrá una ventaja demostrable frente a tabla de patrones completos de **igual acceso observacional** con presupuesto de entrenamiento/evaluación idéntico. Si la ventaja desaparece, detener la integración incremental de esa familia. Esta hipótesis **aún no está preregistrada para ejecución**: faltan definir distribución de episodios, fairness de información y coste.
4. **Coste:** medir sinapsis/parámetros, bytes de estado, ticks de entrenamiento/test y tiempo/ciclo, NO extrapolar benchmark E01 a familia C1. Modelos separados pueden usar tamaños diferentes solo si la comparación lo contabiliza y la afirmación no depende de paridad artificial.
5. **Control indispensable:** comparador simple con **información no privilegiada** y mismos premios entregados; un baseline injusto mejorador/desmejorador no cambia la decisión.
6. **Barrera:** si el protocolo común no conserva las reglas originales o exige un rediseño grande, **no implementar**; cerrar E09 como «evidencia parcial con arquitectura no seleccionable» antes de acumular otra plataforma.

## 5. Estado por subtarea E09 (auditoría, no marcación ficticia)

- **E09.01 congelar variantes/evidencia:** identificación de commit base y archivos reproducibles **parcial**; faltan inventario íntegro de trazas grandes y artefactos temporales.
- **E09.02 evaluación conjunta:** **abierta**; acoplamiento cerebro–química E09 parcial no equivale a los objetivos E03–E08 juntos.
- **E09.03 ablaciones:** ablaciones locales E09 ejecutadas; **comparación integrada transversal abierta**.
- **E09.04 tamaño mínimo:** **abierta**; 6 unidades/8 contactos son elección inicial, no mínimo demostrado.
- **E09.05 baseline tabular:** **parcial**; LRU y memoria exacta comparados, pero no tabular uniforme sin privilegios frente al candidato integrado.
- **E09.06 sensibilidad:** contrastes por semillas y controles particulares; **no barrido robusto conjunto**.
- **E09.07 incertidumbre/negativos:** **parcial**; resultados positivos/negativos y algunos bootstrap por semilla disponibles, no un informe con trazas de todas las condiciones integradas.
- **E09.08 arquitectura mínima:** **sin selección justificada**.
- **E09.09 límites:** **documentados** para modelos aislados, consolidación pendiente de E09.
- **E09.10 próximos experimentos:** **esta decisión documental** delimita una única pregunta potencial, no aprueba una arquitectura ni un ensayo.

## 6. Decisión y siguiente unidad verificable

**NO construir ahora un cerebro completo, ni añadir mecanismos, ni iniciar una campaña de semillas.** Primero fijar un protocolo de comparación entre `ConceptLearner` y tabular **sin fuga de información y sin alterar arbitrariamente las tareas previas**; inspeccionar si el mismo modelo E06 puede operar de manera continua con entradas incluidas en E03. Si la interfaz lo impide, documentar ese bloqueo y estimar el coste de un único adaptador de evaluación, no «resolverlo» con nuevas neuronas.

**Puerta para pasar a ejecución:** hipótesis, definición de datos, estado inicial/tick, muestras, controles, fairness y métrica de éxito registrados **antes de cualquier código**, con valor decisorio frente a `detener`. De no alcanzar esa puerta, informar E09 como abierta/bloqueada. Semillas de confirmación 1400..1419 intactas.
