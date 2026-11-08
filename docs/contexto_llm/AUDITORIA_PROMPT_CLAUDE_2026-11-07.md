# Nilo 0.7.1 · Auditoría conjunta del primer prompt y propuesta Claude v2
**Fecha:** 2026-11-07  
**Estado:** análisis y decisiones preliminares; NO implementado en el motor.  
**Seguimiento vivo:** [issue #31](https://github.com/mxlzz/Nilo_public/issues/31) · relacionado [#63](https://github.com/mxlzz/Nilo_public/issues/63), [#70](https://github.com/mxlzz/Nilo_public/issues/70) y [#3](https://github.com/mxlzz/Nilo_public/issues/3).

## 1. Material de referencia y versión examinada

Propuesta externa íntegra (sin aplicar al ejecutable):

- [`prompt_nilo_v2.md`](propuestas_externas/claude_2026-11-07/prompt_nilo_v2.md) · SHA-256 del archivo recibido `778ae4f3fe9174897a0d6f2af784a12f6d96253928576556e089094193295309`.
- [`nilo_harness_notas.md`](propuestas_externas/claude_2026-11-07/nilo_harness_notas.md) · SHA-256 `c16d8d09fa2aebabdb1aa06c6b4773c0d488edcd56aca369998797ef90ee0fcf`.
- [`nilo_response_schema.json`](propuestas_externas/claude_2026-11-07/nilo_response_schema.json) · SHA-256 `8d9baef60c4cfc5dee798cf3bb7f8e46a3e9ba7d49651719cc01013f45739eef`.

Contrastado con el código de `main` y `work/0.7.1-lab-ui-stage04-visor`. Los contratos `prompts.py`, `budget.py`, `responses.py`, `operations.py` y `agenda.py` presentan las mismas versiones en ambas referencias. `gateway.py` sí varía por instrumentación del visor; se usó la versión de la rama UI para examinar la serialización literal y traza.

Observaciones del análisis anterior del run real (registradas en conversación, a confirmar al integrar muestras de regresión): primera petición 31.191 bytes; 16.066 bytes de instrucciones del sistema; 11.878 bytes del manual operativo; estado dinámico de aprox. 2.134 bytes; 33 de 41 campos de situación vacíos o nulos; 19 intentos capturados. Estas cifras son medidas históricas del run, no un benchmark del nuevo diseño.

## 2. Veredicto sobre cada propuesta

| Propuesta de Claude | Veredicto | Fundamento y trabajo necesario |
|---|---|---|
| Prompt organizado por identidad, reglas del mundo, decisión, formato | **Adoptar como arquitectura** | Reduce duplicaciones y separa política permanente de contratos técnicos; conservar autonomía sin imponer una agenda. El texto candidato NO está validado para reemplazo literal. |
| Instrucciones condicionales según datos presentes | **Adoptar con cambios** | El contexto ya se proyecta (`cognitive_projection.py`) y compacta (`budget.py`), pero `SYSTEM`/manual extenso se envían íntegros a Gemini. Reglas detalladas condicionales sí; índice de todas las acciones siempre visible. |
| Omitir `null` / `[]` | **Adoptar con excepciones** | `compact_context` conserva campos vacíos y pone `contexto_reducido` siempre. Mantener explícito el cero/ausencia cuando semánticamente importa (sin proyecto, sin ruta conocida, lista vacía que acredita búsqueda). Nunca omitir `0`, `false` ni hechos negativos relevantes. |
| Sustituir reglas repetidas por `nota` contextual | **Adoptar concepto, adaptar formato** | Enviar aclaraciones junto al campo relevante y solo si está presente; evitar `nota` inyectada indiscriminadamente en objetos de evidencia. Separar valor y metadatos de interpretación, con procedencia y prueba sobre payload HTTP. |
| Eliminar redundancias de `regla` | **Adoptar** | `brain.context_for` construye una regla repetitiva; `prompts.SYSTEM` y `action_contracts.instructions()` describen gran parte de lo mismo. Comprobar semántica antes/después. |
| `contexto_reducido` solo si se compactó de verdad | **Adoptar** | `budget.compact_context` lo añade incondicionalmente, y menciona un diario sin operación de consulta explícita. Debe significar una reducción realizada, idealmente con razón y conteos (no revelar información interna innecesaria). |
| `metricas_validas` obtenidas del registro del motor | **Investigar/adoptar si verificable** | Evitar ejemplos que sesguen hacia recipientes; publicar solo métricas que el motor puede medir y que Nilo podría conocer, idealmente ligadas a capacidad/ensayo, nunca declarar disponible una métrica no implementada. |
| Ocultar parámetros numéricos de fisiología en manuales/agenda | **Prioridad alta** | `operations.py` describe `drink` con `0,18` y `+27 hidratación`; `prompts.py` describe `menor_que:60`. Esto contradice la proyección perceptiva de necesidades por sensaciones. Corregir información expuesta SIN cambiar el metabolismo. |
| Arreglar contrato de `descend` | **Adoptar** | `operations.ACTION_GUIDE['descend']` reutiliza texto de `ascend` y no enseña la sintaxis propia. La validación física exige entrada accesible; detallar la precondición sin inventar portales. |
| Glosario técnico de resultados | **Adoptar parcialmente** | Útil condicionalmente cuando aparece tal estado; verificar vocabulario real de las distintas capas de diagnóstico antes de fijar equivalencias. No exigir ID de medición para TODO éxito físico: desplazamientos y balances pueden verificarse mediante resultados tipados. |
| Plan de 2 a 12 acciones obligatorio | **No adoptar así** | `responses.normalize_decision` permite una operación y hasta 12; solo exige al menos una si no se cierra/pausa/abandona. Forzar 2 puede crear acciones de relleno y modificar autonomía. Contrato propuesto: 1–12, o [] solo en cierre/pausa/abandono. |
| `sin_proyecto` significa proyecto_actual null | **Corregir en propuesta** | `application/decisions.py::plan_ready` puede conservar el proyecto existente cuando la actividad actual es `sin_proyecto`; no equivale necesariamente a no tener proyecto guardado. |
| Prohibir repetir ensayo salvo variable escrita en cuaderno | **No como obligación universal** | Se puede considerar evidencia previa, pero forzar declaración textual de variación transforma el criterio analítico en misión o bloqueo artificial. Solo exigir comparabilidad cuando la operación/experimento realmente lo necesita. |
| `agenda`/rutinas solo con habilidades verificadas | **No adoptar como regla global** | Las rutinas automáticas sí tienen restricciones de aprendizaje. En cambio, agenda admite decisiones diferidas y recordatorios no ejecutables, incluso sin habilidades; descartarlos silenciosamente suprimiría una capacidad voluntaria. |
| Límite 3 tareas agenda, versus límite actual 6 | **Decisión de diseño, no corrección técnica** | `set_agenda` acepta hasta 6 entradas por deliberación. No cambiar capacidad por el ahorro de un prompt sin evaluación. |
| `cuando_necesidad`: `hambre/sed/cansancio`, `nivel:algo/mucho` | **No compatible hoy; diseñar adaptador** | `autonomy/agenda.py` solo acepta `hidratacion/nutricion/energia` y `menor_que` numérico. Un cambio aislado de prompt produciría tareas inválidas que `set_agenda` descarta. Propuesta: capa perceptiva cualitativa, conversión interna explícita y versionada, tests de frontera y conservación de partidas previas. |
| JSON Schema de respuesta para Gemini | **Prototipar, NO desplegar sin pruebas** | Puede reducir JSON inválido pero NO sustituye la validación semántica/post-schema. El archivo externo incluye 26 operaciones y 44 campos en un objeto genérico de paso, con múltiples claves `nullable`, distinto a contratos por operación. Ver sección 3. |
| Temperatura 0,85 → 0,65; 2300 → 4096 tokens salida | **Hipótesis de experimento** | No hay evidencia en el run que justifique atribuir mejoras a estos valores. Comparar tasa de respuestas truncadas, calidad de planes, latencia y coste con mismo escenario. No actualizar silenciosamente. |
| Reintento por `MAX_TOKENS` recortando plan/agenda | **Reformular** | Capturar `finishReason`, diferenciar truncamiento de error JSON, limitar reintentos y preservar la intención cuando sea recuperable; imponer plan ≤6 y eliminar agenda en un retry puede cambiar sustancialmente la decisión autónoma. |
| `mensaje_sistema` duplicado dentro del HTTP Gemini | **No constatado** | En `gateway.build_deliberation_request`, el texto de sistema va en `systemInstruction.parts[0].text`; el mensaje del usuario contiene manual + `SITUACIÓN REAL`. Un rótulo de observabilidad no constituye segundo campo enviado. Contrastar cuerpo HTTP real. |
| Bloque condicional de delegación | **Adoptar modularización, no gatillo único** | No mostrar manual extenso de delegación cuando no aporta, pero conservar el descubrimiento de la funcionalidad; activarlo cuando exista aprendizaje, agenda, planificación de mantenimiento o interés expresado, no solo cuando `habilidades_verificadas` sea no vacío. |

## 3. Hallazgos adicionales al revisar el código actual

### 3.1. `prediction` en `design`: incompatibilidad real entre dos validadores
En `nilo_runtime/core/operations.py`, `validate_operation` admite `prediction` **string** cuando `op=="design"`. Sin embargo, `nilo_runtime/agent/responses.py::normalize_decision` invoca `normalize_prediction` y elimina `prediction` si la operación no está en su conjunto, que **no incluye design**. Por lo tanto, la predicción textual de diseño puede perderse al normalizar una decisión LLM. La solución de Claude (`design_prediction` más remapeo) es viable solo si existe un adaptador explícito en el lado servidor antes de la normalización, con tests. Otra solución es separar esquemas por operación sin cambiar el contrato interno.

**Acción:** prueba unitaria del circuito normalizador → diseño; corregir sin alterar los otros tipos de predicción.

### 3.2. Campos `nullable` de Claude pueden producir la cadena literal `"None"`
El candidato usa muchas propiedades opcionales con `nullable:true`. El código actual normaliza campos con `str(raw.get("pregunta", ""))`, `str(raw.get("hipotesis", ""))`, `str(raw.get("proyecto_id",""))` y otros. Con un campo presente y `null` se convierte en **`"None"`**, no en ausencia. Este efecto es compatible con el `prueba_cierre:"None"` observado en el análisis previo del run; no se afirma que sea su causa única.

**Acción:** normalización tipada de opcionales (None→vacío o ausencia según semántica), más pruebas con todos los campos opcionales; luego recién integrar schema.

### 3.3. `cuaderno` y las acciones no respetan el mismo límite que las instrucciones
El prompt actual exige máximo 350 caracteres; `responses.normalize_decision` corta a **500**, no 350. La propuesta de Claude mantiene 350. No es una falla física, pero contrato y validación son distintos.

**Acción:** elegir un único límite y aplicarlo en el validador, no solo en prosa.

### 3.4. La semántica real de fallos de plan ya está instrumentada
En `application/clockwork.py`, un fallo NO aborta necesariamente todo el bloque. La navegación bloqueada puede vaciarlo; un `craft/build` fallido cancela `use` dependientes del objeto; un `gather` fallido quita pasos de fabricación dependientes del material; otras acciones independientes continúan. Una acción de agenda fallida cancela los pasos de esa misma agenda. Sustituir el marcador `[DEFINIR SEGÚN MOTOR]` por este contrato factual, no crear un comportamiento nuevo.

### 3.5. `responseSchema` no es un validador de capacidades físicas
El esquema externo contiene **26** valores de `op`, coincidentes con el conjunto nominal actual, y **44 propiedades** posibles en el tipo genérico de cada paso; acepta muchos parámetros que no corresponden a una operación concreta y muchas propiedades nullable. La compatibilidad nominal no verifica precondiciones, coherencia de componentes, disponibilidad ni cierre de proyecto. Un esquema único extenso también añade volumen al JSON HTTP y debe probarse con el endpoint/modelo elegido.

La documentación oficial vigente de Google describe compatibilidad de *structured outputs* con un subconjunto de JSON Schema y recomienda validación adicional de valores semánticos: https://ai.google.dev/gemini-api/docs/structured-output y https://ai.google.dev/api/generate-content. Antes de elegir entre `responseSchema` y `responseJsonSchema`, fijar endpoint y contrato activo; NO mezclar ambos. Mantener fallback seguro si el proveedor lo rechaza y registrar la incompatibilidad.

### 3.6. Los recortes actuales no son una política de relevancia suficiente
`brain.context_for` genera numerosas secciones; `compact_context` incluye un listado fijo aunque los valores estén vacíos; `contexto_reducido` se agrega sin verificar la reducción real; `bounded_context` recorta por bytes, y `context_focus` clasifica principalmente el proyecto activo. Una actividad de fabricación dentro de un proyecto llamado exploración puede seguir tratándose como navegación. Ver [issue #31](https://github.com/mxlzz/Nilo_public/issues/31). Distinguir reducción de bytes, pertinencia cognitiva y recuperación de memoria bajo demanda.

### 3.7. La información ausente también puede ser relevante
No convertir automáticamente `[]`, `null`, `false` y `0` en equivalentes. Ejemplos:
- `proyecto_actual:null` sirve para expresar que no tiene proyecto activo, aunque puede codificarse mediante un estado compacto.
- `navegacion_a_lugares:[]` puede describir ausencia de rutas CONOCIDAS, no inexistencia de lugares físicos.
- `resultados_de_acciones:[]` no necesita un bloque en la primera deliberación si el motor sabe que no hubo operaciones, pero sí cuando conviene distinguir registro perdido de resultado vacío.
- `revisiones/diagnósticos:[]` no equivalen a «no hubo errores físicos».

Se requiere un catálogo semántico de omitibles por campo, no un filtro recursivo indiscriminado.

## 4. Propuesta técnica mínima — versiones comparables

No aplicar directamente `prompt_nilo_v2.md` como prompt productivo.

### Etapa C0 · Congelar baseline y matriz de invariantes
- Capturar primera solicitud y algunos turnos de navegación/fabricación/ensayo/agenda de una misma corrida, con SHA-256 y sin credenciales.
- Congelar comportamiento anterior de `normalize_decision`, `set_agenda`, `build_deliberation_request`.
- Métricas: bytes/tokens reportados por proveedor, cantidad de secciones útiles/duplicadas/vacías, rechazo semántico, validez de acciones, reintentos y fidelidad de evidencias.

### Etapa C1 · Corregir contratos contradictorios
- Manual de `descend`; plan 1–12 y vacío solo en cierre/pausa/abandono; regla real sobre fallos parciales.
- Recuperar/normalizar `prediction` textual de `design`; tratar `None` correctamente.
- Retirar de la percepción instrucciones con valores fisiológicos internos; diseñar traducción de agenda cualitativa a umbrales internos antes de modificar su salida.
- Unificar límite del cuaderno.

### Etapa C2 · Limpiar contexto sin falsificar ausencias
- Semántica por campo: `keep`, `omit_if_empty`, `presence_marker`; no perder falsos/ceros ni información negativa significativa.
- `contexto_reducido` solo si hubo reducción; `regla` sin repeticiones; deduplicar hechos por ID manteniendo procedencia y resultados físicos.
- En payload A/B, mostrar razones de inclusión/exclusión y bytes antes/después.

### Etapa C3 · Componer reglas y manual por pertinencia
- Núcleo permanente corto (identidad, autonomía, verdad física, contrato de respuesta).
- Índice **exhaustivo de 26 operaciones** accesible siempre, con detalle contextual sin inventar capacidades.
- Activar instrucciones según datos/entidades, actividades actuales y recientes y temas investigados, con **múltiples focos simultáneos**; no inferir deseos nuevos de Nilo.
- `nota` contextual con procedencia y ninguna obligación psicológica/cognitiva nueva.

### Etapa C4 · Prototipo de salida estructurada
- Experimento separado con esquema correcto para el endpoint Gemini actual; de ser útil, componer esquemas desde registro de operaciones.
- Validación local obligatoria por operación y por ciclo de proyecto; opcionales nulos seguros; `design.prediction` preservada; parámetros desconocidos rechazados/diagnosticados.
- Reintento acotado solo ante fallo identificable; no cambiar automáticamente las intenciones o agenda para hacer entrar un JSON.

### Etapa C5 · Comparador en laboratorio y evaluación conductual
- Igual estado/semilla → payload **literal** baseline y variante, diferencias por rol/bloque y por secciones.
- Datos originales de captura real inmutables; la variante es reconstrucción aislada y se rotula como tal.
- Ensayos sintéticos deterministas primero; luego runs LLM reales acotados con los mismos recursos y evaluación de coherencia, continuidad, errores y creatividad, no solo reducción de tokens.
- Registrar decisiones, riesgos, tests, commits y evidencias en #31 y documentos versionados antes de modificar otra etapa.

## 5. Criterios de aceptación

- El personaje mantiene autonomía: ningún objetivo/actividad se vuelve obligatorio por reglas de selección.
- Una operación implementada sigue siendo descubrible aunque no esté activa en la situación actual.
- Conocimiento falso no se presenta como verificado; se conservan IDs y evidencia contradictoria relevante.
- No se filtran scores corporales internos ni métricas ocultas que Nilo no puede observar.
- `plan` acepta una acción válida; JSON de opción nula no produce `"None"`.
- `agenda` y `actividades_en_espera` respetan contratos reales y variantes antiguas no pierden compatibilidad.
- Las solicitudes comparadas son cuerpos HTTP completos generados desde el mismo estado; el visor de capturas reales no cambia su semántica.
- La primera reducción no altera motor ni SQLite. Ninguna conclusión de mejora conductual sin run comparativo.

## 6. Registro de decisiones (actualizable)

| Fecha | Decisión | Evidencia siguiente |
|---|---|---|
| 2026-11-07 | Archivar propuesta Claude como **material de referencia**, no como nuevo sistema efectivo. | Tres archivos originales en GitHub; esta auditoría. |
| 2026-11-07 | Priorizar contratos reales, información corporal perceptible y no duplicación. | Pruebas deterministas C1/C2. |
| 2026-11-07 | Prototipar schema y selección contextual solo en variante aislada. | Comparador C4/C5 y resultados por proveedor. |
| 2026-11-07 | Sin decisión sobre temperatura, longitud de respuesta, límite de agenda ni estrategia de reintentos. | Medición A/B y validación del presupuesto. |

**Actualización futura:** editar esta tabla, añadir evidencia de PR/test/run y mantener el seguimiento general en [#31](https://github.com/mxlzz/Nilo_public/issues/31). No interpretar una fase documentada como implementada.
