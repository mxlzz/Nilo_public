# Nilo 0.7.1 — Etapa 01 · Auditoría de infraestructura y baseline

**Fecha:** 2026-11-07 · **Estado:** auditoría de etapa 01 concluida sobre el código inspeccionado y el run aportado; pendiente CI sobre la rama y revisión del PR.  
**Código auditado:** `work/0.7.1-lab-ui-stage04-visor` (head inicial `aeaeb15d9bea54a27afff3ea7846e0861e76b56a`), aún en una cadena de PRs borrador; **no afirmar que todas estas capacidades están en main**.  
**Partida:** copias privadas de `nilo_mundo(20261106-190815).sqlite3` y su sidecar `nilo_mundo.llm_requests(2).sqlite3`. Versión declarada en sesión: `0.7.0`; **`code_commit` es NULL**, por tanto no se puede atribuir de forma exacta la partida a un commit.  
**Privacidad:** no se publican cuerpos HTTP, conversaciones, notas de Nilo ni estados físicos del usuario. El [manifest agregado](../../tests/fixtures/lab_stage01_run_20261106_manifest.json) tiene hashes, tamaños y recuentos; los archivos fuente permanecen privados.

## 1. Inventario de capacidades

| Capacidad / dato | Fuente verificada | Estado para investigación | Límite real |
|---|---|---|---|
| Salida exacta enviada por HTTP | `gateway.py::_post` → `trace_context.py::transport_started` → `storage/llm_requests.py` | **Presente**, por intento, con bytes y SHA-256 | El archivo sidecar conserva máximo 5.000 intentos; no equivale a historial ilimitado. |
| Procedencia y filtros del contexto | `trace_context.py` + `provenance.py` + `provenance_codec.py` | **Presente parcialmente**, seis snapshots efímeros y cambios por ruta, más referencias AST | AST no demuestra la rama ejecutada; procedencia de hijos heredada de raíz, no exacta. Snapshots intermedios **no** se guardan como valores. |
| Visor LLM literal | `labs/llm_read.py`, `labs/literal_segments.py`, `laboratorio_visor_llm.html` | **Presente en rama de interfaz** | Muestra captura real, no puede inventar llamadas no archivadas. |
| Respuesta textual original del LLM | `agent/gateway.py::_response`; esquema `storage/llm_requests.py` | **No archivada en la sidecar** | Solo puede conocerse la decisión normalizada que llegó al historial, no el JSON crudo recibido ni todas las causas de validación. |
| Decisión normalizada y enlace con intento | `application/decisions.py::think` → `archive.add('llm_decision')` | **Presente** por `trace_call_id` en el run | No todos los HTTP aceptados producen necesariamente decisión archivada. |
| Acciones, efectos, mediciones, diagnósticos | `application/clockwork.py`, `archive.py`, `history` | **Presentes**, con categorías y relaciones parciales | La relación exacta de cada operación con su decisión de origen no está normalizada en una sola cadena de IDs. |
| Estado para reproducción histórica | `storage/timeline.py`, `historical_lab.py` | **Presente** desde versiones que guardan checkpoints predecisión y preacción | Reejecuta **motor instalado**, no versión exacta original; UUID, recursos externos y algunas fuentes archivadas pueden diferir. |
| Escenarios aislados y traza de funciones | `laboratorio_casos.py`, `laboratorio_motor.py`, `laboratorio_escenarios.html` | **Presente** como simulación sin LLM; 68 escenarios declarados cubren 26 operaciones según documentación | Las trazas son selectivas; ausencia de una línea no significa que una regla no existiera; pruebas no demuestran una decisión autónoma del LLM. |
| Sandbox físico/manual | `labs/sandbox.py`, `laboratorio_motor.html` | **Presente** | Ejecuta plan dado por observador; no se lo atribuye a Nilo. |
| Ajustes y vistas previas | `labs/hub.py`, `core/lab_settings.py`, `laboratorio_ajustes.html` | **Parcial**: nueve campos opcionales seleccionables, perfil y comparación local | No son checks arbitrarios por ruta; campos obligatorios se bloquean, no hay exportador de revisión vinculada a episodios. |
| Historial de partidas | `historical_lab.py`, `laboratorio_historico.html` | **Presente**, con eventos y checkpoints vinculables | La partida anterior a los checkpoints solo ofrece lectura, no replay fiel. |
| Notas del observador / exportador de exclusiones | Interfaz actual | **Faltante** como expediente autocontenido | No confundir con Cuaderno de Nilo. |
| Seguimiento experiencia → memoria → recuperación posterior | `archive.py` y contexto seleccionado | **Parcial** | IDs de evidencias relacionados ayudan, pero el linaje longitudinal requiere indexación explícita. |
| Análisis transversal (matriz campo×turno) | Sidecar y `provenance` | **No implementado** como vista | Los tokens exactos **por campo** no vienen del proveedor; se estiman. |

## 2. Baseline del run verificado

