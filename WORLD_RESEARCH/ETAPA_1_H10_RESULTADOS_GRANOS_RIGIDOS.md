# Etapa 1 — H10. Dinámica colectiva de granos rígidos 3D

**Fecha:** 2026-11-22. **Estado:** **H10 APROBADA bajo su hipótesis y controles preregistrados**. Etapa 1 sigue ABIERTA; H10 no es prueba de cohesión, deformación ni estructura estable.
**Protocolo registrado antes del código:** [ETAPA_1_H10_PROTOCOLO_GRANOS_RIGIDOS.md](ETAPA_1_H10_PROTOCOLO_GRANOS_RIGIDOS.md).
**Arnés:** [experiments/probe_e1_h10_rigid_grains.py](experiments/probe_e1_h10_rigid_grains.py).
**CI exitosa:** https://github.com/mxlzz/Nilo_public/actions/runs/45049166835 — `240808f3bc50c5bedb6c09b1b0de509bc0337b35`. Entorno Python 3.11.18, PyBullet 3.2.7, xarray 2026.9.0.

## Fenómeno medido

Se situaron 27 esferas separadas, en tres niveles 3×3 ligeramente desfasados (radio 0,1m y masa0,25kg cada una), sobre un plano sin paredes. `PyBullet DIRECT` ejecutó 720 pasos `dt=1/240s`, g=-9,81m/s², coeficiente de fricción lateral0,6 y restitución0. Ninguna ley física fue escrita en el proyecto. La representación material `xarray` mantiene **6,75kg** de material A como único inventario; Bullet mantiene parámetros de masa y cinemática transitoria, **no un segundo inventario**.

- Centro medio de granos: **z inicial1,09m → z final0,09999m**; descenso aproximado 0,99m.
- Contacto suelo con fuerza positiva en **626 pasos** y contacto **grano-grano** con fuerza positiva en **297 pasos**; máximo instantáneo 21 contactos grano-grano.
- Desplazamiento horizontal máximo **2,82325m**; distancia final mínima entre centros **0,20191m**, superior al diámetro0,20m, sin interpenetración final detectable bajo el umbral del protocolo.
- La redistribución fue principalmente **dispersión horizontal** tras chocar y alcanzar un suelo abierto: la cota final de todos los centros quedó próxima al radio de la esfera. **No apareció una pila estable o relieve persistente; no se acreditan estructuras ni emergencia sostenida**.

## Controles y reproducibilidad

- **Sin gravedad**, posiciones finales idénticas a las iniciales (desplazamiento máximo 0m), sin fuerzas de contacto entre granos o suelo.
- **Sin suelo**, caída libre del centro medio hasta **-43,1163m**, sin contactos ni desplazamiento horizontal: los contactos colectivos del caso activo requieren obstáculo/piso.
- **Replay** de todo el caso activo: posiciones y velocidades muestreadas exactamente idénticas; el recuento temporal de pasos con contactos iguales; SHA-256 de muestras `6be3e51cac761698bd81a58265a7fb71bfe48c207e2bef663cadecbbf3ca8677`.
- Hash del inventario xarray permaneció exactamente igual, SHA-256 `23c52cafc222455527dc58e9787bddc7bd76dd4efd07ac4290b8b5546cb2e9c5`.
- Cinco alteraciones inválidas (masa negativa, alta no autorizada, unidad errónea, radio modificado, identidad de grano adulterada) rechazadas antes de ejecutar; no afectan el owner.

## Incidencia documentada y no ocultada

**Primer CI H10** https://github.com/mxlzz/Nilo_public/actions/runs/45049082476 **FAILED**, antes de ejecutar la física, por intentar editar `xarray.coords["grain"].values`, un arreglo de solo lectura. No fue falsación ni validación de la hipótesis granular. Se preregistró diagnóstico en el protocolo, se cambió exclusivamente la inyección de identidad inválida para usar la API de coordenadas pública, y se mantuvieron **todos** los parámetros y criterios físicos. **Segundo CI H10** https://github.com/mxlzz/Nilo_public/actions/runs/45049166835 **SUCCESS**.

## Dictamen y decisión siguiente

H10 completa una **prueba acotada de redistribución colectiva de partículas rígidas** usando Bullet, que anteriormente solo había sido verificado con una caja y una cavidad estática (H7/H8). La dispersión observada es un resultado científicamente válido que evita asumir que el sistema produce pilas estables. **No demuestra** ángulo de reposo calibrado, materia granular como continuo, fricción de suelo real, estabilidad y colapso de cueva, fractura, erosión de un volumen 3D, deposición estable, balance energético o almacenamiento/restauración de velocidades Bullet.

La etapa 1 **permanece ABIERTA**. Próxima pregunta de mayor valor: ¿existe un solver especializado que convierta masa/estado granular 3D en **cambios morfológicos estables y observables** sin recetas manuales, sobre ROI compartida y con costo aceptable? No prometer que GeoTaichi, Chrono o Bullet resuelvan eso antes de probar el fenómeno; no integrar múltiples motores por expectativa. Alternativamente, priorizar una transformación/transferencia térmica solo si se justifica físicamente y con un presupuesto de energía explícito. No abrir etapa 2 formal ni alterar `main` / NeuroLab.

**Fuentes upstream usadas en decisión:** [GeoTaichi](https://github.com/Yihao-Shi/GeoTaichi), [Chrono DEM](https://api.projectchrono.org/group__dem__module.html), [Bullet3](https://github.com/bulletphysics/bullet3), [The Powder Toy](https://github.com/The-Powder-Toy/The-Powder-Toy). Licencias, dependencias y nivel de simulación distintos; ningún solver de deformación de suelo adoptado.
