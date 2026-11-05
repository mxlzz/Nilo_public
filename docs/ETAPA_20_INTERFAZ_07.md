# Nilo 0.7 — Etapa 20: interfaz principal, assets y paridad funcional

**Fecha:** 5 de noviembre de 2026. **Rama:** refactor/0.7. **Baseline:** main, VERSION 0.6.4. **Sin cambios físicos ni en SQLite v5.**

Referencias: [plan integral](PLAN_REESTRUCTURACION_NILO_07.md), [seguimiento](ESTADO_REESTRUCTURACION_07.md), [PR #77](https://github.com/mxlzz/Nilo_public/pull/77), [issue maestro #74](https://github.com/mxlzz/Nilo_public/issues/74).

## 1. Reauditoría del archivo monolítico

La interfaz principal estaba concentrada en interfaz.html, con un único bloque de CSS y un único bloque de JavaScript, ambos dentro de un documento de unos 175 KB. Se revisaron los controles de mundo, mapa, recursos, actividad, cuaderno, investigaciones, ensayos, proyectos, agenda, conducta, propuestas, chat, avisos, ayudas, filtros, preferencias, grupos y «¿Qué me perdí?».

Hallazgos:

- La presentación, el renderizado y las operaciones del observatorio eran difíciles de revisar aisladamente. Los cambios en un renderizador obligaban a manipular un HTML grande con cadenas de plantilla JavaScript y reglas CSS intercaladas.
- No había atributos de eventos inline en el marcado estático, pero sí muchos handlers asociados desde el JavaScript. Se conservaron como listeners/bindings programáticos; no se introdujeron handlers HTML ni comandos directos del mundo desde el markup.
- La suite histórica dependía del detalle de implementación del monolito y extraía literalmente el contenido entre <style> y <script>; algunas pruebas Node leían interfaz.html desde el disco para evaluar funciones. Sustituir sin más esos bloques habría reducido la cobertura de regresión.
- El servidor web de etapa 19 solo entregaba el HTML y la API; servir archivos desde rutas arbitrarias habría ampliado la superficie de acceso, por lo que se añadió una lista exacta de recursos permitidos.
- Las rutas API actuales y los IDs de DOM eran relativamente estables; no había motivo funcional para rediseñar la interfaz. La refactorización debía conservar el aspecto y los textos.

## 2. Arquitectura resultante

| Recurso | Responsabilidad |
| --- | --- |
| interfaz.html | Documento semántico, botones, pestañas, formularios, diálogos y enlace a assets |
| assets/nilo.css | Temas visuales, diseño adaptable, estados, popups y decoración |
| assets/state.js | Estado del observatorio, preferencias, mapa, necesidades y vista general |
| assets/records.js | Renderizadores y enlaces de cuaderno, investigación, ensayos, proyectos, agenda y otros registros |
| assets/feed.js | Vista de registros, pestañas, lectura y notificaciones internas |
| assets/actions.js | Actualización periódica, operaciones HTTP, eventos de controles, preferencias y notificaciones del navegador |
| nilo_runtime/web/assets.py | Catálogo estático de rutas de recursos y MIME; sin acceso a archivos arbitrarios |

Todos los scripts son **JavaScript clásico**, con atributo defer y orden fijo. Comparten el entorno global existente para mantener los contratos entre funciones sin transcribir lógica. No se introdujo empaquetador, framework ni rediseño. El último script conserva las llamadas de inicio y los temporizadores de refresco que antes estaban al final del bloque monolítico.

Las rutas explícitas servidas son /assets/nilo.css, /assets/state.js, /assets/records.js, /assets/feed.js y /assets/actions.js. La entrega incluye MIME correcto, Content-Length, no-store, nosniff y política de acceso del servidor local. La Content-Security-Policy ya no necesita unsafe-inline para JavaScript; **style-src** sigue permitiendo estilos inline presentes en algunos elementos del HTML, conservados por compatibilidad.

## 3. Paridad exacta de código y presentación

Antes de modificar el archivo se separaron por delimitadores exactos los bloques CSS y JS originales. El JavaScript se dividió únicamente en límites de funciones de nivel superior y se comprobó que la concatenación de los cuatro segmentos reproducía el contenido original **sin cambiar un carácter**. La reconstrucción del HTML anterior con los nuevos assets también coincidió exactamente.

Mediciones sobre código fuente:

- Documento original: **174.705 caracteres**.
- Documento posterior: **11.927 caracteres**, con enlaces a los nuevos recursos.
- CSS separado: **37.283 caracteres**.
- JS separado en cuatro archivos: **21.598 + 60.706 + 10.898 + 32.498 = 125.700 caracteres**.
- SHA-1 de blob Git del documento histórico, recomputada sobre la versión reconstruida: **b2140f365ac0344189096cf615b5cf97d69fa8d2**.

Esta huella compara el HTML antiguo con el contenido reconstruido desde los archivos reales. No existe una segunda implementación paralela de la interfaz: tests/ui_fixture.py construye una representación monolítica **solo para pruebas históricas**. Treinta archivos de tests que leían el HTML inline fueron adaptados a ese fixture; los tests Node pueden recibir una copia temporal reconstruida sin alterar la pantalla de producción.

## 4. Controles y compatibilidad inspeccionados

- Se preservan los cuatro grupos: Vida, Conocimiento, Autonomía e Interacción; los tres paneles de recursos: Materiales, Herramientas y Obras; y los controles de mundo y mapa (seguir capa, zoom, rastro, visibilidad y selección por casilla).
- Las pestañas existentes, sus filtros y los indicadores de novedades conservan las funciones de navegación, los atributos semánticos y las transiciones programáticas.
- Cuaderno, actividad, relaciones entre registros, acceso a una medición desde su ID, ayudas emergentes y apertura de proyectos no cambiaron su formato.
- «¿Qué me perdí?», el historial/continuación de síntesis y las marcas de lectura conservan los handlers existentes. Las operaciones de marcado requieren acciones concretas o la sincronización de lectura de la propia interfaz; entregar CSS/JS o consultar GET no marca eventos como leídos.
- La ventana de configuración, preferencias locales y persistidas, temas, avisos del navegador, chat y límites de la API utilizan los mismos contratos de la etapa 19.
- El catálogo HTTP registra únicamente rutas explícitas. Los paths no reconocidos, intentos de traversal o nombres privados no exponen archivos del sistema.
- Los archivos nuevos se registraron en MANIFIESTO_SHA256.json y como entradas obligatorias de tools/verificar_paquete_07.py. El ZIP portable debe incluir CSS y los cuatro scripts, no solo interfaz.html.

## 5. Pruebas de salida

La nueva suite tests/test_interfaz_20.py y tools/auditar_interfaz_20.py verifican:

- Paridad binaria del documento reconstruido con el blob Git anterior a etapa 20.
- Referencias a archivos reales, orden de ejecución de scripts con defer, ausencia de CSS/JS y handlers inline en el HTML y ausencia de IDs duplicados.
- Resolución de referencias literales el('id') contra IDs del marcado; continuidad de filtros, tema, mapa, tabs, diálogo, notificaciones, preferencias, lectura y resumen.
- Sintaxis de cada script y sintaxis de la concatenación original con node --check, si Node está disponible.
- Coincidencia entre llamadas API del frontend y los endpoints declarados.
- Acceso HTTP a cada asset comprobando MIME, headers y bytes exactos; rechazo de traversal y de archivos secretos.
- GET de recursos sin mutación del estado del mundo, del RNG o de SQLite.
- Smoke de ZIP portable y regresión de tests históricos de HTML/JS adaptados al fixture exacto.

**Etapa 20 cerrada.** La [CI integral #42080090727](https://github.com/mxlzz/Nilo_public/actions/runs/42080090727) terminó **success** sobre el [commit de código y pruebas 93d7b351df9d](https://github.com/mxlzz/Nilo_public/commit/93d7b351df9db86be8ee6beebfde51a005583eb1): **971 pruebas ejecutadas (una omitida)**, con **17 pruebas específicas de etapa 20**, auditoría de assets, esquema de rutas, paridad Git de HTML, Node --check, lectura HTTP pura, escenarios físicos, replay y ZIP portable, con todos sus cinco assets incluidos.

La huella de replay entre procesos sigue siendo `9c4d43a5815fb042e06e32789b7dc6606023c3eb0634fe08dd7ad90616dc5c24`. La [compatibilidad histórica #42078863601](https://github.com/mxlzz/Nilo_public/actions/runs/42078863601) terminó **success** sobre el primer commit de extracción: seis partidas SQLite sintéticas anteriores reabiertas en copias. Desde ese commit, los cambios posteriores fueron en tests, manifiesto y documentación, no en el código de simulación o la capa de transporte.

## 6. Límites y próximas etapas

Esta etapa preserva la pantalla existente por equivalencia de código y tests. No demuestra por sí sola una inspección visual manual en Windows, Tizen, BOOX y navegadores móviles. La separación de scripts usa variables globales heredadas y no constituye todavía una migración a módulos ES independientes; hacerlo implicaría gestionar dependencias y ámbitos con una nueva ronda de regresión.

Quedan para etapa 21 el laboratorio, controles de respaldo y perfilado del motor; etapa 22 consolidará pruebas de navegador, QA y rendimiento de partidas largas. La autonomía real con Gemini/Groq se evalúa en etapa 23. main y VERSION continúan en 0.6.4; el PR #77 permanece en borrador, sin fusionar. **Próxima: etapa 21 — Laboratorio unificado y centro de ajustes.**
