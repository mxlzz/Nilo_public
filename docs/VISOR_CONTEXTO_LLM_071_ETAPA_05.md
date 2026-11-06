# Nilo 0.7.1 · Visor LLM — Etapa 05: API local de consulta histórica

**Fecha:** 2026-11-06. **Rama:** `work/0.7.1-visor-contexto-llm`. **Estado:** implementación por validar con CI. **Release estable:** `v0.7.0` intacta.

## Alcance

Las etapas 02–04 ya registran localmente el cuerpo HTTP exacto, los mensajes literales separados por campos y las transiciones de contexto con referencias de origen. La etapa 05 conecta estas fuentes mediante **una API de solo lectura dentro del servidor propio del laboratorio** (`laboratorio_motor.py`, puerto local `8766` por defecto). **No se incorpora a la API del observador de la interfaz principal** (`nilo_runtime/web/api.py`).

La fuente no se elige desde el navegador: `create_lab_server` vincula `LabHub.world` con la partida local configurada, y `LocalLLMReadAPI` deriva únicamente la ruta de la base sidecar `<partida>.llm_requests.sqlite3`. No existe parámetro `file`, `path`, `db` ni carga de código/archivos desde estos endpoints. Si se abre otra partida desde el historial antiguo por upload, **eso no la convierte en fuente del visor**: para mostrar capturas completas hace falta tener su sidecar local correctamente asociada. Las capturas anteriores a la etapa 02 no se pueden recuperar de hashes.

## API

### GET `/api/lab/llm/attempts`

Lista paginada de intentos **sin texto del prompt**. Filtros opcionales validados:
- `limit`: 1–100, por defecto 25.
- `before`: cursor entero positivo de `rowid`, paginación descendente sin offsets de página inestables.
- `provider`: `gemini`, `groq`, `openai_compatible`.
- `purpose`: `deliberacion` o `chat`.
- `status`: estados realmente persistidos por etapa 02.
- `date`: fecha UTC en formato `YYYY-MM-DD` sobre `started_utc`.
- `session`: identificador numérico de sesión registrado.

Respuesta `{"attempts":[...],"next_before":...,"available":true,"source":"local"}`. Cada fila contiene ID de intento, `call_id` de deliberación, `source_id` de chat, sesión, ordinal, proveedor/modelo, estado, fecha real y simulada, código HTTP cuando existe, tamaño y SHA256 del cuerpo, e indicador de procedencia. Nunca devuelve `body`, prompts ni valores del mundo en la lista. Si no hay sidecar, devuelve lista vacía con `available:false` sin crear el archivo.

### GET `/api/lab/llm/attempt?id=<hex32>`

Consulta un intento exacto de la partida del laboratorio. Devuelve:
- Los mismos metadatos verificables.
- `body_utf8`: texto del JSON HTTP capturado, **sin reconstruirlo** ni normalizarlo.
- `messages`: fragmentos, títulos, subtítulos, roles, rutas JSON Pointer y offsets de `index_saved_attempt` (etapa 03); la concatenación de segmentos reconstruye el texto original de cada mensaje.
- `provenance`: transiciones y referencias verificables guardadas en etapa 04, si existían cuando se hizo el intento. Para capturas de etapa 02 sin metadatos, `provenance:null` y `provenance_status:"not_recorded"`; **no se inventa la traza histórica**.
- `linked_record`: cuando existe, ID y secuencia exactos de `history.llm_decision` vinculados por `trace_call_id`, o mensaje humano de `history.chat` vinculado por `source_id`. No se devuelve el texto de la decisión ni el chat en esta referencia. Los intentos fallidos sin decisión tienen `linked_record:null`.

Antes de devolver información se verifica `body_bytes` y SHA256. Para cuerpos incompatibles el endpoint falla explícitamente; no entrega una vista incompleta como si fuera integral. La consulta detallada está limitada a 1 MiB de cuerpo por intento para evitar respuestas incontrolables.

### Errores

- `400`: query, ID, filtro, fecha o cursor inválidos/repetidos.
- `404`: intento inexistente o base sin capturas.
- `409`: cuerpo alterado o metadatos incompatibles.
- `413`: solicitud guardada demasiado grande para respuesta HTTP.
- `422`: contenido no segmentable (p. ej., mensajes multimodales no soportados).
- `503`: base local inaccesible en el transporte.
- `500`: fallo interno inesperado sin detalles sensibles.

## Seguridad y compatibilidad

- Las rutas solo aceptan GET; ningún POST para consultar, guardar, borrar, exportar o alterar las trazas.
- Se reutiliza `authorize` del servidor del laboratorio: solo loopback (`127.0.0.1`), `Host` correcto, `Origin`/`Referer` permitidos y bloqueo de `Sec-Fetch-Site: cross-site`. Respuestas JSON con `Cache-Control: no-store`, `nosniff` y sin CORS.
- SQLite se abre con URI `mode=ro` + `PRAGMA query_only=ON`. **No se llama a `RequestTraceStore._connect` ni se crea/actualiza la partida o sidecar al consultar.** La nueva API no solicita consultas LLM.
- Los cuerpos pueden contener conversaciones personales escritas por el usuario. El acceso permanece exclusivamente local, no se envía a GitHub ni se publica un endpoint remoto.
- El contrato admite sidecars legadas sin tabla de procedencia; la lista informa que no existe y el detalle conserva bloques crudos.
- El endpoint no construye UI, no modifica `gateway`, `Simulation`, leyes físicas ni orden de operaciones. El servidor de Nilo principal sigue devolviendo 404 para rutas `/api/lab/llm/*`.
- La referencia al historial se limita a identidad por ID exacto dentro de la **misma partida**. No se infiere relación de dos textos parecidos.

## Validación

`tests/test_visor_llm_05.py` cubre con escenarios sintéticos:
- Ausencia de sidecar sin archivos creados, listado, filtros combinados y paginación.
- Respuesta literal de Gemini, JSON Pointer y segmentos recuperables íntegros.
- Procedencia y checksum, compatibilidad sin tabla etapa 04, corrupción detectada.
- Vínculo exacto al historial de decisiones y al mensaje humano de chat.
- Aislamiento entre partidas, rechazo de paths arbitrarios y de parámetros inválidos.
- Servidor HTTP local real: GET autorizado, Host/Origin/cross-site rechazados, POST inválido, respuesta sin caché y rechazo en la API de la UI principal.
- Integridad de la sidecar sin escrituras después de consultar.

**Fase siguiente: 06 — interfaz.** La vista simplificada usará literalmente estos `messages[].segments` para dibujar bloques con título original y subtítulo, sin alterar valores. La profesional mostrará también `body_utf8` y `provenance`. La apariencia será editable sin cambiar la API. La prueba mediante consultas reales pagas de proveedores queda para la evaluación de integración (etapa 07), no se realizará en los tests automatizados.
