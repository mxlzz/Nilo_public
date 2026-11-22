# Etapa 1 — H10: redistribución local de granos rígidos 3D con solver existente

**2026-11-22 · PROTOCOLO PRERREGISTRADO ANTES DE CÓDIGO.** Rama aislada `research/world-foundations-2026-11`. Etapa 1 sigue abierta; ensayo exploratorio asociado a mecanismos de etapa 2, sin cambiar sus gates. No instalar ni crear un nuevo motor.

## Gate de alineación y elección de alternativa

**Necesidad concreta:** H9 comprobó transporte de suelo fluvial sobre una superficie 2.5D, H7/H8 comprobaron contacto de *un* objeto rígido en 3D; queda comprobar si un motor existente aporta **redistribución colectiva por colisiones entre unidades materiales** sin fijar a mano la configuración final, para un mundo pequeño. Esto no equivale a deformación de materia continua, fractura de roca ni autoorganización abierta.

**Reutilización evaluada:**
- `PyBullet 3.2.7` (zlib) ya operativo headless en H7/H8; soporta esferas rígidas, contactos, gravedad y fuerzas, sin dependencia nueva. **Preferido para un único microensayo de granos rígidos**, no como modelo universal de tierra.
- `GeoTaichi` (GPL-3.0) implementa DEM/MPM en CPU/GPU, pero la distribución actual incluye Taichi, gmsh, open3d y numerosas dependencias; abordar si hay evidencia de que Bullet rígido no satisface fenómeno requerido. No integrar su código ahora.
- `Chrono::DEM` y DEM-Engine (BSD-3) están orientados a partículas granulares, pero las rutas documentadas DEM requieren GPU CUDA/HIP; es desproporcionado para una CI CPU mínima.
- `Sandspiel` (MIT) y `The Powder Toy` (GPL-3) demostraron transporte discreto 2D (etapa 0), no contacto granular 3D.

**Hipótesis H10:** 27 esferas rígidas de material abstracto A, cada una con 0.25kg y radio 0.1m, inicialmente no solapadas en 3 capas de una matriz 3×3 con leve desfase intercapas y vacíos entre granos, sufrirán bajo gravedad una caída colectiva, contactos con suelo y entre granos, y al menos una redistribución horizontal detectable. El estado granular es resultado de Bullet, no una plantilla de depósito. El inventario xarray de 6.75kg de A seguirá exactamente intacto. El mismo sistema sin gravedad no se desplazará; sin suelo no se formará depósito apoyado.

**Alternativa falsable:** si no aparecen contactos de grano-grano positivos ni movimiento horizontal tras llegar al piso, queda demostrado solo desplazamiento de objetos individuales, no reorganización granular. Si Bullet muestra penetraciones amplias o no reproduce exactamente la misma trayectoria, registrar falla, no quitar criterios retrospectivamente.

## Condiciones fijas

- Motor: PyBullet 3.2.7, Python3.11, `p.DIRECT`, `fixedTimeStep=1/240s`, `numSolverIterations=50`, `deterministicOverlappingPairs=1`.
- 27 esferas: radio 0.10m, masa 0.25kg; x/y de referencia `[-0.24,0,0.24]`m más offsets por capa `(0,0)`, `(0.045,0.025)`, `(0,0)`; z por capas `0.85,1.09,1.33`m. Sin interpenetraciones iniciales, sin paredes.
- Tres escenas, cada una **720 pasos**: activo con gravedad `-9.81m/s²` y suelo plano z=0; control con gravedad `0` y suelo; control gravedad `-9.81` y sin suelo. Sin fuerzas artificiales, sin contacto adicional, fricción lateral 0.6 y restitución 0 para cada grano y piso; sin amortiguación artificial.
- Atributos de material, unidad, identidad de grano y geometría únicos en `xarray.Dataset`; Bullet contiene caché de masas y la **autoridad cinemática temporal**. No duplicar materia ni sumar masa cacheada en Bullet al inventario.

## Pruebas definidas antes de implementar

1. **Integridad:** 27 IDs y masas de 0.25kg, total 6.75kg en owner; el parámetro de masa que recibe Bullet coincide para todos. Sin crear material por caída o contacto; hash de inventario antes/después idéntico. Rechazar masa negativa, unidad errónea, radio <=0, identidades erróneas y masa de origen alterada.
2. **Dinámica activa:** el centro de masa desciende **al menos 0.40m**; z mínimo final de centros `>=0.08m`; al menos un contacto grano-piso con fuerza normal positiva y un contacto grano-grano con fuerza normal positiva **en alguno de los pasos**; al menos un grano cambia posición horizontal más de **0.01m** (efecto colectivo, no solamente caída vertical). Las posiciones finales de centros de granos distintos deben quedar separadas `>=0.18m` (penetración <=0.02m).
3. **Control sin gravedad:** todos los centros iniciales coinciden con los finales con error máximo absoluto `<1e-9m`; ningún contacto grano-piso y ningún contacto intergrano con fuerza positiva.
4. **Control sin suelo:** caída libre (centro promedio z final `< -5m`), sin contactos de apoyo, y sin reorganización horizontal significativa (máximo desplazamiento xy `<1e-9m`).
5. **Replay:** segunda corrida activa con mismos parámetros reproduce **exactamente** todos los valores de posición y velocidad muestreados cada 120 pasos, además de conteos de contacto. No alterar semillas ni integrador entre repeticiones.
6. **Auditabilidad:** JSON con cantidades iniciales y finales, magnitudes de rearrangement, controles, replay, versiones y hash de inventario. No declarar energía conservada: Bullet disipa trabajo mecánico sin balance térmico.

## Gate

**Aceptar** solo si los controles se cumplen; **ajustar** únicamente si se identifica un fallo del arnés o una condición inicial físicamente contradictoria y se documenta antes de modificar; **descartar** si no se observa interacción colectiva. Un éxito probará contacto *entre granos rígidos*, no formación natural de suelo, estabilidad de cavidades, propiedades de sólidos deformables ni pertinencia de miles de partículas. Si se necesitan deformación plástica, fragmentación o flujo granular calibrado, evaluar GeoTaichi/Chrono o solvers especializados con criterio físico y de licencia previo. Nunca subir un solver físico propio a `main`.
