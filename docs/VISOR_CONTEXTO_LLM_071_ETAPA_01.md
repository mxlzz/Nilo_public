# Visor literal de contexto LLM · Etapa 01 — Auditoría y contrato de diseño

**Fecha:** 2026-11-06. **Base auditada:** `main`, Nilo `v0.7.0` (commit `308d9ae88f5526588db4e221ade4a4d4811e1cb2`). **Trabajo:** rama `work/0.7.1-visor-contexto-llm`.
**Resultado:** auditoría estática del código vigente, contrato de fidelidad y propuesta de puntos de instrumentación. **No captura aún solicitudes reales, no introduce UI nueva y no modifica reglas del motor.**

## 1. Requisito funcional acordado

El visor simplificado debe mostrar **el contenido literal que recibe el modelo**, separado en bloques desplegables, conservando nombres, valores, textos, orden y estructura. Cada bloque tiene el **título original** y un **subtítulo explicativo breve**, que es metadato del visor y **NO** se inyecta al prompt. Consultar «origen» permite descubrir módulo, estado/campo fuente, regla de transformación y paso en que se produjo ese valor, sin ocultar que el origen puede ser compuesto o todavía no instrumentado.

«Simplificado» significa **separación y navegación**, nunca interpretación, traducción, síntesis ni modificación del contenido. La vista técnica consulta el mismo registro y agrega JSON HTTP completo, bytes, hash, proveedor/modelo, cortes, omisiones, diagnósticos y correlaciones. Ambas vistas serán clientes del mismo servicio de solo lectura.

**Terminología de verificación:** `vista previa` (construido, no enviado), `preparado` (serializado para transporte), `intento HTTP` (transporte invocado), `respuesta recibida` y `deliberación aceptada` son estados distintos. Ni una llamada HTTP sin respuesta ni un hash demuestran por sí solos recepción por el servicio remoto.

## 2. Recorrido del dato en el motor actual

| Paso | Implementación vigente | Contenido y efecto |
| --- | --- | --- |
| A. Estado real | `nilo_runtime/application/session.py` y `Simulation.s` (mundo, persona, archivo y reloj) | Datos originales, incluidos estados que no son conocimiento del personaje. |
| B. Percepción | `environments.IslandEnvironment.perceive` → `brain.context_for`; `nilo_runtime/application/decisions.py:think` añade `conversaciones_recientes` y `regla_chat` | Contexto completo anterior a la selección. Las últimas 16 entradas de eventos y 8 chats se incorporan en esa ruta de deliberación. |
| C. Proyección cognitiva | `cognitive_projection.project_context`, invocada dentro de `build_deliberation_request` | Clona datos; convierte necesidades a percepción, oculta métricas internas, cambia representaciones de herramientas/proyectos/estructuras y construye `antecedente_relevante`. No modifica SQLite. |
| D. Perfil | `nilo_runtime/core/lab_settings.py` → `_LAB_OMIT_CONTEXT`, `_LAB_PROMPT_NOTE` en `gateway` | Solo nueve campos opcionales pueden omitirse; la nota complementa instrucciones, nunca modifica la física. |
| E. Selección y presupuesto | `nilo_runtime/agent/budget.py`: `compact_context` → `bounded_context`; presupuestos específicos en `gateway` | Elimina campos enteros o entradas completas según prioridad y tamaño. Puede transformar `proyecto_actual` y acortar listas; añade `contexto_reducido`. Nunca asumir que toda la información de B llega a F. |
| F. Solicitud por proveedor | `gateway.build_deliberation_request` | Gemini: `systemInstruction` contiene SYSTEM (+nota) y `contents[0].parts[0].text` contiene contratos de operaciones, «SITUACIÓN REAL: » y JSON compacto. Groq: `messages[0].content` contiene GROQ_SYSTEM + operaciones abreviadas (+nota) y `messages[1].content` contiene JSON; también `reasoning_effort=low` y presupuesto de cuerpo de 14.500 bytes. OpenAI-compatible usa el contrato extenso y otro presupuesto. |
| G. Ruta efectiva/fallback | `providers.candidate_configs` → `providers.route` → `gateway.request_llm` | La misma percepción B puede producir payloads diferentes según modelo/proveedor; un intento fallido y el siguiente no son intercambiables. Se aplican reintentos, cooldowns y fallback. |
| H. Frontera HTTP | `gateway._post` | `json.dumps(payload,ensure_ascii=False).encode("utf-8")` es **el cuerpo exacto generado para la petición**. Los headers contienen credenciales y no forman parte del contenido mostrado ni persistido. |
| I. Resultado | `gateway._response` → `parse_json` → `normalize_decision` → `Simulation.plan_ready` | La respuesta puede fallar por red, formato o contrato. Solo decisiones aceptadas producen una acción. El historial `llm_decision` se agrega después de una deliberación exitosa. |

