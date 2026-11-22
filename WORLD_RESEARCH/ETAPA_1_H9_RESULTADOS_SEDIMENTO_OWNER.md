# Etapa 1 — H9. Transporte nativo de sedimentos hacia propietario material xarray

**Fecha:** 2026-11-22. **Dictamen:** **H9 APROBADA** como prueba de acoplamiento de datos y conservación de sedimento móvil en 2.5D. Etapa 1 **ABIERTA**; NO significa cierre de etapa 2, no constituye un mundo ejecutable, no demuestra emergencia.

**Protocolo previo y ejecutado sin alterar criterios:** [ETAPA_1_H9_PROTOCOLO_SEDIMENTO_OWNER.md](ETAPA_1_H9_PROTOCOLO_SEDIMENTO_OWNER.md).
**Código:** [experiments/probe_e1_h9_sediment_owner.py](experiments/probe_e1_h9_sediment_owner.py).
**CI verificada:** [GitHub Actions 45048479951](https://github.com/mxlzz/Nilo_public/actions/runs/45048479951) — **SUCCESS**, commit `82aff23d64524706178b115ce90dabb22630f9c4`.
**Entorno:** Python3.13.18; Landlab2.11.0; xarray2026.9.0; Linux Ubuntu24.04, instalación wheel binaria. Sin software físico propio.

## Resultado del gate

Una cuenca de 16×16 nodos, celdas interiores de 100m², material A ideal de densidad1200kg/m³, `K_sed=.1`, `K_br=0`, `phi=0`, `F_f=0` y 12 pasos `dt=.2` produjo:
- Inventario original **10.080.000 kg** de material móvil en owner xarray, frontera sin propiedad material.
- Inventario final **9.607.448,861428004 kg**, exportación observada vía API Landlab **472.551,1385719963 kg**. Suma **10.080.000 kg**; residual mostrado **0,0 kg**, tolerancia previamente fijada **0,1008 kg**. El balance no se calculó artificialmente desde la diferencia para inventar el sumidero.
- Hubo erosión y deposición con flujo positivo en los **12 pasos**. **50 nodos** con ganancia neta de material; cambio máximo del relieve derivado **0,32971769099331105 m**. Son datos de un banco artificial, no escala natural calibrada.
- En **control `K_sed=0`**, inventario exactamente inicial, exportación 0kg, 0 pasos erosivos/deposicionales, 0 nodos receptores y cambio de altura 0.
- Dos corridas activas repitieron exactamente arrays de masa y ledger. Se rechazaron cinco candidaturas inválidas antes del commit: material aparecido sin fuente, masa negativa, kg→g, masa en límite no propietario y salida negativa; el estado válido permaneció inalterado.
- Un archivo NetCDF de **5308 bytes** restauró el owner, unidades, topografía derivada y hash exacto. No almacena segunda capa de material como `soil__depth` ni `topographic__elevation`.

**Hash del estado final:** `9b930ea8b912a1d5ba2b8eef7027c264b7bfc2cf56de7387709191030b69a62a`.

## Qué se verificó y qué no

**Verificado:** un componente publicado de transporte fluvial de sedimentos puede reconstruir desde un owner de masa único su estado transitorio de profundidad, calcular erosión/transporte/deposición, medir descarga, validar balance global y publicar el candidato material resultante en cada paso. El control negativo y el replay distinguen dinámica real de variación arbitraria de arrays.

**No verificado:** conservación o acoplamiento en ROI 3D H5, transporte de granos individuales, resistencia y estabilidad de cavernas, mezcla de especies materiales, conservación de energía, densidades/porosidad variables, tiempo geológico calibrado, crecimiento dinámico de ROI, almacenamiento/reanudación del estado interno de Landlab (solo snapshot material) ni coordinación temporal con Bullet. Que cambie relieve no prueba que la materia forme estructuras emergentes.

**Decisión de alcance:** mantener Landlab como solución probada para sedimento fluvial 2.5D, sin inventar código de erosión ni extrapolarlo a colapso granular 3D. Para el siguiente fenómeno faltante, evaluar un solver granular/deformable real (GeoTaichi, Chrono u otro) con una prueba física diferencial y balance autoritativo, o justificar por qué no aporta valor antes de incorporarlo. No expandir infraestructura de formatos por inercia.

## Control de gobierno

El plan de etapa 1 aún requiere propiedades material/energía físicamente justificadas y transformaciones; la energía se incorporará solo en un experimento con ley e inventario precisos. Ninguna ley física nueva, modificación de `Nilo_public/main` ni integración NeuroLab realizada. H9 no sustituye los gates de etapas 2–8.
