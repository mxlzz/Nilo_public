# Etapa 1 — H11. Gate comparativo para deformación plástica 3D

**Fecha:** 2026-11-22. **Estado:** EVALUACIÓN PREVIA y selección de prueba reversible; ningún solver de materia deformable adoptado. **Objetivo rector:** estado material autónomo y persistente, que cambie por relaciones físicas sin imponer estructuras finales. Se mantiene H1–H10 y no se toca Nilo/NeuroLab.

## Brecha física que H9/H10 no resolvieron

H9 transportó suelo fluvial 2,5D; H10 dejó 27 esferas indeformables dispersas sobre un plano, sin dar forma a una masa granular continua. Para saber si un terreno/material puede *deformarse* y generar configuraciones estables por reglas ya publicadas, hace falta una **ley constitutiva + solver de deformación**, no solo cambiar el render, aumentar colisiones o sustituir el owner de inventario.

**Hipótesis alternativa:** quizá un motor especializado no agrega capacidad útil respecto de H9/H10 si sus efectos no superan controles adversariales o los costes de implementación son desproporcionados. Esa conclusión también es un resultado válido; no programar física nueva por ausencia de un ensayo aprobado.

## Alternativas vigentes contrastadas

1. **GeoTaichi** — [upstream](https://github.com/Yihao-Shi/GeoTaichi), [artículo revisado en CPC 2024](https://doi.org/10.1016/j.cpc.2024.109219). MPM/DEM/FEM, constitutivos Drucker–Prager, ejemplos explícitos en 3D, CPU/GPU. **GPL-3.0**, pila de dependencias y compatibilidad de versiones elevadas; excelente referente geomecánico, pero costo para CI mínimo y eventual distribución aún sin resolver. **Conservar como baseline científico más maduro; no adoptar por ahora.**
2. **PINNeAPPle** — [código](https://github.com/PINNeAPPle-Labs/PINNeAPPle), `pinneapple_simulation/particle_dynamics/geo_mpm.py`, **Apache-2.0**. Implementa MPM 2D/3D en PyTorch CPU con tipo `Sand` y regla Drucker–Prager; ejemplos de colapso de columna 2D comparados con fórmula experimental. Ventaja: API Python, instrumentación headless, salida de posiciones, velocidades y volumen; más simple de adaptar y licencia permisiva. **Limitación:** se verificó código y ejemplo, **no validación propia 3D ni precisión de su modelo**. El paquete completo declara `torch` y otros requisitos; el ensayo importará únicamente su código upstream desde un checkout aislado/pineado para no instalar otros subsistemas.
3. **harri665/MPM** — [upstream](https://github.com/harri665/MPM), **MIT**, MPM 3D deformable con OpenGL/CUDA/WebGPU y tests CPU para kernels; la ruta de simulación principal usa GPU y tooling de compilación, no un módulo Python simple para copiar al owner. Referente alternativo a PINNeAPPle si fracasa su prueba.
4. **Matter** — [upstream](https://github.com/larsblatny/matter), GPL-3.0, C++ MPM con material granular elasto-viscoplástico y binding Python; requisitos de compilación y licencia menos favorables para una prueba inicial.
5. **Project Chrono DEM/DEM-Engine** — [docs](https://api.projectchrono.org/group__dem__module.html), [repo DEME](https://github.com/projectchrono/DEM-Engine), BSD-3 para DEME; motor DEM de partículas en GPU CUDA/HIP (no plasma/MPM de suelo deformable). Requiere hardware/toolchain según backend, poco apto para CI CPU pequeña.
6. **Bullet H10**, zlib, **no constitutivo plástico**; ampliar su número de esferas no respondería la pregunta H11.

## Selección del experimento H11, no del motor definitivo

**Probar exclusivamente el GeoMPM 3D upstream de PINNeAPPle** en un laboratorio CPU, antes de decidir su integración. Elegimos la ruta con menor complejidad y una ley de deformación que no existe en H9/H10. La licencia Apache-2.0 permite estudiar y adaptar bajo sus condiciones sin introducir archivos externos al repositorio del mundo. PINNeAPPle no es considerado validado científicamente por popularidad; requiere controles y, a futuro, comparación con GeoTaichi o un benchmark publicado.

**Prohibido por este gate:** importar un solver completo en `main`, integrar varios motores por inercia, afirmar realismo geotécnico sin calibración, escribir nuevas ecuaciones físicas, presentar una masa dispersa como emergencia abierta o prometer estabilidad donde el ensayo aún no la midió. El test detallado es `ETAPA_1_H11_PROTOCOLO_MPM_3D.md`.

## Fuentes y límites de verificación

Las licencias, estructura de paquetes y capacidades son del upstream inspeccionado el 2026-11-22. `PINNeAPPle` main en la revisión observada `c8a6e3dce5daedd10903cc68f7f3a062c42b8bc4`; `GeoTaichi` main observado `6cae5a6998c4f0be9f59b5615bf2e26857df824f`. Son commits externos para reproducibilidad, no evidencia de ejecución 3D H11. **H11 no está completado hasta tener un workflow SUCCESS y resultados que cumplan el protocolo.**
