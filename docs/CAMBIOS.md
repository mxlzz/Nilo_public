## Nilo 0.6.4 · Laboratorio comprensible y solicitud íntegra al LLM (3/11/2026)

- Se consolidaron catálogo y condiciones en la columna izquierda; la derecha usa secciones desplegables con **«Qué recibe el LLM»** abierta primero. Se retiraron el contador de 68 escenarios y el botón «Ejecutar todos» de la interfaz; el catálogo sigue ejecutándose completo en CI.
- La nueva vista muestra **valores del contexto** antes/después, instrucciones del sistema y mensaje del usuario, roles reales de Gemini/Groq y el **cuerpo JSON serializado** por `brain.build_deliberation_request`. Se reconstruye sin credenciales ni red y se puede contrastar lo que se filtró.
- Se añadieron ayudas (?) para normalización, validación, ejecución por ticks, mediciones, trazas y diagnóstico. Se distingue expresamente información **interna del motor** de datos proyectados al LLM.
- `laboratorio_contexto.py` reconstruye el contexto con los mismos argumentos que `Simulation.think` (últimos 16 eventos, conversaciones recientes y regla de comentarios humanos); las nuevas pruebas verifican valores, roles, bytes y serialización.
- **Sin cambios de física, memoria o autonomía del personaje.** La ruta real todavía puede seleccionar otro modelo por fallback; la vista informa cuál se está simulando.

## Nilo 0.6.3 · Laboratorio histórico y puntos de restauración (3/11/2026)

- **Nueva vista `/historico`** del laboratorio: cargar una partida SQLite, navegar mediante slider por decisiones y acciones, inspeccionar registros originales y filtrar momentos.
- **Checkpoints observacionales:** antes de procesar cada deliberación y antes de iniciar cada acción, Nilo almacena el estado anterior completo, RNG local/global, comando y versión en tabla separada `timeline_checkpoints`, comprimida y con SHA-256. No aparece en la memoria del personaje ni modifica sus decisiones.
- **Replay aislado:** restaura un checkpoint en SQLite temporal, ejecuta `Simulation.plan_ready` o `Simulation.tick` y muestra variaciones físicas, trazas de código y comparación de resultados históricos cuando existe relación documentada. Permite modificar la orden para comparar alternativas.
- **Compatibilidad:** las partidas antiguas se muestran como registros históricos **sin replay exacto** si falta el estado anterior. Nunca se reemplaza una partida con su reproducción. La carga desde el navegador copia el archivo local en un directorio temporal; el original se abre en modo solo lectura.
- **Limitaciones:** no se vuelve a generar la decisión de Gemini/Groq; no están capturados todos los UUID, factores de reloj real o intervenciones externas. El motor instalado puede diferir del motor registrado. El historial de checkpoints incrementa el tamaño del SQLite, sin política de poda automática.
- **Sin nuevas leyes físicas, metas o notificaciones de mundo.** [Documentación](LABORATORIO_HISTORICO.md).

## Nilo 0.6.2 · Banco de escenarios y ciclos reales del motor (3/11/2026)

- **Nuevo laboratorio principal:** 68 casos declarativos, agrupados en 8 familias: desde una acción elemental a varios pasos, validación, ejecución por ticks, experiencias y proyectos. Cada caso incluye su fixture explícito, orden LLM preparada, veredicto y mediciones.
- **Motor auténtico:** los escenarios y el sandbox manual pasan por `brain.normalize_decision`, `Simulation.plan_ready` y `Simulation.tick`, con SQLite temporal. Se conserva la lógica real de validación, tiempos, necesidades, navegación, resultados, memoria y archivo; no se duplican reglas físicas.
- **Trazas y diferencias:** secuencia de funciones realmente invocadas con breves explicaciones y líneas de código desplegables. Resultado antes/después, inventarios, necesidades, proyecto y contexto cognitivo filtrado.
- **Controles por botones:** 26 operaciones, con opciones para método, destino, forma y materiales, que permiten crear planes de hasta 12 pasos. JSON avanzado es opcional; el laboratorio de acciones antiguas sigue en `/sandbox`.
- **Cobertura automatizada:** prueba de todo el catálogo contra resultados esperados y regresión de sintaxis JS; los escenarios detectan limitaciones actuales en vez de fingir capacidades. Sin llamadas LLM ni modificaciones de partidas.
- **Sin cambios físicos ni cognitivos de Nilo:** permanecen pendientes `go` por nombre, `gather piedra` probabilístico, memoria 5×5 y cualquier revisión del estancamiento; este lanzamiento solo actualiza herramientas de auditoría.

[Documentación técnica y límites](LABORATORIO_ESCENARIOS.md).

## Nilo 0.6.1 · Laboratorio interactivo del motor (3/11/2026)

- **`ABRIR_LABORATORIO.bat`** inicia un servidor local independiente (`127.0.0.1:8766`) con botones para elegir las operaciones de Nilo, mapa seleccionable, resultado real y diagnóstico físico de cada acción.
- **`laboratorio_motor.py`** ejecuta las mismas funciones del motor real en una **copia aislada en RAM**, obtenida desde un mundo nuevo o desde el último snapshot guardado. No usa proveedores LLM ni escribe sobre la partida original.
- **Trazas reales:** instrumentación de las llamadas a funciones y líneas de Python ejecutadas, descripciones muy breves y enlaces a su ubicación en GitHub. Permite inspeccionar el contexto reducido que habría recibido Gemini o Groq sin contactar APIs.
- **Límites expresos:** el reloj/las necesidades se actualizan por duración de la operación; no se reproduce la planificación completa, los ticks intermedios, la agenda, el archivo de eventos de la aplicación principal ni el comportamiento autónomo. Los formularios cubren operaciones disponibles, con JSON avanzado opcional.
- **Sin cambios de física:** el 33 % de recolección manual de piedra, `go` por nombres, la percepción 5×5 y los nuevos mecanismos de memoria siguen como diseño y NO están implementados.

## Nilo 0.6.0 · Primer corte funcional: construcciones que soportan cargas (2/11/2026)

**Alcance:** primer corte físico de 0.6; capacidades materiales nuevas, sin afirmar completada toda la física composicional. Refs #8, #30, #5, #45.

- Segundo módulo físico independiente `structural_loads.py`, instalado en el registro cerrado de capacidades: `cargas_estructurales` v1.0.0. `interact` dispone de `probar_carga`, `depositar_carga` y `recuperar_carga` para **obras fijas accesibles** por ID.
- La capacidad de soporte depende de la resistencia de los componentes reales, su desgaste, geometría de plataforma/macizo/hueco y relación tamaño/piezas. Renombrar una obra no cambia la carga admisible. El resultado usa unidades abstractas; **no** certifica seguridad estructural, cerramientos ni clima.
- `probar_carga` exige muestras materiales presentes, ensaya una carga adicional sobre la ya almacenada, registra tanto éxito como sobrecarga mediante evidencia física, sin consumir ni duplicar muestras. Nilo no conoce el límite numérico antes de medirlo.
- `depositar_carga` descuenta lotes del inventario y los conserva en la obra hasta `recuperar_carga`; el motor rechaza sobrecargas, cantidades inválidas y obras lejanas sin modificar inventarios. Una modificación o desmontaje no puede hacer desaparecer la carga ni dejar capacidad insuficiente: antes hay que recuperarla o reforzar la obra.
- Las mediciones de carga se vinculan a la **revisión física** ensayada. El contexto perceptivo comunica materiales almacenados y ensayos efectivamente efectuados, nunca capacidad estructural no medida; se conserva la memoria SQLite de versiones anteriores.
- Pruebas de materialización, conservación, resultado negativo auténtico, modificaciones con recursos, invariancia de nombres, limitaciones de distancia, compatibilidad del módulo, contexto y guardado/reapertura. Se conserva el `interact` de recipientes y las operaciones históricas; no se imponen misiones ni una tasa de invenciones.

**Ejemplo comprobable:** construir una obra fija `geometry.shape="plataforma"` con dos unidades de madera; `interact/probar_carga` con `item` (ID de esa obra), `material="piedra"`, `quantity=4`; reforzar con `modify/add` y volver a ensayar. Se puede depositar y recuperar material real tras una prueba satisfactoria.

**Límites pendientes:** estructuras sin modelo 3D, sin colapso dinámico ni deformación, sin nuevas conexiones transitables; observar a Nilo elegir espontáneamente un proyecto con esta capacidad requiere una corrida LLM. Sigue pendiente expandir `interact` a conexiones ambientales, reconocimiento perceptivo de materiales y revisión de estancamiento de `explore`. La 0.6 continuará por cortes físicos, sin parches indefinidos de contexto.

---

## Nilo 0.5.9.4.2 · Proyección perceptiva del contexto LLM (2/11/2026)

