# Nilo 0.7.1 · Laboratorio · Etapa 03: sistema de diseño

Fecha: 2026-11-06. Rama `work/0.7.1-lab-ui-stage03` derivada de `work/0.7.1-lab-ui-stage02`. Etapa 02: [CI corregido aprobado #42295375459](https://github.com/mxlzz/Nilo_public/actions/runs/42295375459).

## Alcance implementado

- **Una sola fuente de tokens visuales:** `assets/laboratorio.css` concentra colores de superficie/texto/bordes/acento/foco/alertas, radios, tipografía y las correspondencias con los alias CSS anteriores. Se quitaron las cinco declaraciones `:root` duplicadas en HTML. Se mantiene CSS local solo para composición/funciones propias de cada pantalla, que serán reorganizadas en la etapa 04.
- **Dos temas y selección automática:** tema claro u oscuro con preferencia del sistema por defecto. Botón accesible presente en las cinco pantallas; alterna `sistema → claro → oscuro`. El controlador `assets/laboratorio_ui.js` guarda únicamente la preferencia visual en `localStorage`, recuperándola al abrir otras pantallas del mismo laboratorio. Si el almacenamiento está bloqueado, sigue funcionando durante la página actual.
- **Componentes transversales:** encabezado, navegación activa, paneles, cabeceras, controles, foco de teclado, texto secundario, código, tarjetas de registros, tablas de diferencias, estados, avisos y áreas técnicas. Los datos de terreno del mapa conservan colores propios como información física.
- **Responsive y accesibilidad:** reglas compartidas a 1000/720/430 px, ajuste de navegación, foco visible con contraste, tamaño mínimo de los controles del menú, soporte `prefers-reduced-motion`. Sin tipografías externas, librerías ni solicitudes de red.
- **Paquete portable y servidor local:** GET de solo lectura y ruta fija autorizada `/assets/laboratorio.css` y `/assets/laboratorio_ui.js`; MIME correcto, no-store, nosniff, mismo control de loopback/Host que el servidor. Ambos assets están en `MANIFIESTO_SHA256.json`. No existe un directorio estático navegable ni selección arbitraria de rutas.

## Decisiones de alcance

No se altera ningún constructor de prompts, transporte LLM, decisiones, datos SQLite, física, `VERSION` o mecanismo de importación de partidas. Las páginas mantienen sus layout especializados y los controles de la etapa 02. La reorganización particular de cada una es trabajo de etapa 04. Se conserva el código original de renderizado literal del visor: el tema visual no modifica el texto, los hashes, los roles ni la procedencia.

Se dejan intactos los mapas de colores de terreno del sandbox para no cambiar su significado semántico. El sistema claro/oscuro está implementado en CSS y puede refinarse en la revisión visual del usuario.

## Verificación

`tests/test_lab_ui_audit_03.py` incluye:
1. Misma hoja de estilos, controlador y control de tema, una vez en cada pantalla.
2. Tokens, estados de tema, puntos de quiebre, foco visible y ausencia de recursos remotos.
3. Simulación Node.js del ciclo completo de selección de tema y persistencia.
4. HTTP del laboratorio: ambas rutas válidas sirven exactamente sus archivos con Content-Type y políticas esperadas; rutas no permitidas y Host externo rechazados.
5. Las cinco páginas se entregan con las referencias a los assets.
6. Ambos assets presentes en el manifiesto portable.

Se adaptó `tests/test_visor_llm_06.py` para admitir exclusivamente el controlador de tema externo. La validación total Linux/Windows del nuevo PR se registra por separado. Antes de integrar, se requiere CI verde; la aceptación visual final permanece pendiente del usuario.

No se publican solicitudes ni partidas del usuario.
