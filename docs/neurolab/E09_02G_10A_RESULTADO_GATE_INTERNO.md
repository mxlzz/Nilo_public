# E09.02g.10a — resultado de memoria interna mínima de procedencia de Concept

**Fecha:** 2026-11-21. **Pre-registro anterior a implementación:** [E09_02G_10A_GATE_INTERNO_PRE_REGISTRO.md](E09_02G_10A_GATE_INTERNO_PRE_REGISTRO.md). **Prueba real:** [Actions #44939579597](https://github.com/mxlzz/Nilo_public/actions/runs/44939579597), commit probado `91a67678aeaf1be8b8356ac4a0441aaa0db93afd`, job `136953597029`, **CI success: 300 tests (2 expectedFailure históricos)**. [Salida completa versionada](resultados/run-44939579597/e09g10a.json).

## Pregunta y diseño

Se implementó una envoltura experimental [e09_intrinsic_gate.py](../../experiments/neurolab/e09_intrinsic_gate.py) alrededor de `C1ContextBrain` **sin modificar la clase C1**, con memoria del par `Concept outputs` usado en la decisión anterior. Si el concepto usado antes y el concepto que interviene ahora en la plasticidad son identificables y no coinciden, se suspende el pulso químico **solo ese tick**. No consulta bandera de cambio contextual, posición de bloque, solución correcta ni resultados futuros. Esta **regla está programada por nosotros; no aprendida ni verificada en el genoma original**.

Se prueban **20 semillas nuevas 100..119**, dos fases de entrenamiento A/B y holdouts idénticos a g.5. Brazos: C original, G compuerta externa de g.8 y IG compuerta interna con **dos valores byte de memoria lógica y un marcador de inicialización**. Los objetos Python consumen más memoria real; no equiparar dos bytes lógicos con uso real de RAM.

## Resultados exactos

**Criterio de factibilidad preregistrado: paridad IG=G de estado completo, químico pendiente, número de supresiones y métricas de holdout por fase para 20/20 semillas.**

**Resultado: APROBADO técnicamente, 20/20 paridades exactas.** El registro conserva métricas por semilla y fase, no solo medias.

| Modelo | Steady A | Steady B | Early A | Early B | Ambos steady≥0.90 |
|---|---:|---:|---:|---:|---:|
| C sin compuerta | 0.9578125 | 0.9229167 | 0.6359375 | 0.6625000 | **12/20** |
| G externa | **0.9718750** | **0.9656250** | 0.5781250 | 0.6234375 | **17/20** |
| IG interna | **0.9718750** | **0.9656250** | 0.5781250 | 0.6234375 | **17/20** |

- IG omite **328** pulsos en fase A y **331** en fase B, exactamente los mismos de G y conserva la misma química pendiente y estado sináptico completo.
- IG reproduce las decisiones y resultados de G sin saber qué es un borde de bloque: basta **comparar la traza interna de la decisión anterior con las salidas Concept presentes en el tick actual** en esta tarea de dos contextos one-hot.
- La misma equivalencia implica que IG hereda **el coste de exactitud temprana** de G; no elimina los errores del contexto ni alcanza el criterio de 18/20.
- El controlador tabular con memoria causal explícita ya obtuvo 1.0 en g.5 con menor complejidad. IG no ha mostrado ventaja para este problema de dos estados y dos acciones.

## Interpretación y decisión de enfoque

La prueba demuestra **suficiencia informacional local para reproducir un filtro temporal específico** con memoria adicional muy pequeña. No prueba formación autónoma de ese mecanismo, ni una solución a los distractores, ni a feedback demorado más allá de un tick. **G05 y G09 siguen abiertas**, y el comportamiento no está demostrado por la genética ni el ejecutable C1 original.

**No adoptar IG en Nilo ni añadir una neurona:** antes de cualquier integración se debe estudiar una tarea que exija atribución temporal auténtica, por ejemplo refuerzo de 1–3 ticks de retraso y estímulos distractores intercalados, con banco que mantenga separado el tiempo de acción del de recompensa. Debe existir un control de memoria de procedencia causal más simple (tabla Q o cola de eventos), y un diseño preregistrado que acepte que el filtro de cambios visibles **podría fallar**. Evaluar primero si el aporte informacional y costo justifican continuar con una red C1-reducida, en lugar de optimizar indefinidamente el juguete S0/S1.

**Estado del repositorio:** PR #103 sigue en borrador; `main` y motor Nilo 0.7 intactos, sin introducir cuerpo, mundo ni LLM.
