# Etapa3 — H20A. pyDeltaRCM funcional y sensible a semilla, PERO no adoptado

**Fecha:** 2026-11-22. **Dictamen: H20A APROBADA únicamente como screening técnico/morfológico**, sin validar patrones estructurales no triviales, conservación estricta ni owner material. [Protocolo previo](ETAPA_3_H20A_PROTOCOLO_PYDELTARCM.md), [ADR-0011](DECISIONES/ADR-0011_H20_SCREENING_PYDELTARCM.md), [script aislado](experiments/probe_e3_h20a_pydeltarcm_screen.py). [CI 45060886245 SUCCESS](https://github.com/mxlzz/Nilo_public/actions/runs/45060886245), revisión `79a44bfd639f0ddd744a09f5b578a58b8716a0c6`.

## Proveedor y condiciones

`pyDeltaRCM` v2.3.0, [fuente upstream MIT pinneada](https://github.com/DeltaRCM/pyDeltaRCM/tree/a107c1d0f6b18ac19ac15ec4586179678329ae35), Python3.11.18, NumPy2.4.6, entorno Ubuntu24.04 headless. `Length1500m`, `Width2000m`, `dx50m`, malla30×40, inlet L0=150m/N0=250m, Np_water=100/Np_sed=100/itermax=1, 12 actualizaciones, tres instancias en output temporal sin archivos gráficos. No se tocaron las ecuaciones ni se copió upstream a Nilo.

- **Seed20261122:** 423 de1200 celdas cambiaron su bedrock/eta más de1e-6m; 408 celdas fuera de la franja inicial de inlet; variación espacial std0,39684m y delta de altura máxima3,01488m. Repetición con **misma semilla** produjo exactamente los mismos arrays, diagnósticos y medidas.
- **Seed20261123:** 421 celdas alteradas, 406 fuera de inlet, std0,39074m. La diferencia máxima de topografía final entre semillas fue **2,49636m** en las mismas condiciones. Esto demuestra que el proveedor puede generar morfología espacial dependiente de trayectorias estocásticas, no que esa diferencia sea emergente o tenga función.
- Primer escenario demoró ~32,54s incluyendo compilación JIT Numba; repeticiones siguientes ~0,12s en mismo proceso/CI. Son tiempos del runner para esos parámetros, no profiling robusto ni predictivo de escalas mayores.
- Se midieron tres intervalos (paso1,6,12), sin artefactos gráficos ni exportación al owner del mundo.

## Advertencia de conservación y estado material

La **documentación propia del proveedor** dice explícitamente que la formulación de DeltaRCM **no conserva estrictamente masa de agua ni de sedimentos**. Se recogieron los indicadores upstream **sin reparar ni confundir pérdidas con materia materializada**.

**Seed20261122:** volumen de sedimento nominal ingresado375.000m³, cambio de volumen de cama `sum((eta-eta_init)*dx²)`361.839,78m³, exportación declarada14.865,18m³, pérdida registrada0m³ y ajuste inlet301,35m³. El cociente aparente `(cambio cama - entrada)/entrada = −3,5094%` es **no conservativo por comparación directa porque ignora exportación, cambios de inlet y otros errores**; NO tratarlo como residuo global cerrado.

**Seed20261123:** entrada375.000m³, cama364.436,96m³, exportación12.859,84m³, pérdida0m³, inlet320,81m³; discrepancia aparente −2,8168%, también no cerrada. La salida tiene magnitudes comparables con la diferencia bruta, y la documentación del proveedor advierte errores residuales; **no se ha verificado un ledger único cuantitativamente suficiente** para aceptar integrarlo con H1/H16.

La prueba usa `eta`/agua/volúmenes como diagnósticos *temporales externos*, **no** como owner del mundo. Nadie fusionó ni escribió `Nilo_public/main` o NeuroLab.

## Decisión y siguiente gate

H20A cumple **solo viabilidad**: el motor original ejecuta, produce cambios espaciales/temporales repetibles y permite medir sus entradas/salidas documentadas. El hallazgo es valioso frente a H19 porque el proveedor se especializa en morfodinámica deltaica. **No cerrar E3**, no elevar a física conservativa, ni seleccionar como simulador ambiental sin controles.

**Siguiente gate H20B si se justifica:** un test preregistrado de conectividad/ramificación de **caudal** con nulos por fila y persistencia temporal a distintas semillas; registrar claramente el presupuesto de sedimento como limitación. Solo si el patrón excede plantilla y conserva estructura, evaluar una vía de reconciliación de masa por modelo/proveedor, sin forzar parches. El default de H20A no demuestra estas características.
