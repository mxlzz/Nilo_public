# NR01.02 — preregistro del desafío mínimo de aprendizaje de representación

**22/11/2026 · PRE-CÓDIGO y PRE-DATOS.** Complementa [plan NR01](NR01_PLAN_INVESTIGACION_REPRESENTACIONES.md) y [alternativas existentes](NR01_REVISION_ALTERNATIVAS_REPRESENTACIONES_20261122.md). **No se ha escrito ni ejecutado el generador**, por lo que estas especificaciones son hipótesis de diseño, no resultados o garantías de solvencia. Toda desviación en código exige un addendum fechado anterior a la primera corrida que afecta; no reescribir este documento.

## Pregunta y regla de decisión

¿Una representación creada **sin etiquetas** a partir de observaciones permite decidir con **menos feedback** y transferir a combinaciones no observadas mejor que memoria literal, aprendizaje discriminativo sobre entrada cruda y centroides adaptables, contabilizando costo? La abstracción útil es **una propiedad evaluada**, no la mera aparición de clusters.

El resultado puede ser negativo sin que se intente salvar una hipótesis añadiendo neuronas. El algoritmo elegido **ARTlib Fuzzy ART** se probará frente a alternativas existentes, no desde una implementación casera.

## 1. Generación reproducible de «mundos» por semilla

Todos los vectores entregados al encoder/control tienen **16 componentes reales en [0,1]**. El evaluador genera factores ocultos mediante `random.Random(world_seed)`; usa sub-RNGs independientes derivados de offsets constantes de la semilla para parámetros de mundo, secuencias de aprendizaje, ruido y test. Documentar offsets y orden de llamadas al implementar: deben congelarse en fixtures antes de correr un modelo.

Se usarán **20 mundos de desarrollo, semillas23000..23019** y **20 mundos de confirmación reservados, 24000..24019**. Estos 40 identificadores son independientes de los 1400..1419 históricos de NeuroLab. No mirar salidas de confirmación durante selección de modelo/hiperparámetros.

### Familia A: identidad reutilizable bajo contexto

- Variables latentes, **solo en generador/evaluador**: identidad `z∈{0,1,2,3}` y contexto `c∈{0,1,2,3}`.
- Vectores de prototipos ocultos `p[z,i]∈{-1,+1}`, `q[c,i]∈{-1,+1}`, muestreados de modo independiente por mundo y dimensión `i∈0..15`. Se prohíbe exponer sus entradas, ID o máscaras al encoder.
- Observación: `x[i] = clip(0.5 + 0.18*p[z,i] + 0.08*q[c,i] + U(-0.06,0.06), 0, 1)`.
- **Doce combinaciones visibles en aprendizaje**, todas las `(z,c)` excepto cuatro parejas `c=(z+3) mod4`. Estas cuatro combinaciones se reservan íntegramente para evaluación en ese mundo; cada identidad y cada contexto aparece en entrenamiento en las otras combinaciones.
- Fase de adquisición no supervisada: **1.200 observaciones sin premio** balanceadas entre las doce combinaciones. Orden barajado por semilla, no agrupar por identidad ni exponer límites de fase.
- Recompensa posterior: `+1` por seleccionar `D(z)=D0 si z∈{0,1}, D1 si z∈{2,3}`; `−1` si falla. **Solo el evaluador conoce z**. Después de una primera fase de feedback, invertir el mapeo por completo. No se da al modelo un aviso de inversión; la secuencia de entrenamiento cambia premios según esa contingencia.
- Presupuestos de feedback a reportar: **8,16,32,64** decisiones por fase; **32** es punto primario de economía de refuerzos, 64 sensibilidad secundaria. Misma cinta de observaciones y presupuesto para todos.
- Evaluación de transferencia, sin nuevo premio: **160 entradas** por fase (40 para cada combinación retenida), ruido re-muestreado y el mismo generador del mundo, encoder y decoder **congelados** en lectura. El evaluador cuenta aciertos sobre el mapeo vigente y abstenciones por separado.

