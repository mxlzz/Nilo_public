# NeuroLab — protocolo maestro de mente neuronal aislada

**Versión del protocolo:** 0.1.0 (documentación, propuesta de investigación)  
**Fecha del registro:** 2026-11-20  
**Registro de referencia:** [issue #102](https://github.com/mxlzz/Nilo_public/issues/102)  
**Origen:** exploración acordada del cerebro de los Norns de *Creatures 1* (1996).

> **Estado real:** plan escrito, no experimento ejecutado. No hay algoritmo neuronal implementado ni resultados obtenidos. La aprobación de documentar no significa aprobar una implementación, integración con Nilo 0.7 o autonomía de un agente externo.

## 1. Pregunta y alcance

**Pregunta central:** ¿cuáles son los mecanismos mínimos inspirados en *Creatures 1* que permiten a un sistema neuronal aislado adquirir, conservar, modificar, transferir y reorganizar asociaciones mediante experiencia verificable?

Dos trabajos distintos que se contrastarán, sin confundirlos:

- **Línea H (histórica):** reconstrucción fiel de lo que se pueda establecer del cerebro C1 y de qué partes del modelo realmente estaban implementadas. Si faltan parámetros, registrar el hueco.
- **Línea N (NeuroLab):** mente mínima experimental, explícitamente inspirada en C1, no réplica fiel a menos que una comparación la acredite.

**Incluido:** neuronas, sinapsis, entradas abstractas, decisiones discretas, aprendizaje, estímulos y refuerzos suministrados por un banco de pruebas externo, registro de trazas y análisis.

**Excluido en esta investigación:** personaje, mapa, cuerpo, mundo de juego, necesidades fisiológicas simuladas, LLM, lenguaje natural, metas narrativas, reproducción, evolución genética, interfaz gráfica compleja, modificación del motor físico Nilo 0.7.

Una señal de refuerzo del banco de pruebas **no convierte a la mente en un agente con cuerpo o mundo**. Es una condición de ensayo.

## 2. Cómo leer y ejecutar este protocolo

Documentos canónicos de esta rama:

| Documento | Uso |
|---|---|
| [FUENTES_Y_RECONSTRUCCION.md](FUENTES_Y_RECONSTRUCCION.md) | Preguntas históricas, prueba de procedencia, dudas y parámetros |
| [ETAPAS_00_09.md](ETAPAS_00_09.md) | Secuencia operativa y puertas verificables, paso a paso |
| [PROTOCOLO_EVALUACION.md](PROTOCOLO_EVALUACION.md) | Ensayos, controles, análisis, métricas y resultados |
| [ESTADO_Y_CONTINUIDAD.md](ESTADO_Y_CONTINUIDAD.md) | Estado real, registro de decisiones, cambios y forma de retomar |
| [PLANTILLA_ENSAYO.md](PLANTILLA_ENSAYO.md) | Ficha que se debe completar por cada experimento ejecutado |

**Orden obligatorio:** (a) comprobar estado en `ESTADO_Y_CONTINUIDAD.md`; (b) verificar la especificación histórica o la decisión de divergencia; (c) ejecutar la siguiente subtarea no terminada; (d) producir su evidencia; (e) verificar criterios; (f) actualizar estado y siguiente subtarea. No saltar una puerta de calidad por una prueba anecdótica.

**Unidad de avance:** una subtarea con identificador inmutable `E00.01` … `E09.xx`, evidencia reproducible y estado. Un documento redactado no demuestra un mecanismo; un test sintético correcto no demuestra autonomía.

## 3. Principios de trabajo

1. **No confundir historia e hipótesis.** Cada afirmación sobre C1 debe indicar fuente, cita o extracto verificable, categoría de evidencia y dudas. La cifra de 952 neuronas para un Norn estándar es una **referencia a contrastar**, no una meta de implementación.
2. **La unidad mínima es experimental, no dogmática.** Se empieza por una neurona/sinapsis y luego un circuito conceptual de dos entradas, dos conceptos y dos decisiones. El circuito de seis neuronas es una hipótesis de diseño, no un hallazgo histórico.
3. **Control antes de capacidad.** Cada nueva capacidad se mide frente al diseño sin esa capacidad, con condiciones comparables.
4. **La función de recompensa reside en el evaluador**, no se debe equiparar a voluntad del sistema ni convertirla en misión universal.
5. **Reproducibilidad estricta:** guardar código, hash/versión, configuración, semillas, estímulos, decisiones, refuerzos, estados relevantes y artefactos. Un generador aleatorio debe tener su estado serializado o reseed verificable.
6. **Incremento justificado:** no aumentar nodos, parámetros, módulos ni tecnologías sin un déficit medido o una hipótesis distinta pre-registrada.
7. **Separación de datos:** estímulos y contingencias de evaluación nunca deben filtrarse al controlador por su implementación.
8. **Errores y resultados negativos se conservan.** Un test fallido no se reescribe para hacerlo aprobar; toda corrección debe dejar una explicación causal.
9. **Un cambio por comparación:** evitar simultáneamente aumentar tamaño, cambiar reglas y cambiar datos, porque se pierde atribución.
10. **Sin inferencias psicológicas gratuitas:** oscilación interna no es pensamiento; acierto asociativo no es comprensión causal; selección autónoma no es conciencia.

## 4. Seguimiento de estado y permisos

El código y los resultados técnicos, si llegan a producirse, tendrán su fuente principal en GitHub. Este documento es un protocolo: **no concede autorización para ejecutar cambios en el código** ni para modificar la versión estable. La investigación puede continuar en ChatGPT; un agente investigador externo es una opción pendiente de evaluación, no un ejecutor activado.

No se debe guardar automáticamente cada conversación o investigación futura. La petición actual autoriza **dejar asentado este plan completo**, no reabrir el permiso general para registrar cualquier cosa.

Al ejecutar un ensayo futuro, registrar progreso técnico cuando el usuario haya autorizado esa intervención y siempre comprobar qué se ha escrito.

## 5. Primer paso ejecutable (aún pendiente)

**E00.01 — Inventario y verificación de fuentes originales.** Registrar para cada documento autor, fecha, URL, accesibilidad, edición, naturaleza (primario/secundario), afirmaciones concretas y limitaciones. **No empezar a escribir `neuron.py` hasta que E00.01–E00.07 permitan una especificación suficientemente precisa y se indique qué convenciones son propias.**

## 6. Enlaces de continuidad

- [Issue #102 — línea de investigación](https://github.com/mxlzz/Nilo_public/issues/102)
- [Issue #101 — comparación de antecedentes de Nilo](https://github.com/mxlzz/Nilo_public/issues/101)
- [README general de Nilo](../../README.md)

**Este protocolo no reemplaza el roadmap del motor Nilo 0.7/0.8 ni convierte NeuroLab en una parte funcional del juego.**
