# NeuroLab — NR01, plan de investigación para adquisición de representaciones

**Versión 0.1.0 · 22/11/2026 · PLAN INVESTIGADOR APROBADO EN SU DIRECCIÓN; SIN CORRIDAS NI MODELOS NUEVOS.** Esta fase **NR01** es sucesora metodológica de [cierre E09](E09_CIERRE_FORMAL_RESULTADO_20261122.md), pero **no es un E10 añadido retroactivamente** al plan E00–E09 ni una redefinición de G05/G09. Su propósito no es «probar que neuronas ganan», sino identificar *la menor solución existente o nueva que aprenda y reutilice representaciones* con utilidad conductual y coste proporcionado.

**Pregunta NR01:** ¿un mecanismo online no supervisado, con información idéntica a un baseline simple, aprende una representación reusable en tareas inéditas y/o condiciones cambiantes que mejora la transferencia por dato, capacidad o tiempo, sin que el diseñador le entregue explícitamente la agrupación correcta?

**Decisiones ya tomadas:**
- Archivar la campaña E09 con puerta G09 NO superada; conservar H histórica separada, detener miniC1 incremental.
- Investigar soluciones existentes antes de código propio. [Revisión de alternativas](NR01_REVISION_ALTERNATIVAS_REPRESENTACIONES_20261122.md).
- Candidatos iniciales limitados: **ARTlib Fuzzy ART** (agrupación incremental), **MiniBatchKMeans** o River clustering simple (representación aprendida de referencia), controles literal/1-NN y una estrategia de aprendizaje online directo sin encoder. **No** reimplementar ART/SOM/GNG desde cero ni introducir motor neuronal propio.
- Mismo presupuesto de observaciones y premios por brazo. Semillas originales NeuroLab1400..1419 intocables. No mezclar cifras de E03/E06 con cifras de NR01.

## 1. Secuencia de puertas auditables (progreso real, no casillas ficticias)

**NR01.00 — Marco, alcance y continuidad.** Entregas: E09 cerrada con resultado parcial (G09 NO superada), respaldo de datos críticos con huellas, reglas de no filtración de GEN/EXE y plan con hipótesis falsables. **Criterio: documental y trazabilidad.** Estado: **ejecutado** por [E09 formal](E09_CIERRE_FORMAL_RESULTADO_20261122.md), [manifiesto](E09_ARCHIVO_EVIDENCIAS_20261122.md) y este plan.

**NR01.01 — Alternativas existentes.** Investigar ART, clustering online, prototipos, SOM, GNG, codificación sparse y alternativas temporales; verificar fuentes/licencias/madurez; seleccionar **máximo un candidato estructural nuevo y dos baselines aprendidos** antes de implementar. [Inventario](NR01_REVISION_ALTERNATIVAS_REPRESENTACIONES_20261122.md). Estado: **documental completado de forma selectiva**; validación real de APIs/versiones y costos aún **pendiente**.

**NR01.02 — Desafío discriminante.** Congelar el generador de mundos/observaciones, reglas latentes, particiones, ruido, reversiones y costos antes de escribir modelos. Demostrar analíticamente que: (a) no se codifica la respuesta correcta ni un detector que identifique qué variables son útiles en el modelo, (b) hay combinaciones realmente no vistas, (c) los mismos inputs y señales temporales llegan a baselines y candidatos, (d) hay al menos una tarea donde solución simple pueda ganar. **No ejecutar sin especificación congelada y revisada.**

**NR01.03 — Controles y harness verificable.** Construir **primero** evaluación independiente y baselines no privilegiados, con tests de fugas de información, igualdad de exposiciones, seeds, endpoints y conteo de memoria; correr en **desarrollo** y guardar trazas. Si un control simple ya agota el problema o el test discrimina solo por una feature precodificada, detener y rediseñar contrato antes de tocar candidatos.

**NR01.04 — Piloto de una solución existente.** Integrar **ARTlib Fuzzy ART** (biblioteca pública, no copia), comparar con KMeans/tabla/clasificador online directo; si API no es portable, sustituir ART por otra implementación ya revisada, **con preregistro de desviación**, nunca por una red ad hoc. Ajustes de desarrollo solamente con cohorte designada. Medir capacidad y estabilidad de categorías, no solo precisión.