### Familia B: composición de dos factores no precodificados

- Variables ocultas: `a,b∈{0,1,2}` y contexto `c∈{0,1,2,3}`.
- Prototipos independientes `u[a,i], v[b,i], w[c,i]∈{-1,+1}`.
- Observación `x[i] = clip(0.5 + 0.12*u[a,i] + 0.12*v[b,i] + 0.07*w[c,i] + U(-0.06,0.06), 0, 1)`.
- **Combinaciones de factores `a=b` totalmente retenidas**, en todos sus contextos. Las seis combinaciones `a≠b` se emplean en adquisición/training; `a`, `b` y cada contexto siguen apareciendo en múltiples casos visibles, pero el par diagonal nunca se ve.
- Fase no supervisada: **1.200 observaciones balanceadas en 24 combinaciones visibles** (`a≠b`×4 contextos), sin recompensa/ID.
- Dos tareas downstream con **misma representación congelada** y decoders nuevos comparables: tarea B1 `D0 si a==0, D1 en otro caso`; tarea B2 `D0 si b==2, D1 en otro caso`. Su utilidad es probar la reusabilidad en objetivos distintos, **no** retención entre tareas incompatibles sin señal de cambio.
- Feedback 8/16/32/64 observaciones por tarea, igual cinta para candidatos y controles.
- Test de combinaciones retenidas: **120 observaciones** por tarea (3 diagonales×4 contextos×10), sin feedback ni cambios en estado.

**Importante:** todos los métodos pueden aprovechar estructura de estas distribuciones. Si un clasificador lineal crudo resuelve todo con pocos premios, el resultado legítimo es **que no hay necesidad de ART** en este problema. No eliminar esa familia para «favorecer» a la red.

## 2. Interfaces y controles

- `observe_unlabelled(x)`: encoder ve solo16 reales, sin recompensa, identidad latente, ID de fase, regla generativa o recompensa futura.
- `freeze_encoder()` y `encode_read_only(x)`: el mapeo a representación no se modifica durante el período con refuerzo downstream ni en el test. Registrar si la API real del candidato no puede garantizarlo; de ser así, **no correr** hasta definir una adaptación que conserve el contrato.
- Decodificador común, versionado, basado en parámetros adaptables de representación→dos acciones, aprendizaje por `reward∈{-1,+1}` posterior a elección. No recibe etiquetas verdaderas ni contadores ocultos. Para comparar con raw 16D, usar al menos un clasificador lineal online supervisado de presupuesto medido: no hacer que el baseline sea artificialmente incapaz.
- Baselines obligatorios: **memoria exacta/kNN de observaciones reales con capacidad limitada**, **clasificador lineal online sobre 16 componentes crudos**, **MiniBatchKMeans** representando prototipos más decoder común; candidato **ARTlib Fuzzy ART** más mismo decoder. **Opción adicional:** River DBSTREAM si se justifica antes de correr desarrollo; no sumar después de ver resultados.
- Hiperparámetros candidatos preregistrados: KMeans `K∈{4,8,16}`; ART `vigilance∈{0.60,0.80,0.90}` con aprendizaje rápido propio documentado y **tope operativo de 16 categorías**; en excedencia, registrar fuera de presupuesto, no ocultar categorías ni forzar recorte que cambie el algoritmo sin preregistro. Las demás opciones y normalización se fijarán tras validar APIs con **tests técnicos sin datos científicos**.
- Como no todos producen el mismo tipo de representación, se reportará frente de Pareto **precisión/bytes de estado/tiempo de aprendizaje**, no una equivalencia falsa de «número de neuronas». Medir encoder + decoder, caches y normalizadores; precios/performance de librería solo después de prueba, no inferidos de README.

## 3. Control negativo y ausencia de fugas

