# E0.4 — Resultados de sedimentos y realimentación ambiental

**Fecha:** 2026-11-21 · **Estado:** H7/H7b verificadas; H8a en ensayo; H8b bloqueado a contrato de tiempo/unidades.

## Procedimiento y trazabilidad
- Plan **previo a ejecutar**: [ETAPA_0_4_PROTOCOLO_SEDIMENTO_FEEDBACK.md](ETAPA_0_4_PROTOCOLO_SEDIMENTO_FEEDBACK.md).
- Código experimental: `experiments/probe_landlab_sediment_budget.py`. Llama solamente APIs existentes de Landlab, `PriorityFloodFlowRouter` y `SpaceLargeScaleEroder`; no crea motor de erosión o depósito.
- Ejecución H7 original (suite completa GitHub Actions): https://github.com/mxlzz/Nilo_public/actions/runs/44951064537 .
- Ejecución H7b con receptor desnudo: https://github.com/mxlzz/Nilo_public/actions/runs/44951204189 .
- Modelo: **Landlab 2.11.0** con `SpaceLargeScaleEroder`, cuenca de 16×16 nodos y espaciado 10 m; bordes cerrados salvo salida id=0, 12 pasos con `dt=0.2` en unidades del experimento; `phi=0`, `K_br=0`, `F_f=0`, `K_sed=0.1`, `v_s=3`. No es calibración natural. Fuente del componente: https://doi.org/10.5194/gmd-10-4577-2017 .

## H7: cuenca con espesor inicial homogéneo
- Volumen sólido inicial: **11760.0 m³**.
- Volumen sólido final: **10964.26275875405 m³**.
- Exportación sedimentaria por la salida: **795.7372412459488 m³**.
- Diferencia de inventario: **-795.7372412459499 m³**.
- Residual de balance (`delta_almacenado + exportado`): **-1.14×10^-12 m³**, error relativo **1.43×10^-15**.
- Erosión y deposición de flujo verificadas en los 12 pasos; **0** nodos con aumento neto de espesor porque erosión local supera la deposición en cada nodo.
- Control con `K_sed=0`: sin erosión, sin depósito, sin salida de sólidos ni variación del espesor.
- No hubo aportes por erosión de roca ni pérdida por finos suspendidos por definición de esta prueba; el presupuesto sólido no incluye otros procesos.
- **Dictamen H7: APROBADO** para el balance y existencia de deposición como flujo, **no** para acreción neta en todos los paisajes.

## H7b: una zona receptora sin aluvión
- Mismo dominio y parámetros de solver. Espesor 0.6 m aguas arriba, 0.0 m en el tercio inferior, sin reacciones/código ad hoc de sedimentación.
- Volumen sólido inicial: **8400.0 m³**.
- Volumen sólido final: **8006.207384523336 m³**.
- Exportación: **393.79261547666385 m³**.
- Diferencia de inventario: **-393.79261547666374 m³**.
- Residual: **1.14×10^-13 m³**, relativo **2.89×10^-16**.
- **50 nodos con aumento neto de espesor de suelo**.
- Control sin erosividad mantuvo el mismo perfil y no generó transporte ni acumulación.
- Repetibilidad del ensayo homogéneo también verificada.
- **Dictamen H7b: APROBADO** para acreción neta y conservación de sólidos en las condiciones simplificadas de cuenca abierta con una salida.

## Qué NO significan estos resultados
- La precisión de balance **no acredita realismo geomorfológico** ni validez de los coeficientes numéricos para una cuenca real.
- No hay evaporación, infiltración, flujos multi-fase ni producción/desaparición de materia distintos de los descritos.
- `phi=0` elimina complejidad de porosidad y `K_br=0` elimina fuente nueva por bedrock para aislar el presupuesto; hay que reintroducir ambos con entradas/salidas en un benchmark físico ulterior.
- Deposición explícita `sediment__deposition_flux>0` no debe confundirse con aumento neto de espesor si simultáneamente existe mayor `sediment__erosion_flux`.
- La variación de altura no prueba una topografía «emergente» abierta ni evolución sin agotamiento.

## H8 — Investigación de relaciones publicadas
- Sharma y Ehlers (2023), artículo https://doi.org/10.5194/esurf-11-1161-2023 ; código y datos https://doi.org/10.5281/zenodo.8033782 . Relación publicada laderas `K_d=K_b exp(-alpha * V)`, con `alpha=0.3` y `K_b=2.5×10^-4` m²/estación (Tabla A1: https://esurf.copernicus.org/articles/11/1161/2023/esurf-11-1161-2023-t02.png).
- La erosión de cauces se modifica mediante rugosidad de Manning y partición de esfuerzo cortante. No corresponde aplicar la fórmula exponencial de laderas al `K_sed` de canales como si ambos procesos fueran idénticos.
- Landlab `LinearDiffuser` acepta difusividades espaciales en nodos o links; `SoilMoisture` y `Vegetation` comparten campos en celdas. El protocolo H8a prueba la compatibilidad básica y el control `alpha=0`; **no prueba conservación de suelo ni un ciclo bidireccional**.
- Los auxiliares que faltaban en el tutorial principal existen en https://github.com/landlab/tutorials/blob/next/ecohydrology/cellular_automaton_vegetation_DEM/Ecohyd_functions_DEM.py . La base científica para ecohidrología también está en https://github.com/landlab/pub_nudurupati_etal_wrr . Su compatibilidad con Landlab 2.11 y licencias de código auxiliares NO se evaluó todavía.

## Control de etapa
Etapa 0 **ABIERTA**. La unidad H7 está validada, H8 permanece incompleta. No se adoptó arquitectura definitiva, no se integró código ajeno ni se modificó NeuroLab. Próximo gate: resultados H8a y diseño de acoplamiento físicamente consistente antes de codificar un circuito continuo.
