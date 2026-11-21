# E0.7 — H11b: prueba de flujo superficial + infiltración de agua

**Fecha:** 2026-11-21 · **Estado:** H11b VALIDADA para presupuesto de dos depósitos bajo cuenca cerrada; selección final ABIERTA.
**Protocolo previo a ejecución:** `ETAPA_0_7_PROTOCOLO_H11_AGUA.md` (extensión H11b).
**Arnés:** `experiments/probe_landlab_kinwave_greenampt_budget.py`.
**Workflow:** `.github/workflows/world-landlab-water-budget.yml`.
**CI real reproducible:** https://github.com/mxlzz/Nilo_public/actions/runs/44953307118 (**SUCCESS**, incluye H11a).

## Fuentes y distinción
- Tutorial original de Landlab: https://github.com/landlab/landlab/blob/master/docs/source/tutorials/overland_flow/soil_infiltration_green_ampt/infilt_green_ampt_with_overland_flow.ipynb . **Combina `KinwaveImplicitOverlandFlow` y `SoilInfiltrationGreenAmpt`**; no confundir con `OverlandFlow` de Almeida que se probó separadamente en H11a.
- Solver cinemático: https://github.com/landlab/landlab/blob/master/src/landlab/components/overland_flow/generate_overland_flow_implicit_kinwave.py . `runoff_rate` en **mm/h**, `dt` en **s**, `changing_topo=True` para reruteo con relieve mutable.
- Infiltración Green-Ampt: https://github.com/landlab/landlab/blob/master/src/landlab/components/soil_moisture/infiltrate_soil_green_ampt.py . Reduce `surface_water__depth` (m, nodos) y aumenta `soil_water_infiltration__depth` (m, nodos) por igual volumen de agua. **El segundo campo registra columna de agua que penetró el suelo, NO saturación del área de raíces**.
- Landlab 2.11.0 MIT. Sin nueva ley física, solo escenario y controles.

## Condiciones
- Raster 12×12, 1m por celda, 100 nodos interiores con 1m² cada uno, bordes cerrados, relieve suavemente inclinado con ondulación analítica; perturbación alternativa de un nodo +0.2m antes de iniciar.
- Lluvia sintética `72mm/h` por 60s, 120 pasos de 0.5s.
- Estado inicial de superficie = 0m, infiltración acumulada inicial = 0.01m en cada nodo interior. En presupuesto conjunto esto constituye **1.0m³ de agua inicialmente infiltrada**, sin lluvia previa representada; se registra como *condición inicial*, no volumen generado.
- `SoilInfiltrationGreenAmpt` K activo `1e-6m/s` de referencia, suelo `sandy loam`. Controles K=0 y lluvia=0. Sin pérdidas por evapotranspiración ni flujo de salida.

## Resultados
- Lluvia nueva total esperada: **0.12000000000000001m³**.
- Escenario activo final: **agua superficial 0.09795358218909696m³**; **columna infiltrada acumulada total 1.0220463186406301m³**, de la cual **0.022046318640630225m³** ingresó durante el evento.
- Inventario total final ~**1.119999900829727m³**, frente al esperado **1.12m³**. Residual de balance **-9.917027288253166×10^-8m³**, relativo al mayor inventario de referencia `9.9170×10^-8`. Tolerancia predefinida <0.1% superada. Esta precisión es menor que el error exacto de máquina de H11a; no atribuirla a mejora de solver.
- Control sin infiltración (K=0): infiltración adicional 0m³, volumen superficial final **0.1199999041165424m³**; residual similar ~-9.59e-8m³.
- Control sin lluvia: incremento de infiltración **0** y superficie final **0m³**, inventario acumulado inicial 1m³ sin cambio.
- Intervención de topografía +0.2m: agua superficial redistribuida, diferencia máxima espacial **0.0013640652482729684m** (~1.364mm); incremento de infiltración 0.02204631860229289m³, frente a 0.022046318640630225m³ del terreno original; preservación volumétrica dentro de tolerancia.
- Repetición determinista del caso activo: mismo array de profundidad superficial.
- Coste aproximado de cada escena 0.79–0.88s para 60s simulados en runner, frente a 0.02–0.03s de H11a para otro solver y parámetros. **Comparación exploratoria, no benchmark normalizado: modelos diferentes, más cálculo en H11b, y condiciones de inicialización distintas**.

## Dictamen
**H11b VALIDADO para el balance `superficie + columna infiltrada` en una cuenca cerrada y ausencia de pérdidas adicionales.** Ahora tenemos dos candidatos abiertos para hidrología: `OverlandFlow` de Almeida para agua superficial con presupuesto (H11a) y `KinwaveImplicitOverlandFlow + SoilInfiltrationGreenAmpt` para flujo e infiltración en el mismo estado (H11b). El segundo ya está documentado por el proyecto upstream como ejemplo de integración.

**No demostrado:** saturación de zona radicular, intercambio con `SoilMoisture`, crecimiento vegetal causado por esta infiltración acumulada, evaporación, aguas subterráneas, fronteras abiertas, estabilidad con pendientes extremas, coherencia entre caudal y `SpaceLargeScaleEroder`, tiempo a escala geológica ni elección de solver definitivo.

## Siguiente gate
Comparar en H11c los dos esquemas de superficie **bajo condiciones normalizadas** antes de elegir. Para extender a la ecología, buscar primero modelo existente que vincule frente de humedad Green-Ampt y saturación radicular o que comparta un presupuesto hídrico integral; no copiar `soil_water_infiltration__depth` directamente a `soil_moisture__initial_saturation_fraction` por ser magnitudes distintas. Antes de acoplar agua y sedimentos `SPACE`, confirmar unidades y flujos. No iniciar etapa 1 ni adoptar motor definitivo.
