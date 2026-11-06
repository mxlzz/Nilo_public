# Etapa 01 · Correcciones funcionales y semánticas del laboratorio

**Fecha:** 2026-11-06. **Rama:** `work/0.7.1-lab-ui-audit`. **Base:** `work/0.7.1-visor-contexto-llm` (PR #79). **Estado:** implementada; validación CI pendiente.

## Evidencias y correcciones

1. **Historial reproducible** (`laboratorio_historico.html`).
   - Hallazgo: al abrir una partida sin eventos o filtrar a cero resultados, podían permanecer el evento, los controles y el detalle del mundo anterior. Una respuesta tardía de `/api/history/event` también podía actualizar la pantalla después de cambiar de partida.
   - Cambio: vaciar la selección y deshabilitar reproducción al cambiar de origen o quedar sin eventos; `sourceToken` y `detailToken` descartan respuestas antiguas de carga, detalle y replay. El historial original sigue siendo de solo lectura.
   - Regresión: el test de Node simula un mundo A con detalle pendiente, abre mundo B sin eventos y verifica que la respuesta retrasada de A no reaparece.

2. **Fidelidad de estados del visor** (`laboratorio_visor_llm.html`).
   - Estados de transporte/validación expresados en español, sin presentar `accepted` como acción ejecutada. El estado crudo se mantiene en el cuerpo y en la vista profesional.
   - Visibilidad de la cobertura de procedencia: completa/parcial/no registrada/no disponible. Reetiquetado de «Origen y transformaciones» a «Procedencia del campo», ya que esa vista no desglosaba las transiciones del campo.
   - Tokens de carga/selección evitan mostrar detalles atrasados tras cambiar filtros o seleccionar otro intento. No se modifica ni reserializa texto del prompt.

3. **Escenarios** (`laboratorio_escenarios.html`).
   - «Órdenes que habría generado el LLM» se sustituyó por «Órdenes predefinidas de prueba»: no se consulta al modelo.
   - Se suprimió el enlace a `mxlzz/Nilo/blob/v<versión>`, que podía apuntar a otro repositorio/revisión. Se mantiene archivo, función y líneas instrumentadas como referencia local. Recuperar enlaces directos exige identificar el commit del código realmente ejecutado; no se infiere a partir de `VERSION`.

4. **Sandbox físico** (`laboratorio_motor.html`).
   - Título histórico `0.6.1` corregido.
   - «Vista LLM» pasa a «Solicitud calculada» y «Contexto exacto enviado» a «Cuerpo JSON que se enviaría», pues no hubo transporte HTTP.

5. **Centro de ajustes** (`laboratorio_ajustes.html`).
   - El check de contexto opcional declara explícitamente que marcar significa **excluir** un campo de la solicitud calculada; no se cambia su comportamiento.

## Fuera del alcance

- Arquitectura de navegación y CSS (etapas 02–03).
- Organización visual de las cinco páginas (etapa 04).
- Instrumentación, cuerpos HTTP, prompts, memoria, física, decisiones, historiales SQLite, funciones del servidor y APIs (sin cambios).
- Enlaces de código fuente por SHA exacto: requieren metadatos verificables adicionales antes de habilitarse.

## Evidencia de pruebas

- `tests/test_lab_ui_audit_01.py`: semántica real/calculada, etiquetas de estado/procedencia, ciclo de vida del historial, enlaces, checks, análisis sintáctico Node de las cinco páginas y regresión asíncrona con respuesta tardía.
- Actualización del contrato de `tests/test_visor_llm_06.py` al título preciso de procedencia.
- Verificar CI Linux y Windows antes de dar la etapa por cerrada. La revisión visual queda pendiente.

No incluir datos de partidas del usuario ni solicitudes LLM en commits.
