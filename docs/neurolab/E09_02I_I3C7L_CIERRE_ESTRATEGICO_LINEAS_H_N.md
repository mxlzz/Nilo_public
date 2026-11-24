# NeuroLab E09.02i–I3c.7l — punto de decisión: cerrar optimización del prototipo y separar investigación histórica H de memoria mínima N

**22/11/2026 · DECISIÓN DE MÉTODO / NO IMPLEMENTACIÓN.** Referencias: [objetivos maestro](README.md), [I3c7j análisis](E09_02I_I3C7J_MEMORIA_DIAGNOSTICO_ESTRATEGIA.md), [I3c7k resultado](E09_02I_I3C7K_RESULTADO_TRANSFERENCIA.md), [estado canónico](ESTADO_Y_CONTINUIDAD.md). Este documento **no aprueba una nueva arquitectura**, no modifica el motor Nilo ni fusiona PR#103. Diferenciar recomendación técnica de autorización posterior de implementación.

## 1. Balance independiente de evidencia (no inflar por cantidad de corridas)

**Logrado con alto grado de trazabilidad dentro del modelo experimental:**
- Se implementaron y auditaron las reglas aisladas C1 de dendrita, fuerza, SVRule, receptores y partes del writer/emitter original por GEN/EXE (rutas históricas parciales, no emulación integral).
- Se verificaron respuestas aprendidas bajo contingencia de recompensa frente a valencia reordenada (I3c7h, +38,65 pp de precisión ACTIVE, control exacto B/Y e invariantes de presupuesto químico), pero con **cinética temporal química diferente**.
- Se demostraron efectos causales locales de señales STW sobre decisiones al lesionar slots (I3c7i), sin demostrar causalidad de la historia de atribución de premio.
- Se comprobó atrofia nominal por falta de emisor histórico efectivo y relajación de STW aun sin atrofia. El incremento de oportunidades LTW hasta señal≥5 no resolvió robustez (I3c7g).
- Se comprobó que **distribución direccional de contenido sináptico** importa: en I3c7k la transferencia oráculo de STW a LTW mejoró aproximadamente+4,9 pp, mientras el control owner-swapped perjudicó, pero **NO** superó gate de suficiencia preestablecido+10 pp.

**No logrado:**
- **G05**, la capacidad de aprender y conservar asociaciones de forma robusta durante evaluación ACTIVE sin nuevo feedback en condiciones predefinidas. En I3c7h sólo2/20 semillas alcanzan≥.90 en ambas fases; gate preexistente18/20.
- **G09**, integración neuronal/conductual como un agente autónomo con entorno, fuera de alcance del laboratorio actual.
- **G00-H**, fidelidad del cerebro y química completa C1, incluido scheduler, puertos/emisores endógenos y escala real de contactos. Los genes/EXE originales fueron inspeccionados, pero no se ha emulado el organismo.

**Riesgo de confusión:** CI verde prueba que el programa hace lo que la prueba especifica, no que el modelo aprenda duraderamente ni reproduzca C1. Las lecturas `learn=False` exageran retención respecto de ACTIVE; las ablaciones locales tienen ventanas congeladas y no reemplazan el test largo. No calcular un promedio de «éxitos» sobre experimentos no independientes para argumentar convergencia.

## 2. Hipótesis agotadas o insuficientes para justificar nuevos desarrollos

Se exploraron de modo controlado (sin convertir cada resultado en nueva arquitectura): aumentar pulso directo, permitir precursor químico, bloquear atrofia, extender entrenamiento para más consolidación LTW, reordenar contingencia, lesionar cada conexión y copiar STW a LTW. Los resultados permiten rechazar **como soluciones suficientes bajo el benchmark actual**: «apagar la atrofia», «entrenar más», «subir LTW numérica», «mantener fuerza» y «copiar el patrón STW una vez». No son teoremas de imposibilidad universales; sí bastan para **detener** la optimización aditiva de este prototipo.

## 3. Alternativas reales y recomendación con costos de oportunidad

**H — reconstrucción histórica C1.** Reutilizar análisis y adaptadores actuales; recuperar el mecanismo original de realimentación53/70 y migración Type1, topología con contactos suficientes y scheduler histórico. Original Decision tiene128 dendritas por clase/neurona; en el circuito reducido el mínimo original de conteos de contactos exhausted no puede alcanzar umbral funcional18. Hay evidencia de **incompatibilidad de escala**, no prueba de que C1 original se comporte mal. **Ventajas**: responder preguntas sobre *Creatures* de forma defendible y tener un referente para NeuroLab. **Riesgos/costo alto**: reconstrucción de fuentes, 16 Decision, cientos/miles de conexiones, timing de química, sin garantía de G05 ni beneficio para una mente mínima. **Recomendación**: continuar H como proyecto de investigación histórica **independiente**, con preguntas cerradas de fidelidad, no usarlo como parche de ocho sinapsis.

