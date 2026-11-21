# Etapa 0 — Informe experimental de elección de bases ambientales

**Fecha:** 2026-11-21. **Estado:** gate de selección ABIERTO, no hay motor adoptado ni código de motor propio nuevo.
**Separación:** mundo/ambiente exclusivamente. NeuroLab y cerebro fuera de alcance. Rama provisional `research/world-foundations-2026-11`, sin cambios a `main`.

## Alineación con el plan

La intervención fue la **etapa 0** del documento `BASES_Y_HOJA_DE_RUTA.md`: comprobar alternativas antes de implementar leyes propias, con controles negativos, reproducibilidad, mediciones y código replicable. Protocolo previo al ensayo: `ETAPA_0_PROTOCOLO_LANDLAB_SHANHAI.md`. No se usaron plantillas de mundos ni se escribió código motor.

## Pruebas ejecutadas, verificadas

**Evidencia inicial positiva CI:** https://github.com/mxlzz/Nilo_public/actions/runs/44947975784

### H1 — Landlab

- Instalación desde PyPI: **Landlab 2.11.0**, Python 3.13, NumPy 2.5.5. Antes falló importación en Python 3.11: una dependencia `requireit` usa sintaxis de parámetros genéricos PEP 695; al actualizar el entorno a 3.13, ejecutó correctamente. El primer error era de compatibilidad del entorno, no prueba de inviabilidad del modelo.
- Usados exclusivamente `RasterModelGrid`, `FlowAccumulator`, `StreamPowerEroder` documentados.
- En malla 18×18 y 12 pasos, descarga máxima con escorrentía de entrada = 16; sin aportes = 0.
- 256 nodos interiores mostraron descenso de cota; descenso máximo aproximado 0.0342 unidades del modelo.
- Control negativo: sin `StreamPowerEroder`, relieve inalterado.
- Reejecución determinista y reanudación desde el campo de elevación serializado produjeron mismo estado final con tolerancia 1e-12.
- Tiempo del cálculo del benchmark (sin instalación) ~0.08 s en runner CI; no extrapolar a mallas grandes o terreno multiescala.

**Lo NO demostrado:** almacenamiento/volumen hidrológico real, conservación de sedimento, deposición, ecología, evolución geológica prolongada, tasas físicas calibradas, reanudación de TODOS los módulos de Landlab y renderizado. `FlowAccumulator` calcula transporte de aporte/descarga; `StreamPowerEroder` excava sin contabilizar sedimento en esta prueba. Guardar solo topografía basta para **este ensayo**, no para simulaciones acopladas futuras.

### H2 — Shanhai

- Se clonó repositorio original; `npm ci`, suite de tests propia y compilación pasaron antes del ensayo independiente. Se copiaron las pruebas a checkout temporal.
- Escenario `riverValleyGrassland`, 64×64, 120 ticks, con fuentes vs mismo estado sin fuentes:
  - agua superficial acumulada 319.626 con fuentes vs 0 sin ellas;
  - suma de humedad 267.467 con fuentes vs 256 sin fuentes;
  - suma de biomasa vegetal 24.322 con fuentes vs 21.367 sin fuentes.
- **Ablación bien definida:** se quitó la lista `state.springs` manteniendo el resto del estado inicial igual. La primera prueba falló por alterar solo `params.springOutput`; las fuentes del escenario tienen propiedad individual `spring.output`, que prevalece. El error pertenecía al arnés de control, no al modelo. Se corrigió y quedó conservado en el historial.
- Dos instancias `basinSpill` con 100 pasos reprodujeron arrays de agua, humedad, plantas y terreno.
- Altura `heightMap` no cambia durante evolución; codifica 5 clases `Uint8` de altura (`0..4`), limitación geológica documentada por su propio diseño.
- `getSnapshot()` **devuelve referencias compartidas** con arrays de estado como agua y relieve, no instantánea independiente: no asumir que su retorno basta para persistencia/replay.

**Lo NO demostrado:** acoplamiento físico real con erosión de Landlab, equivalencia de unidades/geomorfología, evolución indefinida, persistencia inmutable, estabilidad frente a mutaciones de terreno en caliente. No es un motor geológico por producir ríos superficiales.

## Hallazgo arquitectónico

Ya conocemos dos componentes parcialmente válidos con **representaciones geométricas diferentes**:
- Landlab: topografía continua `float` en nodos, con entidades de procesos de superficie, malla y fronteras.
- Shanhai: `heightMap` categórico `Uint8` (0..4) en celdas, junto a `base`, `surface`, humedad y vegetación.

Copiar el array de un sistema al otro sin contrato de unidades y mapeo **sería científicamente incorrecto** y perdería variaciones pequeñas. El hecho de que dos simuladores ejecuten tests no significa que deban conectarse. Antes evaluar Landlab `Space` (transporte de sedimentos) y `SoilMoisture` + `Vegetation` como **alternativas dentro de un solo motor**, con menor esfuerzo de integración.

## Próximas pruebas (H4/H5)

Protocolo extendido antes de implementar: `ETAPA_0_PROTOCOLO_LANDLAB_SHANHAI.md`.

- H4: `Space` vs control de erosividad cero, inspección de `soil__depth`, `bedrock__elevation`, `sediment__outflux`, sin afirmar balance completo.
- H5: `SoilMoisture` + `Vegetation` en una sola malla Landlab, lluvia vs ausencia de lluvia, métricas de saturación y vegetación.
- CI para pruebas H4/H5: https://github.com/mxlzz/Nilo_public/actions/runs/44948182511
- Gate: no cerrar hasta resultados/errores y análisis de costo/compatibilidad.

## Decisión provisional

**Preferir evaluar soluciones nativas Landlab frente a la integración heterogénea Landlab–Shanhai**. Shanhai queda como benchmark funcional y de mecanismos ecológicos; no adaptar un motor de alturas categóricas a geomorfología dinámica sin una prueba que demuestre la conveniencia. No adoptar ninguno definitivamente hasta completar H4/H5 y el análisis de condiciones iniciales.
