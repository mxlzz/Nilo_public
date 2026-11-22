# Etapa 3 — H19. Depósito conectado pero NO distinguible de plantilla inicial

**Fecha:** 2026-11-22. **DICTAMEN: H19 NO APROBADA para organización espacial no trivial.** La prueba completó física, ledger, controles, replay y persistencia; **un gate científico preregistrado falló**. No modificar nulo, estadístico, semilla ni umbral para obtener éxito. [Protocolo](ETAPA_3_H19_PROTOCOLO_DEPOSITO_CONEXO.md) anterior a código. [Script](experiments/probe_e3_h19_deposit_pattern.py). [CI 45060568065 FAILED por hipótesis física](https://github.com/mxlzz/Nilo_public/actions/runs/45060568065). Entorno Python3.13.18, Landlab2.11, NumPy2.5.5, SciPy1.18.1 y xarray2026.9.0.

## Resultado medido

Se continuó la cuenca H9 original sin modificar topografía, densidad, K_sed, erosión/depósito ni el inventario xarray (10.080.000kg iniciales), hasta t12 y t24 pasos. Se consideró depósito neto si masa en el nodo core superó su masa inicial por1e-6kg.

- **T12:** 50 nodos con ganancia neta, **una componente conectada de tamaño50**; sedimento exportado472.551,1385719963kg; masa almacenada9.607.448,861428004kg; mismo SHA del H9 aprobado.
- **T24:** **exactamente los mismos50 nodos** con ganancia neta, **una componente tamaño50**; Jaccard entre máscaras T12 y T24 **1,0**; exportación acumulada916.856,541741362kg; masa almacenada9.163.143,458258636kg. Hay cambio en cantidades, pero no en patrón binario.
- **Nulo no condicionado (512 permutaciones globales):** tamaño de mayor componente media6,918 y percentil95 **11**; el patrón de50 parece extraordinario **si se ignora** estructura de terreno.
- **Nulo preregistrado condicionado por fila (512 permutaciones, misma cantidad de depósitos por fila):** filas core con conteos **[11,12,13,14,0,0,0,0,0,0,0,0,0,0]**, mayor componente promedio**49,834**, percentil95**50**. El patrón observado también tiene componente50, no supera por +3 celdas el nulo exigente. **Falla crítica:** `large_connected_pattern_above_row_null95`.
- **Controles que sí pasaron:** balance de material en 24 pasos con error absoluto máximo1,86e-9kg, erosión y depósito positivos en los 24 pasos, `K_sed=0` sin cambios ni salida, replay exacto de T12/T24 y ledgers, cinco invalidaciones del owner rechazadas, NetCDF5308bytes recuperado con mismo hash. CI terminó exit1 **por gate físico**, no por error instrumental.

## Por qué es científicamente un resultado negativo

La **morfología binaria de depósito está localizada en las primeras cuatro filas** en estrecha relación con el escalón de espesor de suelo y el régimen espacial de la cuenca inicial H9. **La estructura en una sola mancha no es sorprendente al preservar esa heterogeneidad**: el nulo condicionado ya produce manchas casi completamente conectadas. Por tanto, no se puede inferir que interacciones locales hayan generado una organización diferenciada de la plantilla; la persistencia geométrica es real, pero el supuesto patrón «emergente» no se distingue de condiciones iniciales condicionadas.

Este resultado **no invalida** el transporte conservativo de H9 ni la causalidad pendiente/exportación de H18, que tenían otras hipótesis. Evita promocionarlos indebidamente a evidencia de emergencia. La elección de un nulo global solamente habría provocado un **falso positivo**.

## Próxima decisión

**Etapa3 permanece ABIERTA.** El experimento muestra que repetir Landlab/SPACE sobre esa misma cuenca no producirá por sí solo una nueva topología de depósito con el patrón binario ensayado, aunque cambien sus masas. [ADR-0010](DECISIONES/ADR-0010_E3_DEPOSICION_Y_CONTROLES_NULOS.md) indicaba evaluar un modelo **especializado** si el nulo condicionado no separaba la señal. Priorizar inspección documentada de pyDeltaRCM (MIT) u otra herramienta de patrones de depósito/ramificación existentes antes de ampliar física propia; no elegir una nueva física sin comparar costo, posibilidades y límites. Evitar declarar éxito con otra métrica inventada a posteriori.

No se tocaron main ni NeuroLab, ni se programó un solver de erosión.
