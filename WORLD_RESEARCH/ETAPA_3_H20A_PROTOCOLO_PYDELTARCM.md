# Etapa3 — H20A. Prerregistro screening de pyDeltaRCM como alternativa de morfodinámica

**2026-11-22. ANTES DE CÓDIGO Y CI.** [ADR-0011](DECISIONES/ADR-0011_H20_SCREENING_PYDELTARCM.md). **No elegir un motor ni cerrar E3** por aprobar un test de viabilidad.

**Hipótesis:** el modelo reducido de delta `pyDeltaRCM.DeltaModel` (MIT, fuente exacta `a107c1d0f6b18ac19ac15ec4586179678329ae35`) ejecuta en CPU una configuración pequeña, genera modificación no uniforme de relieve bajo transporte y produce historia repetible con semilla; semillas distintas producen al menos una diferencia en relieve final. **Alternativa:** no ejecuta con recursos de CI, los cambios no aparecen tras tiempo acotado o no son reproducibles; en ese caso no justificar integración.

## Condiciones y controles previos

- Ejecutar proveedor upstream intacto, Python3.11 y dependencias de su `pyproject.toml`; `Length=1500m`, `Width=2000m`, `dx=50m`, `L0_meters=150m`, `N0_meters=250m`, `Np_water=100`, `Np_sed=100`, `itermax=1`, `verbose=0`, sin salida de figuras/NetCDF salvo infraestructura interna esencial; `out_dir` temporal distinto en cada réplica; **12 iteraciones `update()`** por escenario, `finalize()` al terminar.
- **Escenarios:** seed20261122 (A); seed20261122 (replay); seed20261123 (B), todos los demás parámetros idénticos.
- Registrar `eta_init`/eta final, cambio `eta-eta_init` global y fuera de franjas de entrada. Medir celdas cambiadas (`abs(delta_eta)>1e-6m`), magnitud máxima y no uniformidad (`std(delta_eta)>1e-7m`), dimensión del dominio, tiempo de ejecución.
- El relevo debe **pasar**: tres escenas completadas con `eta` finita, forma final idéntica y replay bit a bit de A, semilla B distinta en algún valor de eta final (máximo de diferencia >1e-9m), al menos5 celdas de relieve modificado y desviación estándar >1e-7m. Si el tiempo acotado no produce morfología, **no ajustar a posteriori el número de pasos** para aprobar.
- **Diagnóstico obligatorio de masa:** no confundir este solver con H9 material: volumen depositado geométrico `sum((eta-eta_init)*dx²)`, entrada nominal `sum(Qs0*dt)` por iteración, y pérdidas/exportación/frontera según `_sr.Vp_lost/_mr.Vp_lost`, `_sr.Vp_exported/_mr.Vp_exported`, `_Vp_inletbc`, si esos atributos existen. Reportar por separado entradas, depósitos, pérdidas, exportación y corrección inlet; calcular `(depósito-entrada)/entrada` **solo como desviación aparente**, no como residuo cerrado porque las fuentes y salidas no están reconciliadas. Si falta algún campo obligatorio, **fallar screening** en vez de fingir balance.
- **No existe gate de conservación física cerrado en H20A**: el upstream documenta que su formulación no conserva exactamente masa de agua ni sedimentos. Esta prueba no publica xarray ni autoriza adoptar modelo para el motor del mundo.
- Ejecutar con timeout CI máximo16min, sin gráficos, GPU ni módulos ajenos. Registrar `WORLD_EVAL_JSON` con versiones, seeds, métricas y lista de fallos **antes** de salida no-cero.

## Dictamen posterior

- **H20A aprobada** solo como viabilidad/relieve diferencial de proveedor exterior si se cumplen controles de ejecución, variación, replay y métricas completas. Nunca equivale a patrones estructurales no triviales, estabilidad, masa conservada o estado común.
- **H20A rechazada** si no se cumplen; documentar antes de cambiar condiciones. Incluso con éxito, pasar a H20B exige analizar explícitamente la contabilidad de fuentes/salidas y un nulo geomorfológico que preserve restricciones del delta; no repetir error H19 de aceptar un nulo global débil. Mantener E3 abierta.
