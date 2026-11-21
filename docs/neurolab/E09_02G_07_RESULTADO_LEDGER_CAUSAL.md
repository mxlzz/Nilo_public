# E09.02g.7 — resultado del ledger causal por tick, sin modificar C1

**Fecha:** 2026-11-21. **Preregistro anterior al código:** [E09_02G_07_CREDITO_CAUSAL_PRE_REGISTRO.md](E09_02G_07_CREDITO_CAUSAL_PRE_REGISTRO.md). **Ejecución verificada:** [Actions #44938471293](https://github.com/mxlzz/Nilo_public/actions/runs/44938471293), commit probado `b28cc734079c2df8165fa83e12b59c844f54e534`, job `136950251030`, conclusión **success**. Artefactos `metrics/e09g7_causal_ledger.json` (ledger completo por tick/semilla) y `metrics/e09g7_summary.json` (resumen), retención limitada.

El código observacional reproduce **exactamente** por semilla y por fase los estados finales y el químico pendiente de `train_brain` E09g.5, sin modificar `C1ContextBrain` ni su entrenamiento.

## Datos exactos

| Medida en 20 semillas × 2 fases | Conteo |
|---|---:|
| Ticks de entrenamiento auditados | **10.240** |
| Pulsos de recompensa/castigo no nulos | **10.220** |
| Pulsos con Concept anterior y Concept de plasticidad identificables | **10.200** |
| Pulsos con fuente desconocida (arranque inicial) | 20 |
| Pulsos con **desalineación de Concept** | **652** |
| Desalineaciones también con cambio STW en alguna dendrita | **331** |
| Desalineaciones también con cambio LTW | **0** |

La desalineación representa **652/10.200 ≈ 6,39 %** de los pulsos comparables. Se distribuye de forma muy localizada:

- **319** en fase A, posición 1 de bloques cuyo estímulo cambió;
- **324** en fase B, misma posición 1 de los bloques con cambio;
- **9** en fase B, posición 1 del primer bloque de esa fase (posible cambio de contexto respecto al final de A);
- **0 desalineaciones restantes** en todas las demás clases de posición/borde auditadas.

En consecuencia, la falta de alineación *sigue la estructura temporal del cambio de contexto*, no una dispersión aleatoria. En 331/652 ≈ 50,77 % de estos eventos cambió al menos un STW; no se registraron cambios LTW simultáneos en ellos.

## Qué demuestra y qué no

**Sí:** existe una discordancia sistemática verificable en la microred: el Concept leído al elegir una acción anterior puede ser diferente del Concept presente cuando se recibe su recompensa y se actualizan las sinapsis. La localización exacta concuerda con el desfase de la tubería Concept→Decision y con los errores transitorios de g.5a.

**No:** un cambio de STW en ese tick no es prueba suficiente de que el pulso lo causó: puede intervenir relajación/decaimiento; tampoco prueba que esos pulsos expliquen el fracaso de aprendizaje en 8 semillas. El entrenamiento usa un protocolo de laboratorio con feedback externo, no la bioquímica completa ni el scheduler original de Creatures 1. **G05 continúa abierta.**

## Próxima prueba pertinente

Para pasar de correlación temporal a una intervención controlada, preregistrar **E09g.8** sin cambiar neuronas ni sinapsis: comparar (C) feedback original, (G) supresión de pulsos justo en la posición 1 de los cambios de contexto (donde g.7 encontró discordancia), y (S) supresión de igual cantidad en la posición 2 del mismo bloque (control de menor cantidad de feedback). Conservar semillas, entrenamiento, holdouts y prueba del baseline original; no adoptar supresión externa como diseño neuronal. Un beneficio exclusivo de G apoyaría que el crédito desalineado contribuye al rendimiento; un resultado nulo o adverso limita esa hipótesis.
