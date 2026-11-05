# Auditoría integral del contexto que recibe Nilo — 2/11/2026

**Base auditada:** motor publicado `0.5.9.4.1`, sobre `main`. **Alcance:** contratos `action_contracts.py`, contexto `brain.context_for`, selector `compact_context`, `prompt_budget.bounded_context`, serialización final `build_deliberation_request`, versión corta Groq, Gemini y proveedor compatible, recuerdos, proyectos y validadores. Este informe NO corresponde a un run LLM nuevo y no demuestra causalidad conductual. El contexto real depende del estado de cada partida y del proveedor.

**Auditoría reproducible:** `python auditar_contexto_llm.py` (o `--json informe.json`). Construye escenarios sintéticos de partida inicial, proyecto de refugio, pausa y contexto saturado; ejecuta la MISMA preparación de payload usada por los proveedores con claves ficticias, sin efectuar llamadas de red. Reporta secciones enviadas/omitidas, bytes y presencia de señales, **sin conservar el contenido de conversaciones o prompts**. No equivale a comparar decisiones de modelos reales: #3.

## Resultados verificados en código

| Aspecto | Entrada real al LLM | Juicio / prioridad |
| --- | --- | --- |
| Necesidades corporales | `perceived_needs` entrega etiquetas; `_cognitive_needs_context` sanea legados también al final. La cifra se conserva en el motor y en mediciones voluntarias pertinentes. | **Conservar**. Buen patrón de separación percepción/medición. No retirar la cifra de una prueba solicitada. |
| Avance del proyecto | `normalize_decision` acepta `avance_estimado`; `plan_ready` lo guarda como `progress`; `compact_context` **preserva `proyecto_actual.progress`**. No equivale a avance físico verificado. | **Prioridad alta.** Evitar que 95 parezca un déficit pendiente hacia 100. Sustituir la proyección cognitiva por estado narrativo + hitos físicos pertinentes; conservar el porcentaje histórico/UI sin migraciones destructivas. |
| Refugios | `construcciones_fijas[].condicion_abrigo` contiene `cubierto_parcialmente` / `insuficiente`, derivados de componentes/resistencia, no de evaluación geométrica climática. El campo pasa al LLM si cabe en el presupuesto. | **Alta.** Comunicar `clasificacion_esquematica` y qué está o no verificado. No renombrar una condición interna como prueba de protección. Evitar romper la ventaja de descanso ya implementada. |
| Herramientas | `herramientas_que_llevo` incluye `durabilidad`, `componentes[].estado`, `usos_por_verificar` numéricos; `herramientas_de_excavación` incluye `potencia_excavar`. Algunos son resultados calculados del motor, no mediciones de Nilo. | **Media-alta.** Separar apariencia/desgaste observable, capacidad comprobada y predicción calculada. Mantener cantidades de inventario, IDs y resultados de ensayos cuando son conocidos. |
| Predisposiciones y exploración global | `context_for` incluye `predisposiciones` con valores 0–1 y `territorio_descubierto_pct`; `compact_context` **no** los selecciona normalmente para Gemini/Groq, pero la ruta `openai_compatible` **sin compresión** envía el contexto íntegro. | **Alta por divergencia entre proveedores, no por el último bucle Gemini.** No atribuir a porcentajes ausentes un comportamiento observado. Definir una única proyección cognitiva segura para todos los proveedores. |
| Historial y recuperación | `context_for` agrega `antecedentes_relacionados` y `investigaciones_pausadas_relacionadas` de 0.5.9.4.1, pero `prompt_budget._CORE` no los protege y el recorte final los puede descartar. | **Alta.** Mantener al menos el motivo de pausa cuando sea pertinente, incluso con Groq; comprobar preservación en payload saturado sin retener listas enormes. |
| Selección por tema | `context_focus` elige navegación/fabricación/experimento según palabras del proyecto, y protege más registros de ese foco; la selección no examina por sí misma contradicciones entre acciones/reintentos y objetivo. | **Media-alta.** Posible realimentación de interés, **hipótesis a medir**, no prueba causal del bucle. Recuperar también evidencias contrarias y límites comprobados. |
| Estancamiento de exploración | `nilo.py` incrementa `no_progress_steps` para `inspect/use/experiment/...`, pero no para `explore` o `go` fallidos; el detector semántico opera aparte, de modo informativo. | **Falla concreta de cobertura** (#2). Revisar señales basadas en resultado y frontera/objetivo, sin penalizar movimientos útiles ni imponer otra misión. |
| Interacciones espaciales | `interact` ya despacha módulos de contenido; `ascend`/`descend` siguen operaciones especiales, con prevalidación/navegación propias. | **Futuro #30 / 0.6**: pasar conexiones físicas (entradas, puertas, mecanismos) a capacidades de objeto, manteniendo `go` y `explore` independientes. No migrar APIs en este informe. |
| Instrucciones generales | SYSTEM, `ACTION_GUIDE`, `COMMON_RULES`, `GROQ_SYSTEM`, `SHORT_OPERATIONS` indican cómo actuar y evitar errores. No contienen una regla de explorar indefinidamente, pero requieren elegir plan con acciones y priorizan ejemplos concretos. | **Media.** Auditar frecuencia/saliencia de temas e instrucciones equivalentes entre proveedores. La existencia de una instrucción no prueba que cause una decisión observada. |
| Datos contables | Cantidades del inventario, IDs, fechas, posiciones y distancias de rutas conocidas pueden representar conocimiento directo o recuentos del personaje. Mediciones históricas llevan procedencia. | **Conservar números útiles**, con unidades, origen y condición de observabilidad; no aplicar una regla universal «eliminar todos los números». |

## Distinción obligatoria al rediseñar la proyección cognitiva

- **Percibido:** rasgo observable o sensación derivada; puede ser cualitativo. No declarar medido lo que no lo está.
- **Recordado/comprobado:** resultado real de una acción con procedencia; si tiene medida e ID válido, conservar número, unidad, objeto, versión y condiciones.
- **Hipótesis propia:** formulación de Nilo, jamás promovida a ley por la redacción.
- **Estado exclusivo del motor:** recursos, scores, umbrales, cobertura esquemática y verificaciones físicas internas; no exponer directamente si Nilo no puede conocerlos.
- **Limitación de la simulación:** indicar fenómeno y método no evaluables, sin afirmar éxito o fracaso. Se debe poder reformular, pausar o abandonar el proyecto.

## Orden de cambios propuesto, sin patch automático

1. Crear una **proyección cognitiva tipada y única** justo antes de serializar, reutilizable en Gemini, Groq y compatible; mantener telemetría/observador numérica. No interceptar por buscar números indiscriminadamente: cambiar los campos semánticos de origen.
2. Reemplazar `progress` del proyecto por hechos y estado cualitativo; distinguir contador de acciones de prueba de avance demostrado. Verificar proyectos ya al 95 % y cierre sin evidencia.
3. Transformar presentación de construcciones y herramientas en percepciones / hechos probados, especialmente `shelter_condition`, durabilidad y potencias. No filtrar valores calculados internos como experimentos que nunca ocurrieron.
4. Proteger memoria de abandono/pausa pertinente al presupuesto mínimo y ofrecer contradicciones históricas breves; comparar el contenido **después** de `bounded_context`, no antes.
5. Tratar reiteraciones de `explore` fallidas como evidencia estructurada (sector, frontera y resultado) y dejar al LLM decidir qué hacer. Evaluar oportunidades conocidas que no se exploraron (por ejemplo, entradas a cueva) sin imponerlas como objetivos.
6. Extender `interact` a conexiones espaciales dentro del alcance modular de 0.6, con pruebas de replay y de equivalencia de comportamiento.

## Criterios de comprobación

- Para todos los proveedores: mismo principio de observabilidad, sin barras fisiológicas ni scores internos; números permitidos solo cuando representen percepción cuantificable, inventario contable, navegación o medición auténtica.
- Bajo presupuesto mínimo de Groq: el motivo de pausa/cierre relevante no se pierde por contener una lista de resultados recientes; ninguna evidencia se recorta a media frase para que parezca otra.
- Un `inspect` repetido no constituye prueba de resistencia o de protección climática; un `rest` saturado tampoco. Cierres respetan IDs y propiedades instrumentadas.
- Proyecto sin avance y territorio agotado: permitir `design`, `wait`, `sin_proyecto` y cambios de interés; **no** introducir tareas por cuota, ni castigar descanso legítimo.
- CI determinista comprueba proyecciones y metadatos; dos corridas comparables con LLM según #3 serán necesarias para hablar de reducción de bucles, autonomía o creatividad.

## Decisiones de alcance

Este PR **solo introduce la auditoría y su prueba reproducible**. No cambia física, pesos del LLM, claves, normalización, modelos, interfaz, comportamiento ni versión `0.5.9.4.1`. Las correcciones conductuales se implementarán agrupadas con pruebas y con un versionado coherente; priorizar **representación perceptiva y continuidad** antes de añadir nuevos sistemas anti-loop. Referencias: #2, #3, #5, #8, #20, #31, #50, #62 y #30.