**NR01.05 — Confirmación única.** Tras código y parámetros congelados, ejecutar **una sola cohorte** no observada. Si el desarrollo no muestra mejora práctica y mecanismo explicable, **no consumir holdout**; cerrar negativo. Una vez expuesta, la cohorte no vuelve a servir para seleccionar hiperparámetros. Pruebas de ablation y trade-off según contrato; hashes por unidad.

**NR01.06 — Decisión.** (a) adoptar solución existente si es suficiente y económica; (b) justificar una hipótesis y prototipo nuevo solo si ninguno de los existentes resuelve la capacidad identificada y se explica el déficit; (c) detener N y conservar conocimiento. Nunca introducir cuerpo/LLM/juego por haber concluido NR01.

## 2. Contrato de arquitectura y flujo de datos

Una *unidad experimental* = un «mundo» sintético controlado independiente de otros mundos, con estado inicial/version/semilla y eventos que generan únicamente observaciones numéricas y los premios que define el evaluador.

**Separar estrictamente responsabilidades:**
- **Generador/Evaluador oculto:** puede usar factores latentes para producir `x_t`, etiquetas de evaluación y un refuerzo `reward(action)` **después de la acción**; no exponer valores latentes, clases, claves de mezcla ni acciones objetivo a biblioteca, encoder, decoder ni baseline.
- **Encoder `observe(x)`:** recibe secuencias **sin etiquetas ni recompensas**; actualiza su representación por un algoritmo online. Salida `encode(x)` de dimensión declarada, lectura **sin actualización** durante test. No recibe identificadores de mundo o fase.
- **Decoder común:** mapea la representación de cada candidato a dos decisiones utilizando solo presupuesto idéntico de decisiones/refuerzos; debe tratarse como parte del coste del candidato. Para baselines de entrada cruda se usa un decoder de capacidad comparable; no regalar al candidato un decoder más expresivo.
- **Baselines:** (i) memoria de casos/raw 1-NN con capacidad fija (ii) algoritmo online simple que aprende directamente de `x` y recompensa (iii) MiniBatchKMeans+el mismo decoder de prototipos (iv) ARTlib+el mismo decoder, salvo diferencias documentadas. Oráculo con identidad latente o máscaras verdaderas **solo techo diagnóstico; nunca baseline justo**.
- **Estado y costo:** serializar estados reconstruibles, contar parámetros/prototipos y bytes de estado de encoder+decoder, tiempo CPU medido con hardware fijado; incluir etapas de normalización y filtros aprendidos, no esconder memoria en el generador.

**Advertencia:** los modelos ART, KMeans y 1-NN no garantizan una semántica de `predict` idéntica; antes de correr, escribir adaptador sin etiquetas, verificar que `encode` no aprenda durante la lectura y declarar cómo tratar creación de categorías sin recompensas. Un paso de aprendizaje no puede observar etiquetas/objetivos por accidente.

## 3. Desafío propuesto NR01-D1: conceptos reutilizables sin detector predefinido

**Esta sección fija el diseño conceptual, pero NO un preregistro computacional de parámetros exactos.** La implementación del generador y las APIs debe esperar el preregistro **NR01.02**, con distribuciones, tablas de verdad y opciones numéricas totalmente especificadas, *antes de ver métricas*.

Se requieren **dos familias de mundos**, no una única tarea favorable a ART:

**D1a — Identidades latentes y contextos nuevos:** señales sensoriales continuas/multicanal derivadas de la combinación de un factor persistente, varias apariencias/contextos cambiantes y ruido. La identidad aparece en muchos contextos, pero se retienen combinaciones `identidad×contexto` no vistas durante adquisición. No se informa al algoritmo de qué canales proceden de qué factor. El downstream aprende una primera contingencia estímulo→acción y su inversión, con pocas recompensas; se evalúa transferencia a contextos inéditos, sin reward.

**D1b — Factores composicionales:** entradas construidas mezclando **dos regularidades independientes** y distractores; distintos mapeos de decisión reutilizan primero una, luego la otra y/o su relación. Se retienen combinaciones no observadas para exigir composición, no una lista de patrones. Los generadores deben evitar que un simple orden fijo de bits revele el factor objetivo. La red puede fallar: si un baseline simple generaliza mejor, ese resultado cuenta.

**Control negativo de fuga:** destruir el vínculo entre estructura sensorial y el factor relevante (o permutar recompensas en un diseño pareado), conservando presupuestos/etiquetas agregadas, para detectar éxito aparente debido a información externa o confusores.

