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

## H10b — Retorno topografía→radiación→demanda hídrica→vegetación (protocolo anterior a código)

**Justificación:** H10a verificó que `Radiation` solo reconoce geometría actualizada si se reconstruye su instancia; H9 ya mantiene 90 días lluvia→plantas→suelo de forma conservativa. H10b prueba un lazo con retorno real a la entrada ambiental, manteniendo todo dentro de Landlab.

**Modelo existente y contrato:** `Radiation` y `PotentialEvapotranspiration` sobre RasterModelGrid compartido con `SoilMoisture` y `Vegetation`, más `DepthDependentDiffuser`; las celdas físicas y nodos se relacionan mediante `node_at_cell` y proyección a links. `Radiation` se reinstancia con la topografía actual **antes de cada paso diario**; PET temporal por día es `Cosine` con base instrumental de 10 mm/día y factor de radiación por celda. El campo de PET de 30 días para Vegetation se deriva mediante **promedio temporal de los últimos 30 días**, no una nueva ley física. Se usan 1h de evento y 23h de interevento por día; lluvia 12 mm cada 5 días, todos los escenarios. `DepthDependentDiffuser` cada 30 días `dt=30/90` de estación, `Kd=2.5×10^-4 exp(-0.3V)` m²/estación, d*=1m y sin producción de suelo. Todos los parámetros declarados como forzantes de prueba, no calibrados.

**Factor experimental 1:** en el día 45 imponer una *intervención geológica externa* +12 m sobre la cota de un nodo interior; elevar a la vez su roca madre y mantener su espesor de suelo para no crear material móvil. Esta perturbación **no emerge** del modelo y sirve solo para comprobar que el retorno responde a nueva geometría.

**Factor experimental 2:** habilitar o ablar únicamente la influencia de la geometría actual sobre radiación/PET:
- `topographic_link=true`: reconstruir Radiation a diario sobre la topografía real del escenario, para que el suelo modificado en pasos anteriores sí altere la incidencia.
- `topographic_link=false`: calcular radiación de referencia sobre **una copia de la topografía inicial, sin modificar**, para la misma fecha; PET consume ese campo fijo espacialmente. Se conservan lluvia, vegetación y geomorfología activas. Este es un control negativo del retorno geométrico, no del resto del sistema.

**Cuatro escenarios:** sin intervención/activo; intervención/activo; sin intervención/ablación; intervención/ablación. Todos comparten mismo forzante, hora, parámetros, malla y semilla (sin aleatoriedad).

**Métricas/criterios de aceptación:** (a) antes del día 45 los escenarios activos tienen PET idéntica; (b) después de la intervención, los escenarios activos presentan diferente PET y al menos una variable ecohidrológica (humedad o biomasa/cobertura) cuando se compara mismo instante; (c) bajo la ablación, perturbación geológica no cambia PET ni estado ecológico (aunque las cotas/flujo de suelo pueden cambiar porque la pendiente sí lo hace); (d) confirmar que la topografía erosionada entre ventanas participa en `Radiation` (reinstanciación y medición del efecto endógeno, aunque sea diminuto); (e) guardar volumen de suelo móvil de la malla y verificar residuo <0.01%, suelo no negativo, roca madre sin cambios salvo perturbación externa explícita; (f) repetir escenario activo con perturbación y comparar finitud/estados a tolerancia exacta si es determinista; (g) registrar costo computacional aproximado y el efecto máximo PET, saturación y vegetación en el horizonte.

**Resultado si pasa:** hay un lazo informático/físico-modelado explícito y verificable **terreno→radiación/PET→suelo/vegetación→transporte de suelo→terreno**, sometido a ablación. **NO demuestra** un mundo calibrado, que erosión micrométrica endógena genere efecto observable, ni conservación de agua ni erosión fluvial; la perturbación externa se declara inequívocamente como control de sensibilidad.

**Gate:** no integrar `SpaceLargeScaleEroder` con `DepthDependentDiffuser` hasta demostrar compatibilidad de inventarios. Si los controles fallan, preservar evidencia y diagnosticar API/condiciones; no declarar cierre de etapa 0.

## Control de errores H10b (primer ensayo, registrado antes de reparar)
La primera corrida de H10b https://github.com/mxlzz/Nilo_public/actions/runs/44952595861 **falló en el arnés antes de ejecutar el bucle**. `PotentialEvapotranspiration` fue inicializado a `current_time=0.5` y, en el día cero, el script volvió a asignar el mismo valor `pet.current_time=0.5`. La propiedad Landlab exige que `new_time > _current_time`; resultó en AssertionError de control de tiempo (no en un resultado del modelo ecohidrológico). **Corrección acotada:** en d=0 reutilizar el tiempo ya inicializado; solo avanzar explícitamente la fecha en d>0. Sin modificación de hipótesis ni umbrales ni parámetros ambientales. Conservar este fallo en el historial de CI y registrar los resultados de la segunda prueba, sean positivos o negativos.
