# E09.02g.8 — resultado de supresión de pulsos desalineados vs control temporal

**Fecha:** 2026-11-21. **Preregistro anterior al código:** [E09_02G_08_PULSOS_PAREADOS_PRE_REGISTRO.md](E09_02G_08_PULSOS_PAREADOS_PRE_REGISTRO.md). **Ejecución verificada:** [Actions #44938791056](https://github.com/mxlzz/Nilo_public/actions/runs/44938791056), commit `7732e5eb18e89e690f940f85e51cbe2c60d5e366`, job `136951193530`, conclusión **success**. Resultados por semilla en `metrics/e09g8.json` del artefacto `neurolab-metrics` (retención limitada). Se reprodujeron exactamente las medias y la falla 12/20 del control original E09g.5.

## Tres brazos congelados

- **C:** pulso químico original.
- **G:** omitir solo pulso de posición 1 (segundo tick) cuando cambia contexto.
- **S:** omitir igual cantidad de pulsos, en posición 2 de los mismos bloques (control temporal).

Se omitieron **319 pulsos no nulos por brazo G/S en A** y **333 por brazo en B** (652 total, como eventos desalineados en g.7). Mismas 20 semillas 0..19, bloque, tasas, red y holdouts de g.5; ninguna alteración en `C1ContextBrain`.

## Resultados observados

| Condición | Steady A | Steady B | Total A | Total B | Semillas ≥0.90 en ambas |
|---|---:|---:|---:|---:|---:|
| C (original) | 0.9671875 | 0.9302083 | 0.8890625 | 0.8546875 | **12/20** |
| G (omitir desalineados) | 0.9770833 | **0.9614583** | 0.8730469 | 0.8699219 | **16/20** |
| S (omitir adyacentes) | 0.9697917 | 0.9322917 | 0.8906250 | 0.8570313 | **13/20** |

- Diferencia G−S media de `steady`: **+0.0072917 A**, **+0.0291667 B**. La regla orientativa preregistrada exigía **B≥+0.0300** y A≥−0.0200: **NO SUPERADA** (B queda por debajo). No se rebaja el umbral ni se redondea para convertir el resultado en éxito.
- Frente a C en fase B: G +0.03125, S +0.0020833.
- Coste de transición: exactitud `early` A/B de C `0.6546875/0.628125`, de G `0.5609375/0.5953125`, de S `0.653125/0.63125`. Suprimir feedback desalineado **empeora** respuestas tempranas de la fase A y B frente al sham.
- Heterogeneidad: semilla 2 B, C `0.770833`→G `0.947917`→S `0.770833`; semilla 16 B, C `0.6875`→G `0.791667`→S `0.6875`; semilla 17 B **no mejora** (`0.895833` en los tres). No seleccionamos una sola semilla como representante del conjunto.

## Interpretación crítica y decisión

Existe una **señal direccional favorable al filtrado temporal** en `steady` de B, superior al control de igual cantidad de pulsos. Pero la puerta práctica fijada de antemano **falló**; 16/20 sigue por debajo de 18/20 y hay un coste real en respuestas iniciales. Este resultado no demuestra solución completa de crédito causal ni justifica insertar una regla externa de supresión en C1.

El ensayo prueba que el momento del refuerzo importa; no distingue todavía si una capacidad autónoma de recordar qué conexiones produjeron la decisión resolvería mejor el problema. **No** es emulación fiel del Norn ni argumento para aumentar neuronas.

**Siguiente inversión justificada y acotada:** replicar la comparación **sin recalibración** en un lote independiente de semillas no usadas en diseño/diagnóstico (20..99), preservando A/B, G/S y evaluación. Si no se replica, registrar resultado negativo y detener ajustes del banco de dos contextos; si se replica, evaluar si merece prototipo de atribución interna frente a la tabla 2×2. Ninguna fusión a main ni cambios de Nilo.
