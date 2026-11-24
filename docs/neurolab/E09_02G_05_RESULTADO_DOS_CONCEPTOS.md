# E09.02g.5 — resultado de discriminación contextual con seis unidades

**Corte:** 21/11/2026. [Pre-registro anterior al código](E09_02G_05_DOS_CONCEPTOS_PRE_REGISTRO.md). [CI #44934616857](https://github.com/mxlzz/Nilo_public/actions/runs/44934616857), commit probado `8c8d87a6e6c644f1a13c8c838d14435f9fc6fd0d`, `success`, **269 tests**, 2 expected failures de experimentos E09c/d, sin errores de software nuevos. El runner E09g.5 **reporta passed=false**; no confundir suite verde con gate científica superada. [JSON completo por semilla](resultados/run-44934616857/e09g5.json), guardado de stdout de la misma corrida.

## Diseño ejecutado

**Seis unidades P0,P1,C0,C1,D0,D1**, con dos detectores de una entrada cada uno, ocho sinapsis plásticas de Decision basadas en `dad1.gen` y operaciones de `Creatures.exe`. Se presentan dos estímulos abstractos S0/S1 en 32 bloques de 8 ticks por fase (16 de cada contexto), **orden equilibrado aleatorio por semilla**, por lo que no hay alternancia temporal trivial. En Fase A, S0 premia D0 y S1 premia D1; en Fase B se invierten ambos. Recompensa química proveniente del evaluador, no de metabolismo propio.

**Holdouts de 16 bloques**: 128 ticks totales; criterio primario STEADY solo los seis últimos ticks de cada bloque (96). Se reporta también exactitud total y transición inicial (dos primeros ticks).

Controles: misma red frozen, ablación visual ciega que siempre recibe S0, tabla Q 2×2 con trazabilidad de la acción y contexto causales. **La tabla posee memoria de procedencia que el modelo neuronal todavía no tiene**; no atribuir equivalencia informacional de los agentes.

## Resultado exacto (20 semillas)

| Modelo | Precisión steady fase A | Steady fase B | Precisión total fase A | Total fase B |
|---|---:|---:|---:|---:|
| Red neuronal de 6 unidades | **0.9671875** | **0.9302083333** | **0.8890625** | **0.8546875** |
| Frozen (sin plasticidad) | 0.5192708333 | 0.5114583333 | — | — |
| Blind (sin contexto) | 0.4994791667 | 0.496875 | — | — |
| Tabular Q 2×2 con crédito diferido correcto | **1.0000** | **1.0000** | **1.0000** | **1.0000** |

- Ventaja neuronal steady fase A vs frozen **+0.4479166667** y vs blind **+0.4677083333**, ambas superan el umbral preregistrado.
- Pero **solo 12/20 semillas** obtienen steady≥0.90 simultáneamente en A y B; el gate exigía ≥18/20. **E09g.5 NO SUPERADA.**
- Ocho semillas que incumplen la puerta conjunta: **0,2,3,4,8,16,17,19**; todas constan en JSON. Una sola asociación contextual puede causar la mayor parte del fallo (p. ej. semilla16, fase B: C0=1.0, C1=0.375 de precisión steady).
- El rendimiento medio por contexto cae en fase B: C0 de 0.96875→0.92083; C1 de 0.965625→0.93958.
- La diferencia entre steady y total es notable y sugiere que el **cambio de contexto y la persistencia de estado** son un obstáculo adicional; por sí sola no demuestra su causa.

## Interpretación crítica

**Demostrado experimentalmente:** con dos conceptos fijos y dos acciones, la red C1-reducida distingue contextos y adapta sinapsis a contingencias opuestas. Su ventaja frente a frozen/blind demuestra que no se reduce a azar, primer índice ni una preferencia universal.

**NO demostrado:** fiabilidad ≥90 % conjunta en suficientes semillas, creación autónoma de conceptos, continuidad cognitiva, motivación interna ni ventaja frente a tabla simple; la tabla tiene **100 %** en estas condiciones, con memoria causal de eventos y menor complejidad.

**No corregir post hoc** número de bloques, tasas químicas, estado80, política de empate, umbral90%, topología o selección de semillas. La etapa no se declara aprobada; cualquier ajuste debe ser una variante posterior con nuevo preregistro y pruebas comparables, preservando este resultado.

## Siguiente tarea con mejor retorno

**Diagnóstico descriptivo g.5a (posterior a observar resultados):** registrar errores por posición dentro de bloque, especialmente cuando cambia contexto, además de actividad previa, estados neuronales y STW/LTW en semillas fallidas. Declararlo **exploratorio/post hoc**, no convertirlo en evidencia confirmatoria. Comparar con la tabla que retiene contexto+acción de cada evento. Luego formular una hipótesis falsable para g.6 sin inventar nuevos mecanismos antes de localizar la causa.

**Bloqueos generales aún abiertos:** E05 de atribución causal de refuerzo demorado, G00-H de fidelidad total del motor C1, G09 de mente autónoma. Ninguna modificación en Nilo 0.7 o main.