**Chat:** `Simulation.start_chat` prepara otro contexto (hasta 30 eventos, cuaderno, mediciones e historial de conversación), llama a `gateway.build_chat_request` y usa el mismo `_post`. Los roles y la estructura de chat son distintos; el diseño debe identificar `purpose=deliberacion|chat` y no interpretar las conversaciones como decisiones autónomas.

## 3. Fuentes principales de los campos actuales

Esta tabla registra familias de origen verificadas en `brain.context_for`. **No es una afirmación de que siempre se envíen**: la etapa 03 enumerará los campos *realmente presentes* a partir de cada solicitud capturada; la etapa 04 asignará procedencia granular, incluidas transformaciones y campos anidados.

| Campos (nombres literales) | Fuente actual identificada | Transformaciones relevantes |
| --- | --- | --- |
| `momento`, `posición`, `mundo`, `necesidades` | Reloj/posición de `person`, `survival.perceived_needs` en `brain.context_for` | Reservas internas corporales se expresan como sensaciones; `_cognitive_needs_context` sanea legados. |
| `inventario_materiales` | `person.inventory` | Cantidades positivas; se conserva como campo básico del presupuesto. |
| `percepción_local`, `salida_conocida`, `orillas_agua_conocidas_alcanzables`, `navegacion_a_lugares` | `world_view`, `known_exit_route`, `reachable_shores` y `known_site_routes` | Dependen del conocimiento del mapa; truncados/priorizados en presupuesto. |
| `proyecto_actual`, `proyectos_reanudables`, `antecedentes_relacionados`, `ultimo_cierre_rechazado` | `person.project`, `person.projects` y `person.last_closure_rejection` | `cognitive_projection._proyecto` omite `progress` y limita evidencias; `compact_context` restringe campos; ciertos antecedentes dan lugar a `antecedente_relevante`. |
| `investigaciones_activas`, `investigaciones_pausadas_relacionadas` | `projected_research` y `person.research` | Selección de campos, hipótesis/evidencias y últimos registros. |
| `mediciones_reales_recientes`, `resultados_de_acciones`, `diagnosticos_operativos_recientes` | `person.measurements`, `action_outcomes` | Las cifras corporales se incluyen solo cuando el propio tema de investigación las requiere; recorte por presupuesto. |
| `conocimiento_con_procedencia`, `conclusiones_verificadas`, `memorias_relevantes` | Proyecciones de cognición y `recall_relevant` | Selección por relevancia; las listas se acortan en `budget`. |
| `herramientas_que_llevo`, `construcciones_fijas` | Inventario de objetos y `visible_structures` | `project_context` sustituye scores de desgaste y potencia calculada por información observable. |
| `preferencias_en_espera`, `agenda_diferida`, `recordatorios_listos` | `person.waiting_preferences` / `agenda` | Se incluyen según disponibilidad y presupuesto. |
| `regla`, `situacion_inicial`, `escenario_id`, `entorno_id` | `scenario.world_rule`, `scenario.introduction`, `scenario` | La introducción depende del inicio de partida; la regla del escenario sustituye al texto base. |
| `conversaciones_recientes`, `regla_chat` | `Simulation.think`, historial `s.chat` | Se añaden **después** de `context_for`; aun así pueden quedar fuera del payload compacto deliberativo. |
| Instrucciones fuera del JSON | `nilo_runtime/agent/prompts.py`; `action_contracts.instructions` o `brief_actions` | Gemini y Groq difieren en texto y ubicación entre roles; las variantes no deben presentarse como idénticas. |

