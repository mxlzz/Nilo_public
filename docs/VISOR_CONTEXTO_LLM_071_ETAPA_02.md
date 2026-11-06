# Nilo 0.7.1 · Visor LLM — Etapa 02: captura por intento HTTP

**Fecha:** 2026-11-06. **Rama:** `work/0.7.1-visor-contexto-llm`. **Estado:** implementada; validación CI por corroborar. **Versión estable:** `v0.7.0`, sin modificar.

## Implementación y propiedad

- `nilo_runtime/agent/trace_context.py`: `ContextVar` delimita cada deliberación/chat por worker y correlaciona intentos, reintentos y fallback mediante un `call_id` aleatorio independiente del RNG físico de Nilo. Se anotan propósito, sesión, identificador del mensaje de chat, proveedor/modelo y ordinal.
- `nilo_runtime/agent/gateway.py::_post`: serializa **una sola vez** con `json.dumps(payload,ensure_ascii=False).encode("utf-8")`, pasa esos bytes a `urllib.request.Request.data` y registra el mismo BLOB en la frontera HTTP. No almacena cabeceras, tokens ni URLs.
- `providers.route`: identifica el candidato justo antes del handler y distingue respuesta aceptada/rechazada, error HTTP y problema de transporte. Los cooldowns, reintentos, decisiones y la selección del proveedor siguen gobernados por el código anterior.
- `SessionLifecycle` y `DecisionUseCases`: activan la captura **solo en consultas reales** de deliberación y chat. Los previews del laboratorio no generan archivos. En `history.llm_decision` la decisión aceptada incluye `trace_call_id` para enlazar los intentos; en chat se emplea `source_id` del mensaje humano.
- `nilo_runtime/storage/llm_requests.py`: sidecar SQLite independiente, junto a cada partida (`<partida>.llm_requests.sqlite3`), sin introducir tablas ni cambiar datos del mundo. Guarda IDs, fecha, sesión, propósito, ordinal, proveedor/modelo, estado, bytes, SHA256 y **cuerpo literal UTF-8 como BLOB**. Sin HTTP ni JavaScript en esta etapa.

## Semántica de captura

| Estado | Significado |
| --- | --- |
| `transport_attempted` | Se preparó Request.data y se invocará el transporte; no se acredita recepción. |
| `http_error` | Error HTTP explícito, código numérico disponible. |
| `transport_error` | Error de red/lectura o interrupción de transporte. |
| `invalid_http_response` | La respuesta HTTP no pudo interpretarse como JSON. |
| `response_received` | Respuesta HTTP JSON recibida; contrato del LLM aún no validado. |
| `rejected` | Validación posterior rechazó el resultado del proveedor. |
| `accepted` | Router y handler de consulta aceptaron la respuesta. |

`accepted` **no acredita la ejecución física** del plan, ni que Nilo haya terminado un proyecto. Un proceso interrumpido entre la captura y la respuesta puede conservar `transport_attempted`.

## Privacidad, retención y respaldos

- **Retención FIFO:** últimas 5.000 solicitudes HTTP por archivo de partida (constante `MAX_RECORDS`). No se establece caducidad cronológica adicional ni se envían archivos a servicios externos.
- La sidecar no se incluye en el ZIP de release ni en Git (`*.sqlite3` excluido). **Respaldar solamente la partida no respalda automáticamente esta sidecar**. La etapa 05 deberá proporcionar mecanismos explícitos de consulta, exportación y respaldo coherente. La ubicación es deliberadamente local; en POSIX se intenta crear el archivo con permiso 0600 y en Windows hereda los permisos de carpeta.
- No se registran cabeceras de autorización ni errores remotos en crudo. Los **prompts íntegros pueden contener información sensible o secretos introducidos por el propio usuario en un mensaje**: no se filtran ni reformulan porque el requisito es conservar los bytes exactos. Esto requiere cuidado al compartir cualquier SQLite de trazas.
- La captura es de *mejor esfuerzo*: si falla el almacenamiento, la consulta LLM sigue adelante. `capture_errors` conserva un contador técnico en memoria, no una falsa constancia de captura. El historial de la partida no se altera por un fallo de la sidecar.
- El registro técnico utiliza IDs no deterministas fuera del estado simulado. No consume la entropía física ni genera acciones para Nilo.

## Pruebas y límites

`tests/test_visor_llm_02.py` comprueba bajo HTTP simulado (sin API, red ni datos de partidas reales): igualdad byte a byte con `Request.data` para los tres proveedores, hashes/tamaños, fallback Gemini 429 → Groq con dos cuerpos diferentes, reintento del mismo proveedor por red, JSON rechazado, chat ligado a mensaje humano, continuidad ante error de disco, aislamiento del snapshot principal y corrupción detectada al leer.

**Límite explícito:** solicitudes antiguas sin esta captura no pueden reconstruirse desde `context_sha256`. Las consultas fallidas antes de llegar a `_post` no generan un cuerpo HTTP, por lo que tampoco generan un registro de intento de transporte. Los vínculos posteriores con acciones y mediciones, la segmentación literal, el origen por campo y la UI están asignados a las etapas 03–06.

**Próxima etapa:** 03 — segmentación literal de roles y campos usando la cadena registrada, con títulos originales, subtítulos aparte, offsets y pruebas de reconstrucción idéntica. No reconstruir el mensaje desde una partida actual.
