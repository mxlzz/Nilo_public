# ADR-0011 — H20: evaluación limitada de pyDeltaRCM sin adoptar conservación no demostrada

**Fecha:** 2026-11-22. **Estado:** evaluación reversible; **no** adoptar como proveedor del owner del mundo.

## Motivo de avance y hecho crítico verificado

[H19](ETAPA_3_H19_RESULTADOS_DEPOSITO_CONEXO.md) falló su criterio más importante: una sola componente de50 nodos deposicionados era casi idéntica al nulo aleatorio que preservaba el conteo por fila. El gradiente y la discontinuidad de su cuenca explican el supuesto patrón, así que **NO** hay evidencia de organización estructural nueva.

**Candidato especializado, distinto fenómeno:** [pyDeltaRCM](https://github.com/DeltaRCM/pyDeltaRCM), revisión upstream `a107c1d0f6b18ac19ac15ec4586179678329ae35`, licencia MIT, proyecto publicado [Moodie et al. 2021, JOSS](https://doi.org/10.21105/joss.03398), ofrece delta y canales por transporte de agua/sedimentos. CPU Python≥3.11, NumPy/Numba/NetCDF/Scipy/Matplotlib, API `DeltaModel.update()` y semilla.

**Advertencia decisiva del propio upstream:** [guía oficial de conservación de sedimento](https://deltarcm.org/pyDeltaRCM/examples/verify_mass_conservation.html) advierte expresamente: «DeltaRCM formulation is explicitly not conservative of mass (neither water nor sediment)». Identifica pérdidas por `stepmax`, exportación de la frontera e imposición de cotas en inlet. El ejemplo oficial contiene `MassConservationCheck` y expone `Qs0*dt`, `eta-eta_init`, `Vp_lost`, `Vp_exported`, `Vp_inletbc`. Esta limitación **impide adoptarlo directamente** como motor material sin un análisis de tolerancia/residuo, pero **no impide probarlo como benchmark de morfología con medición explícita de incumplimientos**.

**Alternativas:** Landlab H9/H19 (ya ejecutado, patrón explicable por condiciones); GeoTaichi y MPM H12/H13A (falló estabilidad/instalación, excesivo para delta); OpenFOAM (costo y malla mayor, sin necesidad inmediata). No reimplementar física propia ni diseñar módulos de consolidación inventados.

## Decisión acotada

**H20A, prueba de viabilidad de modelo externo**: usar pyDeltaRCM original de revisión pinneada sin modificarlo, en dominio moderado y pasos limitados, y medir si produce cambios de elevación no uniformes, diferencias entre semillas, replay determinista y presupuesto **documentado como diagnóstico sin confundir diferencia de stock con fuente de masa**. No se publicará su `eta` sobre el inventario xarray, y ninguna masa de su solver contará como stock canónico.

**Stop/go:** si ni siquiera genera cambios diferenciados o tiene desviación de sedimento grande sin ledger reconciliable, no integrar; si demuestra patrones plausibles, todavía se exige un experimento H20B posterior con controles de frontera y comparación estructural antes de aprobar E3. **Prohibido concluir «emergencia» por capturas, plumas o distintos seeds.**

**Licencia:** MIT según `pyproject.toml` upstream. El código del proveedor se instala/accede en CI, no se copia al repositorio mundo.