**Importante:** el origen de un campo puede requerir más de una referencia (por ejemplo `momento` viene del reloj, `construcciones_fijas` de estado + proyección). No asignar ficticiamente un módulo único por comodidad de la UI. Una variable sin mapeo validado se mostrará como **origen aún no instrumentado**.

## 4. Qué existe en el laboratorio y qué falta

**Ya existe:**
- `laboratorio_contexto.solicitud_completa` extrae mensajes con valores y roles desde `build_deliberation_request` en una simulación de prueba, sin hacer consultas. `auditar_contexto_llm.py` audita cuatro estados sintéticos en Gemini, Groq y OpenAI-compatible.
- `nilo_runtime/labs/hub.py` permite vista previa/comparación de perfiles con el mismo constructor y envía `solicitud_json`, `campos_enviados`, omisiones y `mensaje_sistema` a su interfaz.
- `nilo_runtime/core/lab_settings.py` y `nilo_runtime/labs/profiles.py` ya resuelven perfiles, validación de omisiones, notas y checkpoints. `SimulationSandbox` ejecuta acciones físicas con el motor real en una SQLite temporal.
- `archive.History` tiene `history(category='llm_decision')`. Guarda una respuesta **normalizada** aceptada, proveedor, modelo, hash `context_sha256`, estadísticas y timestamp simulado. `RunHistory` guarda identidad/versionado y recuentos por modelo y propósito.

**Faltan, y por eso no se debe prometer aún un visor histórico literal:**
1. Persistencia del **cuerpo exacto HTTP** de cada intento: hoy no se guarda, ni tampoco el texto literal final de prompts de un intento concreto.
2. Identificador de correlación **deliberación → intento de proveedor → contenido enviado → respuesta/validación → acciones/mediciones**. El hash actual de `llm_decision` se calcula sobre el contexto de B **antes** de proyección/recorte y no permite recuperar F/H.
3. Registro de intentos fallidos/reintentos y fallback por proveedor: `session_model_usage` cuenta respuestas exitosas, no mensajes HTTP individuales.
4. Tabla/mapa granular de procedencia por ruta JSON y por etapa de transformación; los `campos_omitidos` actuales son diferencias de conjuntos, no diagnósticos completos del porqué de cada exclusión.
5. Separador por bloques **sobre la cadena original**, no sobre un JSON reinterpretado. El visor debe conservar texto y bytes; los subtítulos no pueden contaminar esa cadena.
6. Endpoint de consulta histórica de solo lectura y políticas de retención/privacidad del texto íntegro.

## 5. Contrato para las próximas etapas (propuesta técnica)

### Unidad de captura (etapa 02)

Capturar el cuerpo `utf8` **exacto en la frontera `_post`**, antes de llamar a `urlopen`, preservando el orden serializado. Instrumentar también el router para correlacionar intentos y fallback sin cambiar la selección del proveedor ni el resultado de su handler.

Metadatos mínimos: `request_id`, `deliberation_id` (o `chat_id`), `session_id`, `purpose`, `attempt_index`, `provider`, `model`, `prepared_at`, `transport_attempted_at`, `outcome`, `body_sha256`, `body_bytes`, `engine_commit`, `profile_sha256` y referencias a `llm_decision`/historial cuando existan. Los IDs no se deben construir a partir de fragmentos ambiguos del texto.

**Recomendación:** tabla técnica SQLite local y separada lógicamente del conocimiento de Nilo (en la misma partida o con estrategia de exportación que garantice no perder vínculos). Definir en etapa 02 conservación, migración y manejo de escrituras sin bloquear una decisión; no publicar jamás cuerpos de solicitud, claves ni recuerdos en el repositorio.

**Garantías:** (a) una excepción del observador no interrumpe a Nilo; (b) no almacenar headers de autenticación ni URL con secretos; (c) sin cambios en payload ni comportamiento LLM; (d) no atribuir «recibido» al proveedor sin respuesta; (e) distinguir solicitudes de deliberación y de chat; (f) cada fallback constituye un intento distinto asociado a una sola deliberación.

