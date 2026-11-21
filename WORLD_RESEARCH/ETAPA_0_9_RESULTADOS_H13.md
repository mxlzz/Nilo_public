# E0.9 — Resultados H13: persistencia multiproceso y escalado hídrico

**Fecha:** 2026-11-21. **Dictamen:** H13a y H13b VALIDADAS en alcance limitado. Etapa 0 ABIERTA. Plan previo `ETAPA_0_9_PROTOCOLO_H13_PERSISTENCIA_ESCALA.md`.
CI real **SUCCESS**: https://github.com/mxlzz/Nilo_public/actions/runs/44957211442
Implementación: `experiments/probe_landlab_checkpoint_scale.py` y workflow `world-landlab-checkpoint-scaling.yml`.

## H13a — no confundir replay continuo con checkpoint
- Landlab 2.11.0 y Python 3.13, grilla 12×12 con bordes cerrados, `OverlandFlow` (de Almeida) + `SoilInfiltrationGreenAmpt`.
- Proceso A: ejecución 80 pasos seguidos (dt=0.5s), salida NPZ de todos los campos probados.
- Proceso B: ejecutar 40 pasos, guardar tuple Python pickle `(grid,OverlandFlow,GreenAmpt)` con checksums/versión.
- Proceso C independiente: reabrir su propio pickle, comprobar que ambas instancias siguen apuntando a la misma grilla (`component.grid is grid`), ejecutar 40 pasos más y comparar resultados bit a bit con A.
- Checkpoint íntegro de la pareja: **13,910 bytes**, hash SHA-256 verificado.
- **Coincidencia EXACTA:** `node:topographic__elevation`, `node:surface_water__depth`, `node:soil_water_infiltration__depth`, `link:surface_water__discharge`, `link:water_surface__gradient`. No se incluyeron todos los atributos privados en una comparación byte a byte, pero el tuple pickle los preservó en la instancia serializada.
- Presupuesto de agua al final: lluvia 0.08m³, superficie 0.06528079556481337m³, columna acumulada 1.014720204435187m³, residual **4.44089e-16m³** (error relativo 5.55e-15 sobre lluvia).
- No cargar pickle de terceros: deserializar datos arbitrarios puede ejecutar código. Éxito en mismo SO/versión no autoriza persistencia cross-version ni demuestra guardado de todo el mundo bio-geomorfológico H10b.

## H13b — escalado de agua + infiltración
Par de modelos anterior, 60 pasos de 0.5s por escenario en proceso independiente, raster dx=1m, 2e-5m/s lluvia, borde cerrado, K=1e-6m/s.

- 12×12 = 144 nodos: **0.015489s** cálculo, memoria de proceso pico 207,832KiB.
- 32×32 = 1024 nodos: **0.012508s**, memoria 208,444KiB.
- 64×64 = 4096 nodos: **0.021193s**, memoria 211,148KiB.
- 128×128 = 16,384 nodos: **0.054927s**, memoria 218,800KiB.

Todos produjeron profundidad no negativa/finita y presupuesto de agua dentro del margen de redondeo (error relativo máximo del orden de 1.85e-14). Volumen de lluvia para 128²: 9.5256m³; residual **1.421e-13m³**. Los cambios de 12²→32² menores que cero en tiempo medido son ruido/overhead de microbenchmark, **NO** comportamiento superlineal de mejora. La memoria incluye importación de NumPy/SciPy/Landlab y no es solo memoria del modelo.

## Interpretación y limitaciones
- **H13a** demuestra reanudación de **estos dos componentes** en otros procesos, no del conjunto H10b ni de WorldEngine ni de agentes.
- **H13b** sugiere bajo costo de un bloque hídrico simple hasta 128² en el runner, pero NO es benchmark de mundo extenso, persistente, que ejecuta suelo, vegetación, clima, sedimento, render, ni meses de tiempo. No extrapolar porcentaje de tiempo a escalas de tiempo geológicas.
- Las pruebas no verificaron generación de relieve emergente, clima calibrado ni adecuación física en pendientes rápidas. La film inicial se contabilizó en todos los balances.
- DRYP2 continúa como referencia científica a revisar separadamente, no código integrado.

## Siguiente gate
H14: checkpoint del lazo de 90 días de suelo/vegetación/geomorfología (usando el script H9/H10b como baseline), también entre procesos y control de paso temporal; luego prueba de costo con componentes múltiples. Antes de integrar humedad radicular desde Green-Ampt, verificar ecuaciones y doble contabilización de lluvia.
