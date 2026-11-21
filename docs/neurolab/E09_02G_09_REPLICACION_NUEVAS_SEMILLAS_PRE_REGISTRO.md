# E09.02g.9 — preregistro de replicación fuera de muestra (80 semillas nuevas)

**Fecha:** 2026-11-21, registrado **antes** de implementar y ejecutar g.9. Es una extensión de validación de los tres brazos **ya congelados** en [g.8](E09_02G_08_PULSOS_PAREADOS_PRE_REGISTRO.md), no otro ajuste de una fórmula ni una prueba independiente en un entorno externo.

## Antecedente no aprobado

En g.8, semillas 0..19, `steady_B(G)-steady_B(S)=+0.02916667` pero el criterio práctico `>=+0.03` **no se cumplió**; también hubo perjuicio en precisión `early`. G.8 sigue negativa según su puerta preregistrada. No redondear ni tratar g.9 como reparación de g.8.

## Congelación prospectiva

- **80 semillas nuevas, 20..99 inclusive**, excluyendo estrictamente 0..19 utilizadas en g.5–g.8; selección secuencial fijada antes de ver resultados.
- Se llama la función **inalterada** `e09_paired_pulse_protocol.run_seed` con cada semilla. Mismas 6 unidades, 8 sinapsis, genes/rates de C1, pulsos C/G/S, 32 bloques balanceados×8 ticks por fase A/B, 16 bloques×8 en holdout, orden relativo con PRNG `seed + salt`, criterio `steady` últimos 6 ticks, WTA y corrección A→B. No recalibrar ni retocar parámetros.
- No se incluirá esta nueva serie en el resultado previo de 20 semillas para cambiar su gate; se publican ambas por separado.
- Control de integridad: G y S tienen igual número de omisiones programadas y no nulas por fase; C nunca omite; cada semilla tiene 2 fases×3 brazos. Pruebas de determinismo y de no solapamiento de semillas.

## Métricas y puertas antes de ejecutar

1. **Primaria:** diferencia pareada por semilla `steady_B(G)-steady_B(S)`. Reportar media, mediana, mínimos/máximos y número de semillas con delta positiva/negativa/nula, más intervalo bootstrap percentil al 95 % con **4.000 réplicas**, semilla de remuestreo `20261121` y remuestreo pareado de 80 semillas con reemplazo.
2. **Secundarias:** diferencia `steady_A(G)-steady_A(S)`, mejora frente a C, `early` y exactitud total A/B, fracción de semillas con `steady>=0.90` en A y B simultáneamente para C/G/S, conteos de supresiones, y distribución de deltas (no solo medias).
3. **Apoyo direccional fuera de muestra (no prueba definitiva de mecanismo):** intervalo bootstrap de diferencia media B **completamente > 0**.
4. **Relevancia práctica del umbral original:** media B **≥ +0.03** y media A **≥ −0.02**. Registrar ambos criterios como distintos. No bajar umbrales, no rerun de submuestras hasta encontrar aprobación.
5. Incluso con ambos criterios favorables, seguirán abiertas G05/G09: G y S tienen información externa de fronteras, y no es prueba de que el Norn pueda hacer internamente esas operaciones.

## Política de continuidad

Si la ventaja no se reproduce fuera de muestra, detener el ajuste ad hoc de feedback en el banco S0/S1 y volver a estudiar el reloj histórico/mecanismos internos con un diseño diferente, sin declarar g.8 superada. Si se reproduce, **no** implementar de inmediato un oráculo como regla neuronal: redactar una comparación explícita entre (a) memoria causal interna mínima, (b) concepto temporal intrínseco y (c) controlador tabular más económico. Decidir después si merece desarrollo.
