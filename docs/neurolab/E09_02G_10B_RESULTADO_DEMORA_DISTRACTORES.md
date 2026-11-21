# E09.02g.10b — resultado negativo de crédito diferido con distractores

**Fecha:** 2026-11-21. **Preregistro anterior al código:** [E09_02G_10B_DEMORA_DISTRACTORES_PRE_REGISTRO.md](E09_02G_10B_DEMORA_DISTRACTORES_PRE_REGISTRO.md).

**Evidencia ejecutada:** [GitHub Actions #44942700990](https://github.com/mxlzz/Nilo_public/actions/runs/44942700990), job `136963175838`, commit ensayado `738e002a85b4346eb44af0b83ebf889b5d6b8345`. **CI `success`, 308 tests, dos expectedFailure históricos.** Datos por semilla archivados permanentemente en [e09g10b.json](resultados/run-44942700990/e09g10b.json), no se depende solo de artefactos temporales.

## Diseño ejecutado

40 semillas nuevas **120..159**, 60 ensayos de entrenamiento y 36 de holdout por fase, balance de S0/S1 y 1–3 distractores intermedios, inversión A→B sin reset. Cada ensayo: cuatro ticks del objetivo (solo se evalúa la cuarta decisión), 1–3 ticks del contexto contrario y un último tick de distractor donde llega el pulso correspondiente a aquella decisión objetivo. **Demora de entrega = d+1 ticks después de la decisión**; por eso no describir esta prueba como recompensa aplicada directamente en t+1, t+2 o t+3.

- **C:** microred C1-reducida, plasticidad original.
- **IG:** misma microred más compuerta interna del Concept inmediatamente anterior, **sin modificar esa regla**.
- **F:** mismas sinapsis congeladas.
- **Q:** tabla causal 2×2 que conserva la pareja contexto/acción verdadera hasta la llegada del feedback; tiene información de procedencia que C/IG **no reciben** y no reproduce los ticks internos de un cerebro.

No hay universo físico, bioquímica completa de Creatures ni inteligencia autónoma comprobada.

## Resultado real

| Modelo | Precisión A | Precisión B invertida | Semillas ≥90 % en A y B |
|---|---:|---:|---:|
| C original | **0.8896** | **0.8472** | **16/40** |
| IG compuerta experimental | 0.7278 | 0.7556 | **6/40** |
| F sin plasticidad | 0.5063 | 0.4861 | **0/40** |
| Q con procedencia causal | **1.0000** | **1.0000** | **40/40** |

- **Ambas redes C e IG FALLAN** la puerta preregistrada (≥36/40 semillas, medias ≥0.85 y por demora≥0.70). C supera de forma clara al control F, pero no logra la fiabilidad requerida; IG empeora el resultado frente a C.
- Precisión media de C para 1/2/3 distractores: A 0.8854 / 0.8958 / 0.8875; B 0.8563 / 0.8417 / 0.8438. IG en A 0.7292 / 0.7313 / 0.7229; en B 0.7542 / 0.7521 / 0.7604. El efecto negativo de IG atraviesa los tres grupos de demora, no está aislado en un único grupo de test.
- **IG suprimió exactamente 800 de 2.400 pulsos** en A y **800 de 2.400** en B (20 de 60 ensayos por semilla), pese a que cada pulso remitía a una acción objetivo real. La proporción (1/3) coincide con los ensayos d=1; el código indica que la compuerta detecta un cambio de fuente cuando hay un solo distractor, pero no recupera la procedencia de la acción original para d=2/3. Esta asociación se basa en la estructura del reloj, no en una ablación causal independiente por cada demora.
- Q fue **informacionalmente privilegiado** y recibe una única pareja causal en el momento del target. Demuestra que la tarea tiene una solución pequeña y reproducible *con esa información*, no que una neurona C1 debería alcanzar 100 % ni una ventaja justa con igual presupuesto informacional.
- El criterio adicional registrado para **detención obligatoria** (superioridad de Q sobre mejor neuronal ≥+0.15 promediando ambas fases) **no se activó**: diferencia observada **+0.1316**. No modificar retrospectivamente ese umbral. No obstante, es razonable **no extender la arquitectura ahora**: IG fue inferior, C no logró la puerta y el simple control Q resolvió el problema.

## Conclusión y priorización

El buen resultado anterior de g.10a se limitaba a **filtrar un pulso asociado con un cambio perceptual inmediato**, no a atribuir consecuencias a decisiones más antiguas cuando se intercalan otros estímulos. Aquí descartar químico en vez de asociarlo con la elección de origen perjudica el aprendizaje. El hallazgo **no** prueba cómo aprenden los Norns reales, ni invalida la plasticidad C1 original, porque la tarea y el feedback son artificiales.

**Siguiente trabajo prioritario: análisis comparativo, todavía sin agregar neuronas ni reescribir C1.** Contrastar: (1) cola explícita de eventos, (2) trazas de elegibilidad sinápticas con decaimiento temporal, (3) mecanismos históricos C1 que ya podrían abordar parte de la demora. Considerar fidelidad, presupuesto de estado, riesgo de crédito espurio y compatibilidad con el ejecutable; decidir si existe una prueba **más discriminante y necesaria** antes de implementar. Evitar volver a tunear el simple clasificador S0/S1.

**Ramas:** los resultados y el código están en PR draft #103; `main` y motor Nilo 0.7 intactos. G00-H/G05/G09 global continúan abiertos.
