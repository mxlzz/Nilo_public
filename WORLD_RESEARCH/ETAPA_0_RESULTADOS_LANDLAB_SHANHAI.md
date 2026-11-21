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

**H4-H5 ejecutados con éxito** en GitHub Actions: https://github.com/mxlzz/Nilo_public/actions/runs/44948299834 (Landlab 2.11.0).

- H4 `Space`: diez pasos con erosividad activa produjeron variación de suelo/relieve y flujo sedimentario positivo; el control con erosividades nulas no cambió relieve ni generó flujo; espesores no negativos. **No se demostró aún que exista deposición positiva en alguna celda ni se cerró un balance global de masa**.
- H5 `SoilMoisture` + `Vegetation` sobre la misma malla de celdas: al ingresar lluvia hubo mayor saturación y menor estrés hídrico que sin ella. En condiciones de estación de crecimiento (PET30 = 8, por encima del umbral 6.8), hubo mayor biomasa con lluvia (~100.923 vs ~100.414 en promedios de la prueba).
- Primera corrida H5 con PET30=0.25 mostró biomasa idéntica: **no era evidencia de incapacidad**, sino que `Vegetation` estaba en modo de senescencia, rama que no depende del estrés hídrico para esa comparación. Se inspeccionó su código y se corrigió el control a estación de crecimiento; el resultado anterior queda en historial CI.
- Los componentes de humedad y vegetación comparten celdas/arrays de Landlab, demostrando acoplamiento técnico mínimo, **no el ciclo completo de realimentación con erosión ni conservación de todos los flujos**.
- Gate sigue abierto mientras falta comprobar un circuito integrado (y coste de acople nodo/celda y pasos de tiempo).


## Decisión provisional

**Preferir evaluar soluciones nativas Landlab frente a la integración heterogénea Landlab–Shanhai**. Shanhai queda como benchmark funcional y de mecanismos ecológicos; no adaptar un motor de alturas categóricas a geomorfología dinámica sin una prueba que demuestre la conveniencia. No adoptar ninguno definitivamente hasta completar H4/H5 y el análisis de condiciones iniciales.

## H6 — Estado inicial generado con WorldEngine -> evolución con Landlab

**PRUEBA EJECUTADA CON ÉXITO:** https://github.com/mxlzz/Nilo_public/actions/runs/44948883527 .

- Pipeline aislado: WorldEngine en Python 3.11 genera `NPZ`, otro job en Python 3.13 descarga el mismo archivo y ejecuta Landlab 2.11.0. No se copian/unen motores.
- WorldEngine semilla 7321 y NumPy RNG global 1234 producen la elevación 16×32 de hash SHA-256 `495e97c24477e68e0cffcab8f485481630d4425d31a01442c7ad1cbb0daa170d`, el mismo que en el ensayo previo de WorldEngine.
- Las alturas originales se normalizaron **deliberadamente** al intervalo experimental [0,50] metros sobre malla 100 m por celda/nodo. Esta elección NO calibra física real: WorldEngine no documenta estas alturas como metros; el array de elevaciones representa celdas y aquí se utilizó experimentalmente como alturas nodales de Landlab.
- Landlab produjo erosión efectiva en 406 nodos con pérdida máxima de altura de ~1.291 unidades adoptadas en el ensayo; el control sin eroder dejó elevaciones idénticas.
- **Pérdida significativa de información con Shanhai 0..4:** cuantizar a cinco categorías dio ~1.725 m de error cuadrático medio de reconstrucción bajo esta escala experimental. En ~99.5 % de los nodos erosionados, la categoría de altura no cambió aunque sí cambió la elevación continua. Por tanto **no es viable usar la representación original categórica como intercambio fiel de la evolución topográfica** sin un rediseño amplio del estado.
- **Estado válido:** factibilidad de transferencia de datos, no acoplamiento físico multiescala ni simulación ecohidrológica completa. Pendiente contratos de nodos vs celdas, resolución, fronteras, unidades, tiempo y conservación.
- Evidencia en código: `experiments/export_worldengine_height.py`, `experiments/probe_worldengine_to_landlab.py` y workflow `world-worldengine-landlab-bridge.yml`. El flujo está configurado para publicar archivos de entrada y salida como artifacts.
- Infraestructura: primera versión de workflow falló sin jobs por YAML mal formado: `run: python -m pip install --only-binary=:all: landlab numpy` contenía `: ` sin comillas en valor simple. Se corrigió convirtiendo el comando a escalar de bloque. Esta falla era **del arnés CI**, no del generador ni del modelo geológico.

## Estado de selección

1. **Confirmado mediante ejecución:** WorldEngine como fuente técnica de elevaciones iniciales; Landlab como fuente de escorrentía simplificada, erosión, transporte sedimentario y componentes de humedad/vegetación; Shanhai como baseline ecológico con terreno de cinco niveles.
2. **No demostrado:** que convenga unir Landlab y Shanhai (de hecho, hay pérdida medible de resolución), retroalimentación completa clima-vegetación-erosión, balance de sedimentos con condiciones de borde, desempeño a escala del mundo objetivo y características visuales.
3. **Recomendación condicionada:** para el siguiente experimento **priorizar Landlab en un único núcleo**, importar alturas iniciales de WorldEngine por datos, conservar Shanhai como benchmark sin copiar su formato de terreno. Abrir ADR de decisión experimental reversible. **No cerrar la etapa 0 como selección definitiva** hasta ensayos de acoplamiento interno y evaluación de costo/alternativas.
