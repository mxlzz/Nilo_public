# NeuroLab NR01.03-DP — resultado del piloto preregistrado (desarrollo, semilla 23000)

**Fecha 2026-11-22 · ESTADO: PILOTO DE SOFTWARE/EXPLORACIÓN APROBADO, HIPÓTESIS CIENTÍFICA NO APROBADA.**

## Identidad y procedencia
- Preregistro anterior al runner: [NR01_03D_PREREGISTRO_PILOTO_DESARROLLO_20261122.md](NR01_03D_PREREGISTRO_PILOTO_DESARROLLO_20261122.md), commit `aa2bdc2a6a6e89d7a8d412d7382b2dc95a7cda31`.
- Implementación de piloto y workflow: commit `2816eaec0b6269342678fd1befb89fa8185ab81d`.
- [GitHub Actions 45049410694](https://github.com/mxlzz/Nilo_public/actions/runs/45049410694) **SUCCESS**: compilación/instalación de `artlib==0.1.12`, `scikit-learn==1.9.1`, ejecución 16/16 condiciones, artefacto subido.
- Artefacto temporal: [nr01-development-pilot-23000](https://github.com/mxlzz/Nilo_public/actions/runs/45049410694/artifacts/14764527835), ID `14764527835`, ZIP SHA256 `5fdbe5dea6a4deb8feb23e9922f32ac568e8a7609bed597213bfefadbf54b1f8`, expiración declarada 2027-02-20. Contiene JSON completo y JSONL incremental. **No se ha archivado todavía el JSON completo en Git**; los números siguientes provienen del stdout del job, no de inspección integral del JSON.
- Semilla desarrollo: **23000** únicamente. Históricas1400..1419 y confirmación24000..24019 **sin usar**.

## Lectura literal de las métricas primarias checkpoint32 (un único mundo por familia)

| Brazo | A original | A inversión | B1 | B2 | Estado |
|---|---:|---:|---:|---:|---|
| raw lineal | 1.0000 | 0.5000 | 0.6667 | 0.6667 | completo |
| FIFO 1-NN16 | 1.0000 | 1.0000 | 0.5000 | 0.9167 | completo |
| KMeans K4 | 1.0000 | 0.2500 | 0.6667 | 0.8917 | completo |
| KMeans K8 | 0.9875 | 0.0000 | 0.4417 | 0.8917 | completo |
| KMeans K16 | 1.0000 | 0.3188 | 0.6083 | 0.6667 | completo |
| FuzzyART rho .60 | — | — | — | — | fuera de presupuesto: 29 categorías A, 26 B |
| FuzzyART rho .80 | — | — | — | — | fuera de presupuesto: 58 A, 139 B |
| FuzzyART rho .90 | — | — | — | — | fuera de presupuesto: 119 A, 167 B |

Las condiciones ART (6/6) excedieron el límite preregistrado de **16 categorías**. El pipeline no las recortó ni les atribuyó 0% de precisión: quedaron **inelegibles por costo/capacidad**. Las otras 10 condiciones completaron el piloto; **0 excepciones**. Todos los reportes de cada familia usaron cintas de adquisición, feedback y test comprobadas por SHA; el runner aborta ante discrepancia.

## Interpretación y siguiente decisión

1. El éxito CI valida **ejecución e invariantes del harness**, no beneficio cognitivo ni G09, que sigue no superada.
2. **No hay justificación para ajustar rho, K, topes o complejidad del decoder** tras ver esta semilla. Tampoco corresponde declarar que ART *siempre* excede16 en todos los mundos: solo se midió una semilla.
3. Los baselines simples son suficientemente competitivos y la reversión en A perjudica varios brazos KMeans; sin comparación pareada por mundos y ablaciones no se puede atribuir causalidad.
4. **Propuesta alineada con NR01.03/04:** ejecutar una sola cohorte restante de desarrollo **23001..23019**, con el mismo código/parámetros/semillas preregistradas, registrando los fallos de ART por presupuesto. El resultado de semilla23000 se agrega descriptivamente al informe de desarrollo, pero no se transforma en confirmación. No ejecutar confirmación24000..24019 si no aparece ventaja práctica y mecanismo defendible en desarrollo.
5. Antes del desarrollo completo: verificar que el programa serialice los **20 mundos por brazo**, derive métricas pareadas por mundo y preserve resultados permanentes (no solo artefactos temporales). Ninguna nueva arquitectura, mundo/LLM ni modificación de main.

**Siguiente unidad: NR01.04-A, preregistro y runner de cohorte de desarrollo completa, sin tuning y con stop gate previo a confirmación.** El PR#103 permanece borrador, aislado de main/Nilo0.7.
