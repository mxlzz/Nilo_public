# Nilo 0.7 — Etapa 19: servidor, API y observatorio

**Fecha:** 5 de noviembre de 2026. **Rama:** refactor/0.7. **Referencia estable:** main 0.6.4. **Esquema SQLite de partida:** 5 (sin cambios).

[Plan general](PLAN_REESTRUCTURACION_NILO_07.md) · [Tablero de etapas](ESTADO_REESTRUCTURACION_07.md) · [PR #77](https://github.com/mxlzz/Nilo_public/pull/77) · [Issue maestro #74](https://github.com/mxlzz/Nilo_public/issues/74).

## 1. Alcance de la reauditoría

Se revisó el servidor local previo en nilo_runtime/web/http.py, las interfaces públicas de application/records.py, decisions.py y clockwork.py, la selección de fuentes del observador en observer.py, las preferencias de interface_prefs.py, la proyección de proveedores en providers.py, el adaptador histórico nilo.py y los contratos consumidos por interfaz.html.

Se verificaron los 8 endpoints de consulta y las 13 rutas de mutación/operaciones existentes, además de la nueva ruta informativa de versión. Se mantuvo la compatibilidad de rutas y del import histórico nilo.Handler.

### Problemas identificados

1. El handler HTTP combinaba parsing, permisos, invocación de comandos, manejo de excepciones y serialización en dos métodos grandes. La simulación podía depender de detalles del transporte al crecer el número de endpoints.
2. Los POST admitían datos JSON sin comprobar el Content-Type y no verificaban Host ni Origin/Referer. Un servidor ligado a loopback no equivale por sí mismo a autorizar solicitudes de sitios web externos.
3. Las solicitudes con JSON de nivel superior distinto de un objeto, contenido inválido o tipos inesperados podían producir errores 500 en lugar de respuestas de validación. El código aceptaba silenciosamente truncamientos de IDs; la nueva validación rechaza longitudes fuera de contrato.
4. Un fallo inesperado dentro de una ruta no tenía un límite uniforme para impedir detalles internos en respuestas HTTP. Ahora se retorna un error 500 genérico, sin traceback ni secretos.
5. La lectura de estado de proveedores invocaba _health(), que inicializaba o reiniciaba contadores de disponibilidad y estadísticas diarias dentro del mundo. Consultar /api/state modificaba indirectamente el estado persistible del motor. Se corrigió providers.public_info() para proyectar esos contadores sin escribir.
6. El campo routing.providers[].health_key incluía identificadores derivados de claves de credenciales de proveedores. Aunque no eran claves en texto plano, eran innecesarios para la interfaz. La proyección pública ya no transmite esos identificadores.
7. El Handler anterior usaba una variable de clase global Handler.sim, por lo que dos servidores de prueba simultáneos podían compartir accidentalmente una simulación. create_server(sim,port) crea un handler específico para cada instancia.

## 2. Arquitectura resultante

- **nilo_runtime/web/http.py:** transporte mínimo, headers HTTP, servidor loopback, entrega de interfaz HTML, lectura JSON y cierre de sesión. Conserva Handler, HTML_FILE y main() para importaciones heredadas y deja de contener la lógica de cada comando.
- **nilo_runtime/web/api.py:** contrato API v1, rutas GET y POST declaradas, validación de tipos, clasificación de errores 400/404/405/409/503, y delegación a casos de uso existentes del motor. El GET de la partida pasa por una proyección explícita; ninguna ruta de lectura llama a write, plan_ready, think o cambio de velocidad.
- **nilo_runtime/web/security.py:** protección de solicitudes locales: Host loopback con el puerto correcto, Origin y Referer del mismo servidor, rechazo de Sec-Fetch-Site cross-site; POST con application/json, Content-Length limitado, UTF-8/JSON válido, rechazo de transferencias chunked no soportadas, NaN/Infinity JSON y cuerpos que no sean objetos.
- **nilo_runtime/web/projections.py:** adaptador de salida del observatorio. Copia únicamente los campos que transforma y excluye health_key, api_key, token y otras identidades sensibles de la información de ruteo. Los nombres, estados, estadísticas y tiempos para la interfaz continúan disponibles.
- **providers.py:** public_info() lee los valores registrados, produce contadores diarios predeterminados o vigentes y no crea/actualiza health en un GET. La escritura real de métricas sigue perteneciendo a route().

## 3. Contrato de API v1

**Consultas GET:** /api/state, /api/version, /api/summary-history, /api/unread, /api/record, /api/measurement, /api/ui-preferences, /api/diagnostic.

**Operaciones POST:** /api/settings, /api/chat, /api/read-news, /api/read, /api/read-all, /api/read-summary, /api/review-rule, /api/retry-llm, /api/ui-preferences, /api/review-bootstrap, /api/review-mark, /api/summary-generate, /api/summary-ack.

La ruta nueva GET /api/version responde con api_version (1), schema_version (5) y engine_version, evitando confundir el número de la API con la versión comercial 0.6.4/0.7 o con el formato del save.

Se mantienen respuestas 202 al aceptar chat, 409 cuando retry-llm no procede, 503 ante fallo de disponibilidad del proveedor, 404 para rutas/archivos inexistentes, y 400 para entrada inválida. El límite de entrada normal es 3.000 bytes; la selección del observador y revisiones permite hasta 65.000 bytes, como antes. Los errores internos no revelan rutas locales, credenciales ni detalles de Python.

El observador continúa diferenciando los registros archivados de decisiones/hypótesis del agente y no marca entradas como leídas por consultarlas o generar una síntesis. La confirmación de lectura requiere los comandos existentes. No se asignan objetivos a Nilo desde la API.

## 4. Seguridad local y límites

El servidor continúa escuchando exclusivamente en 127.0.0.1. Se validan el Host y, cuando están presentes, Origin/Referer. Se rechaza explícitamente Sec-Fetch-Site cross-site. No se habilita CORS ni se incorpora acceso remoto. Esto protege ante solicitudes ordinarias del navegador desde otras páginas y errores de DNS rebinding, pero **no equivale a autenticar aplicaciones nativas que corran en el mismo equipo**; la simulación conserva su modelo de herramienta local de usuario único.

La proyección pública evita compartir el health_key vinculado a credenciales. No hay cambios sobre la lógica física, el RNG, el mapa, los proveedores efectivos ni el esquema SQLite; se conserva el nombre y firma de nilo.Handler para compatibilidad con tests, UI y código de versiones anteriores.

## 5. Pruebas y puerta de salida

- tools/auditar_api_19.py comprueba la frontera entre HTTP y API, propietarios, aislamiento local, ocho consultas GET y trece operaciones POST, la proyección de credenciales y ausencia de actualización de salud por consultar.
- tests/test_api_19.py ejecuta peticiones reales HTTP contra un servidor local efímero: consulta sin mutaciones de mundo ni RNG, HTML y versión, categorías/IDs, comandos con validación, chat 202, síntesis no marcada como leída, Host/Origin/Referer y cabeceras de seguridad, errores 400/403/404/405/413/415/500, Unicode/JSON malformado, datos no finitos, identidad de simulación por servidor y compatibilidad nilo.Handler.
- La CI integral sigue comprobando escenarios físicos, huellas de replay entre procesos, integridad de ZIP portable y 932 pruebas heredadas previas a la nueva suite.
- La compatibilidad histórica reabre seis partidas SQLite sintéticas de versiones anteriores **sobre copias**, sin cambiar originales.
- Las comprobaciones de la interfaz principal, fragmentación de HTML/JS y navegación quedan reservadas para **etapa 20**, sin introducir un rediseño visual en esta etapa.

## 6. Resultado y trabajo pendiente

**Etapa 19:** implementación y tests específicos integrados. El cierre se registra con el resultado final del pipeline de validación. La comprobación de la interfaz y sus assets queda en la etapa 20. El laboratorio y sus controles de backup se tratarán en la etapa 21.

No se fusiona PR #77 ni se publica 0.7.0 antes de finalizar las etapas 19–24 y la evaluación real de autonomía.
