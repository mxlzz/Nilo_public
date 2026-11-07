# Laboratorio Nilo 0.7.1 — Etapa 02 · Trazabilidad de episodios

**Fecha:** 2026-11-07  
**PR:** [#86 (borrador)](https://github.com/mxlzz/Nilo_public/pull/86), apilado sobre [#85](https://github.com/mxlzz/Nilo_public/pull/85) y la cadena de UI del laboratorio.  
**Estado:** implementación presentada para pruebas y revisión. Este documento no implica que el PR se haya integrado a main.

## Objetivo

Poder seguir una deliberación real y **distinguir**:
1. Cuerpo HTTP original **enviado** a Gemini/Groq.
2. Texto original **devuelto por el modelo** (extraído del sobre JSON del proveedor, antes de strip/parseo; no la respuesta HTTP completa).
3. Fase alcanzada por el parseo y normalización de la decisión (o rechazo sin mensaje de error privado).
4. Decisión que se incorporó al historial de Nilo, vinculada por ID **exacto**.
5. Checkpoint de predecisión, nota del cuaderno originada en esa deliberación y acciones que realmente se iniciaron con esa nota.
6. Evidencias que conservan enlaces explícitos: journal → measurement → diagnostic → experience, cuando están registradas.

No inferir que una acción fue causada por una decisión simplemente porque ocurrió después. No deducir intención/razonamiento interno a partir del cuaderno. No inventar respuesta o memoria donde no se archivó.

## 1. Captura local de respuestas

**Fuente:** `nilo_runtime/agent/gateway.py`, `nilo_runtime/agent/trace_context.py` y `nilo_runtime/storage/llm_requests.py`.

Tabla nueva y aditiva `llm_response_traces`, indexada por el `attempt_id` ya existente. Por cada intento se pueden archivar:

- Texto UTF-8 exacto del campo textual reconstruido por `gateway._response`, **antes** de `.strip()`, parseo JSON y recorte de chat.
- SHA-256 y tamaño del texto original.
- `capture_status=captured` o `too_large`: a partir de **1 MiB** el texto **no** se guarda; sólo tamaño/hash y la ausencia expresa de literal.
- `parse_phase=text_received|json_parsed|invalid_json|normalized|invalid_contract|chat_returned`.

El estado HTTP anterior `transport_attempted|response_received|accepted|rejected|http_error|transport_error|invalid_http_response` sigue siendo independiente del parseo. Un intento puede tener respuesta recibida y validación rechazada. La respuesta generada no contiene encabezados API; no se persisten mensajes crudos de excepción. El observador es **best-effort** y no interrumpe la deliberación si falla el registro.

El nuevo texto original se guarda sólo **a partir de esta versión**: los intentos del run 06/11/2026 continúan sin cuerpo de respuesta. La sidecar retiene hasta 5.000 intentos recientes y elimina las respuestas satélite de intentos expulsados.

## 2. Uniones exactas de decisión y plan

**Fuente:** `nilo_runtime/storage/timeline.py` y `nilo_runtime/application/decisions.py`.

Se agregan a la SQLite del mundo **únicamente metadatos técnicos observacionales**:

- Columna nullable `timeline_checkpoints.trace_call_id`, con migración de partidas que ya tengan checkpoints.
- Tabla `lab_journal_trace(journal_id,trace_call_id,decision_checkpoint_id)`.
- Tabla `lab_action_links(action_checkpoint_id,journal_id,trace_call_id)`.

El `trace_call_id` se pasa directamente a `plan_ready` sólo cuando la deliberación LLM fue aceptada; se guarda en el checkpoint **fuera del snapshot físico**. El plan **ya** asignaba `_journal_id` a sus acciones; se reutiliza ese vínculo para indexar únicamente operaciones **no automáticas**. Los pasos con origen o fuente `agenda`, `rutina`, `espera` o `motor` no se atribuyen al LLM aunque compartan un timestamp.

En cierres, pausas y otras decisiones sin una nueva nota del cuaderno puede existir el vínculo al checkpoint y **no** el vínculo a acciones; es correcto.

El motor, las leyes físicas, la memoria perceptible, la selección de proyectos, el contenido del cuaderno y la decisión enviada al proveedor **no se modifican** por estas tablas.

## 3. Lector read-only y límites de evidencia

`nilo_runtime/labs/episode_links.py::inspect_episode(world_path,call_id)` consulta una partida en modo SQLite **sólo lectura**. Retorna:

- **Decisión normalizada archivada** por igualdad exacta de `history.llm_decision.trace_call_id`.
- **Checkpoint predecisión** por `timeline_checkpoints.trace_call_id`.
- **Acciones planificadas realmente iniciadas** por `lab_action_links` y coincidencia de `journal_id`.
- **Registros originales relacionados**, si existen: notas del cuaderno cuyo `id` coincide; mediciones cuyo `journal_id` coincide; diagnósticos que referencian exactamente su `physical_result.measurement_id`; experiencias que refieren exactamente `measurement_id` o `action_id`.

Las relaciones se etiquetan `matched_by`. Los registros conservan su objeto JSON original, sin paráfrasis. Se marca explícitamente la falta de datos, las tablas heredadas y los límites de recuento. **No** se enlazan diagnósticos sin IDs mediante una hora/op similar. No se deduce automáticamente qué recuerdos fueron **seleccionados** para un turno posterior: esa será una cuestión del análisis longitudinal posterior (etapa 08).

`LocalLLMReadAPI.get_attempt`, ya restringida a la partida abierta en el laboratorio, ahora incluye la captura literal de respuesta (`response`, nullable) y las relaciones del episodio (`episode`, si hay ID canónico y deliberación). El listado paginado de intentos **no** agrega textos completos. La UI del visor actual permanece sin cambios en esta etapa; el contenido quedará disponible para la ficha de episodio de la etapa 03.

## 4. Casos de verificación

1. Respuesta UTF-8 con espacios y saltos de línea: comparar bytes, longitud y SHA sin normalizarla.
2. Respuesta JSON inválida o contrato rechazado: resultado original accesible, fase rotulada, estado de intento rechazado, sin registrar mensaje privado de excepción.
3. Reintento y fallback: un `call_id`, varios `attempt_id`; las respuestas y los estados no se sobreescriben.
4. Texto mayor que 1 MiB: metadatos íntegros, literal ausente explícito.
5. Acción planificada con `_journal_id`: asociada a la deliberación de origen; acción `agenda` con el mismo ID, **no** atribuida.
6. Evidencias: vínculo por IDs exactos, con registros vecinos deliberadamente falsos sin asociación.
7. Partidas anteriores a la instrumentación: lectura y «sin vínculo» honestos, con migración aditiva al abrirlas en el motor.
8. Integridad: corrupción de texto devuelto o cuerpo enviado se detecta; una copia de partida consultada en lectura no se altera.
9. Compatibilidad con visor existente, contratos Gemini/Groq y empaquetado portátil Windows.

**Pruebas automatizadas:** `tests/test_lab_stage02_traceability.py` más regresión preexistente `test_visor_llm_0{1..7}.py`, `test_historical_lab.py` y auditoría de manifiesto. Estado de CI consultable en [PR #86](https://github.com/mxlzz/Nilo_public/pull/86).

## 5. Lo pendiente

- **Etapa 03:** recorrido visual y ficha de episodio integrada, con acceso gradual a los literales y advertencias de ausencia.
- **Etapa 04:** explicación contextual de condiciones físicas realmente evaluadas, sin afirmar causalidad de ramas no instrumentadas.
- **Etapa 05:** jerarquía visual del contexto LLM, preservando texto original.
- **Etapa 06:** selección, notas humanas y exportador de auditoría.
- **Etapa 08:** linaje longitudinal (memoria guardada, recuperada y enviada en otro turno), patrones y matriz de presencia.

No convertir estos pendientes en nuevas reglas cognitivas del personaje ni instalar nuevas acciones físicas por una necesidad de observación.