- `history`: **317** registros. `llm_decision`: **17**; `decision`: **17**; `diagnostic`: **35**; `measurement`: **35**.
- `timeline_checkpoints`: **53**, de ellos **17** predecisión y **36** preacción. **53/53** SHA-256 válidos.
- `llm_requests`: **19 intentos**, **18 deliberaciones únicas**; estados **18 accepted** y **1 transport_error**. **19/19** hashes y longitudes del cuerpo válidos.
- `llm_request_provenance`: **19/19** metadatos decodificados y `payload_verification=verificado_con_payload_http`, `trace_status=complete`. Esto verifica igualdad semántica final del contexto y el cuerpo, **no** ramas Python ejecutadas.
- Los **17** `llm_decision` archivados poseen `trace_call_id` y **17/17** enlazan con uno o más intentos. Un `call_id` contiene **dos intentos** (error de transporte + reintento aceptado con mismo SHA del cuerpo).
- Existe **1 intento `accepted` sin `llm_decision` archivada** en la copia del run, al final de la ventana. No atribuirle una causa: puede haber terminado la partida antes de archivar o existir una discrepancia de persistencia. El estado `accepted` significa «transporte recibido y normalización aceptada según el capturador», no resultado físico garantizado.
- Las 36 acciones checkpoint incluyen `explore`, `inspect`, `excavate`, `go`, `use`, `gather`, `craft` y `forage`; se cuentan 35 diagnósticos. El checkpoint final `forage` carece de diagnóstico `forage` en la copia suministrada. **No inferir fallo del motor** sin examinar el estado o una ejecución completa.
- El archivo JSON separado de la **primera solicitud** subido por el observador es idéntico en bytes al primer cuerpo del sidecar: SHA-256 `1d3c480277dea758afd1d296c0112261d135913eddc46870772c55d986cf8ced`, longitud 31.191.
- La procedencia almacenada cubre seis etapas: `percepcion → proyeccion → perfil → compactacion → presupuesto → solicitud_preparada`. La captura preserva la salida efectiva del constructor, pero no el texto intermedio omitido.

Los SHA completos de las **dos copias SQLite privadas**, cuatro intentos seleccionados y todos los conteos se conservan en [manifest](../../tests/fixtures/lab_stage01_run_20261106_manifest.json), sin subir datos internos.

## 3. Casos de referencia fijados

| Caso | Hecho / pregunta de investigación | Material disponible |
|---|---|---|
| **F01** Primer turno | ¿Qué información recibió exactamente al comenzar? | Cuerpo literal del primer HTTP, procedencia, decisión normalizada, checkpoint predecisión. |
| **F02** Reintento de transporte | ¿Puede la misma deliberación producir dos intentos? | Dos registros con un `call_id`, igual SHA HTTP y estados diferentes; solo una decisión archivada. |
| **F03** Acción sin éxito verificado | ¿El motor rechazó o ejecutó sin el efecto buscado? | Diagnósticos `use` y `excavate` con `verified_failure`, mediciones y checkpoints donde existan. No hay respuesta LLM cruda. |
| **F04** Acción y medición normales | ¿Cómo relacionar plan, acción y resultado físico? | `gather`/`craft` con `verified_success`, diagnósticos y mediciones; vínculo decisión→acción debe cotejarse. |
| **F05** Solicitud aceptada sin decisión archivada | ¿Cómo se ve una cadena incompleta? | Solicitud literal y estado `accepted`; **ausencia documentada** del archivo de decisiones. |
| **F06** Preacción sin diagnóstico de la misma op | ¿Qué muestra el laboratorio cuando todavía no hay resultado verificable? | Checkpoint `forage` sin diagnóstico `forage` en este archivo. |

**No publicar las capturas crudas en el repositorio público.** Los ejemplos se pueden reconstruir desde las bases locales mediante `tools/lab_stage01_manifest.py` y sus SHA, no desde el manifest público.

## 4. Restricciones para las etapas 02–08

1. **Primero el vínculo, luego la UI:** un episodio debe admitir múltiples HTTP por deliberación, varias operaciones, acciones de rutina sin LLM y ausencia explícita de respuesta/resultado.
2. **Separar cuatro evidencias:** estado físico real, información perceptible, entrada HTTP efectiva, decisión/plan/ejecución. No inventar explicaciones del razonamiento interno del modelo.
3. **No atribuir causalidad a hashes o timestamps cercanos**: priorizar IDs comprobados; usar asociación temporal solo rotulada como tentativa.
4. **Privacidad por diseño:** la exportación futura sí podrá incluir texto literal seleccionado, pero **solo por acción local explícita** y sin claves API. Nunca sincronizar automáticamente a GitHub capturas del mundo.
5. **Replay histórico con límites claros:** checkpoints existentes permiten rehacer procesamiento bajo motor actual, pero los casos `F05` y `F06` no pueden reconstruir hechos que nunca se registraron.
6. **Fidelidad de contexto:** la interfaz puede agrupar por campos y roles sin reescribir valores; marcar origen heredado/inferido cuando no es exacto.

## 5. Verificación y cierre

Se preparó `tools/lab_stage01_manifest.py` (solo lectura), el manifest agregado y `tests/test_lab_stage01_manifest.py` con pruebas de reintento/vínculo, corrupción de hash y **no mutación** de ambas bases. **Las 3 pruebas unitarias pasaron localmente** en el entorno de auditoría, y la salida real del run se generó dos veces sin diferencias. **No se ejecutó aquí la suite completa del repositorio**; dependerá de CI de este PR.

**Etapa 01: inventario y baseline terminados**. La siguiente, **etapa 02**, instrumentará las uniones faltantes y la respuesta cruda segura sin recrear la parte ya construida.
