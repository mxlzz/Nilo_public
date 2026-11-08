# Nilo 0.7.1 · Laboratorio — Etapa 08: análisis transversal y QA de navegación

**Fecha:** 08/11/2026.  
**Rama:** `work/0.7.1-lab-stage08-transversal`, sobre etapa 07 ([PR #91](https://github.com/mxlzz/Nilo_public/pull/91)).  
**Estado:** implementación en rama, pendiente de CI y prueba visual/funcional de una partida real.

## Decisión de diseño

El usuario quiere poder responder preguntas prácticas al observar a Nilo: **qué vio el LLM, qué ocurrió después, por qué una acción pudo repetirse y qué información ocupó contexto en varios turnos**. El laboratorio no debe afirmar causalidades ausentes del registro ni interpretar las justificaciones del LLM como causas comprobadas.

Se agrega una pantalla **Análisis** (`/analisis`) a la navegación de las seis vistas existentes. Su contenido está dividido en bloques ordenados de lectura y no requiere explorar los JSON de cada turno para encontrar diferencias. **La columna derecha de Pruebas no se rediseña todavía**: la inspección visual de esa interfaz depende de observar muestras reales con el usuario.

## Tres vistas y niveles de evidencia

### 1. Matriz campo × deliberación

La fuente es el SQLite de capturas exacto de la partida actual (`world.stem + ".llm_requests.sqlite3"`). Cada columna representa un **`call_id`**, no un intento HTTP. Se elige el intento aceptado cuando existe, de lo contrario el último archivado. Reintentos cuentan como una sola deliberación y pueden abrirse en el visor literal.

La ventana predefinida cubre **24 deliberaciones**, ajustable a 12 o 48. Se limita la lectura de cuerpos a 300 intentos para evitar cargar toda la partida. Una captura de más de 1 MiB o cuyo cuerpo no coincida con SHA-256/bytes queda **ilegible**, con advertencia; no se reconstruye su contenido desde el estado actual.

Cada celda informa bytes UTF-8 de los fragmentos del campo, su hash y si el valor JSON es explícitamente vacío. **No son tokens reales del proveedor**. La UI distingue campo ausente, presente, vacío y captura inválida. Orden de filas por volumen total; filtros por familia y nombre. El enlace de una celda abre el intento exacto en `/visor-llm?id=...`.

Una cadena con SHA idéntica durante muchos turnos puede ser una candidata a revisión, pero **no demuestra irrelevancia**; los campos esenciales o reglas estáticas pueden ser repetidos intencionalmente.

### 2. Huellas operativas

Fuente: registros `history.category = 'diagnostic'`. Se usan solamente `op`, `target` y `success` o clasificación explícita presentes **en el mismo registro**. Un campo ausente se indica como no archivado y no se rellena con objetivos supuestos ni se une por proximidad a una decisión.

El panel agrega ocurrencias por firma `(op, target, result)`. La racha se calcula únicamente entre **diagnósticos consecutivos en la ventana**: no prueba que Nilo realizara acciones consecutivas sin otras actividades intercaladas. Se entregan números `seq` para recuperar el original en Historial. **No se ejecuta el motor**.

### 3. Experiencia → aparición por ID en contexto

Fuente: `history.category = 'experience'` con ID y campo de memoria/evidencia enviado literalmente en la petición HTTP. El analizador exige **igualdad explícita de identificador** dentro de posiciones estructuradas `id`, `experience_id`, `source_id`, etc., no coincidencias de texto libre ni substrings.

Salida: experiencia archivada con `history_seq`, posible ID de medición y lista de intentos donde ese mismo ID aparece en un bloque de memoria/evidencia.

Alcance: esto demuestra **presencia del ID en el prompt indexado**, no que haya habido recuperación semántica, que el LLM leyera efectivamente el valor, que se haya aplicado el conocimiento, ni que una experiencia explique el comportamiento. Si el contexto elimina el ID pero conserva una paráfrasis, la relación queda **desconocida**. Las ventanas de retención del mundo y de la sidecar no garantizan cronología cruzada exacta.

## Ruta de uso del observador

Tres situaciones quedan expresadas en la propia pantalla:

1. **Decisión inesperada:** abrir la solicitud original de la columna correspondiente, después su ficha en Historial; contrastar lo recibido, la respuesta literal y la ejecución registrada.
2. **Acción infructuosa repetida:** revisar firmas de diagnóstico, secuencias originales y episodios; no atribuir causalidad a la coincidencia de operación.
3. **Contexto excesivo:** filtrar filas por bytes y huellas, abrir el bloque literal en Visor LLM, proponer exclusión con los checks de la etapa 06, y comparar perfiles mediante Experimentos A/B si corresponde.

El resultado transversal puede exportarse a JSON local. **No contiene las solicitudes completas ni el texto de las experiencias**: solo indicadores, IDs, tamaños y hashes. Para una auditoría de contenidos se utiliza el exportador autocontenido del visor.

## Técnica y compatibilidad

- `nilo_runtime/labs/cross_analysis.py`: lector sin mutaciones, lecturas SQLite mediante `mode=ro`, tablas opcionales de versiones antiguas, límites acotados, metadatos estrictos, sin SQL de actualización. No modifica física ni prompts ni dispara proveedores.
- `GET /api/lab/analysis?limit=...`: endpoint de solo lectura; exclusivamente partida actual de `LabHub`, no acepta rutas, IDs ajenos, nombres de bases ni URLs.
- `laboratorio_analisis.html`: matriz de navegación, patrones y evidencia por IDs, con renderizado mediante `textContent` y creación de nodos, **sin usar HTML dinámico de registros archivados**. Usa el sistema de diseño compartido (`/assets/laboratorio.css` y `/assets/laboratorio_ui.js`), sin abrir rutas adicionales de assets.
- Los seis visores reciben únicamente un enlace de navegación hacia Análisis. La navegación original de Pruebas, Historial y Solicitudes LLM permanece intacta.
- `MANIFIESTO_SHA256.json`: incorpora el nuevo lector y la pantalla al paquete Windows; **las pruebas automatizadas permanecen fuera del ZIP distribuible**.

### Tests de aceptación

1. Cada `call_id` se cuenta una vez; un fallback HTTP fallido no oculta la solicitud aceptada posterior.
2. Comprobación SHA y rechazo de capturas corruptas; los otros turnos siguen siendo analizables.
3. Matriz distingue campos cambiantes, estáticos, ausentes, explícitamente vacíos y tamaño total, sin inventar tokens.
4. Las huellas y rachas usan únicamente diagnósticos archivados, no acciones hipotéticas.
5. Una referencia por ID solo cuenta si coincide exactamente en un campo estructurado de memoria/evidencia.
6. Archivo de historia anterior a la instrumentación o sin sidecar devuelve ausencia explícita, no datos reconstruidos.
7. Endpoint rechaza rutas externas y parámetros ajenos; mundo y sidecar mantienen sus bytes.
8. La nueva pantalla conserva sintaxis JS válida y el sistema de estilos/tema compartido.
9. Instalación y rollback Windows; regresión completa sin consultas reales a Gemini/Groq.

## Cierre y límites pendientes

**No se redefine aún el diseño de la columna derecha de Pruebas**. El usuario ya indicó que esa sección es confusa, pero pidió discutirla después de tener la estructura de datos implementada. Antes de declarar una validación de experiencia de uso hace falta una sesión con la partida real y evaluar si la matriz, los títulos y el acceso al original son comprensibles. Los tests sintéticos no sustituyen esa comprobación.

Las asociaciones por ID se consideran evidencia de procedencia literal, no un diagnóstico del funcionamiento interno del LLM. La calidad de comportamiento, causalidad A/B y autonomía permanecen hipótesis hasta realizar varios ensayos y lectura cualitativa de los resultados.
