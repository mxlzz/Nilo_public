# Etapa 0 — H16: evaluación de caja negra Ecosystem Explorer

**Fecha:** 2026-11-21 · **Estado:** preregistro antes de ensayo. Marco `BASES_Y_HOJA_DE_RUTA.md` etapa 0, `PROCEDIMIENTO_Y_AUDITORIA.md`, ADR-0001. Este ensayo es de **producto interactivo completo**, NO de un motor reutilizable.

## Fuentes y licencia
- https://www.ethanjhulbert.org/ecosystem-explorer/
- https://www.ethanjhulbert.org/ecosystem-explorer/about/
- https://www.ethanjhulbert.org/privacy-legal/ (actualizado 10 octubre 2026). Reconoce el acceso y uso personal ordinario, pero el código original no está publicado bajo licencia libre identificada; no copiar JS ni distribuir activos. No realizar scraping exhaustivo ni volumen de visitas. Un único acceso rutinario en Chromium a la interfaz pública sin capturar código oculto para la prueba.
- El autor describe mundo generativo por seed, ciclos día/estación/año, clima, agua, vegetación, erosión, intervención e inspección, y guardado portable, con física simplificada **NO calibrada**. Documentación = **afirmaciones del autor**, no evidencia empírica independiente.

## Hipótesis evaluable por un navegador automatizado (sin acceso a API privada)
H16A: la interfaz pública permite alcanzar un estado de mundo inicial no vacío, expone controles de creación y observación, y permite activar progreso temporal medible en una sesión de exploración bajo un solo usuario/bot ordinario.

**Procedimiento** (Playwright en CI Linux, Chromium efímero):
1. Visitar página oficial una sola vez; no descargar código fuente para reimplementarlo ni guardar página/capturas/assets. Esperar inicialización razonable (máx 90s).
2. Registrar **solo indicadores visibles de UI**: encabezado Año/estación, presencia de control de nueva generación/semilla, pausa/velocidad, inspector, guardar/exportar. Usar `innerText` de elementos visibles y texto de botones; no leer objetos JS internos ni alterar las funciones globales de la app.
3. Pulsar un control de velocidad de simulación `28×` o `7×` si es accesible y esperar entre 10 y 15s; extraer encabezado de fecha antes/después para saber si avanzó el reloj. Si hay panel abierto que impide uso, cerrar modal por botón visible estándar; evitar acciones ambiguas que regeneren accidentalmente el mundo.
4. Registrar si cambió `Year N` o estación, y si los controles son accesibles. No **inferir** humedad/erosión/vegetación de un cambio de fecha; sus leyes NO quedan verificadas por este smoke.
5. **Criterio mínimo H16A:** cargó página, estaban disponibles controles de generación y observación, y evolucionó reloj por UI (si no evolucionó, anotar no verificado, no cambiar criterio). Fallos por bloqueo de sitio/navegador deben identificarse por separado.
6. No efectuar más de una sesión automatizada; no exportar archivos ajenos ni modificar contenido persistente. No contacto con autor hasta que sea útil.

## Qué NO validará H16A
- Exactitud física, causalidad multivariada, persistencia tras importación, repetibilidad por seed, emergentismo, tiempo autónomo cuando nadie mira, interfaz de integración/API, licencias del código. Es **benchmark funcional** y no candidato de base legalmente reutilizable.
- H16B (futuro, condicionado) requeriría evaluación manual o navegador de controles de intervención con registro por región + guardado/restauración; no ejecutarla si H16A falla o no puede obtener estados verificables.
- No mezclar con pruebas de NeuroLab ni afirmar motor seleccionado a partir de UI.

## Gates
La etapa 0 requiere cotejar H16 con H15 material y con Landlab ecohidrológico/WorldEngine; no comparar producto terminado de tercera parte vs biblioteca científica mediante un único score. El punto de decisión es **reutilizar** lo que tiene licencia y API apropiadas, y usar Ecosystem Explorer como benchmark de experiencia, sin copiarlo.

## Incidencia H16.1 — prueba de reloj pasó; indicador de controles incorrecto
CI https://github.com/mxlzz/Nilo_public/actions/runs/44957981477 (**FAIL** total). La aplicación devolvió HTTP200, renderizó seis canvas, permitía pulsar **28×**, y el reloj observado pasó de **Year 1 Spring** a **Year 3 Autumn** durante 15s. El test `ui_controls_present` falló porque buscaba etiquetas de **paneles plegados** solo en `document.body.innerText`, que ignora contenido no visible, sin abrir los paneles mediante sus controles. Esto **no significa** que las funciones no existan. El criterio original de disponibilidad sigue válido; falta visitar las secciones visibles para comprobarlo.

**Corrección antes de nueva ejecución:** tras medir el reloj, usar botones públicos visibles `✳` (menú nuevo mundo/guardar) y `⌖` (inspector) por Playwright, sin leer estado interno; comprobar que sus etiquetas se vuelven visibles al abrir los paneles. Si son inaccesibles, reportar nombres de botones visibles, no asumir ausencia. Mantener requisito H16A de controls accesibles + reloj que avanza; no relajar criterios ni probar física.

## Incidencia H16.2 — semántica de botones accesibles, NO fallo del producto
Segunda CI https://github.com/mxlzz/Nilo_public/actions/runs/44958150544, reloj volvió a avanzar de Year1 Spring a Year3 Autumn, `28×` funcionó, HTTP200. El script buscó icono `✳` como botón de nuevo mundo, pero el sitio usa **`⊙`** con `aria-label="Create a new world"`. `✳` abre las herramientas de **intervención**, no generación. El botón `⌖` tiene `aria-label="Inspect a tile"`: activa un **modo de inspección**, no necesariamente abre de inmediato un panel con encabezado `Tile inspector`. La segunda falla `ui_controls_present=false` sigue atribuible al arnés que interpretó mal los controles. Los datos visibles de `button.title`/`button.aria-label` resolvieron la ambigüedad; no se capturó código del sitio.
**Enmienda antes del tercer ensayo:** seleccionar por **nombre accesible semántico**, no por glifo: `get_by_role("button",name="Create a new world")` para abrir menú y verificar labels `Seed` y `Export file`; `get_by_role("button",name="Inspect a tile")` para confirmar disponibilidad y activación del modo (no exigir panel antes de clicar una celda). Mantener reloj que avanza, control 28x, mismo criterio de acceso a generar/guardar/observar, sin hacer test de física.
