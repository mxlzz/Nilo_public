# E09.02g.4 — resultados de robustez, orden invertido, ruido y retraso

**Fecha:** 2026-11-21. **Preregistro previo al código:** [E09_02G_04_ROBUSTEZ_PRE_REGISTRO.md](E09_02G_04_ROBUSTEZ_PRE_REGISTRO.md). **Evidencia:** [Actions #44934175507](https://github.com/mxlzz/Nilo_public/actions/runs/44934175507), commit efectivamente probado `bdc2a9ab83b45fc5525bbda9297bc65eeb82d9e5`. Suite de **256 tests**, dos expectedFailure históricos E09c/d, sin fallos no previstos. Métricas y estados por semilla: [e09g4.json](resultados/run-44934175507/e09g4.json), guardado de stdout del job y versionado sin modificar el binario del juego.

## Resultados exactos (20 semillas por condición)

| Primera → segunda recompensa | Perturbación | Precisión inicial | Precisión reversión | Baseline congelado (inicial) | Misma semilla supera ambas ≥0.90 | Gate |
|---|---|---:|---:|---:|---:|---|
| D0→D1 | limpia, delay1 | 1.000000 | 1.000000 | 0.492500 | 20/20 | **Sí** |
| D1→D0 | limpia, delay1 | 1.000000 | 1.000000 | 0.507500 | 20/20 | **Sí** |
| D0→D1 | limpia, delay3 | 1.000000 | 1.000000 | 0.492500 | 20/20 | **Sí** |
| D1→D0 | limpia, delay3 | 1.000000 | 1.000000 | 0.507500 | 20/20 | **Sí** |
| D0→D1 | 10 % de pulsos invertidos, delay1 | 0.903125 | 0.850000 | 0.492500 | 16/20 | **No** |
| D1→D0 | 10 % de pulsos invertidos, delay1 | 0.904375 | 0.950000 | 0.507500 | 17/20 | **No** |

- Ruido de feedback reproducible por `random.Random(seed*2_000_000 + tick + 93017)`. **352 pulsos invertidos** por grupo de 20 semillas x180 ticks; ~9,78% de 3600. La misma cantidad para ambos órdenes porque mismo seed/tick.
- El control congelado no modifica sinapsis, y con primer objetivo D1 la precisión base es cercana al azar. **El aprendizaje no depende únicamente de haber elegido D0 como primer objetivo.**
- El retraso 3 funciona bajo **CONCEPTO ÚNICO** y estados de decisión estables; **no demuestra crédito causal correcto en presencia de distractores o cambios frecuentes de contexto**.
- Los dos ensayos con 10% de pulsos incorrectos **no superaron** el umbral conjunto de 18/20 semillas. No se redefinieron tasas ni duración tras observar resultado negativo.

## Diagnóstico y decisión de próxima etapa

1. **E09g.3/g.4 siguen siendo un aprendizaje de UNA asociación contextual**: Concept fijo C=253 con P0=P1=255. Con una única señal, el cerebro puede memorizar una preferencia sin distinguir situaciones.
2. **No aumentar el número de unidades para mejorar exactitud simplemente.** La siguiente prueba debe separar dos estímulos y dos preferencias incompatibles y mantener un baseline tabular; exige un segundo detector Concept, por tanto **seis unidades** P0,P1,C0,C1,D0,D1. Esta es una necesidad experimental, no una promesa de mejor inteligencia.
3. Comparar con un baseline tabular de dos estados que reciba los mismos pulsos y número de ensayos; una red de sinapsis no se justifica por precisión si la solución tabular iguala o supera su rendimiento con menos complejidad.
4. El siguiente protocolo **E09g.5** debe comprobar aprendizaje de dos contextos **intercalados en el tiempo**, cambio de contexto y retraso real de la señal. Si el refuerzo de contexto A llega cuando B está activo, la elegibilidad local podría reforzar B por error, reproduciendo E05. Registrar fallos.
5. No introducir ahora metabolismo, motivaciones, un LLM, cuerpo ni mundo. Mantener separadas las reglas verificadas por genética/C1 PE32 de decisiones de laboratorio sobre el número de neuronas y el evaluador de pulsos.

**Estado de alcance:** dos fórmulas de almacenamiento, WTA, SVRule, migración y aritmética neuronal se han estudiado; G00-H (fidelidad total del ejecutable), G05 (crédito diferido), G09 (mente libre integrada) permanecen **abiertas**. No fusionar PR #103 ni modificar el motor de Nilo.
