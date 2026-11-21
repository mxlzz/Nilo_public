# E0.4 — Resultados de sedimentos y realimentación ambiental

**Fecha:** 2026-11-21 · **Estado:** H7/H7b, H8a y H8b verificadas; **ciclo dinámico multi-etapa todavía NO validado**.

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


## H8a: lluvia y vegetación afectan difusividad de ladera

Primera ejecución https://github.com/mxlzz/Nilo_public/actions/runs/44951386764 : falló correctamente el control de cobertura. `Vegetation` con `Bdead_init=450` (valor por defecto) llenaba el índice foliar máximo en ambos ensayos; la biomasa crecía con lluvia, pero la cobertura estaba saturada a 0.7768698, anulando diferencia en Kd. No era fallo de `LinearDiffuser` ni razón para quitar la aserción.

Segunda ejecución https://github.com/mxlzz/Nilo_public/actions/runs/44951510991 : se dejó sin biomasa muerta inicial `Bdead_init=0` (condición de prueba explícita), manteniendo ecuaciones intactas. **PASS**.
- Escenario sin lluvia: saturación media 0.23434, biomasa media 108.61757 y fracción de cobertura 0.3130824.
- Escenario con lluvia: saturación 0.40359, biomasa 119.91507, cobertura 0.32692795.
- Kd sobre nodos interiores: 0.0002275878 seco frente a 0.0002266445 húmedo, siguiendo `K_d=K_b exp(-0.3 V)`; `K_b=2.5e-4 m²/estación`, ambos de Tabla A1 publicada por Sharma y Ehlers (2023).
- Diferencia máxima de relieve por el efecto de la vegetación: **1.5542e-6 m** en la prueba; con alfa=0, **0.0 m**.
- **Interpretación:** conexión matemática causal entre cobertura y difusión de relieve en un paso. `LinearDiffuser` no distingue ni conserva una capa móvil, por lo que NO se usa H8a para demostrar conservación sedimentaria.

## H8b: conexión sobre material móvil de suelo en terreno cerrado

Código: `experiments/probe_landlab_mobile_soil_feedback.py` y workflow independiente `.github/workflows/world-landlab-mobile-soil.yml`.

Ejecución GitHub Actions **PASS**: https://github.com/mxlzz/Nilo_public/actions/runs/44951675896 .
- `SoilMoisture` + `Vegetation` en celdas → cobertura interpolada de nodos a links → `DepthDependentDiffuser` (flujo de ladera limitado por capa disponible), **sin crear un solver nuevo**.
- Parámetros: Kb=0.00025 m²/estación y alfa=0.3 de Sharma y Ehlers 2023. Espesor de decaimiento de transporte `d*=1 m`, igual al predeterminado del componente y declarado como supuesto experimental; capa inicial 0.6 m; producción de suelo 0, fronteras cerradas.
- Una intervención lluvia 25 mm produce mayor saturación (0.40359 vs 0.23434), biomasa (119.915 vs 108.618) y cobertura (0.32693 vs 0.31308) que 0 mm.
- Diferencia máxima del relieve entre escenas **7.01247e-7 m**. Con `alpha=0`, **0 m**.
- Volumen inicial de suelo = **21.600000000000005 m³**, final = **21.599999999999998 m³**; residual **-7.1054e-15 m³**. Roca madre sin cambios y capa móvil no negativa; resultado reproducible.
- **Interpretación:** suelo redistribuido conservativamente dentro del dominio cerrado según el ensayo, con sensibilidad causal a vegetación. NO verifica ciclo estacional prolongado, routing hídrico condicionado por nuevo relieve ni acoplamiento fluvial a `SPACE`.
- Se aisló la prueba en un workflow solo Landlab para evitar repetir costos de `npm ci` y la suite completa Shanhai en cada cambio.

## Auditoría del alcance de H8

**Aceptado:**
1. Hidrología de evento → biomasa/cobertura; comprobado con intervención y ablación.
2. Cobertura → difusividad de ladera, ecuación y parámetros de fuente académica; comprobado.
3. Difusión → redistribución de capa móvil sin fuente ni pérdida en cuenca cerrada; verificado balance y control.

**No demostrado:**
1. Retroalimentación completa relieve→escorrentía→vegetación a través del tiempo.
2. Conservación simultánea cuando `DepthDependentDiffuser` y `SpaceLargeScaleEroder` alteran el mismo suelo.
3. Compatibilidad de pasos: `SoilMoisture` recibe un evento meteorológico, mientras que Kb del artículo se expresa por estación (3 meses). Un solo paso de cada uno **no constituye un paso físico conjunto coherente**.
4. Respuesta ecológica sostenida ni formación de estructuras biológicas nuevas.
5. Calibración de los parámetros contra un clima/territorio objetivo.

**Gate siguiente:** antes de implementar un bucle autónomo, definir cronograma de subpasos con unidades, propietario único para masa/agua/sedimentos, intercambios entre procesos y escenarios de ablación; buscar un esquema de referencia ya publicado. Mantener la etapa 0 **ABIERTA**.
