# Etapa 1 — H12. Resultado adversarial de reposo MPM 3D

**Fecha:** 2026-11-22. **Dictamen:** **H12 NO APROBADA** como demostración de morfología 3D en reposo independiente del límite inferior. **Una sola condición fuerte preregistrada falló**; conservar el resultado y el job rojo. No modificar umbrales retrospectivamente. Etapa1 ABIERTA.
**Protocolo previo:** [ETAPA_1_H12_PROTOCOLO_REPOSO_MPM.md](ETAPA_1_H12_PROTOCOLO_REPOSO_MPM.md).
**Código:** [experiments/probe_e1_h12_mpm_settling.py](experiments/probe_e1_h12_mpm_settling.py).
**CI:** https://github.com/mxlzz/Nilo_public/actions/runs/45055570920 — **FAIL esperado por gate físico**, no error de instalación ni crash de solver. Versión PINNeAPPle upstream `c8a6e3dce5daedd10903cc68f7f3a062c42b8bc4`, Python3.11.18, PyTorch2.10.0+cpu y xarray2026.9.0.

## Escenario y controles

216 puntos, 5,4kg de material A abstracto, volumen inicial 0,15×0,15×0,15m, dominio 0,80×0,80×0,36m, dx0,025m. Modelo constitutivo Sand con E20.000Pa, nu0.3, rho1600kg/m³; fricción interna30° vs0°, gravedad−9,81 vs0, tiempos 0 / 0,4 / 0,8 / 1,2s. Se usó código upstream sin reimplementar ecuaciones, y no hubo paredes físicas laterales próximas al depósito activo.

### A, g y fricción interna30°

- Centro material z **0,1500m → 0,04113428m** en 1,2s (caída0,10886572m).
- Ancho x por cuantiles q01–q99 **0,31725931m** al final (entre x0,21637035 y x0,53362965), centro horizontal sin desviación neta.
- Entre t=0,8 y1,2s: variación de bordes q01/q99 de x/y **~0,002384m**, de q99 z **~0,002098m**, todos por debajo del límite preregistrado0,005m.
- Velocidad máxima final **0,025908m/s**, por debajo del límite0,05m/s; **cero puntos próximos a las paredes laterales**. Esto muestra ralentización y una envolvente casi constante durante la ventana estudiada.
- Altura por cuantiles q99–q01 z final **0,026569m**, apenas por encima de una celda de0,025m.
- **Fallo decisivo: 61,1111% de partículas quedaron exactamente en z=1,5dx=0,0375m**, que es el límite inferior impuesto por el propio solver (el código upstream recorta posiciones a `[1.5*dx, domain-1.5*dx]`). El gate previo exigía ≤50% para no confundir **clamp posicional** con soporte mecánico. Se reportó como falla y el workflow devolvió exit code1.

### Controles B/C

- **B sin gravedad**, con fricción interna30°, quedó exactamente inmóvil durante los 1,2s (posiciones/velocidades0 en diferencia).
- **C con gravedad pero fricción interna0°** presentó fuerte dispersión: 60 de216 partículas en banda de límite lateral al final, **84,7222% en floor clamp**, altura cuantil0,002635m y velocidad máxima1,85336m/s. No es depósito reposado. En t=0,4s incluso 100% de partículas estaba en cota mínima del clamp; no modelar como pila real. Su forma difiere fuertemente de A (media absoluta de posición0,09621m).
- Repetición A/A' produjo posiciones/velocidades exactamente iguales en los cuatro snapshots. Inventario total constante **5,400000000000001kg**, igual en casos y replay, SHA owner `09d67f7d207a5177cfd4f8ede72e4249c816d0d57605bda2c3436c32ce87fe36`.

## Interpretación y decisiones

**H12 verifica** sensibilidad a fricción constitutiva y ralentización de arena con fricción30° sin pared lateral. **NO verifica una estructura volumétrica físicamente estable**: alta fracción de clamp inferior, apenas una celda de altura y ausencia de validación de esfuerzos/contactos o resolución convergente. El código upstream impide bajar de z=1,5dx por diseño; una posición constante allí no prueba por sí misma soporte de presión ni consolidación. El fracaso es científico frente a un criterio previo, no un fallo del workflow; **no modificar el umbral ni retocar condiciones a posteriori para obtener PASS**.

**Próximo gate recomendado:** contrastar con una implementación especializada y con trayectoria científica independiente (por ejemplo GeoTaichi, MPM/DEM) antes de invertir en integrar PINNeAPPle con ROI H5. Preferir benchmark controlado de columna granular con datos de contacto/estrés/energía, runout o validación de malla. Hasta esa comparación, PINNeAPPle sigue siendo **candidato experimental**, no motor de terreno adoptado. Si una segunda implementación también depende de piso impuesto, habrá que definir soporte físico/condición de frontera a nivel del modelo y no confundir restricciones numéricas con emergencia. No abordar energía térmica ni vida aquí.

**Alcance actual:** H11 (deformación con masa conservada) permanece válido bajo sus condiciones cortas; H12 no lo invalida, pero **limita la conclusión de estabilidad**. Etapa1 ABIERTA; ninguna etapa 2–8 cerrada.
