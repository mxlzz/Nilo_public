# Etapa3 — H25. Preregistro de asentamiento tardío SIN alterar física granular H24

**2026-11-22. ANTES DE CÓDIGO Y CI.** [H24 resultado negativo parcial](ETAPA_3_H24_RESULTADOS_PILA_GRANULAR.md): sin paredes, PyBullet3.2.7 creó montículos por fricción (~0,75m) vs monocapa0,15m sin ella, con masa y replay correctos, pero fallaron tamaño de red de contactos (40/35<45) y reposo al paso1600 (`v_P90≈0,23/0,19m/s`, `desplazamiento_med≈0,037/0,045m`). **H24 sigue NO APROBADA.** La nueva hipótesis es que la pila está **todavía asentándose**, no que deban reprogramarse contactos o intervenir con cohesión.

## Hipótesis

Si ese mecanismo granular rígido realmente forma una estructura estable, **al continuar exactamente la misma física durante más tiempo**, ambos montículos deben reducir velocidades y mantener componente de contactos conectada ≥45, sin paredes ni paradas artificiales. Si se siguen redistribuyendo, se dispersan o no alcanzan límites, **H25 NO APROBADA** y se documenta que la pila era transitoria, no estable.

## Contrafactual de trayectoria y configuración fija

- Reusar `WORLD_RESEARCH/experiments/probe_e3_h24_granular_pile.py` **sin editarlo**: mismos125 granos radio0,075m, masa0,025kg (total3,125kg), mismo 5×5×5 inicial jitter±0,008m, mismas semillas20261122 y20261123, Bullet DIRECT, gravedad−9,81, piso sin paredes, `dt=1/240`, iteraciones solver60, Damping0,02 y mismo `lateral/rolling/spinning` (1,5/0,15/0,10). Control fricción0, misma semilla; replay de activo seed20261122.
- **Único cambio físico/operativo frente H24:** duración total **3.600 pasos** (15s) en vez de1.600 (6,667s), **sin reiniciar el mundo en el paso1600**. Se almacena por read-only snapshot t1200, t1600, t3000 y t3600. Ventana de reposo preregistrada **3000→3600**, distinta de la ventana temprana H24 1200→1600.
- Para ambos activos y control sin fricción, **reconstruir temporalmente owner en t1600 desde la muestra** y verificar SHA-256 exacto contra los ya publicados de H24:
  - activo seed20261122 `9e249c09b73176f81a696c4443ccbc36a2aed274cc9e8c4a44160d922d17ca96`
  - activo seed20261123 `ec6d269e7621dfbd8244ed57722fc0b6e71b721d870a7d3653321f151a647b67`
  - control sin fricción `aa35551b0e761173696e0fc89916152ed98663dd549a23cc214c4b3d588ca594`
  Esto garantiza que **los primeros1600 pasos realmente reproducen H24**, no una escena alterada. No sobrescribir H24 para lograrlo.

## Gates de aceptación H25

1. **Trayectoria/masa:** coincidencia exacta de los tres SHA de prefijo, y en los 4 escenarios cantidad125/masa total3,125kg, identidades y geometría sin alteración. Estado final sin interpenetración >0,02m, penetración de piso >0,02m ni finitos inválidos, usando exactamente validador H24. No inventar reservas de masa o energía.
2. **Altura/conectividad real en ambos activos:** en t3600 `altura>0.36m`, más de30 granos con centro z>0,26m, más de0,15m de descenso medio; contactos positivos tanto grano-grano como grano-suelo, componente conectada de grano-grano (sin usar piso) **≥45 granos** en cada seed.
3. **Reposo persistente en ambos activos:** entre pasos3000 y3600 mediana desplazamiento espacial de granos **<0,025m**; al paso3600 `p90_velocity<0,08m/s`. No reemplazar esto por solo «alto» ni bajar el umbral frente H24.
4. **Ablación de rozamiento:** al finalizar t3600, pila activa seed20261122 mayor altura que sin-fricción por≥0,08m, radio horizontal P90 menor por≥0,06m, componente de contactos mayor al menos10 granos. Mismas condiciones salvo fricción. Las esferas sin fricción no tienen por qué guardar reposo final y se informa su movilidad.
5. **Variación y reproducción:** los activos de dos semillas difieren en al menos1 posición final >0,01m; repetición seed20261122 idéntica bit a bit para poses, velocidades lineal/angular, orientación y muestras t1200/t1600/t3000/t3600. Sin nuevas semillas oportunistas.
6. **Owner auditable:** rechazo de al menos8 corrupciones de H24 antes del commit, NetCDF final conserva unidades, id, geometría, masa, posición, velocidad/angular/quaternion, tiempo y hash exacto. Reportar ambos resultados activos, ablación y dictamen en `WORLD_EVAL_JSON` antes de exit1.

**No exigimos escena sin gravedad adicional** porque H24 ya la ejecutó exactamente sin movimiento y **no cambiaron ni física ni inicialización**; una repetición redundante no cambia la pregunta temporal de H25.

**Resultado permitido:** éxito solo si se satisfacen TODOS los gates1–6; demostraría un **agregado granular rígido que alcanza reposo en un horizonte más largo**, no terreno natural, cohesión de roca ni un mundo con historia abierta. Si falla H25, evaluar si esta línea justifica más costo: no ampliar pasos o ajustar fricciones sin antes revisar significado del resultado y oportunidades reales. Etapa3 ABIERTA.