**N — cerebro neuronal pequeño con memoria durable, claramente NO C1 fiel.** El prototipo de8 slots es el control negativo. Antes de escoger una modificación, comparar literatura y herramientas existentes: reglas locales de aprendizaje de tres factores con `eligibility traces` (Gerstner et al. 2018: https://pmc.ncbi.nlm.nih.gov/articles/PMC6079224/), consolidación lenta estable que preserve **contrastes útiles**, y esquemas de estabilización sináptica. **No adoptar automáticamente EWC, Synaptic Intelligence, buffers de replay o backprop**: están documentados pero introducen estimadores/gradientes/memoria externa o nuevos supuestos ajenos al diseño pequeño; además una regla que mejora olvido puede dañar la reversión/plasticidad. El trabajo `Loss of plasticity in deep continual learning` (Dohare et al., Nature 2024, https://www.nature.com/articles/s41586-024-07711-7) distingue pérdida de capacidad de aprendizaje de olvido de una asociación, y no puede transferirse sin más a ocho dendritas.

**C — cambiar métrica de evaluación a feedback ecológico intermitente.** Puede ser útil para medir robustez en un agente real. Pero **NO** arregla el problema de memoria actual ni autoriza reemplazar G05 por una prueba fácil; si el evaluador sigue reforzando durante lectura, la variable «retención sin feedback» dejó de evaluarse. Mantener como métrica complementaria, no cambio retroactivo.

**D — otro simulador de neuronas como sustituto completo.** Frameworks de SNN pueden facilitar redes grandes pero no reproducen automáticamente los genes C1, ni resolverían por sí solos la conservación de asociaciones; introducir ahora un stack entero añadiendo dependencias, hardware y debugging no tiene retorno justificado. Sólo investigarlos si H o N pasan el filtro de hipótesis/arquitectura.

**Recomendación técnica priorizada:** congelar mini C1 actual como benchmark auditable y **no introducir otro algoritmo en ese mismo código**. Mantener H como línea de arqueología verificable. Para la aspiración de mente autónoma N, el paso previo debe ser una **especificación de memoria**, no código: identificar qué estado debe persistir cuando cesa el premio, cómo se recupera sin contexto privilegiado y cómo se reemplaza tras inversión, en una red que mantenga plasticidad.

## 4. Requisitos que deberá superar una eventual propuesta N nueva

No optimizar sobre semillas ya usadas. Antes de programar:
1. **Proponer una propiedad/fenómeno discriminante** que mini C1 no logra, respaldada por evidencia externa o mecanismo demostrado, y distinguir «replay», estabilidad de pesos y elegibilidad temporal: son problemas distintos. No extender una hipótesis como solución a todos.
2. **Reusar implementación existente cuando exista** y medir costo en estado por sinapsis, operaciones por tick, dependencia externa y auditabilidad. No aprobar por resultar fácil de codificar o «bioinspirado».
3. Una sola hipótesis pre-registrada, con control con mecanismo desactivado, sham misma carga química, control negativo frozen, baseline tabular simple sin etiqueta privilegiada y medidas de acierto ACTIVE, olvido y velocidad de inversión bajo **idéntico presupuesto de entrenamiento**. Un readout frozen puede agregarse solo como techo, no ser puerta central.
4. **Revisar contraejemplos**: redes que recuerdan pero ya no se adaptan, recompensas permutadas, interferencia, conexiones no alineadas, fuente de premio ajena a su propia acción. Penalizar el éxito al inflar fuerza uniforme; comparar ambos contextos y acciones.
5. **Puerta de esfuerzo:** una alternativa no pasa a desarrollo salvo que exista una hipótesis de suficiencia más convincente que «STW→LTW instantáneo» y una razón concreta para esperar ventaja mayor que+10pp con margen de incertidumbre, sin afectar la reversión. Si esa evidencia no existe, **detener y no consumir más semillas**.
6. Sólo un mecanismo que supere gate de desarrollo puede ser sometido a **confirmación nueva** con semillas1400..1419; no gastarlas en elegir parámetros, ventanas o modelos. Gate G05 **no cambia**. Un conjunto de resultados confirmatorios no reemplaza la integración G09.

## 5. Decisión, no aprobación ficticia

- **Decisión metodológica aplicada:** STOP de trabajo incremental sobre `C1ContextBrain` de8 dendritas; conservar código, oráculos, registros y resultados como baseline, no borrar ni declarar obsoleto.
- **Recomendación no ejecutada:** priorizar investigación N de una regla local de memoria estable, **con revisión externa y ensayo de suficiencia antes de implementar**; continuar H en paralelo sólo en tareas históricas que resuelvan hechos del GEN/EXE, no reconstruir todo por principio.
- **No se aprobó** ni implementó nuevo motor, red, genoma, agentes, UI o versión Nilo. En el estado canónico la siguiente unidad deberá ser **I3c.8 (evaluación de mecanismo N existente)** o una pregunta histórica de alcance concreto, no «I3c.7m ajustar un parámetro».
- La reserva **1400..1419** permanece sin consumir. **G05/G09/G00-H ABIERTAS**, PR#103 draft, `main` y Nilo0.7 intactos.

**Criterio para detener NeuroLab si no hay nueva hipótesis:** si el relevamiento de métodos existentes no produce una implementación candidata con predicción falsable sobre memoria ACTIVE y costo acotado, cerrar esta línea experimental como negativa y conservar únicamente los hallazgos verificables. El esfuerzo ya invertido no es justificación para seguir.
