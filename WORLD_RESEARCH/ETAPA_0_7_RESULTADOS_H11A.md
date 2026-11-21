# E0.7 — H11a: conservación de agua superficial y cambio de distribución por relieve

**Fecha:** 2026-11-21 · **Estado:** H11a VALIDADA en sus supuestos. Etapa 0 general ABIERTA.
**Plan previo:** `ETAPA_0_7_PROTOCOLO_H11_AGUA.md`
**Arnés:** `experiments/probe_landlab_overland_water.py`
**Workflow:** `.github/workflows/world-landlab-water-budget.yml`
**Ejecución GitHub Actions:** https://github.com/mxlzz/Nilo_public/actions/runs/44953015600 (**SUCCESS**).

## Función estudiada
Landlab 2.11.0 `OverlandFlow` (modelo de flujo superficial de de Almeida et al. 2012/Bates et al. 2010), con agua almacenada como `surface_water__depth` (m, nodos), movimiento en links `surface_water__discharge` (m²/s), aporte de lluvia en m/s y paso temporal en segundos. Se eligió porque `FlowAccumulator` rutea caudales sin mantener el mismo inventario dinámico de profundidad. No se desarrolló física de fluidos propia.

## Configuración
- Cuadrícula 12×12 nodos, espaciado 1m, con 100 nodos interiores que poseen área de celda 1m².
- Bordes cerrados, pendiente suave y una ondulación determinista.
- Película inicial `h_init=1e-5 m`, total inicial en nodos interiores **0.001m³**; el modelo necesita esta película para estabilidad. Se incluye explícitamente en el balance.
- Lluvia de ensayo `2e-5m/s` (72mm/h) durante **60s** con `dt=0.5s`, 120 pasos. No hay infiltración, evapotranspiración ni salida externa.
- Control de lluvia nula con mismo estado inicial; intervención topográfica fija +0.2m en un nodo interior antes de iniciar el flujo; repetición exacta del primer escenario.
- `steep_slopes=False`, Manning n=.03, sin parámetros hidrológicos calibrados.

## Resultados medidos
- Aporte de lluvia esperado: **0.12000000000000001m³**.
- Volumen inicial: **0.001m³**; volumen final sin relieve perturbado **0.12100000000000001m³**. Residual registrado: **0m³** dentro del redondeo.
- Escenario de topografía perturbada: volumen final **0.12100000000000002m³**, residual **1.3877787807814457e-17m³**, relativo **1.1565e-16**. Diferencia espacial máxima de profundidad entre terrenos: **0.0018068937230360173m** (~1.807mm).
- Control sin precipitación: volumen inicial=final=**0.001m³**, residual 0; la película se redistribuyó internamente.
- Las profundidades se mantuvieron finitas y no negativas, con descarga dinámica en links. Ejecución repetida del mismo escenario produjo exactamente el mismo array de profundidades.
- Tiempo interno del ensayo ~0.03–0.04s por escenario en el runner (excluye instalación y overhead de CI). No permite extrapolar a cuenca grande ni malla multiescala.

## Dictamen y límites
**H11a APROBADO:** `OverlandFlow` es candidato preexistente para evolución de almacenamiento/distribución de agua en terreno mutable, con conservación de volumen en cuenca cerrada bajo ausencia de pérdidas y aportes explícitos. El cambio de relieve alteró rutas/estado espacial sin variar inventario.

**No demostrado:**
- salida por fronteras abiertas, evaporación o infiltración;
- balance del agua junto con `SoilMoisture` (que trabaja en mm/evento sobre celdas, no m/s sobre nodos);
- adecuación de `OverlandFlow` a pendientes fuertes, terreno 3D realista o lluvia prolongada y desbordes;
- acoplamiento de profundidad/descarga con `SpaceLargeScaleEroder` y el balance sólido compartido;
- calibración, turbulencia, dinámica meteorológica, tiempo acelerado geológico o persistencia de todos los campos.

## Gate para H11b
Antes de integrar `OverlandFlow` y `SoilMoisture` se requiere un contrato detallado y auditado:
1. dueño de **precipitación**: lluvia debe entrar una sola vez, no mediante dos campos simultáneos independientes;
2. conversión m↔mm y s↔evento/hora;
3. transferencia entre nodo hidráulico y celda de humedad, tratamiento de borde;
4. conservación integral de agua superficial + incremento de humedad + fuga de raíz + evapotranspiración + caudales de salida;
5. control negativo sin lluvia, intervención con infiltración y recuperación de estado;
6. comparación de costo con un modelo ecohidrológico acoplado ya existente antes de crear adaptador.

No se autoriza todavía un acoplamiento que pueda contar dos veces la lluvia o los sumideros. Continuar dentro de etapa 0, sin cambiar arquitectura ni NeuroLab.
