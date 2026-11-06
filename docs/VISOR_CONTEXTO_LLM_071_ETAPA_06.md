# Nilo 0.7.1 · Visor LLM — Etapa 06: primera interfaz

**Fecha:** 2026-11-06. **Rama:** `work/0.7.1-visor-contexto-llm`. **Estado:** implementación pendiente de validación CI y revisión visual del usuario. **Release estable:** `v0.7.0`.

## Interfaz incorporada

Se crea `laboratorio_visor_llm.html`, disponible en **`http://127.0.0.1:8766/visor-llm`** cuando se inicia `ABRIR_LABORATORIO.bat` (salvo puerto de laboratorio personalizado). Es una página distinta del motor de Nilo, del sandbox y de los ajustes. Se agrega enlace de navegación en las cuatro páginas preexistentes del laboratorio. El archivo está incluido en `MANIFIESTO_SHA256.json`, para el empaquetado portátil posterior.

### Vista simplificada (predeterminada)

- Barra lateral con historial de solicitudes y filtros por proveedor, modelo, tipo, estado, fecha UTC, sesión y deliberación; paginación de 25/50/100 intentos sin reconstruir estados.
- Selector de un intento específico. Se muestran proveedor, modelo, estado del intento, hora simulada, momento real, número de intento y huella SHA256.
- Mensajes agrupados **por rol auténtico** (`system`, `user`, `model` / `assistant`) y ruta del payload.
- Dentro de cada mensaje, **bloques desplegables con el nombre original de la clave** (`necesidades`, `proyecto_actual`, etc.) y **subtítulo breve**, cuando está documentado. El contenido de cada bloque es `segments[].literal` de la etapa 03: **sin reordenar, renombrar, resumir, traducir ni reinterpretar**. Las instrucciones del sistema y otros fragmentos de texto libre se presentan como texto literal.
- Acción para copiar cada bloque y toda la solicitud original. Abrir «Origen y transformaciones» muestra referencias AST, precisión de la atribución y campos internos anidados registrados para esa captura. Es información externa al prompt.

**Fidelidad:** el texto fuente **no se resintetiza**. La segmentación conserva también separadores y otros fragmentos sintácticos en los datos originales (fase 03), aunque el visor simple se concentra en los bloques para facilitar lectura; la vista técnica ofrece el cuerpo HTTP íntegro y cada mensaje sin cortes.

### Vista profesional

La misma captura y el mismo `attempt_id`; cambia solo su presentación. Incluye el cuerpo HTTP completo (`body_utf8`), mensajes íntegros por rol, transiciones reales por etapa (`added` / `removed` / `modified`), JSON Pointers, fuente y precisión de origen, referencias de archivo/función/línea, y campos omitidos.

No se debe afirmar que una referencia AST demuestra la ejecución de una rama. Si la captura antigua no tiene procedencia, se muestra explícitamente «no archivada», sin calcularla desde la partida actual.

### Seguridad y privacidad

- El servidor reutiliza validación de loopback/Host/Origin y entrega `Cache-Control: no-store`. Ninguna API nueva entra en la interfaz principal `/api/*` de Nilo.
- La pantalla **no** permite editar archivos, borrar historial, aplicar parámetros, generar nuevas decisiones ni ejecutar llamadas LLM.
- Las respuestas llegan a la página por `fetch` solo desde el mismo origen, con `no-store`.
- Todo texto proveniente de la solicitud se agrega mediante `document.createElement` y `textContent`: **nunca** con `innerHTML`, `insertAdjacentHTML` o interpretación de Markdown/HTML. Un prompt que incluya código HTML/JavaScript se muestra como caracteres literales.
- La copia manual a portapapeles requiere interacción. Los textos crudos pueden contener información sensible incluida por el usuario en sus mensajes, por lo que no deben publicarse.
- Los filtros tienen límites impuestos por el servidor; no hay selección libre de archivos por parámetro de consulta.

## Evidencia de verificación

`tests/test_visor_llm_06.py` comprueba:
- Componentes de ambas vistas y controles de búsqueda presentes en el HTML.
- JavaScript sintácticamente válido con Node.js cuando está instalado.
- El código de UI renderiza textos variables con `textContent`, sin inyección HTML dinámica.
- Servidor HTTP real del laboratorio sirve la página en `/visor-llm`, integra navegación desde secciones existentes y rechaza Host/Origin ajenos y POST.
- La API principal no expone esta página ni sus endpoints.
- Una captura sintética que contiene `<img src=x onerror=alert(1)>` se conserva literalmente en API como texto y no modifica el prompt.
- El archivo se incluye en el manifiesto portátil.

La **etapa 07** hará la auditoría integral de seguridad, compatibilidad del ZIP, pruebas prolongadas y verificación en un run real de Nilo. La experiencia visual y jerarquía de las secciones pueden ajustarse con las observaciones del usuario **sin modificar el contrato de captura ni el motor**.

**Importante:** las versiones 0.7.0 ya ejecutadas no contienen capturas históricas. La pantalla empezará vacía hasta que una versión con los hooks de etapa 02 genere solicitudes reales y persista su sidecar. Las pruebas automatizadas utilizan solicitudes sintéticas, sin coste de API.
