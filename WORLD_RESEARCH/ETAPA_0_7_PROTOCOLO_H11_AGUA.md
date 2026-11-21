# E0.7 — H11: modelo de agua superficial dinámico y presupuesto hídrico

**Estado:** protocolo previo a implementar, 21-11-2026. **Etapa 0 ABIERTA.**
**Base:** H10b demuestra retorno de topografía a energía/PET, no a escorrentía real. ADR-0002 prioriza bibliotecas preexistentes; ninguna ley hidrológica nueva está autorizada.

## Dos alternativas de Landlab y distinción de capacidades
- `FlowAccumulator`: lee `topographic__elevation` en nodos y el aporte de caudal/equivalente (campo `water__unit_flux_in`); calcula rutas, cuenca de aporte y `surface_water__discharge` sobre nodos. **No acumula por sí mismo una profundidad de agua dinámica en el tiempo**.
- `OverlandFlow` (de Almeida et al., 2012 y Bates et al., 2010): modelo 2D de flujo superficial con `surface_water__depth` en nodos (m), `surface_water__discharge` por links (m²/s), `rainfall_intensity` (m/s), y `dt` (s), con flujo por gradientes de superficie libre y Manning. Documentación/código oficial: https://github.com/landlab/landlab/blob/master/src/landlab/components/overland_flow/generate_overland_flow_deAlmeida.py.
- `OverlandFlow` añade por defecto una película inicial `h_init` de 1e-5m para estabilidad; `steep_slopes=True` puede aplicar un suelo de profundidad mínimo que cambia ligeramente el balance. **H11a usa `steep_slopes=False` y pendiente moderada**, contabiliza siempre película inicial como masa y guarda ese límite. No extrapolar a relieve montañoso.

## H11a — Ensayo del balance de agua sobre terreno mutable

**Hipótesis:** OverlandFlow puede evolucionar la profundidad superficial, conservar el inventario acuoso en una cuenca con todos los bordes cerrados y modificar la distribución del agua ante un relieve diferente, sin alterar el aporte total.

**Escenario A:** 12×12 nodos, malla 1m, relieve inclinado ligeramente con depresión/ondulación reproducible, fronteras cerradas, sin infiltración ni evaporación, lluvia `2e-5 m/s` durante 60 s, `dt=0.5s` por paso exterior. `h_init=1e-5 m`; calcular volumen de agua en nodos interiores (`surface_water__depth×area`) después de instanciar solver y después de 60 s.

**Escenario B (control de fuente):** mismo relieve, misma película inicial, lluvia=0, mismo tiempo. Volumen sin incremento neto fuera de tolerancia.

**Escenario C (intervención de relieve):** idénticas condiciones que A, pero se eleva un nodo interior +0.2m ANTES de empezar la lluvia, para observar cambio de distribución del agua. Registrar campo de profundidad final, balance y diferencia espacial.

**Pruebas:** confirmar tiempo simulado ≈60s, profundidad finita y no negativa (o registrar fallo de estabilidad), volumen final - inicial = `rainfall_intensity×60s×área activa` dentro de 0.1% (o tolerancia equivalente explicitada); escenario B ≈0; escenarios A y C difieren espacialmente, pero no en volumen. Repetibilidad determinista. Medir duración CPU y documentar los enlaces perimetrales; no permitir pérdidas ocultas a través de bordes cerrados.

**Condición de cierre H11a:** suficiente para sostener que puede ser un solver de almacenamiento/flujo hídrico en un mundo dinámico, **pero no** para aprobar acople con `SoilMoisture`: las salidas de éste son mm por evento y sus resultados de infiltración/ET/leakage deben transformarse y descontarse del balance del agua, sin contar lluvia dos veces.

