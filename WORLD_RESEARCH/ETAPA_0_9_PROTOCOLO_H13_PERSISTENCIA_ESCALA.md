# E0.9 — Protocolo H13: persistencia real y escalado de agua/suelo nativos

Fecha: 2026-11-21. Estado: **plan de pruebas previo a implementación**. Objetivo original: mundo físico autónomo con procesos ambientales comprobables, separado de NeuroLab. Etapa 0 ABIERTA; sin motor final seleccionado.

## Evidencia disponible
H7–H11c validan leyes y presupuestos en microgrillas, pero no prueban que puedan reanudarse sin perder estado interno ni que sean viables en un mapa extenso. El camino hidrológico experimental más prometedor en H11c fue Landlab `OverlandFlow` de Almeida + `SoilInfiltrationGreenAmpt`, con ~43x menor tiempo que Kinwave en el caso ensayado. DRYP 2.0 está disponible pero solo ha pasado inspección estática (H12a), no runtime ni licencia de adaptación.

## H13a — checkpoint integral entre procesos Python
**Hipótesis:** al serializar **juntos** grilla + instancias `OverlandFlow` + `SoilInfiltrationGreenAmpt` vía `pickle` del propio Python, se conservan el estado del agua, las variables internas del solver y sus referencias compartidas, permitiendo continuar con los mismos resultados bit a bit tras arrancar otro proceso Python.

- Simular un paisaje fijo 12×12, dx=1m, borde cerrado, K=1e-6m/s, lluvia 2e-5m/s, 80 pasos de 0.5s, con `OverlandFlow` de Almeida y Green-Ampt.
- **Referencia:** ejecutar 80 pasos desde estado inicial y guardar los campos finales `surface_water__depth`, `soil_water_infiltration__depth`, `surface_water__discharge`, `topographic__elevation` y checksum en NPZ.
- **Checkpoint:** arrancar un segundo proceso y ejecutar 40 pasos desde condiciones iniciales idénticas. Escribir un solo archivo pickle del tuple `(grid,overland,greenampt)` con protocolo máximo, acompañado de metadatos JSON: versiones Python/Landlab, nodos, paso temporal, checksum SHA-256 del archivo.
- **Resume:** tercer proceso diferente lee su propio pickle generado por el ensayo; verifica identidad `overland.grid is grid` e `infiltration.grid is grid`, completa 40 pasos y compara arrays finales exactamente con la referencia sin interrupción.
- Test de presupuesto hídrico y validación de finitud/positividad tras continuar. **Criterio:** coincidencia bit a bit de TODOS los campos guardados, misma cantidad de pasos, checksum y versiones registradas; residual de agua <0.1% del aporte. Si falla pickle o el estado restaurado no coincide, registrar error, **no** declarar checkpoint aprobado y estudiar campos internos/alternativa de serialization. El pickle no puede cargarse desde terceros: solo archivos que generamos, porque deserializar pickle arbitrario ejecuta código.
- **Límite:** éxito de pickle dentro del mismo Python/Landlab y sistema operativo no prueba compatibilidad cross-version ni cross-OS ni checkpoint completo del mundo eco-geomorfológico H10b; se necesita auditar todos los componentes antes de producción.

## H13b — escalado básico del módulo de agua
**Hipótesis:** el par `OverlandFlow`+GreenAmpt es viable en mallas crecientes con error de balance acotado y tiempo sub-cuadrático versus nodos (medir, no imponer ventaja).

- Mallas de **12×12, 32×32, 64×64, 128×128** nodos con dx=1m, pendiente suave, borde cerrado, K=1e-6m/s, lluvia 2e-5m/s, 60 pasos de 0.5s.
- Ejecutar cada tamaño en proceso aislado en GitHub Actions para registrar tiempo `time.perf_counter()`, cantidad de nodos y memoria pico `resource.getrusage` en Linux; excluir instalación/importación de bibliotecas del tiempo medido.
- Criterios duros: cálculos finitos y no negativos, presupuesto conjunto agua superficial+infiltrada residual relativo <0.1% del **aporte** por lluvia; repetir tamaño más grande y comparar campos exactamente.
- **No** declarar rendimiento sostenible del mundo autónomo: mallas mayores, horizonte de meses/años, clima y geomorfología integrados, tamaño de estado de checkpoint y renderización siguen por medir. Reportar costo por nodo y paso, no extrapolar linealmente sin evidencia.
- Si falla tamaño, conservar registro de tamaño/costo/error y evaluar frontera y dt; **no** reajustar parámetros para aprobar sin documentar.

## H14 bloqueado
No extender H11b hacia agua radicular mediante `soil_moisture__saturation_fraction = soil_water_infiltration__depth` ni copiar DRYP 2.0 al repo. Antes, comprobar ecuaciones de porosidad/capacidad de suelo y estado de agua. La literatura sobre DRYP2 da alternativas ya acopladas; reevaluar costo/atribución/licencia. Esto es gate de investigación, no negación de posibilidad.

**Salida:** resultados CI, informe y ADR revisable. Mantener branch research/world-foundations-2026-11 y main intacto.
