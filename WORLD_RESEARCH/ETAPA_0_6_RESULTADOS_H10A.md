# E0.6 — Resultado H10a: la radiación necesita refrescar la geometría

**Fecha:** 2026-11-21. **Estado:** H10a VALIDADA; H10b no iniciada. **Etapa 0 ABIERTA.**
**Protocolo anterior al código:** `ETAPA_0_6_PROTOCOLO_RETORNO_RADIACION.md`.
**Ensayo:** `experiments/probe_landlab_radiation_topography.py` + `.github/workflows/world-landlab-radiation-return.yml`.
**Evidencia GitHub Actions (SUCCESS):** https://github.com/mxlzz/Nilo_public/actions/runs/44952322090 .

## Fuente y contexto
Landlab 2.11.0 `Radiation` calcula pendiente y orientación (slope, aspect) en `__init__`, a partir de topografía en nodos. `update()` usa esos arreglos sin volver a calcularlos. `PotentialEvapotranspiration` consume el campo geométrico `radiation__ratio_to_flat_surface` y modifica PET por celda. La prueba no incorpora nuevas leyes físicas.

## Escenarios empíricos
- 8×8 nodos, malla 10m, relieve ≥100m con pendiente. Día fijo = 0.5 fracción de año; perturbación de un nodo central: +12m.
- A: topografía original, nueva instancia de Radiation+PET; repetición A idéntica.
- B: topografía modificada, reutilizando la **misma** instancia de Radiation.
- C: la misma topografía modificada, **recreando** Radiation y calculando de nuevo PET.

## Valores CI (unidades y escala de prueba, no calibración)
- Radio de incidencia medio inicial: 1.0019617224 (adimensional).
- B, instancia obsoleta: 1.0019617224; cambio máximo radio **0**. Pendientes almacenadas sin cambios.
- C, instancia nueva: radio medio 0.9974032653; cambio máximo de ratio por celda **0.0980859156**.
- Cambio máximo de pendiente por reinit: **0.2797033831** radianes.
- PET media inicial: 8.0156937792; PET media nueva: 7.9792261221; diferencia PET máxima frente a instancia obsoleta: **0.7846873247 mm/día**.
- H10a: **PASS** para reproducibilidad, sensibilidad geométrica al reiniciar, y falsación de la hipótesis implícita de auto-refresco geométrico.

## Dictamen
`Radiation.update()` **no** es seguro como actualización completa de un relieve dinámico; una instancia almacenada puede producir incidencia topográficamente obsoleta. Una ruta viable, aún experimental, es construir una instancia nueva cuando cambia la topografía (pudiendo ser costosa en mallas grandes). No interpretar PET diferente ante una perturbación de +12m como sensibilidad perceptible a erosión natural micrométrica. **No se aprobó aún rendimiento ni ciclo completo ni preservación de energía/agua.**

## Siguiente gate
Diseñar H10b como prueba controlada de un lazo temporal topografía→Radiation→PET→SoilMoisture→Vegetation→DepthDependentDiffuser→topografía, con control que congela únicamente la relación relieve→radiación, pero mantiene dinámica ecológica. Verificar material sólido cerrado y magnitud real de respuesta. Conservar control de perturbación externa grande separado de la señal endógena muy pequeña de H9. No introducir `SPACE` en el mismo inventario hasta reconciliar su paso temporal y conservación.
