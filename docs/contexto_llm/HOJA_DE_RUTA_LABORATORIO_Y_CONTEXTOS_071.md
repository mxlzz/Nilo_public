# Nilo 0.7.1 — Hoja de ruta: laboratorio → contexto LLM → evaluación

**Fecha:** 2026-11-07  
**Estado:** propuesta de trabajo, no implementación aprobada.  
**Seguimiento:** [#70 — Laboratorio](https://github.com/mxlzz/Nilo_public/issues/70), [#31 — Contexto adaptativo](https://github.com/mxlzz/Nilo_public/issues/31), [#63 — Proyección cognitiva](https://github.com/mxlzz/Nilo_public/issues/63) y [#3 — Evaluación](https://github.com/mxlzz/Nilo_public/issues/3).  
**Referencias:** [auditoría del primer prompt y Claude](AUDITORIA_PROMPT_CLAUDE_2026-11-07.md), [propuestas externas](propuestas_externas/claude_2026-11-07/).

## Propósito

Desarrollar primero un laboratorio que permita **comprender las reglas efectivamente ejecutadas por el motor**, distinguir el estado físico de su proyección cognitiva y del cuerpo HTTP calculado; **marcar exclusiones propuestas** por secciones y exportar un paquete autocontenido para revisión. Usar luego la herramienta para corregir el contexto y evaluar variantes sin imponer objetivos a Nilo.

No confundir inspección de reglas con edición del motor; propuesta de exclusión con aplicación; prompt reconstruido con captura de una llamada realmente realizada; disminución del tamaño del prompt con mejora de autonomía.

## Fase A · Instrumental de laboratorio (hacer primero)

| Paso | Entregable | Criterio de cierre |
|---|---|---|
| A1 · Baseline de auditoría | Fixtures del primer HTTP real y turnos representativos (navegación, fabricación, ensayo, proyectos) con hashes, procedencia y versión; secretos excluidos. | Reproducción del payload capturado o explicación de divergencia; regresión sobre constructor actual. |
| A2 · Inspector de motor | Resultados de **Pruebas** en categorías desplegables: entrada, validaciones/reglas, estado físico antes/después, acciones, mediciones, diagnósticos, trazas y proyección. Los valores permanecen **literales**. | Expandir/cerrar secciones jamás modifica bytes/orden/valor del dato; cada explicación identifica la función/fuente real. |
| A3 · Inspector de contexto + checks | Árbol por campo/ruta de datos antes y después de proyección/presupuesto; marca explícita **«proponer excluir del prompt»** (secciones o campos). Campos obligatorios marcables para revisión, **no aplicables automáticamente**. | No muta mundo ni partida; distingue ausente, vacío, omitido por presupuesto, obligatorio y propuesto; independencia de selección UI respecto de valor bruto. |
| A4 · Exportar revisión | Botón superior: JSON versionado autocontenido con versión/commit, escenario/semilla/checkpoint, proveedor, rutas y valores, selección del usuario, efectos de presupuesto, payload calculado baseline y hashes; sin API keys ni datos externos innecesarios. | Exportado entendible sin sesión viva; validación del esquema, importabilidad para auditoría, prueba de no mutación. |
| A5 · Comparación A/B | Dos payloads HTTP **calculados localmente** del mismo estado (baseline y variante); diferencias por roles, secciones, rutas e información omitida y métricas de bytes/tokens disponibles. | La variante no altera la captura real, no dispara consultas ni modifica comportamiento por defecto; registrar qué cambia y por qué. |

La discusión detallada sobre la **columna derecha de Pruebas** se posterga hasta disponer de los componentes de inspección; no acoplarla a la instrumentación. Aprovechar **Visor LLM** para llamadas reales, **Ajustes** para perfiles experimentales y las rutas actuales de **Escenarios/Sandbox** sin duplicar motores.

**Integración con el plan de UI existente:** A2–A5 deben coordinarse con las subetapas previstas **04.3 Escenarios**, **04.4 Mundo interactivo/Sandbox**, **04.5 Ajustes** y **05 QA/packaging**, sin reemplazar o declarar terminadas 04.2 Historial ni otras ramas de interfaz. El visor conserva la semántica de capturas literales y no se reescribe como parte de este roadmap.

## Fase B · Mejoras del motor LLM (a partir de evidencias)

| Paso | Entregable | Criterio de cierre |
|---|---|---|
| B1 · Inconsistencias verificadas | Correcciones aisladas: `null` → `"None"`, `design.prediction`, plan de una operación, descripción `descend`, límites cuaderno, continuación dependiente de fallos y fugas numéricas de fisiología. | Tests de contratos y replay, sin inventar resultados físicos ni romper saves/agenda. |
| B2 · Contexto más pertinente | Política semántica de vacíos, referencias/IDs de evidencia, deduplicación sin perder proveniencia; `contexto_reducido` solo si hubo recorte; varios focos de relevancia. | Comparación A/B demuestra qué se incluyó/excluyó; ausencias importantes siguen explícitas. |
| B3 · Reglas modulares | Núcleo estable de identidad/autonomía/verdad física; catálogo breve pero **exhaustivo** de acciones; contratos y advertencias pertinentes al estado actual, proyecto, intentos y entidades; detalle recuperable sin agregar misiones. | Ninguna acción física vigente se vuelve invisible; Gemini/Groq conservan semántica; documentación no contradice reglas. |
| B4 · Respuesta estructurada | Prototipo opcional de schema, validación por operación y semántica, compatibilidad con agenda y proyectos; pruebas de truncamiento/reintentos; temperatura y máximo de tokens como experimentos separados. | JSON válido y ejecución consistente, con fallback seguro por proveedor; sin imposición arbitraria de planes extras. |
| B5 · Validación longitudinal | Runs LLM controlados en escenarios comparables: validez, errores, bucles, mantenimiento, proyectos, creatividad espontánea, memoria y consumo. | Conclusiones basadas en registros reales; decisión de aceptar/descartar ajustes con evidencias, no solo menos bytes. |

## Decisiones de alcance

1. No modificar `world`, registros SQLite ni la fisiología desde un checkbox; solamente preparar un expediente de propuesta para revisión.
2. La vista literal separa **motor interno**, **percepción/contexto** y **HTTP calculado**. Un dato interno no enviado al LLM no se trata como texto «a excluir».
3. No omitir indiscriminadamente valores `null`, `[]`, `0` o `false`: algunas ausencias y hechos negativos son necesarios.
4. No aplicar como norma la propuesta de Claude. Sus archivos sirven de referencia y sus ideas se integran solo después de contrastarlas con código y evidencia.
5. No confundir escenario determinista con una decisión autónoma real ni concluir «mejora» sin evaluación conductual.

## Estado de ejecución (actualizar en cada PR)

| Paso | Estado | Evidencia |
|---|---|---|
| A1 | En curso | Auditoría inicial de run y propuesta externa en PR #84; falta fixture reproducible completo. |
| A2 | Pendiente | — |
| A3 | Pendiente | — |
| A4 | Pendiente | — |
| A5 | Pendiente | — |
| B1 | Pendiente | — |
| B2 | Pendiente | — |
| B3 | Pendiente | — |
| B4 | Pendiente | — |
| B5 | Pendiente | — |

**Próximo paso de implementación recomendado:** A1 (fijar muestras y tests) y luego A2 (inspector por secciones con fuente de reglas), evitando iniciar B2/B3 antes de contar con un comparador reproducible.

> Este documento organiza la propuesta surgida de la conversación del 07/11/2026. Las prioridades y los límites pueden ajustarse; anotar toda variación aquí y en #70/#31.