- **Premios permutados** sin cambiar distribución agregada y sin correlación con `x`: dentro de cada semilla y tarea, barajar en forma determinista las etiquetas de prueba *solo para diagnóstico* después de fijar observaciones; no entrenar candidatos con identidad oculta.
- Control **encoder sin entrenar** (misma inicialización y decoder) y **encoder con orden de observaciones barajado** (si no cambia las estadísticas, debería producir equivalencia o sensibilidad explicable). Si un encoder entrenado no supera al congelado, no atribuir efecto a formación de representación.
- Registro de cinta `x` SHA256 por mundo/etapa; igualdad entre candidatos. Ningún modelo importa clases `WorldGenerator` con propiedades latentes ni accede al RNG interno del evaluador.
- El clasificador que recibe `reward ±1` puede inferir cuál de las **dos acciones** es correcta después de cada elección; esto es una consecuencia legítima del protocolo **para todos los brazos**, y debe informarse en interpretación. La adquisición de representación sigue ocurriendo **antes y sin feedback**.

## 4. Inferencia estadística y puertas

- Unidad de inferencia = mundo/semilla, no cada uno de los 160 ticks de un mismo mundo; comparar diferencias **pareadas** por mundo.
- Primario: transferencia en entradas retenidas con **32 recompensas** para A posterior a primera contingencia y B1/B2; tratar A postinversión por separado. Se reportan tres métricas primarias por familia y un resumen combinado solo con pesos definidos de antemano (promedio igual de A/B).
- **Regla para optar a desarrollo N adicional:** mejora media confirmatoria >=5 puntos porcentuales vs **mejor baseline simple seleccionable en desarrollo**, IC bootstrap por mundo95% estrictamente positiva y resultado no enteramente concentrado en una sola familia. El umbral 5pp es ingeniería pragmática, NO estadística universal. Hacer intervalos por familia; si solo A mejora, conclusión restringida a A, sin aprobación de generalidad.
- **Ablación:** encoder sin actualizar durante la fase no supervisada debe perder parte de la ventaja; si no, el supuesto «aprendió representación útil» queda sin evidencia causal.
- **Restricción de costo:** registrar exactitud a memoria y CPU comparables, sin establecer que una diferencia significativa justifica automáticamente un método mucho más costoso. **Decisión final combina desempeño y coste** y puede adoptar una solución convencional.
- **Gate de software NR01.02:** tests contra cálculos manuales en un mundo ficticio fijo (no perteneciente a cohortes de desarrollo/confirmación), sin filtrar factores, número de ejemplos y recompensas correctos. No interpretar una prueba de software verde como evidencia científica.
- **NR01.03/04:** sólo desarrollo; **NR01.05** confirmación una vez, después de configuración congelada. Si no hay poder discriminante en desarrollo, detener sin consumir 24000..24019.

## 5. Riesgos reconocidos ANTES de ejecutar

1. A/B podrían ser demasiado sencillos para un clasificador lineal; **es resultado útil**, no falla que obligue a inventar dificultad. Registrar y cerrar en lugar de ajustar el mundo después de mirar su desempeño.
2. Algunas categorías podrían codificar distractores o romperse con diferentes contextos; reportar tamaño/estabilidad, no rescatar seleccionando mundos exitosos.
3. Fijar exactamente 16 dimensiones y ruido uniforme puede favorecer ciertos métodos; generalización fuera de las dos familias **no demostrada** sin un conjunto externo.
4. ARTlib no está instalado ni se verificó que su `predict` sea read-only; **antes del test** hay que verificar contrato real. Una implementación que aprenda durante test invalida la comparación.
5. Este preregistro fija ecuaciones, cohortes y límites **antes del código**, pero para una ejecución aún faltan versiones exactas de paquetes y reglas del decoder por dimensión. Esas precisiones requieren una adenda **pre-run**; no queda autorizado reportar «gates superadas» sin ella.

**Estado:** protocolo de tarea preregistrado documentalmente, NO ejecutado. **Siguiente unidad:** NR01.03 verificar interfaces reales, crear generator con fixtures y pruebas de no filtración, implementar controles simples; si el protocolo no puede respetarse, documentar bloqueo y no ejecutar cohortes.