**No** entregar pares positivos de «mismo objeto», máscaras verdaderas, transformaciones inversas ni etiquetas de identidad como datos de entrenamiento: eso sería otra pregunta (aprendizaje autosupervisado con supervisión de invariancia).

## 4. Particiones y presupuesto propuesto (a congelar antes de código)

- **Desarrollo:** 20 semillas de mundo de la serie `23000..23019`, usadas para verificar software y ajustar SOLO parámetros preregistrados.
- **Confirmación bloqueada:** `24000..24019`, estrictamente **no ejecutar ni inspeccionar** antes de declarar un candidato/configuración final. Si el tamaño/varianza es insuficiente, ampliar ANTES de ejecutar y conservar una única evaluación confirmatoria.
- **Semillas históricas `1400..1419`** nunca entran en NR01.
- Para cada semilla, entrenamiento/adquisición no etiquetado; downstream con presupuesto fijo de premios y acciones; prueba nunca recompensada; medición tras inversión; continuidad sin reset accidental del encoder.
- Los presupuestos de observaciones, memoria máxima (por ejemplo, varias cuotas en kilobytes), número de categorías admisibles y premio se fijarán con justificación operacional **antes** de la primera corrida. No establecer un tamaño de «neurona mínima» mediante preferencia estética.
- Todos los resultados negativos y de modelos fuera de presupuesto se registran, no se excluyen del promedio sin declarar criterio previo.

## 5. Métricas y criterios de continuación

**Métrica primaria propuesta:** precisión pareada **en combinaciones/situaciones nuevas**, medida después de un presupuesto idéntico de recompensas, frente al **mejor baseline simple no privilegiado** seleccionado y congelado en desarrollo. Evaluar por mundo, no por tick pseudorrepetido; IC de diferencia pareada con remuestreo por mundo. Informar ambas familias por separado y reporte agregado solo si previamente se define el peso.

**Métricas secundarias obligatorias:** eficiencia de muestras (curva según recompensa disponible), exactitud temprana y tardía, tasa de formación/fusión de categorías, retención tras segunda tarea, adaptación a inversión, memoria real reproducible y tiempo de CPU, reproducibilidad checkpoint, diversidad/estabilidad de códigos y falsos descubrimientos en control negativo.

**Criterio provisional para abrir una nueva fase de ingeniería (debe fijarse antes de ejecución):**
1. Ventaja práctica no trivial sobre baseline de igual información y presupuesto en mundos de confirmación (por ejemplo, **≥5 puntos porcentuales promedio**, junto con **IC bootstrap pareado 95 % completamente >0**). El 5pp es un **umbral de decisión de ingeniería**, no una verdad estadística ni criterio del antiguo G09.
2. Resultado no concentrado en una sola semilla o una familia elegida después: exigir informe por familia y sensibilidad; un único tipo de mundo exitoso **no** acredita generalidad.
3. Memoria, tiempo y estabilidad razonables frente a baseline: si el método complejo gana 1pp a costa de 20× computación, no justifica sustituir el simple.
4. Evidencia causal de que la representación aprendida importa: ablación de encoder aprendido / representación no entrenada bajo idéntica tarea (mantener decoder controlado); evaluar si el éxito proviene de features precodificadas.
5. No comprometer reversión y retención para ganar precisión de transferencia sin reportar el costo.

**Si no se cumple:** no inventar otro mecanismo de consolidación ni prolongar entrenamiento de manera oportunista; documentar resultado negativo y considerar usar solución no neuronal.

## 6. Auditoría de desvíos obligatoria

Antes y después de cada unidad verificable responder: ¿qué subpregunta NR01 resuelve? ¿Qué evidencia la autoriza? ¿Qué control más simple la refuta? ¿Se observaron datos de confirmación? ¿Aumentó la complejidad sin beneficio? ¿Quedó guardado el estado? Un cambio de tarea, costo, representación o umbral necesita adenda y nuevas cohortes, nunca actualización silenciosa.

**Próxima unidad exacta:** **NR01.02, preregistro cerrado del desafío D1** (generador completo, fixtures analíticos, presupuesto, matrices de información y plan de baselines). Hasta entonces: **cero llamadas de modelos nuevos, cero nuevos experimentos, cero integración en Nilo**.
