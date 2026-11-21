# E09.02g.5a — diagnóstico temporal exploratorio (post hoc)

**Fecha:** 2026-11-21. **Carácter:** exploratorio; se inició después de observar la falla de E09g.5. **NO** modifica el preregistro, los criterios, las semillas ni la red de E09g.5.

**Evidencia ejecutada:** [Actions #44934965506](https://github.com/mxlzz/Nilo_public/actions/runs/44934965506), HEAD `ac610b25c6e9f8afd73665db5687604a6fd76cfc`, job `136939486819`, paso «E09g5a exploratory temporal context diagnostics». Se ejecutó `python -m experiments.neurolab.e09_context_diagnostics` y la suite completa resultó `success`. El JSON por tick también quedó en los artefactos de Actions (retención limitada); se extraen aquí los indicadores relevantes del log real. El diagnóstico verifica paridad de precisión *steady* contra `e09_context_protocol.evaluate_brain` para las 20 semillas.

## Hallazgos descriptivos

| Posición dentro del bloque (0–7) | Fase A, precisión media | Fase B invertida, precisión media |
|---|---:|---:|
| 0 | 0.453125 | 0.468750 |
| 1 | 0.856250 | 0.787500 |
| 2 | 0.906250 | 0.878125 |
| 3 | 0.940625 | 0.896875 |
| 4 | 0.975000 | 0.918750 |
| 5 | 0.984375 | 0.943750 |
| 6 | 0.996875 | 0.965625 |
| 7 | 1.000000 | 0.978125 |

- Precisión media del **primer tick después de cambio de contexto**: fase A `0.000000`, fase B `0.011111`. **Primer tick después de bloque del mismo contexto**: `1.000000` y `0.975000`, respectivamente. La agregación promedia por semilla; no confundir estos valores con una prueba causal de la fuente del fallo.
- `steady` (= posiciones 2–7): fase A `0.9671875`, fase B `0.9302083333`; se reproducen exactamente los promedios del ensayo original E09g.5.
- Semillas que no alcanzan ambas puertas individuales ≥0.90: **0, 2, 3, 4, 8, 16, 17 y 19**. No se descartó ninguna.
- **Persistencia que no explica solo la latencia inicial:** en semilla 16 fase B, precisión steady `0.6875`; las posiciones 1–7 del holdout alcanzan apenas `0.6875` cada una y la precisión total del contexto S1 es `0.328125`. Las trazas muestran que se sigue eligiendo D1 en S1 a lo largo del bloque aunque la contingencia invertida exige D0. Para semilla 2 fase B, posiciones 1–4 en `0.6875`, con recuperación a `1.0` recién en posición 7. Estos patrones indican errores sostenidos, no exclusivamente el retraso de un tick.
- La neurona Decision utiliza la activación de Concept del tick anterior y un estado de decisión persistente. **Hipótesis aún no verificada:** el retraso sensorial, la persistencia del estado y/o una asociación sináptica insuficiente podrían explicar partes diferentes del fallo. El informe presente no distingue causalmente esas explicaciones.

## Interpretación y límites

1. El retardo transitorio al cambiar de contexto es real; no es un artefacto del redondeo del indicador global.
2. La persistencia de errores en S1 de algunas semillas descarta la explicación **«todos los errores son exclusivamente del primer tick»**.
3. E09g.5 sigue **NO APROBADA (12/20)**; la suite verde significa integridad de ejecución, no éxito científico.
4. El control tabular 2×2 conservó ventaja clara, pero dispone de cola causal explícita y exploración; su comparación no aísla la causa de la diferencia.
5. No se agrega todavía ninguna neurona, cuerpo, mundo, LLM ni nueva política de aprendizaje. El motor de Nilo sigue intacto.

## Próxima unidad verificable: E09g.6

Pre-registrar un **diagnóstico pareado de reinicio de estado y precarga de Concept solo en la evaluación**, conservando sinapsis y entrenamiento de E09g.5. El factorial 2×2 separará el efecto de memoria dinámica de Decision y el de la latencia de Concept, comparando con el control original en las mismas 20 semillas y secuencias. Cualquier beneficio será atribuido **a una intervención de laboratorio en el holdout**, no a una mejora cognitiva de C1 ni a una solución de crédito causal. Posteriormente estudiar crédito diferido de manera específica, sin inferirlo de este resultado.
