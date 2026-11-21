# E0.8 — H11c: comparación normalizada de dos rutas hídricas Landlab

**Fecha:** 2026-11-21. **Estado:** H11c VALIDADA, selección provisional; no motor definitivo.
**Pre-registro:** `ETAPA_0_8_DRYp_ALTERNATIVAS_Y_H11C_PLAN.md`.
**Código:** `experiments/probe_water_solver_normalized.py`.
**CI final:** https://github.com/mxlzz/Nilo_public/actions/runs/44956883575 (**SUCCESS**).
**CI previo con defecto de indicador:** https://github.com/mxlzz/Nilo_public/actions/runs/44956774655 (**FAIL**). Se corrigió sin relajar tolerancias de escenario con lluvia.

## Comparación justa y exclusiones
- Landlab 2.11.0. Malla 12×12, 1m, 100 celdas/nodos interiores, pendiente analítica y cierre de bordes, 60s con pasos 0.5s; lluvia 72mm/h durante 60s; profundidad superficial inicial compartida `1e-8m`; columna infiltrada inicial `0.01m`; Green–Ampt de ambas con conductividad 1e-6m/s, sandy loam, Manning 0.03.
- Solver A: `OverlandFlow` de Almeida con lluvia m/s.
- Solver B: `KinwaveImplicitOverlandFlow` con `changing_topo=True`, lluvia mm/h y exponente 5/3.
- Pruebas A/B para (1) lluvia+infiltración; (2) lluvia+K=0; (3) sin lluvia+K>0; (4) lluvia+infiltración y +0.2m a un nodo, y replay.
- Presupuesto **normalizado al agua agregada** (0.120m³). No inflar exactitud dividiendo por el ~1m³ de columna ya infiltrada al inicio.
- **NOTA**: los dos solvers tienen ecuaciones distintas y son candidatos, no dos implementaciones que deban dar la misma distribución espacial.

## Resultados CI

### de Almeida + Green-Ampt
- Aporte de lluvia: `0.12000000000000001m³`.
- Agua superficial al final: **0.09795467982349458m³** (no confundir con agua añadida total, la película inicial suma 1e-6m³).
- Nuevo volumen infiltrado: **0.022046320176505874m³**.
- Error absoluto de presupuesto conjunto: **2.220446049250313e-16m³**, error relativo versus lluvia 1.85e-15.
- Tiempo de cálculo del par agua+infiltración para un evento: **0.019636 s** en runner. No incluye import/instalación.
- Con K=0: 0 infiltración; con lluvia=0: 0 infiltración. Relieve modificado: distribución de agua cambia en hasta 0.001421165m; balance correcto.
- Replay bit a bit idéntico.

### Kinwave + Green-Ampt
- Agua superficial final: **0.0979545807196176m³**.
- Nuevo volumen infiltrado: **0.022046320111763218m³**.
- Residual conjunto: **-9.916861931635879e-8m³**, relativo a lluvia **8.264e-7** (muy por debajo del límite 0.001).
- Tiempo de cálculo del par: **0.836652 s**.
- K=0: 0 infiltración. Sin lluvia, el modelo movió una cantidad diminuta de la película inicial al subsuelo (~2.348e-10m³), mientras el balance conjunto se conservó con error **8.66e-15m³**; la aserción predefinida para control sin lluvia (<1e-9m³ de infiltración nueva) pasó.
- Terreno modificado: diferencia máxima de distribución de profundidad 0.001364103m, balance correcto.
- Replay bit a bit idéntico.

### Desempeño relativo
- Tiempo `Kinwave/Almeida` en ensayo activo ~**42.61** veces.
- Diferencia de almacenamiento superficial entre activos aproximadamente **9.91e-8m³**. Las infiltraciones calculadas difirieron solo **6.47e-11m³**, pero esto NO implica equivalencia física general; es una condición uniforme y extremadamente corta.
- Ambos aprobados en agua no negativa, ausencia de creación bajo controles, respuesta topográfica y cierre de balance.

## Incidencia CI y diagnóstico
El primer H11c falló por un indicador sin sentido: en el caso sin lluvia se reportaba `abs(residual)/1e-12`. Un error flotante de ~8.66e-15m³ producía un aparente 0.00866 relativo. Se separó criterio: con lluvia, residual relativo <0.001 respecto de lluvia real; sin lluvia residual absoluto <1e-9m³; se añadieron diagnósticos por escenario, no se cambiaron parámetros del modelo. La corrida final pasó.

## Decisión experimental, REVERSIBLE
**Priorizar provisionalmente `OverlandFlow` de Almeida + Green–Ampt para las siguientes pruebas de escala y agua superficial/infiltración:** misma interoperabilidad básica en este caso, menor error numérico y menor costo; `KinwaveImplicit` queda como alternativa control y benchmark, sobre todo para casos donde su formulación implícita demuestre ventaja.

**Bloqueos:** resultados de 12×12, lluvia de 60s y borde cerrado no caracterizan pendientes extremas, sequías, acuífero, componente radicular, evapotranspiración, salida de cuenca, performance de áreas grandes. Un comparativo sin calibración/benchmarks de procesos más exigentes no autoriza elegir arquitectura de mundo. DRYP2/CUWALID requiere evaluación independiente.
