# ADR-0013 — Retornar a agregación física granular antes de ampliar mezclas ideales

**2026-11-22. Estado: decisión reversible de evaluación H24; NO adopción de motor universal.** [Etapa3 del plan](../BASES_Y_HOJA_DE_RUTA.md) exige que depósito, cohesión, transporte o agregación produzcan configuraciones **estables**, no plantadas; medir tamaño/conectividad/persistencia con semillas, ablación de regla y nulos.

## Resultados que provocan el giro

- H10, 27 esferas PyBullet sin rozamiento de rodadura: contacto/gravedad válidos pero **dispersión horizontal y ninguna pila persistente** ([informe](../ETAPA_1_H10_RESULTADOS_GRANOS_RIGIDOS.md)).
- H12, continuum MPM PINNeAPPle: baja velocidad pero apoyo artificial del **61% del material exactamente en clamp inferior**, hipótesis de soporte granular no aprobada ([informe](../ETAPA_1_H12_RESULTADOS_REPOSO_MPM.md)).
- H19, Landlab: 50 nodos conectados de depósito pero conectividad explicable por distribución inicial al condicionar nulo por filas ([informe](../ETAPA_3_H19_RESULTADOS_DEPOSITO_CONEXO.md)).
- H21, Cahn–Hilliard `epsilon=1`: homogeneizó mezcla. H22, `epsilon=.5`: **separación A/B causal** y masa conservada, pero fallaron umbrales de patrón/persistencia. H23, prolongación a600 pasos: seed20261124 paso579 `phi=1.0010109` excedió el límite físico1, en un solver sin garantía de bound preservation. [Informe](../ETAPA_3_H23_RESULTADOS_PERSISTENCIA_SEMILLAS.md). Una literatura especializada propone esquemas *bound-preserving* ([Bailo et al., 2023](https://www.global-sci.com/cicp/article/view/7202)), pero implementar otro solver solo para patrones composicionales **no aporta suficiente evidencia de agregados estables** en el mundo investigado.

## Alternativas existentes comparadas y criterio

1. **PyBullet3.2.7**, licencia permisiva tipo zlib del proyecto Bullet, CPU/headless. Ya auditado en H7/H8/H10/H17, permite contacto esfera-esfera, fricción lateral, **rollingFriction**, **spinningFriction**, restitución y damping, cuerpos con identidades/masas. El repositorio MIT [Angle of Repose Digital Twin](https://github.com/DillGrammer/angle-of-repose-digital-twin) registra18 ensayos y distingue esfera lisa/áspera, control de colisiones, semilla y rechazo de granos fuera de pila; sus datos y calibraciones propias **no son validados por este proyecto**. El artículo [Quantifying impact ... PyBullet angle of repose, 2025](https://www.sciencedirect.com/science/article/abs/pii/S1674200125002718) presenta formación de montículos con fricción de rodadura. Reutilizar la API de Bullet, **no** copiar su aplicación de visualización ni tratar resultados ajenos como hechos propios.
2. **MuJoCo**, Apache-2.0, C++ y Python, tiene contacto/fricción con cono elíptico/piramidal y opciones para estabilidad de pilas. [Documentación](https://mujoco.readthedocs.io/en/stable/computation.html). Es alternativa madura si Bullet no forma pilas reproducibles, pero introducir un segundo engine rígido ahora duplicaría integraciones sin necesidad.
3. **GeoTaichi**, GPL-3.0 e instalación más costosa; H13A no alcanzó a ejecutar MPM por Open3D/Plotly, por lo que no se refutó la física. **Chrono DEM** más orientado a GPU y especialización granular. No prioritarios para pequeña prueba local sin paredes.
4. **Pilas manualmente colocadas, cohesión artificial, reposo fijado por reglas propias**: producirían falsos positivos; descartadas.

**Elección:** nueva H24 de agregación **3D rígida en suelo abierto sin paredes**, con la misma escena inicial para caso de rodadura/fricción activa y control sin fricción, g0, replay y dos distribuciones/semillas. Registrar posición+velocidad/rotación con masa en **un owner validado** al terminar. A diferencia de H10, evaluar **altura, contactos grano-grano, conectividad, velocidad residual y persistencia** y contraste físico con ablación. [Protocolo H24](../ETAPA_3_H24_PROTOCOLO_PILA_GRANULAR.md).

## Alcance y stop

No equivale a roca/arena calibrada, cohesión geológica, estructura de cavidad, fractura, coalescencia ni geometría volumétrica de ROI H5. Si no hay agregado estable/reproducible o el control sin fricción forma la misma estructura, **H24 NO APROBADA**; no añadir parámetros libres en CI hasta hallar una explicación. Etapa3 ABIERTA; main y NeuroLab intocados.