## H11b (gate condicionado)
Si H11a pasa, buscar antes de desarrollar un adaptador existente para combinar `OverlandFlow` y `SoilMoisture` mediante unidades m↔mm, t(s)↔eventos(h), ubicación nodo↔celda, y propietario único del agua. Definir si fuente atmosférica entra al agua superficial directamente o si primero se reparte por `SoilMoisture`; no sumar los dos mecanismos de lluvia. Diseñar pruebas del presupuesto conjunto agua superficial + humedad + evaporación + fuga + salidas.
No conectar `SpaceLargeScaleEroder` a estos solvers hasta que el caudal tenga unidades y geometría compatibles (los módulos `SPACE` utilizan caudal acumulado bajo otro esquema), y la materia sólida conserve inventario.

**No hay intervención del usuario requerida para H11a; H11b exige decisión técnica fundamentada, no implementación automática de un modelo hídrico nuevo.**

## H11b — Reutilización inmediata de acoplamiento nativo de flujo + infiltración (plan antes de código)

**Antecedente descubierto después de H11a:** Landlab tiene `SoilInfiltrationGreenAmpt`, componente que consume directamente `surface_water__depth` y actualiza `soil_water_infiltration__depth` en los mismos nodos; tutorial oficial: https://github.com/landlab/landlab/blob/master/docs/source/tutorials/overland_flow/soil_infiltration_green_ampt/infilt_green_ampt_with_overland_flow.ipynb . **Precisión crítica**: el tutorial enlaza `KinwaveImplicitOverlandFlow` con Green-Ampt, **NO** el de Almeida `OverlandFlow` de H11a; los modelos de escorrentía no son equivalentes. La fuente del modelo de onda cinemática `generate_overland_flow_implicit_kinwave.py` acepta `runoff_rate` **en mm/h** y `dt` **en segundos**, a diferencia de `OverlandFlow` de Almeida, que acepta `rainfall_intensity` **en m/s**. `KinwaveImplicitOverlandFlow` tiene además `changing_topo=True` para rerutear cuando el relieve cambia.

**Objetivo concreto:** evaluar primero el **par nativo documentado** sin inventar nuevo adaptador de infiltración. El estado acuoso compartido se limita a *agua superficial* + *columna de agua infiltrada*; aún **NO** representa humedad de raíces de `SoilMoisture`.

**Pruebas predefinidas:**
1. Malla cerrada 12×12, 1m spacing, pendiente moderada; `surface_water__depth=0` al empezar y `soil_water_infiltration__depth=0.01m` inicial para evitar frente húmedo singular; `runoff_rate=72mm/h`, `dt=0.5s`, 120 pasos (=60s). K de Green-Ampt `1e-6m/s`, tipo de suelo `sandy loam` (parámetros de biblioteca); ningún flujo externo de salida.
2. Control lluvia cero; sin aporte ni agua superficial inicial, el acumulado de infiltración no debería aumentar más allá de tolerancia del modelo.
3. Control de infiltración `K=0`: con lluvia el agua debe permanecer superficial (salvo redistribución horizontal); el inventario conjunto no cambia.
4. Escenario activo K>0: `soil_water_infiltration__depth` aumenta y `surface_water__depth` muestra volumen inferior al control K=0 al finalizar; el total `V_surface + V_infiltrated` aumenta exactamente según lluvia×área×tiempo, dentro de tolerancia de 0.1%.
5. Intervención topográfica +0.2m en un nodo ANTES de simular; activa `changing_topo=True`, distribuciones de superficie distintas, mismo presupuesto conjunto. Replay exacto con parámetros iguales.
6. Registrar coste CPU, formatos de entrada, conservación por límites y campos: no clasificar infiltración acumulada como saturación de zona radicular.

**Si pasa:** autorizar elección de un solver de agua/infiltración del conjunto Landlab para un nuevo experimento de acoplamiento ecológico, **sin** copiar agua infiltrada directamente a `SoilMoisture` (distinto estado y ecuaciones). Si falla: comparar componente o método del tutorial, cuantificar piso de agua y condiciones de borde antes de concluir.

**Próximo gate H11c:** comparar este esquema frente al par `OverlandFlow` + Green-Ampt (ambos leen el mismo nombre `surface_water__depth` pero con diferente time step; no afirmar interoperabilidad por nombres), y con otras soluciones comunitarias existentes; seleccionar según balance, costo y capacidad de topografía mutable. Mantener arquitectura reversible.
