# Nilo 0.7.1 — consolidación C1 · 11/11/2026

Registro principal de continuidad: [issue #97](https://github.com/mxlzz/Nilo_public/issues/97).

## Punto de partida verificado
- `main`: 0.7.0, conservar sin cambios.
- `work/0.7.1-lab-stage11-evaluation`: base de esta rama, commit `437f9f1a70a4cb4002bfe1feeb2fbc0a71823b81`.
- PRs #85–#95: cadena de etapas de laboratorio abiertas y en borrador; no incorporadas a main. No intentar fusionarlas individualmente fuera de su orden de dependencia.
- La CI de la rama de etapa 11 (run #42553792750) concluyó correctamente. No equivale a validación longitudinal de memoria/autonomía.
- Estudio A/B documentado en `docs/laboratorio/EVALUACION_ETAPA_11_2026-11-08.md`: hasta dos deliberaciones por variante; no hay evidencia de mejora cognitiva.

## Antecedente recuperado de conversaciones del 08/11/2026
El problema de selección compartida **Historial ↔ Experimentos A/B** ya se había corregido en etapa 11 (run #42512569088: 1.212 pruebas, 0 fallos). C1a no debe describirse como solución de ese problema previo: su alcance son exclusivamente **Visor LLM y Análisis transversal**. Hay un límite independiente de importación de la sidecar.

## C1a: coherencia de partida seleccionada
**Defecto localizado:** `/api/history/episodes` lee `HistorySource`, pero `/api/lab/llm/attempts`, `/api/lab/llm/attempt` y `/api/lab/analysis` leían `LabHub.world`. Se mezclaban fuentes si el usuario elegía otra partida.

**Cambio:** alinear lectura de visor y análisis con `HistorySource.selected_world(fallback=self.hub.world)`. No hay cambios en el motor, la física ni los prompts; no se aceptan rutas arbitrarias del navegador.

**Regresión agregada:** `tests/test_lab_source_consistency_071.py` levanta el servidor HTTP con dos bases y dos sidecars distintos; comprueba selección de mundo, detalle del intento, análisis y ausencia de fugas desde una partida con sidecar ausente. Prueba sin red externa.

**Límite pendiente:** cargar una SQLite con `HistorySource.load_bytes` no carga su sidecar de solicitudes, y la copia temporal cambia el nombre del mundo. Hasta implementar una importación explícita y segura del par mundo+sidecar, el visor no puede mostrar capturas históricas de una partida importada. No atribuir esa ausencia a fallos de memoria del LLM.

## Criterios para cerrar C1
1. Revisar y aprobar CI de esta rama.
2. Verificar con partida real y sidecar emparejado (sin alterar el original).
3. Revisar dependencias y conflictos antes de integrar 0.7.1; no fusionar a main automáticamente.
4. Registrar resultado y próximo paso en issue #97.

**Siguiente investigación (C2):** reconstruir la cadena resultado físico → experiencia → recuperación → payload → decisión del bucle de ensayos de carga, con IDs verificables. No cambiar memoria ni autonomía hasta localizar la falla.

## Verificación de CI posterior al primer commit C1a
- [Run #43022795131](https://github.com/mxlzz/Nilo_public/actions/runs/43022795131): **falló** con 3 pruebas del visor LLM anterior (HTTP 500 por ausencia de SQLite mundo, aunque existe la sidecar). La nueva regresión de selección sí pasó.
- Causa: `HistorySource.selected_world` exige que el mundo exista; algunos tests/instalaciones anteriores generan capturas LLM antes de crear la SQLite del mundo.
- Corrección de compatibilidad: `HistorySource.world_for_read` prioriza partida seleccionada existente y, si no hay selección, permite la ruta local configurada sin exigir presencia de mundo. El lector del sidecar ya gestiona esa condición.
- **La ejecución completa de CI del nuevo commit debe verificarse por separado.**
