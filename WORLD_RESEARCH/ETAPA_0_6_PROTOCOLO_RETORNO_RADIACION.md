# E0.6 — H10: retorno del relieve hacia radiación y demanda hídrica

**Estado:** protocolo previo a ensayos, 21-11-2026. **Etapa 0 ABIERTA**, solo reutilización de modelos publicados, sin motor propio.

## Alineación
La H9 demostró *lluvia→saturación→vegetación→transporte de suelo* durante 90 días, pero no *relieve→ambiente*. El objetivo acordado requiere condiciones físicas que interactúen de vuelta; antes de unirlo se debe comprobar una ruta de Landlab que ya existe. Escoger una prueba con un modelo nativo y un control negativo evita inventar fórmulas de incidencia energética o evapotranspiración.

## Candidatos preexistentes y fuente
- Landlab `Radiation`: `src/landlab/components/radiation/radiation.py`, inspirado en Bras (1990), ASCE-EWRI (2005) y Flores-Cervantes et al. (2014). Lee `topographic__elevation` (m, nodos) y produce `radiation__ratio_to_flat_surface` (adimensional, celdas), además de radiación incidente W/m².
- Landlab `PotentialEvapotranspiration`: `src/landlab/components/pet/potential_evapotranspiration_field.py`. Lee proporción de radiación por celda y calcula `surface__potential_evapotranspiration_rate`. Método `Cosine` con forzante base (unidades indicadas en documentación del componente), usado únicamente para inspeccionar respuesta causal de pendientes.
- **Riesgo encontrado ANTES del ensayo:** `Radiation.__init__` ejecuta `grid.calculate_slope_aspect_at_nodes_burrough()` y guarda pendientes y orientaciones internas `self._slope, self._aspect`. `Radiation.update()` recalcula incidencia usando estos arreglos pero no ejecuta de nuevo el cálculo de pendientes. Por tanto un relieve modificado puede cambiar su altura efectiva pero dejar el ángulo de incidencia obsoleto. Se prueba antes de integrarlo.

## H10a — dependencia geométrica y caché
Objetivo: comprobar con el mismo terreno, fecha y parámetros si cambiar una topografía actualiza realmente el campo de radiación.

- Escenario A: malla 8×8, separación 10 m, altura base ≥100 m, paisaje inclinado suavemente. Crear `Radiation` y PET, evaluar ratio y PET para día fijo (por ejemplo mitad de año).
- Escenario B: modificar 1 nodo central con perturbación topográfica explícita +12 m, sin cambiar fecha, humedad o parámetros. Reusar la MISMA instancia `Radiation` y ejecutar `update()`; registrar incidencia, PET y campo de pendientes.
- Escenario C: con exactamente la topografía perturbada del B, **crear nueva instancia** de `Radiation` en la misma malla y fecha, y volver a calcular ratio y PET. Esta instancia actualiza las pendientes originales, a diferencia de la que se conserva.
- Controles: mismo estado A repetido debe dar salida idéntica. Escenario B debe producir igual incidencia geométrica que A si `_slope` y `_aspect` quedaron congelados; si varía la radiación por corrección de altura atmosférica, distinguirlo del ratio geométrico. C debe producir cambios mensurables en `radiation__ratio_to_flat_surface` y PET; si no los produce, no declarar aptitud como retorno ambiental.
- Reproducibilidad, finitud y sin clip excesivo; registrar rango y magnitudes de variación.

**Criterio H10a:** demostrar (o refutar) sensibilidad geométrica con un terreno variable y confirmar si se requiere reconstrucción/reinicialización. Esto autoriza diseñar un adaptador de re-inicialización o buscar alternativa, **NO aún acoplamiento temporal completo**. Si el efecto es demasiado pequeño o el modelo es incapaz de actualizar topografía mutable, registrar incompatibilidad.

## H10b — posible circuito de varios períodos
Tras aprobar H10a y documentar procedimiento seguro de actualización, se permitiría un ensayo experimental `relieve→Radiation→PET→SoilMoisture→Vegetation→DepthDependentDiffuser→relieve`. Asegurar que se **recalculan pendientes** tras cambio del relieve, que las horas/días/estaciones no se confunden y que no hay segunda implementación de radiación propia. Pruebas futuras: dos topografías iniciales distintas con forzantes iguales y ablación del vínculo topográfico a radiación, conservación de sólidos, replay y magnitudes temporales. En particular, la alteración de milímetros o micrómetros de H9 puede ser físicamente imperceptible para radiación: un resultado nulo no debe maquillarse.

## Gate
No construir H10b antes de comprobar H10a en CI y evaluar si reconstruir `Radiation` requiere un coste por período razonable. Continúa pendiente el modelo hidrológico con balance, deposición fluvial y unificación de inventarios; un retorno mediante PET no equivale al ciclo de ríos.