### Bloques literales (etapa 03)

Descomponer la **cadena exacta de texto de cada rol** mediante un índice de segmentos. Para contexto JSON, identificar bloques por **clave original presente** con su porción literal, sin `json.dumps` adicional, sin renombrar ni reordenar. Para instrucciones de sistema/contratos, conservar el texto del rol de forma íntegra; subtítulos fuera de la cadena original. Mostrar orden, tipo, estado y longitud. Mantener una vista «cuerpo HTTP completo» para reconstrucción/verificación y un test de fidelidad que compruebe que la segmentación conserva exactamente el texto de partida.

### Orígenes y API (etapas 04–05)

Registro trazable por `JSON Pointer` o ruta de mensaje: estado fuente, función que calcula, transformaciones (proyección/perfil/compactación/presupuesto), valores y exclusiones, con **evidencia verificable** y etiqueta de incertidumbre si hay atribución incompleta. API local de **solo lectura** que sirva los registros ya capturados; no recalcular contextos históricos desde una partida que siguió evolucionando.

### Presentación (etapa 06)

Vista simple: selector de intento, agrupación por rol y bloques del JSON, **título original + subtítulo breve + contenido literal desplegable**, con acceso opcional al origen. Vista profesional: mismo registro más bytes/hash, historial de fallbacks, diferencias, mapa de procedencia y diagnóstico. No asignar al modo «simplificado» el significado de resumir o explicar el contenido.

## 6. Puertas de calidad / riesgos descubiertos

| Caso de prueba | Criterio de salida |
| --- | --- |
| Gemini deliberación | Capturar `systemInstruction` y texto completo `contents`, incluidos contratos y JSON; coincide en bytes con el cuerpo que se envía. |
| Groq deliberación | Capturar `messages` y presupuesto final después del último recorte, no antes; registrar `model` y `reasoning_effort` del intento. |
| Fallback/reintento | Dos HTTP = dos registros de intento, con igual deliberación y distintos bytes/modelo si corresponde. |
| Chat | Historial y roles reales, separado del motor autónomo. |
| Listas recortadas/campos omitidos | La vista simple solo presenta lo **presente**; la técnica explica los descartes rastreados. |
| Integridad y compatibilidad | Ningún campo agregado al contexto del LLM; mismo payload y mismo comportamiento con y sin observación. SQLite anterior abre y permanece íntegra. |
| Privacidad, fallos y rendimiento | Datos crudos locales con retención configurable, sin exportación implícita; la telemetría no bloquea solicitudes ni contamina `History` cognitivo. |

**Límite del legado:** los snapshots del run del 5–6/11 conservan 566 decisiones y hashes del contexto, pero **no** el cuerpo HTTP literal. La instrumentación futura no puede retroactivamente recuperar ese cuerpo de un hash.

## 7. Cierre de etapa 01 y continuidad

La auditoría identificó los componentes y las diferencias entre **percepción, proyección, selección, payload final y transporte**; determinó el punto de captura y el contrato de fidelidad. Queda disponible un test de referencia del gateway sin red para fijar las formas de Gemini/Groq, sin modificar su conducta.

**Etapa 02:** implementar trazas de solicitudes **por intento real** en la frontera de transporte y su correlación con el router, con redacción de secretos HTTP, migración, retención y tests. Las vistas visuales permanecen pendientes hasta etapa 06. Esta rama es independiente de [PR #78](https://github.com/mxlzz/Nilo_public/pull/78) (corrección de proyectos).

## Evidencia posterior de etapa 01

Los workflows [#42240559090](https://github.com/mxlzz/Nilo_public/actions/runs/42240559090) (PR) y [#42240518998](https://github.com/mxlzz/Nilo_public/actions/runs/42240518998) (push) finalizaron **success**. La etapa 01 queda técnicamente validada y se continúa con la [etapa 02](VISOR_CONTEXTO_LLM_071_ETAPA_02.md). No se atribuye a la auditoría la captura histórica, que recién se implementa en esta nueva etapa.