**Alcance:** primer corte implementado del [#63](https://github.com/mxlzz/Nilo_public/issues/63), resultado de la [auditoría de contexto](AUDITORIA_CONTEXTO_LLM_2026-11-02.md), PR `referencia privada #131`. La física del mundo, la memoria SQLite y el cálculo de necesidades permanecen sin cambios.

- `cognitive_projection.py`: vista del personaje diferenciada del estado del motor, sin mutar los registros; aplicada antes de serializar deliberaciones de Gemini, Groq y OpenAI-compatible, así como el chat. Ningún proveedor recibe scores internos solo por omitir el modo compacto.
- Los proyectos ya no presentan a Nilo `progress` numérico estimado; reciben estado, resultados físicos registrados, IDs de evidencias y motivos de pausas. La UI/historial puede seguir mostrando ese valor sin validarlo como prueba.
- Las construcciones tipo habitáculo se presentan sin `condicion_abrigo` esquemática que sugiera protección climática validada; se indica expresamente que esa protección no está evaluada. Los planos siguen siendo esquemáticos.
- Las herramientas presentan desgaste como descripción orientativa; las potencias y usos predichos por el motor no se exponen como mediciones comprobadas. Las cantidades de materiales, dimensiones de esquemas y ensayos reales continúan identificables.
- Un antecedente pertinente de proyecto pausado con su motivo se conserva en el núcleo del contexto incluso bajo presupuesto Groq. No obliga a retomarlo ni a dejarlo.
- Se corrige un sesgo: investigar un **refugio** sin investigar recuperación de energía deja de activar automáticamente la telemetría especializada del descanso.
- Pruebas de contexto sobre estado normal, saturado, versiones heredadas y tres rutas de proveedor. El auditor `auditar_contexto_llm.py` incorpora el antecedente derivado; sin credenciales ni llamadas de red.
- **Pendiente de comprobar en run LLM real:** reducción de bucles, cambios espontáneos de interés, preservación de oportunidades fuera de contexto. El cambio no introduce tareas ni una cuota de creatividad. La reconsideración de `explore` fallido (#2) y el `interact` ambiental (#30/0.6) siguen pendientes.

---

## Nilo 0.5.9.4.1 · Corrección del bucle de validación de refugios (2/11/2026)

**Origen:** corrida real de 0.5.9.4 en la que Nilo vuelve repetidamente a inspeccionar y descansar junto a un refugio sin conseguir una prueba funcional. Esta corrección es del **motor y la memoria contextual**, no del ajuste visual pendiente en #51.

- **Continuidad por identidad física:** una construcción creada en un proyecto previo se reconoce al verificar un proyecto posterior que la modifica, pero solo con IDs de obra coincidentes en mediciones verificadas; no basta el nombre.
- **Cierre conservador:** construir, modificar o inspeccionar registra hechos distintos. Una mejora funcional o una protección climática no se acreditan por el número de piezas, ni por una inspección, ni por descansos saturados. Los objetivos que dependen de propiedades no instrumentadas reciben una causa explícita en `ultimo_cierre_rechazado`.
- **Memoria de decisiones:** nuevas deliberaciones reciben antecedentes relevantes de proyectos e investigaciones pausadas, incluidos sus motivos; se preservan también en el contexto reducido. Crear un proyecto relacionado no lo convierte automáticamente en continuación ni obliga a abandonarlo.
- **Regresión:** tests sobre continuidad entre proyectos, IDs físicos, no-evaluabilidad de abrigo, construcción simple de refugio y recuperación contextual de pausas.
- **Límites:** no introduce clima, protección geométrica, nuevos fenómenos físicos ni impide repetir actividades legítimas. La eficacia conductual debe evaluarse con una nueva corrida LLM comparable (#3); la estructura de la física de refugios pertenece a 0.6 (#8).

PR `referencia privada #128` (`referencia-historica-privada-pull-128`).

---

## Nilo 0.5.9.4 · Corridas comparables y evaluación reproducible (2/11/2026)

**Alcance:** [#3](https://github.com/mxlzz/Nilo_public/issues/3), con evidencia pertinente para [#2](https://github.com/mxlzz/Nilo_public/issues/2), [#50](https://github.com/mxlzz/Nilo_public/issues/50) y preparación observacional de 0.6.

- **`evaluar_corridas.py`**: lectura **solo lectura** de uno a ocho SQLite (snapshot, archivo histórico, sesiones, usos de modelos), informe JSON/Markdown; métricas de exploración, experimentación, mantenimiento, resultados físicos y evidencia antigua disponible. Compara partidas con avisos de falta de condiciones equivalentes; no pretende inferir mejoría ni causalidad por un puntaje.
- **Origen auditable** de nuevas acciones: si consta, `llm`, `demo`, `agenda`, `espera`, `rutina` o `motor`; `desconocido` para acciones antiguas. Añade a los diagnósticos de `explore` orientado tramos recorridos y casillas reveladas, sin cambiar navegación.
- **`run_history.py`**: cada sesión nueva incorpora la semilla **RNG efectiva** y SHA256 del estado físico inicial, además de versión, entorno, modelo real y tramo simulado. La migración agrega columnas opcionales sin reconstruir valores antiguos; los replays históricos no reciben cambios retrospectivos de su secuencia.
- **Conserva** las reservas actuales y el motor físico de 0.5.9.3.35; no agrega recompensas artificiales, proyectos, objetivos ni llamadas LLM. Puede ejecutarse sin conexión a proveedores.
- **Tests** con bases SQLite temporales, solo lectura, huellas, resultados por origen, versiones mixtas, datos antiguos y avisos de comparabilidad. CI además conserva replays deterministas y escenarios físicos.
- **Límite:** el informe cuenta `diagnostic` para acciones físicas archivadas; no incluye cada acto documental. Una misma semilla y hash inicial no garantizan respuestas iguales de un LLM externo. **Todavía no se evaluó el comportamiento de .4 con corridas nuevas controladas.**

Uso: `python evaluar_corridas.py "partida_A.sqlite3" "partida_B.sqlite3" --json informe.json --markdown informe.md`. Protocolo completo: [PROTOCOLO_EVALUACION_0594.md](PROTOCOLO_EVALUACION_0594.md).

---

## Nilo 0.5.9.3.35 · Exploración dirigida y cardinales verificados (2/11/2026)

**Alcance:** [#60](https://github.com/mxlzz/Nilo_public/issues/60) y [#26](https://github.com/mxlzz/Nilo_public/issues/26), con casos verificables para el protocolo de [#3](https://github.com/mxlzz/Nilo_public/issues/3).

- `explore` **sin parámetros** conserva la selección de frontera aleatoria anterior, sus penalizaciones de recorrido/visitas y el estado RNG para compatibilidad de partidas y replays antiguos.
- Nilo puede elegir `{"op":"explore","direction":"north"}` (north/south/east/west; alias castellanos aceptados) y/o `{"region":{"x":14,"y":9}}`. La región debe ser una **casilla ya conocida del mismo nivel** y actúa como anclaje, sin convertirse en destino oculto ni revelar su contenido.
- Con dirección sola, el sector es relativo a la **posición de Nilo**; con región y dirección, es relativo al **anclaje conocido**. Si no existen fronteras transitables y alcanzables del sector indicado, devuelve diagnóstico explícito y **no sustituye** el rumbo por el contrario.
- El motor sigue eligiendo rutas `known_only`, respetando obstáculos, agua y nivel; ejecuta pasos de tres minutos progresivamente, con revelado local y rastro real. En un resultado orientado registra dirección solicitada, frontera escogida, tramos recorridos, desplazamiento neto cardinal y casillas observadas; una intención textual no se convierte en resultado físico acreditado.
- Contexto LLM y guía operativa de Gemini/Groq explican la convención de coordenadas: **norte −Y, sur +Y, este +X, oeste −X**. El título de la acción también muestra el sector que Nilo eligió.
- Pruebas con ambos niveles, cardinales, alias, región conocida/desconocida, ausencia de frontera sectorial, compatibilidad de exploración genérica y navegación histórica; sin nuevos objetivos, recursos ni física.
- **Pendiente:** evaluar con runs reales si mejora la continuidad de intereses espaciales sin provocar exploraciones repetitivas (#3). No se modifica el diagnóstico de una narración histórica cuyo desplazamiento no se pueda reproducir.

**Siguiente paso preferido:** revisar solo dependencias técnicas efectivas y preparar el hito `0.5.9.4` antes del salto físico propuesto para `0.6`. La guía vigente se mantiene en `docs/FUTUROS_CAMINOS.md`.

---

## Nilo 0.5.9.3.34.1 · Percepción corporal cualitativa (2/11/2026)

**Alcance:** #62 (sensaciones), #50 (autonomía), #51 (interfaz), #31 (selección contextual) y pruebas para #3.

- El **motor** conserva las cinco reservas internas continuas, umbrales, tensión corporal, recuperación y efectos físicos. `needs_summary` sigue dando números al observador y a la interfaz.
- La **deliberación y el chat del personaje** reciben únicamente etiquetas perceptivas para hidratación, alimentación y energía: «bien hidratado», «completamente saciado», «con mucha energía», «sin sed», «sin hambre», «descansado», «algo de sed/hambre», «algo cansado», «mucha sed/hambre», «muy cansado», «sed/hambre extrema», «agotamiento severo» o «inconsciente» según el estado. Los umbrales permanecen privados del motor.
- Una barrera en `build_deliberation_request` y `request_chat` transforma automáticamente contextos heredados con barras numéricas antes de llamar al modelo; no modifica el objeto ni su persistencia.
- La telemetría de cambios energéticos automáticos deja de exponerse como percepción cotidiana. Si Nilo decide investigar descanso, hidratación o nutrición, conserva acceso a **resultados históricos medidos** pertinentes (energía tras descansar, hidratación tras beber y nutrición tras comer), con sus IDs, sin recibir la reserva corporal actual ni condiciones numéricas internas de validación. El aprovisionamiento cotidiano no equivale a un ensayo. Los resultados físicos de experimentos con materiales siguen visibles.
- Las instrucciones dejan explícito que Nilo no conoce sus reservas exactas por introspección y que sentirse bien no obliga a llenar barras. Puede elegir abastecerse, comer, beber o descansar sin medidas ni urgencia.
- Las etiquetas visibles del **observador** son específicas para cada necesidad; conserva porcentajes, tasas y ayudas numéricas para inspeccionar la simulación.
- Se mantienen replays, importación, SQLite y el mecanismo de delegación finita de la .34. **No** incorpora embeddings, FTS5, nuevos modelos fisiológicos ni el alcance de exploración dirigida reservado para .35.

**Validación:** límites de categorías, no mutación de reservas, protección del payload Groq/Gemini y disponibilidad de resultados realmente medidos en un contexto de investigación. El impacto conductual con modelos reales permanece pendiente (#3).

---

## Nilo 0.5.9.3.34 · Percepción corporal y memoria contextual (2/11/2026)

**Integración coordinada:** [#62](https://github.com/mxlzz/Nilo_public/issues/62), [#56](https://github.com/mxlzz/Nilo_public/issues/56), [#51](https://github.com/mxlzz/Nilo_public/issues/51), [#20](https://github.com/mxlzz/Nilo_public/issues/20) y [#31](https://github.com/mxlzz/Nilo_public/issues/31).

- **Sensaciones:** nueva vista derivada para sed, hambre y cansancio, separada de las reservas físicas de 0–100. Sed/hambre: ≥90 ninguna; 60–<90 normal sin urgencia; 30–<60 progresiva; 15–<30 intensa; <15 crítica. Cansancio: ≥90 ninguno, 60–<90 normal, 30–<60 progresivo, 12–<30 intenso, <12 tensión corporal, ≤5 inconsciencia. No se cambian tasas ni reglas fisiológicas; descansar, comer o beber siguen siendo elecciones de Nilo.
- **Autocuidado delegado:** las preferencias de espera \`rest\`, \`drink\` y \`eat\` se ejecutan solo una vez por delegación salvo repetición explícita \`veces\` (1–8), con condición opcional \`menor_que\` definida por Nilo. La cuota se descuenta al **programar** el paso; una deliberación posterior puede renovar la autorización. No se introducen umbrales globales de ingestión ni descanso; la ruta de replay histórico permanece diferenciada.
- **Memoria y contexto:** se corrige el orden de \`memorias_relevantes\` para conservar los mejores puntajes de \`episodic_memory.recall_relevant\` en vez de los últimos; cuando haya que reducir más, se descartan primero los menos relevantes. Se conservan materiales de inventario y delegaciones, así como la sensación actual; se priorizan navegación, objetos o mediciones según el proyecto elegido. Las orillas de agua no dominan el contexto cuando no existe interés por agua ni sed presente, pero permanece una referencia y no se bloquea la planificación futura.
- **Telemetría:** para deliberaciones exitosas registra bytes reales de cada sección, bytes del contexto e instrucciones, tamaño HTTP del payload, campos priorizados/omitidos y IDs de recuerdos incluidos. El uso de tokens continúa proveniendo exclusivamente de la respuesta API. No persiste el prompt completo, credenciales ni texto de errores.
- **Interfaz:** barras conservadas con etiqueta de sensación corporal, ayudas consistentes para las tres reservas, abrigo y seguridad sin nueva física.
- **Compatibilidad:** sin modificación del mundo, física o historia existente, sin embeddings ni índices FTS5 todavía. Pruebas de límites 90/60/30/15, consentimiento de rutinas, contexto Groq/Gemini, recuperación y replay.

**Aún pendiente:** evaluación longitudinal del impacto real en decisiones (#3, 0.5.9.4); búsqueda histórica por FTS5, memoria consultable bajo demanda y consolidación (#20/#65) en futuras iteraciones; exploración orientada (#60) propuesta para la siguiente versión.

---

## Nilo 0.5.9.3.33 · Reducir solicitudes LLM y diagnosticar respuestas (2/11/2026)

- **Run real (.32):** Groq devolvió HTTP 413 por tamaño; Gemini 3.1 y 3.8 respondieron 429 de cuota, Gemini 3.5 declaró respuesta incompatible. El último éxito Gemini consumió 18.799 tokens de entrada. Se estudiaron códigos/estado guardados, sin reproducir claves ni enviar SQLite al repositorio.
- **Groq:** el respaldo recibe instrucciones compactas que conservan autonomía, principios físicos, distinciones de evidencia, contratos de todas las operaciones y salida JSON válida. Además de compactar el contexto, se valida el **payload completo** (instrucciones, contratos, situación y estructura HTTP) con tope preventivo de 14.500 bytes UTF-8; se reduce por registros completos y no se corta JSON.
- **Gemini:** conserva las instrucciones generales y documentación de operaciones; el contexto se selecciona y limita por campos con presupuesto 9.100 bytes, sin modificar los recuerdos en SQLite. Esto reduce tokens pero no elude las cuotas 429 reales.
- **Relevancia y trazabilidad:** se priorizan estado corporal, posición, proyecto activo, razones de rechazo de cierre, recordatorios cumplidos y evidencias con identificadores auténticos. No se convierte resumen en hecho ni se obliga a Nilo a cambiar intereses.
- **Errores de respuesta:** se distinguen fallas de JSON, plan sin acciones válidas o falta de nota de cuaderno. Solo se guardan códigos y mensajes seguros, sin texto crudo del modelo.
- **Reintento Groq:** nuevo perfil de presupuesto para no heredar una espera 413 de solicitudes anteriores más grandes. Los cooldown 429 de Gemini no se reinician.
- **Compatibilidad:** no hay migración de la partida, cambios de física ni acciones automáticas nuevas. Se preservan replays deterministas.
- **Pruebas:** límite del payload HTTP, selección con contexto grande, retención de evidencia, cobertura de operaciones, aislamiento de estado y clasificación de errores; validación integral y empaquetado.

**Limitación:** los límites en bytes ofrecen margen de seguridad pero no equivalen a un conteo exacto de tokens del proveedor. Ni un error 429 auténtico ni una salida defectuosa del LLM pueden resolverse simplemente con compresión.

---

## Nilo 0.5.9.3.32 · Progreso físico, continuidad y reconsideración (1/11/2026)

- **Navegación (#61):** el progreso y los contadores del proyecto ahora usan el número de casillas reveladas desde el inicio real de la acción (`pending.behavior_revealed_at_start`). Un bloqueo tras descubrir casillas se registra como descubrimiento parcial; recorrer una ruta ya revelada no da crédito nuevo. Los registros antiguos sin marcador no reciben avances ficticios.
- **Estancamiento (#2):** en reglas actuales, varias operaciones `explore`, `inspect` o `use` sin progreso son evidencia para reconsiderar, pero el motor no prohíbe indiscriminadamente toda la familia de acciones ni borra planes legítimos. El detector de duplicados exactos conserva el plan en vez de cancelarlo; presenta el aviso y Nilo conserva la decisión. Los contadores se reinician tras progreso físico verificado.
- **Cierre de proyectos (#13):** rechazos con códigos distintos para `sin_mediciones_del_proyecto`, `condicion_fisica_no_demostrada`, `criterio_no_instrumentado` y cita faltante. Ningún porcentaje, texto del diario ni paso de agenda acredita por sí mismo cumplimiento. El diagnóstico no relaja las validaciones físicas existentes.
- **Agenda/continuidad (#13/#81):** una secuencia completada mantiene estado de ejecución y marca por separado su propósito como no verificado automáticamente. El contexto conserva el motivo de pausa y expone proyectos con recordatorios cumplidos para que Nilo decida reanudarlos, incluidos los contextos reducidos.
- **Replays:** `reproducir.py` identifica cada replay histórico y preserva la huella original de cualquier ruleset publicado. Los cambios de instrumentación .32 solo se aplican a ejecución vigente. No se reescriben históricos SQLite ni se crean objetivos.
- **Pruebas:** navegación revelada antes del cierre, rutas repetidas, bloqueo parcial, ausencia de marcador, distinción de objetivos, agenda y continuidad voluntaria; suite integral y replays.

**Pendiente de evaluación:** verificar si estas correcciones reducen efectivamente falsos estancamientos en corridas reales comparables (#3). La exploración dirigida (#60), índices de memoria (#20/#65) y ampliación composicional de herramientas (#45/#89) quedan para la siguiente etapa.

---

## Nilo 0.5.9.3.31 · Etiquetas de acciones con nombre de herramienta (1/11/2026)

- La actividad activa y los registros narrativos de `use` muestran el nombre registrado de la herramienta en vez de `obj-...`, conservando intacto el ID para ejecutar la operación y enlazar la evidencia.
- Los pasos pendientes de la interfaz resuelven referencias exactas contra las herramientas presentes en la partida; si un ID no existe, se mantiene visible para diagnosticarlo sin inventar nombres.
- Pruebas con nombres duplicados, referencia inexistente, nombre histórico y preservación del ID.
- Sin cambios en la física, en la memoria, en las partidas SQLite ni en las reglas de avance; hallazgos del run 2026-11-01 se siguen por issues separados.

---

## Nilo 0.5.9.3.30 · Memoria contextual y revisión informativa de estrategias (1/11/2026)

- **Episodios nuevos con procedencia:** los registros de experiencia incorporan ID estable, objetivo registrado, proyecto, ubicación al finalizar, objeto físico identificado por el motor, ID de acción e ID de medición cuando existen. Los históricos no se reinterpretan ni se les asignan posiciones o identidades inventadas.
- **Recuperación contextual:** se consideran objetivo, último intento del proyecto, vínculo exacto de entidad, proyecto y cercanía a ubicaciones realmente registradas. Se conservan las reglas de no revelar lugares ocultos. Sigue siendo una selección en memoria, no el futuro índice SQLite general de #20/#65.
- **Revisión semántica:** un nuevo módulo compara deliberaciones del mismo proyecto por secuencia operativa y un conjunto limitado de efectos verificables. Puede identificar variantes de desplazamientos cortos seguidos de descansos investigativos saturados. Exige tres deliberaciones equivalentes sin información nueva y distingue direcciones/regiones distintas de exploración y cambios de métodos o resultados.
- **Autonomía:** la señal es informativa. No descarta planes, prohíbe descansos, cambia proyectos ni exige nuevas llamadas al LLM. Se entrega en contexto completo y compacto. Permanece activo el detector previo de duplicados exactos, independiente de la nueva señal.
- **Compatibilidad de reproducción:** las partidas con rulesets históricos conservan la estructura exacta de los episodios y el historial de decisiones al ejecutar replays; la nueva instrumentación solo se aplica a sesiones con reglas actuales.
- **Pruebas:** casos deterministas de procedencia, recuperación de un episodio antiguo frente a cientos de entradas recientes, compatibilidad de históricos, progresos que invalidan la repetición y estrategias espaciales distintas. No se afirma eficacia conductual sin un run comparativo con proveedor real.

**Pendiente:** recuperación indexada desde SQLite, consultas históricas a demanda, análisis de repetición por resultados físicos más ricos, comparación en runs controlados (#3) y autonomía de propuestas (#29).

---

## Nilo 0.5.9.3.29 · Consistencia material de fichas y prototipos (1/11/2026)

- Si `craft`, `build` o `assemble` indican `design_id`, los materiales y cantidades consumidos deben corresponderse con las piezas de la última versión documentada. Se rechaza el vínculo inconsistente antes de gastar recursos. Fabricar libremente sin vincular sigue permitido.
- Caso observado: un refugio descrito con **un poste de madera** no puede asociarse a una obra de **cuatro unidades de madera** sin corregir el desglose en una nueva versión de la ficha.
- `assemble` conserva `design_id`, `design_version` y el ID del objeto materializado para documentar la construcción; crear el objeto no demuestra su función.
- Se conservan fichas y mediciones anteriores. Un balance coincidente es condición necesaria para un vínculo nuevo, pero **no acredita la forma, las uniones ni el rendimiento funcional**.
- Regresiones sobre rechazos sin pérdidas, versiones nuevas y asociación de ensamblajes. No cambian la física, los recipientes, el descanso ni la autonomía de Nilo.

---

## Nilo 0.5.9.3.28 · Continuidad experimental y diseños verificables (1/11/2026)

- **Fichas de diseño:** al fabricar o construir con `design_id` válido, el objeto conserva físicamente ese identificador. El motor relaciona la ficha con el ID real fabricado y la medición, pero **fabricar no acredita función**.
- **Pruebas de herramientas:** los usos exitosos sobre el objeto vinculado pueden verificar una función mediante su método explícito `expected_test` o, si no se especificó, un método reconocible con el propósito declarado. Exige ensayo real de la revisión vigente; no basta mencionar el ID del diseño en otra herramienta.
- **Refugios:** una recuperación efectiva de energía en un habitáculo con cobertura física válida se vincula al diseño de esa construcción. Su estado será **función parcialmente comprobada**, porque no demuestra seguridad ni ventaja causal frente al exterior. No se atribuyen funciones retroactivamente a objetos históricos sin relación física identificable.
- **Bucle energético:** el contexto entrega el umbral de energía y duración exigidos por la comparación de descansos (≤60 inicial, menor a 74,9 final y 15 min mínimo), número de pruebas recientes no comparables, estado real del abrigo de construcciones y recordatorio de que `wait` no reduce energía. Se preservan estos datos incluso con contexto compacto de Groq.
- **Cierre de proyectos:** el rechazo del motor conserva su razón concreta y proyecto de origen para la siguiente deliberación, sin cerrarlo ni asignar nuevos objetivos. Descansos no comparables cuentan como pasos informativamente infructuosos **solo en investigaciones explícitas de descanso**; no se prohíbe descansar.
- **Recipientes (corrección de .27):** la vía tipada principal `action_results.py` y las variables autorizadas de predicción ahora coinciden con el laboratorio: `capacidad_util_agua`. Las etiquetas de mediciones históricas permanecen legibles; no existe pérdida de agua en el tiempo.
- **Interfaz:** apartado de diseños muestra funciones comprobadas con IDs de medición y aclara la diferencia con prototipos. Continúa sin cambiar las reglas físicas de sueño o seguridad.

**Límites:** no es todavía la evaluación integral de autonomía del issue #2; la semántica de objetivos abiertos sigue dependiendo de la deliberación autónoma de Nilo. La prueba prolongada con modelos reales continúa pendiente.

---

## Nilo 0.5.9.3.27 · Espera voluntaria y claridad de interfaz (2026-11-01)

**Cambios de comportamiento y presentación, sin cambiar reglas de capacidad física ni borrar mediciones históricas.**

- **Nueva acción `wait`:** Nilo puede esperar voluntariamente de 1 a 1440 minutos simulados (30 por defecto), sin ejecutar otra acción ni declarar un ensayo de descanso. La evolución corporal sigue siendo la de inactividad (aprox. +0,8 energía/h), diferente de `rest` (+6,6/h a la intemperie o +10,6/h en refugio). **No existe `sleep` como operación separada y esperar no reduce la energía para un experimento.** No se genera actividad ni logro automáticamente; el reloj avanza y las condiciones diferidas siguen evaluándose. Colapso fisiológico independiente e inalterado.
- **Recipientes:** «retención estimada %; puede perder líquido» se reemplaza por **«capacidad útil estimada»**, que ya incorpora el factor estático de permeabilidad. No se simula evaporación ni filtración a lo largo del tiempo. Los nuevos ensayos registran `capacidad_util_agua` como métrica observada; el antiguo `retencion_pct` y `agua_retenida` siguen siendo legibles en archivos históricos con etiquetas aclaratorias, sin modificar ni interpretar retrospectivamente sus resultados.
- **Proyectos:** se muestra el vínculo más reciente por categoría física/documental y se pliegan las referencias anteriores de cada familia en «Ver anteriores (N)», cerrados inicialmente. Se mantiene la exposición completa de vínculos en el Cuaderno. La nueva agrupación usa `seq` del índice histórico, sin confundir estado `new/updated` con recencia.
- **Mapa:** el borde de referencias pasa de arriba a debajo de todo el desplegable.
- **Márgenes:** el layout deja de imponer 1800px de ancho máximo; margen exterior de 12px por lado, alineado con encabezado y pie.
- **Compatibilidad:** no hay cambios en esquema SQLite, velocidad ni reglas físicas; se conservan mediciones, objetos, diarios y replays anteriores. Pruebas nuevas comprueban validaciones de duración, diferencia entre esperar/descansar/actividad, ejecución de acción en simulación con persistencia, presentación de vínculos en JS real, terminología y CSS.

**Alcances pendientes:** el nuevo indicador «capacidad útil» es una capacidad estática calculada; una simulación temporal de fugas sería una física distinta y requeriría reglas y evidencia nuevas. La comprobación visual humana con partidas grandes en Windows queda fuera de las pruebas automáticas.

---

## Nilo 0.5.9.3.26 · Cuaderno, vínculos completos y verificación de interfaz (2026-11-01)

**Tercera etapa acordada: #38, #51, #52, #53, #54.** Basada en 0.5.9.3.25, sin modificar reglas de autonomía, física corporal, tiempos de las acciones ni sus datos históricos.

- **#38 — Relaciones del Cuaderno:** `recordLinks` muestra TODOS los registros relacionados directamente, agrupados por familia sin subtítulos ni separadores, con prioridad de fase y orden histórico dentro de cada grupo; se elimina el control «Ver N relaciones más».
- `History.relations_for`, `relations_batch` y `Simulation.public_state` dejan de truncar vínculos a 40/25/32 por registro. La consulta individual `/api/record` también devuelve el grafo completo. Se deduplican referencias por entidad y se conserva la procedencia de las mediciones vinculadas al cuaderno.
- Los cortes de indexación de evidencias y `entity_links` (80/100/150) también se retiran. Migración `indexed_v2_full` reconstruye los índices de IDs explícitos una sola vez en bases existentes, sin reinterpretar texto, inventar relaciones ni modificar las partidas.
- **Integración con #49:** las transferencias, recargas, consumos, descargas y almacenamientos de recipientes ahora enlazan las herramientas u obras reales por ID, y distinguen origen/destino cuando hay evidencia tipada de éxito. La narración sin efecto físico o una operación rechazada no crea vínculo. Se conservan las variaciones de inventario como registros de material, sin inventar objetos.
- **#51–#54:** conservar las ayudas corporales vigentes, popovers flotantes, filtros y motivos de Investigaciones/Proyectos, y contorno del objetivo físico en el mapa. Esta versión agrega regresiones de arranque e integración contra el nuevo motor; no afirma verificación visual en Windows sin prueba humana.
- Pruebas de relaciones con más de 150 entidades por categoría, reconstrucción de índices históricos, ausencia de vínculos por texto, orden/presentación ejecutados en Node, simulación de transferencia con persistencia/reapertura SQLite; también se ejecutan pruebas y replays históricos.

**Pendiente de observación:** confirmar visualmente el comportamiento de ayudas, filtros, contorno y navegación/lectura del Cuaderno en una partida real; en acciones instantáneas el contorno puede no permanecer en pantalla. La cobertura futura de vínculos con terreno o fichas navegables de materiales depende de identidades físicas todavía no instrumentadas.

---

## Nilo 0.5.9.3.25 · Capacidades físicas y recipientes (2026-11-01)

**Segunda etapa acordada: #59, #39, #30 y #49.** Esta versión añade un primer módulo operativo completo, pero NO presupone que toda la arquitectura de plugins futuros esté terminada.

- **#59:** fabricación de objetos blandos y duplicados materiales independientes; sin veto universal por resistencia media inferior a 3 ni pérdida automática de materiales por ese veto. La resistencia sigue representada para evaluar usos. Se conserva el límite de componentes y las restricciones de obra fija superpuesta.
- **#30:** registro cerrado y versionado de capacidades físicas en `capabilities.py`, con despacho genérico `interact` y módulo `vessels.py`; se registra la versión de contenidos en el mundo al primer uso, y la evidencia de cada operación incluye ID y versión. Las partidas anteriores no cambian de leyes hasta ejecutar una operación nueva; si una partida requiere otra versión o la capacidad está deshabilitada, la operación se rechaza. No se cargan paquetes arbitrarios ni se habilitan propuestas automáticamente. Quedan pendientes activación explícita por instalación, migraciones entre versiones incompatibles y generación de otros módulos.
- **#49:** recipientes esquemáticos pueden llenarse parcialmente desde agua ambiental contigua, transferir cantidad comprobable entre dos objetos, descargar al entorno, beber explícitamente del contenido, guardar y retirar sólidos del inventario. Se valida capacidad, disponibilidad, cercanía, material compatible, integridad y cantidad sin duplicaciones. El agua ambiental aún no tiene un balance de depósito finito; descargar no produce charcos modelados. Los recipientes llenos no pueden desmontarse ni modificarse de manera que el contenido exceda la capacidad final sin vaciarlos o transferirlos previamente. La acción histórica `use/llenar` permanece para compatibilidad; el módulo nuevo utiliza `interact/rellenar`.
- **#39:** métodos físicos reconocidos por registro y diagnóstico tipado de la ausencia de método, con alcance, variables no evaluables e ID de evidencia. Los rechazos del módulo por precondición se distinguen de fallos físicos medidos y de `no_evaluable`. No se reinterpreta el historial anterior, ni se infiere filtración/potabilidad a partir de contención.
- Continúan sin cambiar los contratos corporales #55–#58, la autonomía del personaje, la física geométrica detallada y la interfaz del run anterior. Replays históricos preservados.
- Tests nuevos de conservación de contenidos, duplicados, intentos rechazados sin efectos, consumo explícito, cambios de capacidad, diagnóstico y arranque. Se complementan con la suite y replays de CI.

---

## Nilo 0.5.9.3.24 · Casilla de intervención en mapa (2026-11-01)

- #54: marca con un contorno interior discreto la casilla concreta de una intervención física durante una acción pendiente, sin modificar símbolos, rastro ni geometría. Disponible en superficie y cueva, y en mapas cercano y general.
- El motor expone `active_intervention` de solo lectura: `x,y,z,op`, exclusivamente si puede identificar una casilla observada y real. No se escribe en SQLite ni modifica memoria, acciones, tiempos o necesidades.
- Inspección: admite terreno por coordenadas, terreno/obra inequívocos y omite herramientas portátiles. Excavación: valida roca adyacente y herramienta con capacidad. Recolección: muestra fuente real cuando ya se trabaja allí, no casilla de apoyo; `forage` utiliza el selector físico compartido. Obras fijas: se distingue de modificaciones de herramientas portátiles.
- Durante una navegación, incluso si ya hay fuente seleccionada, no se anticipa el contorno: aparece solo durante intervención física, si ese estado dura hasta el próximo refresco. En operaciones que se ejecutan instantáneamente al terminar un trayecto, puede no ser visible; no se introducen esperas artificiales para forzar animaciones.
- Si se cancela la acción, se pierde conciencia, cambia de nivel o el terreno no está revelado, no aparece marca. Pueden comprobarse estos casos con pruebas de contrato y ejecución de mapa JavaScript.
- Basada en la corrección de arranque 0.5.9.3.23.1. Sin cambios de #38, #39, #30, #49 o de supervivencia.

---

## Nilo 0.5.9.3.23.1 · Corrección de arranque de interfaz (2026-11-01)

- La versión 0.5.9.3.23 intentaba ejecutar `stored('nilo.researchView.v1',...)` **antes de inicializar `const stored`**, provocando un `ReferenceError` de JavaScript durante el arranque de la página.
- La 0.5.9.3.23.1 corrige el orden de las declaraciones sin cambiar las reglas del motor, el formato de partidas ni los filtros.
- Se añadió una prueba de ejecución real de la secuencia de inicialización con Node.js; `node --check` no detectaba este fallo en tiempo de ejecución.
- No contiene cambios del mapa (#54): la 0.5.9.3.24 quedó suspendida hasta resolver y verificar el arranque.

---

## Nilo 0.5.9.3.23 — Lectura de registros (2026-11-01)

- #51: ayudas de hidratación, alimentación y energía actualizadas conforme a las reglas efectivamente publicadas en 0.5.9.3.22 (sin ingestas por umbral; descanso libre y colapso).
- #52: ayudas contextuales de Ensayos y otras secciones como popup flotante en `body`, sin desplazar registros; cierre por Escape, clic exterior, scroll y cambio de solapa.
- #53: filtro **independiente** de investigaciones por estado, incluyendo integradas; motivos registrados de pausas, abandonos y cierre en fichas, sin inferir razones ausentes.
- El filtro de Proyectos se conserva exactamente como en 0.5.9.3.22.
- No incluye agrupación de relaciones del Cuaderno #38 ni resaltado de casillas de intervención #54; ambos requieren pruebas específicas y quedan para otra versión.

---

## Nilo 0.5.9.3.22 · Autonomía corporal y agenda (2026-11-01)

- Descanso voluntario con duración explícita; colapso por agotamiento extremo como estado involuntario que impide actuar y deliberar.
- Retiradas ingestas, descansos y provisiones predefinidas; las preferencias delegadas sobreviven.
- Agenda sin bloqueos globales de necesidades, conservando las precondiciones de cada operación.
- Factor de fatiga aplicado también a rutas, respetando cálculo por casilla y cronómetro.
- Replays anteriores conservan reglas históricas de ingesta y duraciones.

---

## Nilo 0.5.9.3.21 · QMP y autonomía del descanso (2026-11-01)

- QMP se traslada al pie anclado de la columna del registro, visible al recorrer o cambiar solapas. Barra superior de lectura compacta, sin carrusel horizontal.
- Necesidades: se corrige la explicación energética para la versión vigente, se elimina leyenda redundante y se atenúan los indicadores inactivos de abrigo y seguridad.
- Actividad: porcentaje y ambos tiempos restantes en un único renglón.
- Cuaderno: se conservan y verifican vínculos físicos basados en mediciones y IDs reales, incorporados en la versión anterior (#38).
- Se retira la promoción cognitiva especial del estudio de descanso: deja de inyectarse en cada deliberación la recomendación de comparar tasas y no se generan conclusiones espontáneas por descansos rutinarios. Las mediciones objetivas persisten.
- Se habilita la deliberación sin proyecto formal mediante sin_proyecto, sin alterar el control previo de pausas/recordatorios.
- Replays antiguos conservan los estados y textos originales; las partidas importadas no pierden historial.

---
## Nilo 0.5.9.3.20 · Registros y lecturas compactas (2026-11-01)

- Energía regenerable hasta 100 sin techo artificial de 75; estados históricos reproducibles conservan la física vieja de replay. Las reglas de comparación científica de descansos siguen distinguiendo muestras saturadas.
- Registros relacionados del Cuaderno enriquecidos con deltas medidos de inventario (adquiridos/consumidos) y objetos/obras con identificadores verificados antes y después de una acción. Sin inferir objetos por cantidad ni causalidad por proximidad.
- Una sola ficha desplegada por grupo semántico; detalles anidados y grupos de otra sección independientes.
- Textos explicativos de Ensayos, Hallazgos, Creaciones, Investigaciones, Propuestas y Agenda accesibles desde ayudas (?) en lugar de tarjetas grandes; información dinámica preservada.
- Clic en pestaña activa u otra pestaña vuelve al registro reciente; un clic en enlace histórico mantiene la navegación al destino.
- Estado no leído de habilidades en Conducta resaltado de forma visible.
- Pruebas y compatibilidad: no se alteró lógica de pausa/recordatorios del agente. Seguimientos de catálogo y física más compleja permanecen abiertos.

---

## Nilo 0.5.9.3.19 · Cierre por evidencia de reconocimiento (2026-11-01)

- Solucionado el bloqueo observado en el run del día 2: «Reconocimiento del terreno y hallazgo de agua.» no tenía criterio instrumentado a pesar de existir ensayos físicos útiles. Nilo podía solicitar completar indefinidamente.
- Reconocimiento del terreno: exigir exploración verificada; hallazgo de agua: observación, inspección o llegada a orilla probada y autoría del proyecto. Preferir dentro de la prueba de cierre las mediciones pertinentes que Nilo cite.
- Si el objetivo es verificable pero la cita es inválida, comunicar los IDs válidos para evitar deliberaciones repetidas sin información nueva. Nunca permitir cierre basándose únicamente en narración.
- Localizar agua no demuestra potabilidad; robustecido el reconocimiento de «potable», «potabilidad» y «purificación».
- Sin cambios de física, interfaz ni estado histórico. Próximos cambios de interfaz en #42 y #43. Validación determinista y de compatibilidad incluida.

---

## Nilo 0.5.9.3.18 · Recordatorios y filtros (2026-11-01)

- Nuevo recordatorio condicionado elegido por Nilo. El proyecto puede quedar pausado hasta que se cumpla una condición; su cumplimiento habilita volver a considerarlo en una deliberación, sin lanzar acciones ni simular un resultado físico.
- Mantener separado un recordatorio (`modo: recordatorio`, sin pasos) de una tarea delegada de Agenda. Se conserva la compatibilidad con tareas antiguas; el evento se genera una sola vez y se reconoce al retomar el proyecto.
- Interfaz: en Agenda y Proyectos, filtro compacto por estado junto al indicador de novedades. Controles en una sola línea, con desplazamiento horizontal de ser necesario. Preferencias de filtro persistentes por solapa; no modifica lectura ni archivo.
- No se cambian leyes, valores físicos, tasas de supervivencia ni contadores cognitivos históricos. #39 (diagnóstico central de límites físicos) continúa pendiente para el registro modular #30.
- Pruebas de nuevo comportamiento, interfaz, escenarios y replays antiguos.

---

## Nilo 0.5.9.3.17 · Diagnóstico trazable y orientación (2026-11-01)

- Integrado el PR `referencia privada #72`: las propuestas de fenómenos no modelados y los reportes de posibles defectos seleccionan evidencias identificables. Sin IDs auténticos y pertinentes no presentan vínculo probatorio ficticio. Devoluciones humanas anteriores se recuperan al deliberar, sin confundirse con mediciones.
- El contexto LLM, también en su formato reducido, incorpora lugares ya revelados y rutas comprobables sobre el mapa conocido, con distinción explícita entre ausencia de ruta conocida, estar en otro nivel y llegar al sitio. No expone lugares todavía ocultos.
- No se impone un nuevo objetivo, una ruta ni una cuota de solicitudes a Nilo. Las leyes físicas y partidas anteriores no cambian.
- Se difirió el cambio en la contabilización de descansos saturados: modificaba el resultado de una reproducción histórica y necesita una política de compatibilidad por versión. #2 permanece abierto.
- Pruebas del diagnóstico, reconocimiento espacial, compresión, mundo, escenarios y replay determinista.

---

## Nilo 0.5.9.3.16 · Primera extracción modular (2026-11-01)

- Las definiciones de materiales, terrenos y formas/partes de objetos del entorno actual viven en tres JSON independientes y validados por `catalogo.py`. Sin cambiar propiedades, leyes o generación original.
- Los consumidores físicos conservan sus interfaces históricas y cada partida recibe copias independientes de los materiales originales.
- La API de velocidad ahora acepta ×80 y rechaza ×300/×600, en concordancia con los botones y el motor.
- Valor predeterminado del mínimo real entre deliberaciones exitosas: 15 s en nuevas instalaciones; acotado a 10–300 s y respetando cuotas y cooldowns de proveedores. El archivo `config.env` existente se preserva, sin reemplazar automáticamente su valor.
- Configuración muestra el intervalo real utilizado.
- Pruebas del catálogo, velocidades vía HTTP, límites de cadencia, escenarios y replay. No se incorporó el PR `referencia privada #72` ni se alteraron los runs actuales.

---

## Nilo 0.5.9.3.15 · Interfaz compacta y temas grises (2026-10-31)

- Referencias del mapa plegables y control de visibilidad binario; opción anterior «Solo mapa» migrada a mapa con referencias plegadas.
- Materiales, Herramientas y Obras reorganizados en tres solapas compactas y persistentes.
- Agregados Grises oscuros y Grises claros (casi blanco) a los tres temas existentes.
- Eliminado «Volver a conexión anterior» de la columna de registros; se conserva la navegación dentro del diálogo de vínculos.
- Pruebas de interfaz, migraciones de preferencias y regresiones del comportamiento anterior. Sin modificaciones de mecánicas ni partidas.

---

## Nilo 0.5.9.3.14 · Corrección de auditoría (2026-10-31)

- Corregida la adquisición de habilidades de recolección; ahora se acredita por incremento tangible del inventario y material solicitado, sin depender de la puntuación o el singular/plural del mensaje.
- Eliminados falsos cierres de objetivos genéricos que solo compartían vocabulario con una medición. Se conserva explícita la distinción entre «no verificado» y proyecto abandonado/pausado.
- El desplazamiento auxiliar `move()` solo utiliza terreno revelado. La planificación principal ya respetaba esta condición.
- Añadidas pruebas de integración de recolección de una/dos unidades, alias, inactividad sin habilidad, intentos fallidos, medidas no pertinentes y rutas conocidas.
- Continúan pendientes la normalización física a un único `ActionResult`, el modelado de objetivos arbitrarios y el índice de memoria histórica.

---

## Nilo 0.5.9.3.7 · ×300, ×600 y reloj de deliberación (2026-10-29)

- ×300 y ×600 en controles, API y estado persistido. Motor dividido en subpasos de hasta un minuto simulado con corte exacto al terminar una acción.
- Consulta activa del LLM a ×1 temporal; pausa automática ×0 también en cooldown ordinario sin tareas, respetando las agendas cuyo reloj debe avanzar y los reintentos por tiempo real.
- Escritura rápida sin animación a ×300/×600; duración simulada conservada, ×2 en modos anteriores.
- Etiqueta de velocidad efectiva y resaltado de habilidades pendientes en Conducta (#21).
- Replay determinista actualizado al nuevo procesamiento del tiempo; pruebas de regresión, escenarios y verificación de paquete íntegro.

---

## Nilo 0.5.9.3.6 · Recuperación de experiencias y evidencia primaria (2026-10-29)

- Recuperación determinista de experiencias pasadas vinculadas al objetivo/lugar con ID, fecha, resultado y procedencia; prioriza, entre otras, transiciones de cueva verificadas aunque sean antiguas. El campo no se descarta al compactar el contexto para Groq.
- `conclude` y otras operaciones derivadas dejan de servir como medición primaria para otra conclusión. No se registra éxito ficticio por recuperar una conclusión existente; la deduplicación de pruebas no depende de su orden.
- Los avances verificables de proyectos excluyen `conclude`, `compare` y acciones administrativas. El cierre rechaza pruebas explícitamente inconclusas y exige datos físicos para potabilidad. Los datos históricos se preservan sin falsificar reversiones.
- Pruebas de regresión con la cueva del día 6/10, conclusiones encadenadas y objetivos no demostrados. Persisten issues para validación semántica general del objetivo y evaluación longitudinal de autonomía.

---

## Nilo 0.5.9.3.5 · «¿Qué me perdí?» por relevancia y resumen incremental (2026-10-29)

- Selección editorial de acontecimientos importantes en todo el conjunto pendiente, ordenados por relevancia y no por secuencia cronológica. El máximo de siete fuentes evita abarcar cien registros que no se explican explícitamente.
- El botón «¿Qué más?» continúa desde la página anterior con novedades adicionales de importancia no creciente; conserva el conjunto temporal de hechos originales y detiene la secuencia cuando quedan solamente eventos rutinarios.
- Cada respuesta muestra las fuentes originales que cubre. Solo esas fichas reciben la marca de lectura al confirmar la síntesis. Otros pendientes y nuevos acontecimientos no quedan silenciados.
- Mantiene el historial de resúmenes por capa y la separación entre interpretación del observador y decisiones del agente.
- Se añaden pruebas de selección fuera de los primeros cien registros, navegación entre páginas, lectura exacta y eventos concurrentes; no hay cambios de física.

---

## Nilo 0.5.9.3.4 · Preservar desplegables al actualizar y lectura del registro origen (2026-10-29)

- El redibujado de la solapa ya no cierra los desplegables que el usuario abrió, incluso cuando Nilo sigue escribiendo o inserta novedades. Se preserva la identidad de cada ficha y sus elementos anidados.
- Abrir un vínculo documental dentro de una ficha registra como leído el documento **de origen** al completar la navegación; el de destino conserva su estado previo. Funciona en Cuaderno, Novedades y las solapas con seguimiento de lectura.
- Pruebas de actualización con registros nuevos intercalados, restauración de estado anidado y navegación sin marcar automáticamente el destino. Se actualizó la prueba histórica que solo contemplaba aperturas de Novedades.
- Los cambios de síntesis jerarquizada de «¿Qué me perdí?» están registrados en issue #16 para una implementación independiente.

---

## Nilo 0.5.9.3.3 · Contratos operativos y diagnóstico estructurado (2026-10-29)

- Sustituido el manual duplicado y su acción física por un catálogo único en `action_contracts.py`, que genera las instrucciones del agente y describe los criterios verificables de las acciones.
- Captura de estado antes de ejecutar una acción; verificación posterior de seis operaciones prioritarias. La clasificación distingue uso incorrecto, física no implementada, anomalía verificable, comprobación correcta y datos insuficientes.
- Informes automáticos solo ante contradicciones fuertes: adjuntan `act-...`, se deduplican por operación/código y requieren evaluación humana.
- Nilo recibe los últimos diagnósticos operativos en su contexto y puede solicitar correcciones o ampliaciones por las acciones ya existentes `report_issue` y `propose`.
- Las consultas `manual` heredadas no se ejecutan al importar una partida; desaparece `action_manual.py`.
- Referencia de replay actualizada y nuevas pruebas contra falsos positivos; motor físico conservado.

---

## Nilo 0.5.9.3.2 · Manual, diagnósticos y mejoras del motor (2026-10-29)

- Manual operativo consultable por Nilo a través de `manual`; documenta las acciones reales y sus límites, no la física desconocida.
- `inspect` admite objetos fabricados, herramientas llevadas, ID y coordenadas; informa distancia, visibilidad y datos de objeto sin suponer desapariciones. La búsqueda de terreno no queda truncada por la percepción resumida.
- Inicio de proyectos independientes, revisión del progreso estimado, diagnóstico de deliberaciones estancadas y cierre por evidencia física vinculada al proyecto. Un manual consultado nunca se considera un resultado físico.
- Preguntas semejantes se agrupan de manera más consistente. Se avisa antes de ejecutar un ensayo si la variable prevista no tiene un modelo cuantitativo; el descanso comparable puede medir energía recuperada por hora.
- Diagnósticos clasificados como posible error, uso incorrecto o limitación; referencias a evidencias reales y filtros dentro de Propuestas. Los informes no modifican reglas ni código.
- Límite de recolección de alimento cuando ya existen 12 porciones; optimización del archivo para evitar reinsertar registros históricos existentes y hacer crecer artificialmente la secuencia SQLite.
- Nueva cobertura de pruebas funcionales y replay de referencia actualizado tras los cambios intencionales.

---

## Nilo 0.5.9.3.1 · Resúmenes de pendientes y enlaces de estado (2026-10-28)

- Nuevo proceso «¿Qué me perdí?» que sintetiza transversalmente entradas pendientes; no vuelve a narrar registros marcados como leídos. El texto lo elabora un cronista externo con el LLM configurado; cuando la consulta falla, no se marcan registros.
- Al mostrar correctamente el resumen, el cliente confirma únicamente los registros incluidos, preservando los que aparezcan durante la generación. Historial con fecha, texto y vínculos a fuentes originales, guardado en SQLite.
- Estado de lectura persistente por solapa con migración desde preferencias anteriores del navegador; se preservan el clic sobre cada tarjeta y el marcado global de la solapa.
- Se elimina «Archivo y pensamiento» y se renombran los «Resultados comprobados» a «Conocimientos registrados», con acceso directo a Hallazgos. Las «Herramientas que llevo» llevan ahora a la herramienta específica en Creaciones.
- Nuevas pruebas de selección de pendientes, no duplicación, confirmación posterior, persistencia y accesos navegables. Motor físico intacto.

---

## Nilo 0.5.9.3.0 · Trazabilidad documentada entre registros (2026-10-28)

- Nueva capa de relaciones explícitas por identificador, bidireccional y persistente en `record_links.py` y `archive.py`.
- Cuaderno con enlaces contextuales a los proyectos, investigaciones y resultados originados en sus deliberaciones; texto escrito sin modificar.
- Medidas, predicciones, propuestas, diseños y resultados guardan procedencia documental verificable; no se atribuyen resultados automáticos a una deliberación ajena.
- Las fichas relacionadas permiten navegación cruzada entre solapas o consulta histórica de solo lectura mediante `GET /api/record`. Se preserva el primer asiento y se recupera la última revisión disponible de los registros mutables.
- Retrocompatibilidad sin reconstrucción temporal de vínculos, pruebas de grafo real e integración del motor y actualización de la huella de replay por los campos de procedencia.

---

## Nilo 0.5.9.2.9 · Reorganización del archivo (2026-10-28)

- 15 → 12 solapas visibles agrupadas en Vida, Conocimiento, Autonomía e Interacción, con filtros para las fuentes integradas; Versiones pasa a Configuración.
- Novedades/Hechos → Actividad con Destacados/Todos; Inventos/Planos → Creaciones con Diseños/Objetos físicos; Hipótesis aparece junto a Investigaciones, con enlaces a los ensayos correspondientes.
- Nueva vista Hallazgos que diferencia conclusiones respaldadas de propiedades registradas por el motor.
- Memoria: hitos por capítulo y etiqueta explícita para tendencias calculadas. Proyectos: trayectoria, hitos y resultados conservados; no confundir el límite de resultados históricos con el total de éxitos.
- Agenda sin duplicar avisos por registros históricos y ordenada por atención; Conducta sin atribuciones psicológicas por porcentajes automáticos.
- Ensayos filtra pruebas deliberadas y mediciones generales. Saltos entre medición y construcción se actualizan para la nueva navegación.
- «¿Qué me perdí?» es un índice real de pendientes de cada sección. La API local `/api/unread` recupera los no leídos de Cuaderno/Novedades desde SQLite; consulta sin marcarlos como leídos y permite abrir entradas históricas.
- Compatibilidad de ajustes de indicadores anteriores, pruebas de regresión y prueba HTTP de archivo. Motor físico y partida intactos.

---

## Nilo 0.5.9.2.8 · Navegación y legibilidad (2026-10-27)

- Salto por ID de construcción desde «Ver plano, componentes e historial»: apertura de ficha y revisiones, más desplazamiento.
- Barra simplificada y posicionada en tres sectores, sin textos redundantes de novedades; modo Discreto mantiene resaltado de entradas pendientes. También se destacan entradas nuevas de Memoria, Hechos y registros recientes de Agenda.
- Retirados desplegables de identificadores técnicos en Planos y de JSON/ID en Agenda. Los datos internos siguen intactos.
- Códigos de medición legibles y clicables en proyectos, conclusiones, agenda, investigaciones y propuestas; recuperables por API desde el archivo SQLite histórico aunque hayan salido del recorte visible.
- Cabecera del mundo sin «Mundo conocido», etiquetas compactas de coordenadas; glifos transitables a 50 % sin reducir el contraste del rastro.
- Regresiones de navegación, lectura, CSS y recuperación del archivo, además de validaciones previas. No altera física ni LLM.

---

## Nilo 0.5.9.2.7 · Lectura, indicadores y cartografía (2026-10-27)

- Lectura por clic en el contenedor: sin checks de Cuaderno/Novedades ni botones ✓ en otras tarjetas; se mantiene lectura individual persistente en el servidor para los registros archivados.
- Corrección del resaltado que permanecía tras marcar como leída una solapa local. El clic individual retira la señal sin recrear el desplegable abierto.
- Selector contextual Normal, Discreto u Oculto, integrado con los indicadores portables preexistentes.
- Roca azul pizarra; suelo y hierba visualmente más silenciosos en temas Bosque/Grafito/Terracota, manteniendo rastro ámbar.
- Investigaciones enumeran los hechos/fechas vinculados y describen mediciones de conclusiones sin atribuirles confirmación causal.
- Pruebas de interfaz y conservación del archivo de partida y reglas del motor.

---

## Nilo 0.5.9.2.6 · Lectura de Ensayos y Agenda (2026-10-27)

- Ensayos: títulos descriptivos basados en `op`, `target` y posición final **registrada**; `go` pasa a «Desplazamiento hasta (x, y)», con cantidad de tramos si figura en hechos verificados. Acciones restantes traducidas a etiquetas legibles sin inventar resultados.
- Los códigos `go`, `med-...` y estados internos se muestran bajo «Información técnica». «Acción completada» no equivale a «hipótesis comprobada».
- Agenda: activa tareas por condiciones presentadas en lenguaje natural; separa motivación/objetivo, momento de activación, pasos programados y resultados observados. La espera de 60 minutos no se confunde con descansar 60 minutos.
- Detecta el caso de una tarea de descanso que solo registra `conclude` sin operaciones `rest` ni `compare`; advierte que completar la secuencia no demuestra una recuperación energética. Mantiene evidencias y JSON originales.
- Regresiones mediante ejecución JavaScript con los ejemplos «go» hasta (16,16) y «Comparar descanso» con condición de 60 min pero conclusión acerca de la construcción.
- Solo interfaz y documentación; sin cambios físicos, cognitivos ni de base de datos.

---

## Nilo 0.5.9.2.5 · Preferencias, lectura por entrada y fichas técnicas (2026-10-27)

- Nuevo archivo `preferencias_interfaz.json` validado y gestionado vía API localhost: tema, mapa, zoom, vistas, rastro, modos de notificación e indicadores de las subpestañas. Sin credenciales ni cambios cognitivos. El importador de primer uso y `migrar.py` copian preferencias disponibles; las de versiones antiguas en localStorage no son recuperables de otra carpeta sin abrir el navegador original.
- Tarjetas nuevas con fondo temático, marcadores individuales y distinción entre actualizado y leído según las firmas de cada pestaña; Cuaderno y Novedades usan estado de lectura real en servidor. Se elimina «Leído hasta aquí».
- Explicaciones de secciones de laboratorio/agenda/versiones al final del listado cuando hay contenido; Memoria conserva resumen biográfico primero.
- Construcciones en Mundo conocido: ficha contextual breve y enlace a Planos. Planos contiene piezas, historial y revisiones; IDs internos relegados a detalle técnico.
- Herramientas portátiles: retirada la cifra de m² no acreditada por su geometría. Esquema de piezas sin escala, sin convertirlo en un modelo geométrico físico inventado.
- Pruebas de importación, saneamiento, visuales y compatibilidad sin modificar mundo, inventario o leyes físicas.

---

## Nilo 0.5.9.2.4 · Paquete versionado e importación de partidas (2026-10-27)

- Distribución mediante `empaquetar_version.py`: crea `dist/Nilo-<VERSION>.zip` cuya carpeta interna es `Nilo-<VERSION>/`. Selección segura desde manifiesto versionado; excluye datos de usuario, configuración sensible y bases SQLite.
- Nuevo workflow de GitHub `Paquete versionado Nilo`: cuando cambia `VERSION` en `main`, prueba el motor, genera un ZIP y lo publica como activo de GitHub Releases. No modifica el nombre impuesto por GitHub a su propia acción **Code → Download ZIP**.
- Primera ejecución: la opción numérica `0` (además de la letra `O`) permite indicar otra carpeta; se amplía la detección de instalaciones `Nilo-main` y `Nilo-<versión>`, sin depender de una lista histórica fija.
- Entradas de menú inválidas o rutas vacías después de elegir importar abortan el asistente con explicación, **sin** marcar la instalación como configurada ni crear un mundo nuevo por omisión.
- El título de la ventana de inicio deja de exhibir una versión 05.7 obsoleta.
- Regresiones con directorios temporales que verifican copia/importación elegida con 0, O, N, errores y contenido/estructura/seguridad del ZIP.

---

## Nilo 0.5.9.2.3 · Corrección de interfaz y preferencias de avisos (2026-10-27)

- Una única zona vertical de desplazamiento para todo el panel Mundo conocido. Mapa, leyenda y recursos ya no contienen scrolls verticales independientes.
- Selector persistente Mapa y referencias / Solo mapa / Ocultar ambos; controles compactados al tamaño de los botones de velocidad.
- Indicadores por solapa configurables: normal (rojo, agregado en madre), discreto (tono neutro, no participa en agregado de madre) u oculto. Estado de lectura real independiente de la preferencia visual.
- Único botón Marcar como leído que afecta solo la subpestaña activa; Propuestas distingue acuse de lectura local de la decisión de aprobar o rechazar.
- ¿Qué me perdí? abre Chat con un borrador específico de la subpestaña de origen, sin enviarlo automáticamente.
- Barras de desplazamiento adaptadas a Bosque/Grafito/Terracota, con propiedades estandarizadas y WebKit.
- Tests de estructura, comportamiento JS y CSS temático; no se alteran ni física ni base de datos.

---

## Nilo 0.5.9.2.2 · Reparación de obtención de piedra (2026-10-27)

- Recolección: llegar físicamente al depósito y extraer su material se verifican como fases distintas de una misma operación. Sin inventario aumentado no hay éxito de `gather`.
- `gather` usa material normalizado y equivalencias exactas para terrenos observados; se elimina el fallback que recolectaba materiales distintos por coincidencia de ubicación.
- Navegación específica de `gather` ejecuta la extracción al llegar a la casilla de trabajo; avance incompleto registra fallo de extracción en lugar de éxito.
- `inspect piedra` puede identificar el terreno `roca`; planificación anticipa exclusivamente el recurso que produce el depósito indicado.
- Contexto LLM: se exponen contradicciones históricas comprobables entre intención y `inventory_delta`, sin retocar los hechos originales ni adjudicar causalidad.
- Pruebas basadas en el seed 7321, incluyendo piedra en (5,17), afloramiento (7,15) frente a arboleda (7,14), navegador y migración de memoria previa.
- Sin nuevos fenómenos físicos, cambios de propiedades de materiales, ni permisos automáticos de modificación del programa.

---

## Nilo 0.5.9.2.1 · Interfaz compacta y novedades por sección (2026-10-27)

- Se retiran los contadores numéricos en solapas: punto rojo en pestaña hija y madre ante novedades pendientes, sin recolorear solapas. Cuaderno/Novedades usan lectura del servidor; Propuestas conserva su estado pendiente. Las otras categorías detectan registros o versiones nuevas respecto de un marcador local, eliminable solo con «Marcar como revisada».
- Posibilidad persistente de ocultar mapa, controles y referencias sin ocultar materiales, herramientas ni construcciones; mapa replegable de forma reversible.
- «Modelo y consultas» pasa a la ventana Configuración junto a Avisos; permanece visible el estado de LLM en Nilo ahora.
- Disposición de escritorio sin scroll de documento en pantallas suficientemente altas, con scroll en los paneles de contenido extenso; mantiene diseño responsive para móviles.
- No se modifica motor cognitivo, leyes físicas ni memoria SQLite. Tests de estructura, accesibilidad y sintaxis JavaScript, CI y replay.

---

## Nilo 0.5.9.2 · Contraste de predicciones físicas (2026-10-27)

- Campo opcional `prediction` en acciones del plan: hipótesis y efecto esperado, métrica opcional, operador y umbral numérico. Saneamiento en la normalización del LLM.
- Registro en `prediction_log` **antes** de cada ensayo y copia append-only en `history`/`history_revisions`; la revisión posterior nunca borra lo predicho inicialmente.
- Evaluación por métrica numérica devuelta en `ActionResult.physical.metrics`: coincidencia, desacuerdo, variable no medida, física no evaluable o predicción cualitativa. Sin heurísticas de texto ni equiparar éxito de ejecución con hipótesis confirmada.
- Enlace a identificadores de acción `act-...` y medición `med-...`, contexto compacto del LLM con los contrastes y nueva pestaña **Laboratorio → Hipótesis**.
- Sin propuestas automáticas de leyes, modificaciones físicas, llamadas extra obligatorias al LLM ni reescrituras de partidas antiguas.
- Casos de regresión para filtración vs contención, métricas faltantes, incertidumbre y persistencia. CI y replay conservan el comportamiento de runs que no incluyen predicciones.

---

## Nilo 0.5.9.1 · Historial verificable de versiones por mundo (2026-10-27)

- Nueva tabla SQLite `engine_sessions`: entrada inmutable por inicio de ejecución, versión real del archivo VERSION, timestamps UTC, minutos simulados, escenario y entorno; cierre explícito al terminar normalmente. Último guardado sirve como marca de actividad sin inventar un fin ante interrupciones.
- Nueva tabla `session_model_usage`: cuenta proveedor/modelo realmente usado para deliberación o chat. No se confunde con la preferencia de API configurada al inicio.
- Se registra commit Git si existe un repositorio local identificable; las instalaciones ZIP informan «no disponible». Hash SHA256 del manifiesto para identificar el paquete.
- Pestaña **Diario → Versiones** en la interfaz; registros fuera del estado `person` y sin exponer claves ni hechos ocultos.
- Compatibilidad: partidas previas conservan su mundo e historial; solo se añaden nuevas sesiones. No se reconstruyen versiones históricas a partir del formato `version: 5`.
- Suite de regresión 0.5.9.1; la actualización no modifica física, epistemología, prompts ni decisiones anteriores. Siguientes hitos 0.5.9.2–4: contraste de hipótesis, revisión estratégica y comparación de runs. La decisión de modificar código continúa siendo exclusivamente del observador.

---

## Nilo 0.5.9.0 · Primer circuito de autodiagnóstico (2026-10-27)

- `diagnostics.py`: comprobaciones deterministas de integridad (inventario negativo, necesidades fuera de 0..100, coordenadas imposibles en isla_v1 y estado de resultado inconsistente). Nunca interpretan mensajes narrativos como reglas físicas.
- Si una acción ocasiona un incumplimiento de estas invariantes, el motor registra una **posible anomalía** con ID `bug-...`, origen `motor` y el ID de acción `act-...` como evidencia. Los reportes iguales pendientes se deduplican.
- Siguen vigentes `propose` (vacío del motor) y `report_issue` (sospecha de Nilo). Ningún fracaso ordinario genera por sí solo un bug.
- Endpoint local `GET /api/diagnostic?id=...` y botón **Exportar informe JSON** en Propuestas. El paquete reúne motivo, evidencia tipada, ids verificados, estado de revisión y pasos orientativos; incluye hash de integridad. No envía código, secretos ni estado oculto.
- El LLM recibe estado y procedencia de reportes pendientes, con énfasis en separar hechos, hipótesis y capacidad física ausente.
- Revisión humana obligatoria; ninguna aceptación cambia la física. La reproducción aislada automática necesita aún snapshot/RNG/reloj de acción y se realizará en una etapa posterior. Este hito no significa que Nilo edite, pruebe ni repare su propio código.
- Tests de contratos de evidencia, falsos positivos, deduplicación, flujo de revisión e integración UI. Replays anteriores y CI obligatorios.

---

## Nilo 0.5.8.3 · Resultados físicos estructurados, etapa 1 (2026-10-27)

- Nuevo `action_results.py`: `ActionResult` tipado con `status` (`verified_success`, `verified_failure`, `no_evaluable`), hechos narrativos, indicador de interés, duración y evidencia física con métricas.
- `IslandEnvironment.perform_result` toma una instantánea mínima de evidencias antes de ejecutar la acción y determina el estado a partir de registros físicos posteriores, no a partir de frases.
- Las medidas de dureza/resistencia de muestras, flotación, contención de agua y ciertos ensayos de ensamblajes se obtienen de pruebas y conocimientos registrados por el motor; repetir una prueba sin ensayo nuevo no produce otra evidencia.
- `Simulation` conserva adaptadores de compatibilidad para navegación, diseños y otros casos documentales, pero archiva un bloque `action_result` en sus diagnósticos, y pasa el contrato a `experiment_log.measure`.
- `brain.context_for` incorpora `estado_evaluacion`, `evidencia_fisica` y `cambios_medidos` en el historial de acciones que recibe el LLM; la compresión del contexto incluye un subconjunto reciente.
- **Límite:** `world.execute_action` aún conserva su retorno de cuatro valores y `laboratory.measured_physics` permanece como compatibilidad para consumidores legados. Las acciones no físicas y la navegación usan un adaptador al contrato, y algunos consumidores internos todavía utilizan los hechos narrativos. Las propiedades son magnitudes abstractas del motor, no datos experimentales de laboratorio real.
- Pruebas unitarias e integración para impedir evidencia fantasma y verificar que la redacción no altere la clasificación de resultados. Replays deterministas deben actualizar su huella base únicamente tras confirmar la salida estructurada.

---

## Nilo 0.5.8.2 · Reglas de planificación y temas visuales (2026-10-27)

- `island_planning.py` concentra la prevalidación conservadora del plan y el filtro de experimentos, herramientas y operaciones redundantes. `Simulation` conserva métodos delegadores, pero deja de implementar directamente esas reglas.
- El contrato `Environment` admite `validate_plan` e `improve_plan`, además de ejecutar, observar y representar. El adaptador `isla_v1` aplica las mismas reglas anteriores y comunica sus rechazos mediante los mismos eventos y memorias.
- Recuperada la jerarquía cromática del mapa: suelo, hierba y superficies transitables discretas; roca y paredes macizas con fondo y tipografía de mayor contraste. Agua, depósitos, entradas/salidas, obras y rastro siguen distinguiéndose.
- La interfaz ofrece tres temas: **Bosque** (actual, predeterminado), **Grafito** y **Terracota**. El tema elegido persiste en `localStorage` del navegador; no se guarda en la partida ni modifica reglas físicas.
- Nuevas pruebas de plan, rechazo de destinos ocultos, delegación, integridad de pasos y selección de tema. Replays y pruebas anteriores siguen siendo obligatorios.
- **Límite:** la continuación de experimentos, la supervisión de necesidades, las migraciones y partes de la planificación siguen teniendo dependencias de isla_v1. No implica que otros mundos sean ejecutables todavía.

---

## Nilo 0.5.8.1 · Separación de observación y representación (2026-10-27)

- `island_views.py` contiene ahora la interpretación de refugios y fuentes de agua cercanas, y la composición de mapas, estructuras, capas y rastros para la interfaz.
- `Environment` incorpora `surroundings` y `render_map`; `Simulation.tick` y `Simulation.public_state` utilizan esas operaciones sin leer directamente la topología de isla_v1 para esas responsabilidades.
- Se mantiene exactamente el contrato JSON del mapa existente, las reglas de supervivencia y las leyes físicas. Las partidas guardadas conservan su formato.
- Pruebas específicas de condiciones, representación multicapa, niebla de guerra, obras coincidentes y delegación del entorno, además del replay determinista.
- **Límite:** la planificación, las migraciones y parte del contexto LLM todavía dependen de la geografía actual. La separación completa seguirá por etapas.

---

## Nilo 0.5.8 · Primera separación agente / entorno / escenario (2026-10-27)

- `agent.py`: construcción independiente de identidad, inventario, perfil y memoria inicial. La memoria adquirida sigue en `person`, sin reinicios al cargar una partida.
- `scenarios.py`: escenarios explícitos con configuración de entorno, ubicación, equipo y contexto inicial. Se conserva `territorio_desconocido` y se agrega `territorio_sin_equipo` para probar un inicio distinto **en el mismo mundo**.
- `environments.py`: contrato de entorno y adaptador `isla_v1`. Nilo enruta a través de ese adaptador las principales operaciones de ejecución, desplazamiento, validación de destinos y construcción del contexto perceptivo.
- `brain.context_for` acepta el contexto inicial y las reglas del escenario seleccionado, sin permitir que esa descripción modifique hechos del motor.
- `Simulation` carga el escenario del snapshot preexistente en vez de aplicar silenciosamente otra elección; partidas anteriores sin `scenario_id` siguen usando el escenario original.
- `reproducir.py` acepta `scenario_id` para comparar condiciones iniciales con las mismas decisiones y semillas. Los resultados quedan vinculados al escenario elegido.
- Corrección complementaria: una escritura a medio terminar conserva el progreso del snapshot al reabrir la aplicación, sin atribuirle escritura realizada mientras estuvo cerrada.
- **Límite explícito:** migraciones, supervivencia, interfaz y numerosas reglas de planificación siguen acopladas a `isla_v1`. Aún no es posible cargar y jugar mundos arbitrarios completos simplemente cambiando un archivo. Esta revisión define una frontera estable para continuar desacoplando sin cambiar la física.

---

## Nilo 0.5.7.3 · Escritura con tiempo coherente (2026-10-27)

- La escritura del cuaderno aplica ×1 si la velocidad elegida es ×1, y ×2 temporal si es ×10 o ×60; la selección del usuario permanece intacta.
- El reloj simulado y los caracteres escritos avanzan según la misma velocidad efectiva; al terminar se retoma la velocidad elegida, también en un tick que atraviese el fin de la escritura.
- La interfaz distingue la velocidad temporal y calcula correctamente el tiempo restante y la animación de caracteres. Pausar y cambiar la velocidad durante la escritura se respetan.
- Política temporal independiente en `timing.py`, con pruebas de integración; ninguna regla física o registro histórico se altera.

---

## Nilo 0.5.7.2 · Reproducción determinista inicial (2026-10-27)

- `Simulation` admite ahora inyección explícita de ruta SQLite, semilla del mundo y semilla del agente. Sin argumentos mantiene las rutas y semillas anteriores.
- `reproducir.py` ejecuta respuestas JSON del LLM con `plan_ready` y `tick` originales, reloj virtual, UUID y RNG deterministas, sin conexiones API ni servidor.
- Cada ejecución utiliza una base SQLite temporal independiente y calcula SHA256 del estado completo y del archivo histórico, con error explícito por divergencia o límite de ticks.
- Durante deliberaciones reales posteriores a esta versión, los JSON normalizados se guardan en SQLite como `llm_decision`, junto con proveedor, modelo, minuto simulado y huella del contexto, sin credenciales.
- Casos de prueba comparan dos ejecuciones idénticas, divergencias al cambiar semilla o decisión, agotamiento y aislamiento de la partida real.
- Sigue pendiente reproducir **una corrida histórica real**: no se registran aún todas las intervenciones externas, latencias, reintentos y snapshots iniciales. El replay actual usa un guion de decisiones y un inicio por semilla.
- Se corrigió la fuga de no determinismo: `reveal` conserva el orden de descubrimiento en lugar de convertir un `set` en lista; las mediciones registran deltas en orden canónico. Esta corrección es necesaria para repetir rutas de exploración con el mismo RNG.
- CI compara ahora procesos independientes con diferentes `PYTHONHASHSEED` y comprueba el mismo SHA256 integral.
- Ninguna ley física se modifica. La instalación y las partidas preexistentes permanecen compatibles.

---

## Nilo 0.5.7.1 · Métricas de conducta observada (2026-10-27)

- Preserva como histórico el primer intento 0.5.7-alpha.1 en `archive/0.5.7-alpha.1`. El segundo intento es la base de desarrollo (0.5.7).
- Nuevo `behavior.py`: registra resultados completados desde esta actualización, sin reconstruir retrospectivamente la vida anterior. Tipos y orígenes de acción, duraciones efectivamente medidas, novedad objetiva, lugares visitados y proyectos cambiados.
- Las métricas se exponen a la interfaz (Autonomía → Hábitos), al estado público y al contexto del LLM. En contexto compacto pueden omitirse antes que proyecto actual y conclusiones.
- Las continuaciones locales creadas por el motor quedan identificadas como `_origin=motor`, sin atribuirse como nuevas decisiones del LLM.
- Nuevas pruebas de regresión para origen, cifras, incertidumbre temporal y compatibilidad de datos antiguos.
- Sin alteración de las leyes físicas, ni de los archivos SQLite existentes. El contador comienza sin valores al migrar.
- Pendiente: ejecutar la batería completa en Python y ampliar el arnés para reproducir deliberaciones; aún no implica que esas etapas estén completas.

---

## Nilo 0.5.7 · Consolidación (2026-10-27)

Navegación solo por conocimiento observado; compuestos físicos persistentes; preservación de contexto de proyecto; acciones no inyectadas; metadatos históricos en lote; mapa multicapa, navegación agrupada, reloj visible y ejecución determinista de escenarios. Los resultados de acciones ahora contienen deltas numéricos y un estado tipado (transición parcial).

# 0.5.6.3 — Planificación autónoma y estabilización
- Agenda de acciones diferidas, pasos enlazados y condiciones verificadas.
- Detector de estrategias repetitivas que impide insistir sin cambios físicos comprobables; autonomía de salida y otras técnicas disponibles.
- Reconciliación de proyectos iniciales cumplidos con evidencia del motor; consolidación idempotente de investigaciones.
- Inspección estricta de objetivos y errores claros cuando no están disponibles.
- Pausa automática configurable solo sin acciones pendientes, tareas temporizadas ni LLM; reloj real y reintentos del proveedor continúan.
- Control de reintento manual sin eludir HTTP 429 ni límites de solicitudes.
- Registro de agenda, resultados físicos, razón de selección y estado de inactividad en interfaz.
- Importación de partidas anteriores sin sobrescribir originales; pruebas de regresión.

# 0.5.6.2
- Portal de salida en cuevas y ascenso con ruta conocida.
- Resultados no evaluables de física ausente y evidencia para propuestas.
- Mejora de contraste del mapa subterráneo.

# Nilo 0.5.6.1 — Estabilización

- Hábito de descanso: objetivo alcanzable (<70), prioridad hídrica sin bucles.
- Autonomía: navegación hasta una orilla de agua ya conocida, verificada y transitable.
- Migración explícita de abrigo y seguridad previamente agotados a cero por modelo sin amenazas.
- Groq: contexto reducido estructuralmente, máximo de tokens de respuesta acotado; error 413 distinguido.
- Las pruebas físicas de versiones anteriores de objetos quedan en historial, no certifican revisiones nuevas.
- Tooltips accesibles en las cinco necesidades (cursor y foco de teclado).

No se han agregado criaturas ni peligros físicos nuevos. No reemplazar la partida anterior sin copia.

- El resumen de pendientes se pagina de diez entradas por consulta, para preservar evidencia completa incluso con Groq y evitar solicitudes 413.
