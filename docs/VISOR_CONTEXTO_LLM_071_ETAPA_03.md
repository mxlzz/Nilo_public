# Nilo 0.7.1 · Visor LLM — Etapa 03: segmentación literal

**Fecha:** 2026-11-06. **Rama:** `work/0.7.1-visor-contexto-llm`. **Estado:** código implementado, pendiente de validación del commit por CI. **Versión estable:** `v0.7.0` sin cambios.

## Problema y criterio

La etapa 02 almacena el **cuerpo HTTP exacto** (`Request.data`) como bytes UTF-8, separado de la partida. Para que la vista simple permita leer literalmente lo que recibió el LLM, hay que distinguir:

- El cuerpo JSON de transporte contiene escapes (por ejemplo `\n` y `\"` para serializar las cadenas). **El texto real de cada mensaje**, una vez que la API deserializa ese JSON, es el contenido de `systemInstruction.parts[].text`, `contents[].parts[].text` o `messages[].content`. Esas cadenas se recuperan **sin reescribirlas**.
- Dentro de una cadena de mensaje puede haber otro JSON de contexto, previamente serializado por el motor. Sus campos `"necesidades"`, `"proyecto_actual"`, etc. también deben mostrarse **con su escritura exacta**, incluidos espacios, escapes y nombres de clave.
- Toda explicación de la UI está **fuera del texto original**. Vista simplificada = organización literal, no resumen, paráfrasis o diagnóstico del contenido.

## Implementación

`nilo_runtime/labs/literal_segments.py` es un indexador puro, sin conexiones de red, escritura SQLite, imports del motor o cambios de prompts. Funciones:

- `index_request(body, provider, purpose)`: deserializa el cuerpo HTTP recibido de la sidecar y enumera cada mensaje textual con **su ruta real en el payload** y rol. Apoya `gemini`, `groq` y `openai_compatible`, tanto `deliberacion` como `chat`.
- `_json_interval` reconoce el JSON de contexto en la solicitud de deliberación de Gemini (`SITUACIÓN REAL: `) y el JSON directo de Groq/compatible. En chat reconoce `CONTEXTO COMPROBADO (no lo contradigas): ` y conserva separado el texto de la conversación posterior. Un marcador de ejemplo dentro de instrucciones o valores no reemplaza al JSON verdadero.
- `_scan_value` calcula intervalos de los campos en el **texto original**, sin usar `json.dumps` para reconstruirlos. Produce `JSON Pointer` RFC 6901 (`/proyecto_actual/title`, `/na~1me/1/camino`) y offsets sobre el mensaje decodificado. Admite objetos/listas anidados; limita el indexado a profundidad 32 y 20.000 campos, explicitando errores.
- `_message` entrega `segments` contiguos —`text`, `syntax` y `field`— que preservan **todos los caracteres originales**. `blocks` reúne solo texto y campos para la futura interfaz simplificada, mientras que `field_index` incluye rutas anidadas para la etapa 04.
- `index_saved_attempt(row)` consume una fila ya leída de la sidecar, **revalida SHA256/longitud** y adjunta IDs/ordinal del intento. No reabre ni modifica la partida.

**Contrato de fidelidad:** concatenar los `segments[].literal` de un mismo mensaje debe recuperar exactamente `messages[].text`. Cada `literal` es `messages[].text[start:end]`, con offsets medidos en **caracteres Unicode de Python (codepoints)**, no en bytes HTTP. El cuerpo original sigue disponible como BLOB inmutable de la etapa 02. Los fragmentos sintácticos no se eliminan; pueden quedar ocultos en la interfaz sencilla, pero forman parte de la reconstrucción integral y de la vista técnica.

## Metadatos de presentación, nunca datos del LLM

Cada campo de JSON se titula con su **clave real**: `necesidades`, `proyecto_actual`, `memorias_relevantes`, etc. Un diccionario de subtítulos breves (`_SUBTITLES`) explica **qué contiene el apartado**, sin inferir, traducir ni evaluar valores. Para campos desconocidos se conserva el título y el subtítulo queda vacío. Los nombres de sección no se normalizan. El título del texto libre de cada rol coincide con su campo de transporte original (`text` en Gemini, `content` en Groq/compatible); el rol viaja como metadato propio.

La etapa 06 determinará cómo se despliega cada apartado. **Ningún cambio visual requerirá regenerar o editar el contenido histórico**.

## Verificaciones

`tests/test_visor_llm_03.py` incluye:

1. Deliberación Gemini: `systemInstruction` y `contents` intactos, contexto, títulos/subtítulos, JSON Pointer anidado y reconstrucción exacta.
2. Groq y OpenAI-compatible: roles originales, recorte definitivo y metadatos propios de Groq.
3. Chat Gemini y Groq: rol `model`/`assistant`, texto histórico, contexto comprobado y mensajes de usuario sin interpretación.
4. JSON artificial con Unicode, espacios, escapes de comillas, claves con `/` y campos anidados: igualdad **carácter a carácter**, sin normalización.
5. Marcadores engañosos dentro de instrucciones: la partición se efectúa sobre el JSON que corresponde.
6. Campo desconocido y texto con `<script>`: preservación literal, sin crear subtítulo ni ejecutar HTML (la etapa 06 deberá escapar/sanitizar al dibujar).
7. Contenido multimodal no soportado: falla **de forma explícita**, sin ocultar mensajes.
8. Capturas Gemini/Groq de una misma deliberación: cuerpos distintos e identificadores preservados; lectura sin escritura.
9. Captura adulterada: rechazo por checksum.

Los tests no consumen API ni necesitan bases privadas. **No demuestran todavía fidelidad con respuestas reales de proveedores**; esa comprobación operacional corresponde a etapa 07.

## Compatibilidad y límites

- Se agrega una función pura, **sin modificar `gateway`, `providers.route`, `Simulation`, `RequestTraceStore` ni la interfaz** de Nilo.
- Los intentos previos a etapa 02 que no tengan un cuerpo literal guardado no pueden indexarse retroactivamente desde el hash.
- Si una solicitud futura incluye partes de imagen, audio u otras modalidades, el indexador **rechaza explícitamente** ese tipo hasta tener un contrato; nunca presenta una selección parcial como si fuera todo lo enviado.
- El indexador no calcula procedencia real de variables ni registra por qué se omitieron. Esa instrumentación será la etapa **04**. El endpoint y los dos diseños de interfaz pertenecen a etapas **05–06**.
