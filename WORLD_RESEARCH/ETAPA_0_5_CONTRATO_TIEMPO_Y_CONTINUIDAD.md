# E0.5 — Contrato experimental de tiempo y continuidad eco-geomorfológica

**Estado:** PLAN PREVIO A CODIFICAR · 2026-11-21. Hereda ADR-0002, H7, H8a/H8b y la auditoría de etapa 0.

## Razón de la etapa
H8b demostró causalidad con conservación de suelo, pero solo para **una** entrada hidrológica y **un** paso geomorfológico. No permite concluir continuidad. Antes de añadir procesos o introducir motores propios, comprobar que los componentes Landlab existentes aceptan subpasos con unidades y estados compartidos.

## Evidencia primaria sobre escalas
- `SoilMoisture.update()` lee `Tr` (duración de tormenta, horas), `Tb` (intertormenta, horas) y actualiza internamente `current_time += (Tb+Tr)/(24×365.25)` años. El campo `soil_moisture__initial_saturation_fraction` se actualiza con la saturación al cerrar cada evento.
- `Vegetation.update()` usa `Tr`, `Tb`, humedad y evapotranspiración para actualizar biomasa, área foliar y cobertura. Los parámetros `Tb` y `Tr` tienen setters documentados.
- Un antecedente funcional del equipo Landlab usa *storm/interstorm loop* (eventos), actualiza SoilMoisture y Vegetation en cada evento y VegCA a cadencia anual: https://github.com/landlab/pub_nudurupati_etal_wrr/blob/master/DEM_model_driver/CA_flat.py . **El código histórico invoca `update(current_time, Tr=..., Tb=...)` y NO funciona sin adaptación con la firma actual `update(self)` de Landlab 2.11**; no copiar el script obsoleto literalmente.
- Sharma y Ehlers 2023 publican `K_d=K_b exp(-alpha V)`, `alpha=0.3`, `K_b=2.5e-4 m² por estación`, `dt=1 estación=3 meses`, ref. https://doi.org/10.5194/esurf-11-1161-2023 y tabla oficial https://esurf.copernicus.org/articles/11/1161/2023/esurf-11-1161-2023-t02.png .

## H9 — Mini experimento multi-evento, unidireccional pero conservativo
**Hipótesis:** usando únicamente `SoilMoisture`, `Vegetation` y `DepthDependentDiffuser`, pueden ejecutarse 90 días (3 ventanas de 30 días) con un único estado de suelo y una cadencia geomorfológica explícita de 1/3 de estación por ventana, preservando suelo en una malla de bordes cerrados.

1. Identidad de malla: 8×8 RasterModelGrid, celdas ecohidrológicas vinculadas a nodos centrales, cobertura convertida explícitamente a links mediante promedio de extremos; altura, capa móvil y roca en nodos; propiedad del estado a cargo de Landlab.
2. Cada día: `Tr=1 hora`, `Tb=23 horas`, tiempo hidrológico 1 día/evento. Escena húmeda: 12 mm cada 5 días (forzante sintético declarado). Escena seca: 0 mm/día. PET constante 8 mm/día como condición instrumental de estación de crecimiento, **no calibración climática**.
3. Cada 30 días: actualizar velocidad de transporte de suelo a partir de cobertura del momento y la ecuación publicada `K_b exp(-alpha V)/d_*`, con `d_*=1m` por defecto del componente. Ejecutar una vez `DepthDependentDiffuser(dt=30/90)`, unidades de temporadas según `K_b`.
4. Controles: misma secuencia húmedo/seco con `alpha=0` para anular el vínculo vegetación→terreno, sin anular diferencias de agua; doble ejecución de escenario húmedo para reproducibilidad. No aparecen nuevas fuentes o sumideros de sedimentos.
5. Medir por ventana: `current_time` hidrológico, biomasa/cobertura, difusividad, espesor suelo, cambio del relieve, masa almacenada y diferencias húmedo-seco. Comprobar que el paso total es 90 días y el presupuesto de suelo se conserva dentro de 0.01%.

**Resultado exitoso demostraría:** actualizaciones temporales coherentes de las APIs con intercambio causal y balance de capa móvil en un horizonte de 90 días sintéticos. **NO demostraría:** topografía afectando de vuelta hidrología (está ausente), clima realista, erosión fluvial, difusión+SPACE sobre el mismo inventario, ni que las plantas evolucionen novedosamente. Se deberá entonces formular un experimento específico de feedback inverso relieve→hidrología, sobre una fuente existente (p.ej. Radiación, OverlandFlow o FlowAccumulator) y presupuesto de agua.

## Bloqueo posterior
No unir todavía `SpaceLargeScaleEroder` al mismo suelo del H9 ni llamar al modelo «mundo completo» hasta establecer separación de subprocesos, balance de entradas/salidas y validación de orden de operadores. Este experimento debe ejecutarse en job CI independiente para evitar repetir tests no afectados.
