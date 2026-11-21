# E09.02d — resultado negativo con mejora parcial por exploración

**Fecha 2026-11-21.** Preregistro previo al código: [E09_02D_EXPLORACION_PRE_REGISTRO.md](E09_02D_EXPLORACION_PRE_REGISTRO.md).
Primera ejecución de tests con resultado negativo: [CI #44920313877](https://github.com/mxlzz/Nilo_public/actions/runs/44920313877), SHA `16b01907cd41d988c849d1607871ed0aa987968b`.

| Métrica | E09.02c (solo exploración en empate) | E09.02d epsilon=0.10 |
|---|---:|---:|
| Precisión media antes de inversión | 1.0000 | **0.9450** |
| Control congelado | 0.4925 | **0.4375** |
| Precisión media después de inversión | 0.3000 | **0.8000** |
| Semillas que superan ≥90 % antes de inversión | 20/20 | **19/20** |
| Semillas que superan ≥90 % tras inversión | 6/20 | **16/20** |
| Umbral preregistrado de inversión | ≥18/20 | **NO ALCANZADO** |

**Conclusión:** el cambio en la política de selección *mejora* la reversibilidad sin alterar pesos ni el refuerzo, pero **G09.02d permanece NO APROBADA**. No cambiar epsilon=0.10, umbrales, semillas, duración ni hipótesis después de ver resultados. La versión original E09.02c con tasa base y su evaluación negativa se preserva.

Un test de la suite mantiene el criterio original e indica `expectedFailure` para separar un resultado científico conocido negativo de errores de código regresivos. Ello **no convierte la hipótesis en confirmada**: ejecutar los scripts originales como protocolos estrictos sigue dando fallo en la puerta.

### Interpretación

La exploración limitada tiene un coste en exactitud una vez aprendida la preferencia; pasar de 100 % a 94,5 % es consistente con elecciones exploratorias. La reversión mejora de 30 % a 80 % pero falla en 4 semillas del umbral requerido y no justifica ajustar repetidamente la probabilidad de explorar.

La mejor siguiente línea de trabajo, dado que ahora poseemos el genoma original, es **reconstruir la actualización real de susceptibilidad, STW, LTW y fortaleza según las reglas documentadas de Creatures 1**, con dos canales químicos independientes Reward/Punishment y hormonas antiatrofia, sin sustituirlas por el incremento fijo de +16 del experimento. Comparar más tarde contra ambos controles negativos E09.02c/d.

Fuentes: [C1 Brain Guide, Processing Dendrite Reinforcement and Atrophy](https://zenzoa.com/creatures/c1-brains.html), [paper histórico](https://www.cp.eng.chula.ac.th/~vishnu/gameResearch/AI/creatures.pdf), [C1 Chemical List](https://creatures.fandom.com/wiki/C1_Chemical_List).
