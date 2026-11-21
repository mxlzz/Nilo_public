# E09.02g.6 — resultado de ablaciones temporales, sin cambiar aprendizaje

**Fecha:** 2026-11-21. **Preregistro anterior al código:** [E09_02G_06_ABLACIONES_TEMPORALES_PRE_REGISTRO.md](E09_02G_06_ABLACIONES_TEMPORALES_PRE_REGISTRO.md). **Resultado real:** [Actions #44938181968](https://github.com/mxlzz/Nilo_public/actions/runs/44938181968), commit probado `61728a68216d6d8a312802209c3bb1edbd07329f`, conclusión **success**, job `136949340363`, paso «E09g6 preregistered holdout-only perceptual latency and decision state ablations». JSON por semilla en `metrics/e09g6.json` dentro del artefacto `neurolab-metrics` (retención limitada).

**Alcance:** red E09g.5 intacta (6 unidades, 8 sinapsis, entrenamientos congelados, 20 semillas, 256 ticks/fase, 16×8 ticks de holdout); solo se cambió artificialmente el estado de evaluación en los bordes de bloque. Ningún resultado reabre retroactivamente el gate E09g.5.

## Resultados exactos

`C` = sin intervención; `N` = reset a Decision basal al inicio de cada bloque; `W` = precargar Concept correcto del contexto actual; `NW` = ambas a la vez. **N y W usan el conocimiento externo de dónde comienza cada bloque; W también precarga su contexto**, cosa que el cerebro original no puede hacer sin tiempo de procesamiento.

| Condición | Steady fase A | Steady fase B | Exactitud total A | Total B |
|---|---:|---:|---:|---:|
| C (original E09g.5) | **0.9671875** | **0.9302083** | 0.8890625 | 0.8546875 |
| N | 0.9916667 | 0.9692708 | 0.9136719 | 0.8921875 |
| W | 0.9838542 | 0.9505208 | 0.9550781 | 0.9199219 |
| NW (oracle combinado) | **1.0000000** | **1.0000000** | **1.0000000** | **1.0000000** |

- Precisión `early` (primeros 2 de 8 ticks), fases A/B: **C** 0.6546875/0.628125; **N** 0.6796875/0.6609375; **W** 0.86875/0.828125; **NW** 1/1. W aporta una corrección inmediata marcada pero por sí sola no elimina errores steady.
- Delta medio de `steady` frente a C, A/B: **N** +0.0244792/+0.0390625, **W** +0.0166667/+0.0203125, **NW** +0.0328125/+0.0697917. Los deltas medios tienen techo: C ya era alto en muchas semillas.
- Entre las **8 semillas que fallaron originalmente**, N supera +0.10 steady en 2 (A) y 3 (B); W en 0/0; NW en **3 (A) y 7 (B)**. Se cumplió en la fase B, pero no en la A, la regla operativa preregistrada de contribución relevante en 4/8 semillas. No es una puerta de éxito cognitivo.
- Ejemplo **semilla 16 fase B**: C 0.6875 → N 0.7708333 → W 0.7291667 → NW **1.0**. Ejemplo semilla 2 B: C 0.7708333 → N 0.9270833 → W 0.8333333 → NW **1.0**.
- Se reprodujo por control la falla **12/20 semillas** de g.5 sin intervención, con las mismas semillas fallidas `[0,2,3,4,8,16,17,19]`. Los 20 pares de resultados se conservaron en el JSON, sin exclusión ni ajuste posterior.

## Interpretación

El patrón es **compatible con interacción entre persistencia de Decision y latencia de Concept**: cada intervención aislada ayuda de forma parcial, y el combinado elimina los errores del holdout dado. Puesto que las sinapsis permanecen idénticas, los pesos aprendidos **son capaces de producir todas las elecciones correctas en estas pruebas cuando el banco de evaluación suministra los estados favorables**. No está probado que la red pueda descubrir esos estados o reiniciarse con la información disponible; el resultado no convierte la microred en mente autónoma.

**Límite causal clave:** N y W no son mecanismos internos de C1, sino intervenciones oráculo en los límites del bloque. No se debe implementar N/W como «arreglo» sin diseñar y validar un disparador biológico/interno plausible y sin distinguirlo de la fidelidad histórica. La tabla Q 2×2 sigue siendo una solución más económica para el problema de dos estados y dos acciones; E09g.5 original sigue fallida, G05 y G09 siguen abiertas.

## Próximo paso con prioridad

Antes de añadir neuronas o cambiar constantes del genoma, **E09g.7: trazar por tick la procedencia del refuerzo** en el entrenamiento original: acción premiada/castigada, Concept leído al elegirla, Concept activo cuando se aplica la plasticidad, y presencia de discordancia al cruzar contextos. Medir las 20 semillas A/B y contrastar controles de frontera. Esto permitirá decidir si hay un problema de crédito temporal real adicional a los estados persistentes. **No** es autorización para introducir un oráculo de contexto en el cerebro ni integrar con Nilo.
