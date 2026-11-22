# Etapa1 — H15: transformación de fracción sólido/líquido por energía interna

**Fecha:** 2026-11-22. **Dictamen:** **H15 APROBADA como transformación térmica en mezcla sólido/líquido idealizada, reversible, homogénea, 1D y de una sola clase de material.** **Etapa1 general sigue ABIERTA**: no conecta dos materiales simultáneos ni volumen/ROI H5, no integra movimiento o liquidación mecánica. [Protocolo](ETAPA_1_H15_PROTOCOLO_FASE_ENTALPIA.md), [ADR-0008](DECISIONES/ADR-0008_ENTALPIA_FASE_CAMBIO.md), [script](experiments/probe_e1_h15_phase_enthalpy.py).

**Primera CI:** https://github.com/mxlzz/Nilo_public/actions/runs/45058864901 **FAIL** antes de emitir resumen completo. `np.int32` en atributo NetCDF no serializable con `json.dumps` al crear hash; protocolo actualizado con incidente ANTES de cambio. Normalización `numpy.generic.item()` exclusivamente para hash de atributos, conservando todos los criterios físicos, commit `dd78bcb3ad5f04db5b4f0efc94f5e1afb41dec36`. **Segunda CI:** https://github.com/mxlzz/Nilo_public/actions/runs/45058971601 **SUCCESS**, todos los gates sin cambios en ecuaciones ni tolerancias.

## Modelo y observaciones

FiPy 4.0.3 (NIST) resuelve difusión térmica por volumen finito en 8 celdas 1D aisladas del exterior, durante100 pasos `dt=0.1s`. Materia A total16kg, calor específico500J/(kg·K), latente ficticio50.000J/kg, franja de transición290–310K; 4 celdas306K / 4 celdas294K; conducción1000W/(m·K). Energía interna *única* del owner `xarray` integra componente sensible y latente `E=m*(cp*T+L*f)`, fracción de fase derivada `f=(T-290)/(310-290)` dentro de banda. A lo largo de la simulación nadie cruza fuera de banda; sin física propia de FV ni nuevos modelos cinéticos.

- **Celda caliente3:** 306→**301,37944371013253K**; porción líquida **0,8→0,5689721855066268**.
- **Celda fría4:** 294→**298,6205562898666K**; porción líquida **0,2→0,43102781449333066**.
- **Materia:** exactamente16kg, nunca transferida entre celdas, partición virtual sólido+líquido equivale a toda la materia local sin stocks independientes. Suma líquida derivada inicialmente8kg y final ~7,99999999999947kg debido a simetría del caso, **no un invariante universal**.
- **Energía total:** inicial2.800.000J, final2.799.999,9999999683J, error máximo por paso **3,166496753692627e−8J**, tolerancia previa0,02J. Sin compensación de redondeo.
- **Ablaciones:** k=0 y gradiente inicial0 produjeron cambios0; al quitar calor latente, gradiente entre celdas3 y4 terminó **0,6621356K** frente a **2,7588874K** con latente, evidenciando la resistencia térmica aparente de transición con otras condiciones constantes.
- **Calidad:** reproducción bit a bit del caso A; 7 entradas corruptas rechazadas (energía creada/negativa, masa negativa, J→kJ, cambio de latente, sólido alterado, duplicar inventario de fase); NetCDF de840bytes recuperó atributos, campos e inversa térmica/partición idénticos. SHA del owner final `7e5b1f870b500eb8b8136b5e1fc0b4defcc5fe7761d454003cadaa8108c61c5b`.

## Auditoría de interpretación

**Nuevo fenómeno probado:** bajo difusión físicamente modelada, una cantidad **derivada** de masa cambia entre estado sólido y líquido al absorber/ceder energía, respetando balance total de masa y energía. No es un campo visual aleatorio.

**No demostrado:** transformación completa al atravesar solidus/liquidus, difusión no lineal, densidad/volumen de líquido distinto, mezcla de materiales, movimiento real de fase, calor producido por mecánica, cavidades, estructuras emergentes. Los parámetros son nominales **inventados como escenario abstracto, no medidos de sustancia real**. La física de fracción en equilibrio no equivale a cristalización real ni implica formación de estructuras.

## Próximo gate

Volver al requisito exacto de etapa1: **un esquema pequeño con materiales diferentes, masa, volumen y energía bajo reglas compartidas sin objetos prefabricados**. H1/H5 ya representan A/B y volumen sin energía; H15 ya integra energía y estado de fase, pero solo A en una malla 1D. Antes de dar por cerrada la etapa, comprobar en un único owner A/B, volumen y energía con una transformación/transferencia causal. Evitar añadir motor, nuevos formatos o un sistema completo de procesos. **No avanzar formalmente a etapa2 hasta auditar ese gate.**
