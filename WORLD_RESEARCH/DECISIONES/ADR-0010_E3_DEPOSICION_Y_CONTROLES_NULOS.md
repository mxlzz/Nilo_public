# ADR-0010 — E3: probar estructura sedimentaria existente antes de incorporar nuevo motor

**Fecha:** 2026-11-22. **Estado:** selección experimental reversible para H19, NO adopción de formación emergente. [Etapa3 en plan](../BASES_Y_HOJA_DE_RUTA.md) exige patrones **estables, no plantados**, conectividad, tamaño, ablación de reglas y comparación con azar. Las pruebas de E2 muestran deposición por Landlab, pero no muestran organización diferenciada de la plantilla inicial.

## Alternativas relevantes (reutilización temprana)

- **Landlab2.11 / SPACE + PriorityFlood** (MIT): [reusado con resultados propios H9](../ETAPA_1_H9_RESULTADOS_SEDIMENTO_OWNER.md) y [H18](../ETAPA_2_H18_RESULTADOS_GRADIENTE_SEDIMENTO.md), mide deposición/erosión con presupuesto de masa y estado validado. Es el **menor costo y mayor continuidad experimental**, pero sus patrones pueden depender trivialmente de la cuenca prescrita y del escalón artificial inicial de suelo. No probar «emergencia» solo porque haya nuevas capas.
- **pyDeltaRCM**, https://github.com/DeltaRCM/pyDeltaRCM, MIT, framework especializado en evolución de canales y depósitos deltaicos, con modelo de complejidad reducida y salida temporal. Ofrece un fenómeno geomorfológico más adecuado para deposición ramificada, pero necesita otra geometría y escala hidrodinámica y sería difícil comparar sin cambiar hipótesis. Se reserva para una brecha demostrada en Landlab; no está validado experimentalmente dentro de este proyecto.
- **scipy.ndimage.label** (BSD-3-Clause) y NumPy: análisis reproducible de componentes conexas, bordes y nulos aleatorizados **sin implementar física**. La conectividad es una medición descriptiva, no una fuerza que genera patrones.
- **Estructura prefabricada por plantilla o autoencolado programado ad hoc**: no aporta evidencia de organización espontánea; no utilizar.
- **Granular 3D MPM PINNeAPPle / GeoTaichi**: H12 dejó sin aprobar estabilidad volumétrica libre de clamp, H13A ni importó GeoTaichi; no justificar otra dependencia para responder el interrogante H19 de **sedimento superficial**.

## Decisión acotada

Prerregistrar **H19** como análisis de *deposición conectada y persistente* sobre el estado y solver H9, ejecutando más pasos con mismas condiciones. Comparar contra dos nulos: (a) permutación espacial simple con igual número de nodos depositados (control débil), (b) permutación **dentro de cada fila y entre celdas core** que conserva la tasa de deposición por y y controla la plantilla geográfica inicial de H9 (control exigente). Ningún nulo recibe reglas físicas. Registro de conectividad por 4 vecinos, Jaccard temporal, presupuestos, ablación K=0 y replay.

**Hipótesis abierta:** el depósito físico supera nulo condicionado y persiste. **Alternativa plausible y valiosa:** se forman manchas/filas totalmente explicables por el escalón inicial de suelo y la ruta de drenaje, por lo que H19 no validaría organización emergente; entonces no cerrar E3 y comparar otras soluciones solo si el objetivo lo exige.

**Limitación:** incluso si H19 pasa, conectividad y persistencia no equivalen a estructura física funcional, resistencia mecánica, autoorganización universal o evolución abierta. Para cerrar E3 se necesitará intervención causal/estabilidad comparada, no solo apariencia.
