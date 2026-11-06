# Nilo 0.7.1 · Auditoría de interfaz · Etapa 02

**Fecha:** 2026-11-06. **Rama:** `work/0.7.1-lab-ui-stage02`. **Base:** `work/0.7.1-lab-ui-audit` (etapa 01, CI #42292210597 aprobado). **Estado:** implementada, pendiente de CI del PR. **No se cambia VERSION ni el motor.**

## Inventario y decisión de arquitectura

El laboratorio tiene cinco páginas HTML, cuatro secciones globales y tres modos de ensayo. Se conserva cada herramienta y endpoint existente. Los antiguos vínculos globales mezclaban páginas, submodos y nombres (`Sandbox`, `Acciones`, `Partidas históricas`, `Visor LLM`), con omisiones diferentes en cada pantalla. El contrato nuevo es:

| Sección principal | Ruta estable | Fuente y sentido |
| --- | --- | --- |
| **Solicitudes LLM** | `/visor-llm` | Intentos de transporte **reales**, archivados en sidecar por partida. El estado `accepted` no prueba ejecución física. |
| **Historial** | `/historico` | Registros auténticos, en lectura; reproducción posterior en simulación aislada. |
| **Pruebas** | `/` | Escenarios y planes **simulados**, con motor real, sin efectuar llamadas LLM. |
| **Ajustes** | `/ajustes` | Edición y evaluación de perfiles; solicitudes **calculadas** y aplicación condicionada al reinicio. |

La navegación principal usa los mismos cuatro enlaces y orden en las cinco páginas, con `aria-label="Secciones del laboratorio"` y `aria-current="page"` para la sección actual. Las rutas no cambian y los enlaces permanecen locales; el servidor no recibe nuevas rutas.

## Modos de Pruebas

| Modo | Acceso | Comportamiento |
| --- | --- | --- |
| **Escenarios** | `/` | Catálogo de casos reproducibles con resultado esperado y comparación física. |
| **Plan de acciones** | `/?modo=plan` | Constructor manual de hasta 12 operaciones y ejecución sobre Simulation aislada; reemplaza la etiqueta ambigua «Sandbox de acciones». |
| **Mundo interactivo** | `/sandbox` | Copia aislada del mundo, mapa seleccionable y ejecución incremental de acciones. |

En la página de escenarios los dos primeros modos siguen usando los controles originales y las mismas funciones JavaScript; la barra de direcciones ahora refleja el modo mediante `history.pushState`. Los botones, `aria-pressed` y `aria-current` se sincronizan y `popstate` restaura la pestaña tras navegar hacia atrás/adelante. Así `/?modo=plan` es compartible y accesible desde el mundo interactivo. El tercer modo sigue siendo una página independiente.

## Jerarquía transversal acordada

1. **Identidad y clase de fuente** en el encabezado: real archivada, historial, prueba aislada o ajuste calculado. Se aclara cuándo hay un motor real procesando acciones pero **no** una solicitud LLM real.
2. **Navegación principal** por propósito del usuario y **navegación secundaria** solo cuando existe una modalidad de la misma herramienta.
3. **Selección o preparación** del registro/caso.
4. **Contenido y resultados** originales/calculados, con trazabilidad y estados propios. No se convierten automáticamente en conclusiones.
5. **Detalle de procedencia/código** disponible sin inferir que un enlace a `VERSION` apunte al commit correcto.

La futura reorganización interna de paneles, tablas, órdenes de resultados, componentes y estilos corresponde a etapas 03 y 04, no a esta etapa. En particular, aún no se altera el orden de secciones de los reportes de escenarios ni los bloques literales del visor.

## Implementación

- Se unificaron los enlaces del encabezado de los cinco HTML, marcando la sección activa.
- Se agregó navegación contextual en Escenarios y Mundo interactivo.
- Se alinearon los nombres visibles de las vistas, sin eliminar funcionalidades.
- Se añadió solo el CSS mínimo para que la navegación principal conserve distribución y foco legible; el sistema visual compartido queda para etapa 03.
- Se mantuvieron las rutas, operaciones de los formularios, APIs HTTP y almacenamiento existentes.
- No se modificaron prompts, física, archivos SQLite ni instrumentación de solicitudes.

## Validación

- Test `tests/test_lab_ui_audit_02.py`: estructura y orden de navegación, único enlace activo, rutas y submodos, indicadores de tipo de datos y simulación con Node de cambio de modo y navegación `popstate`.
- Se adaptó el test heredado `tests/test_visor_llm_06.py` al nuevo menú global sin quitar los controles de literalidad.
- JavaScript de las cinco páginas verificado sintácticamente; prueba manual simulada en JS de apertura de Plan, regreso y avance: aprobada.
- **Pendiente:** CI completo de GitHub del nuevo PR y revisión visual conjunta posterior a etapa 03.

No fusionar la rama en `main`, ni publicar 0.7.1 por este cambio.
