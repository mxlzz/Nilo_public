# Nilo 0.7.1 · Auditoría de interfaz · Etapa 04.1 (Visor LLM)

**Fecha:** 2026-11-06. **Rama:** `work/0.7.1-lab-ui-stage04-visor`. **Base:** `work/0.7.1-lab-ui-stage03` (PR #82). **Estado:** implementación terminada; CI y revisión visual por verificar.

## Revisión de alcance

El visor ya capturaba solicitudes reales con cuerpo HTTP exacto y procedencia verificable. La etapa 04.1 busca reducir la carga cognitiva de leer intentos y bloques sin interpretar ni modificar el material de origen. Se revisaron la lista, filtros, encabezados, resumen, secciones literales y niveles técnicos. No se reescribe ninguna solicitud ni se modifican el transporte o el motor.

## Cambios

1. **Selector de intentos:** los intentos de una misma consulta (`session_id + call_id`) aparecen agrupados. Cada intento conserva un botón distinto, estado y orden original; jamás se deduplican, fusionan ni omiten reintentos. Las consultas separadas siguen separadas aunque coincida la hora. La cifra superior indica grupos e intentos **cargados**, no inventa solicitudes fuera de la paginación.
2. **Filtros progresivos:** proveedor, tipo y estado permanecen visibles. Fecha UTC, modelo, identificador de consulta, sesión y límite se muestran bajo «Más filtros»; los ocho campos y la consulta de la API permanecen exactamente iguales. No se filtra ni resume contenido literal.
3. **Vista simplificada:** índice de bloques navegable por rol y campo, construido con los títulos preexistentes; un clic expande el bloque real y desplaza el foco. El texto de cada bloque se muestra mediante `textContent` con `block.literal` sin traducción, reinterpretación ni Markdown. Los títulos y subtítulos siguen por fuera del texto.
4. **Jerarquía de detalle:** resumen visible de modelo, estado del intento, momento simulado y cobertura de procedencia. Proveedor, intento, fecha UTC, sesión, identificadores y SHA-256 permanecen en metadatos desplegables. El vínculo con un registro histórico se sigue presentando como coincidencia de ID, sin afirmar ejecución física.
5. **Vista profesional:** preserva cuerpo HTTP completo (`body_utf8`), mensajes, transiciones y referencias de origen. No se alteró la presentación de datos archivados, únicamente la jerarquía compartida del detalle.
6. **Accesibilidad y responsive:** grupos con etiquetas accesibles, botones de selección con `aria-pressed`, índice de navegación con foco sobre el resumen real, rejillas y filtros adaptables al ancho. Se conserva el selector de tema de etapa 03.

## Límites

- No se cambian `nilo_runtime/labs/literal_segments.py`, `provenance.py`, `llm_read.py`, SQLite, APIs, prompts, física, decisiones ni versión.
- No se agrega un análisis/interpretación automático de lo que recibe el modelo.
- No se oculta información: los filtros avanzados pueden expandirse; cada intento, texto original y metadato permanece accesible.
- El sistema de diseño transversal no se reescribe; los cambios de layout son locales al visor.
- **Próximas subetapas:** 04.2 Historial, 04.3 Escenarios, 04.4 Mundo interactivo, 04.5 Ajustes.

## Verificación

`tests/test_lab_ui_audit_041.py` comprueba IDs y filtros, segmentación sin HTML dinámico, integridad literal de cadenas arbitrarias, agrupación de reintentos sin deduplicación, índice por bloques, foco/navegación y sintaxis JS. Se mantienen y deben pasar las pruebas anteriores de captura literal del laboratorio y las suites Linux/Windows. La revisión visual del usuario sigue diferida.

No publicar release ni fusionar esta rama antes de pasar CI y revisión de la arquitectura final.
