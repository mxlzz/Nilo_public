# Etapa 1 — H11. Primer ensayo MPM deformable 3D con proveedor existente

**Fecha:** 2026-11-22. **Dictamen:** **H11 APROBADA como prueba mínima de deformación 3D con controles**. No es elección del motor definitivo ni aceptación de realismo geotécnico. Etapa 1 **ABIERTA**.
**Protocolo previo:** [ETAPA_1_H11_PROTOCOLO_MPM_3D.md](ETAPA_1_H11_PROTOCOLO_MPM_3D.md).
**Decisión de alternativas:** [ADR-0007](DECISIONES/ADR-0007_GATE_MPM_3D.md).
**Arnés:** [experiments/probe_e1_h11_upstream_mpm3d.py](experiments/probe_e1_h11_upstream_mpm3d.py). **CI exitosa:** https://github.com/mxlzz/Nilo_public/actions/runs/45055263832. **Commit ejecutado:** `a8f7b3d2c8fe4362301e384209b0824850951c26`.

## Qué se ejecutó realmente

Código MPM/constitutivo **íntegro del upstream PINNeAPPle** en commit fijo `c8a6e3dce5daedd10903cc68f7f3a062c42b8bc4`, licencia Apache-2.0, descargado fuera del repositorio y cargado sin copiar su código; Python3.11.18, PyTorch2.10.0+cpu, xarray2026.9.0. 108 puntos materiales de un único tipo A, cada punto con masa constante, total **2,7kg**, densidad de entrada1600kg/m³, E=20.000Pa, Poisson0,3, espacio (0,60×0,24×0,36)m, dx0,025m, 0,25 segundos físicos por escenario. No existe calibración de estos coeficientes para roca/suelo real.

**Con gravedad -9,81m/s² y ángulo de fricción interno30°:** el centro de masa z **0,1500→0,0421597m** (caída 0,1078403m), anchura q99-q01 en x **0,21623m**, extensión de borde q99 x **0,26480m**. Velocidad máxima final **0,47116m/s**. **La muestra NO está en reposo**, así que no afirmar que creó una forma estable.

**Con gravedad y ángulo de fricción0°**, demás parámetros iguales: centro z final **0,0406510m**, anchura q99-q01 x **0,28830m**, borde q99 x **0,32719m**, velocidad máxima final **1,20768m/s**. Diferencia de posiciones del mismo conjunto (media absoluta de coordenadas) **0,007115846m** > umbral preregistrado 0,002m. Se verificó una respuesta causal a un único parámetro constitutivo, no se atribuye toda la morfología a ese parámetro sin descomponer bordes.

**Control sin gravedad** y fricción30°: posiciones y velocidades completamente idénticas al inicio; desplazamiento y velocidad máxima **0**. Repetir caso activo g-9,81/30° con mismos hilos CPU produjo arrays de posición y velocidad exactamente iguales. Cuatro corrupciones de xarray (masa creada, negativa, kg→g e identidad) fueron rechazadas sin alterar owner. Persistencia del inventario NetCDF exacta, SHA-256 `a6ef258a0579d69660acb9bcc3baa1a8f1352ae759e534a568cfca664cf48fb4`. La masa del solver no varió y se verificó contra los valores del único owner; la matriz de masa computacional no cuenta como inventario duplicado.

## Qué demuestra y qué NO

**Sí:** código publicado genera caída y cambio de forma de un material volumétrico 3D con propiedad constitutiva diferencial; masa material inalterada, sin movimiento cuando se retira gravedad, replay y owner/checkpoint auditable. No se programó un solver nuevo.

**NO:** estabilidad, consolidación tras muchos segundos, deformación irreversible calibrada bajo descarga/recarga, independencia de paredes del recinto, benchmark independiente 3D comparativo, exactitud de esfuerzos, acoplamiento ROI H5, mezcla de materiales, calor/fractura/erosión bajo techo, ni evolución estructural abierta. El `GeoMPM` upstream tiene salida numérica y condiciones en fronteras, pero **no preservamos aún el estado interno F/C para reanudar**; NetCDF aquí almacena inventario, no checkpoint cinemático del material. La física no fue contrastada con una solución analítica o mediciones 3D.

## Próximo gate selectivo

**H12 propuesto:** evaluar si se alcanza reposo y persiste una morfología 3D sin intervención, **con dominio suficientemente ancho para que no sean las paredes laterales quienes detengan el movimiento**. Medir velocidad residual, ancho/alto, dispersión, contacto artificial con límites, masa y replay; comparar fricción y control sin gravedad cuando aporten causalidad. Si hay apoyo solo por pared/clamp, no declarar estructura estable. Después, antes de adoptar un proveedor o acoplar a ROI, requerir referencia independiente (GeoTaichi/u otro test publicado) y evaluación de costo/licencia. Etapa1 sigue abierta: energía/transformaciones y varias leyes constitutivas siguen sin validación.
