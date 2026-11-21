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
