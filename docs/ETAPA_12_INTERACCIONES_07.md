# Nilo 0.7 · Etapa 12 — Interacciones y construcción

**Fecha:** 5 de noviembre de 2026. **Rama:** `refactor/0.7`.  
**Estado: COMPLETADA.** [CI integral #42020647740](https://github.com/mxlzz/Nilo_public/actions/runs/42020647740): **success, 815 pruebas (una omitida)**; [compatibilidad histórica #42020647714](https://github.com/mxlzz/Nilo_public/actions/runs/42020647714): **success, seis SQLite sintéticas**.  
**Referencia:** `main` / 0.6.4, esquema SQLite v5 y partidas personales sin cambios. [Plan](PLAN_REESTRUCTURACION_NILO_07.md) · [Seguimiento](ESTADO_REESTRUCTURACION_07.md) · [PR #77](https://github.com/mxlzz/Nilo_public/pull/77) · [Issue #74](https://github.com/mxlzz/Nilo_public/issues/74).

## 1. Reauditoría real del alcance

Se relevaron `world.execute_action`, `construction.apply_intervention`, `construction.salvage`, `mechanics.create_assembly/test_assembly`, `inventions.register_design/design_materials_error`, `capabilities.dispatch`, `vessels.interact`, `structural_loads.interact`, la procedencia de eventos y el reloj de ejecución por fases.

| Comportamiento auditado | Problema confirmado o contrato ya protegido |
| --- | --- |
| `combine`, `craft`, `build` | Débitos directos dentro de `world.py` y fabricación mezclada con la lógica general; era posible añadir reglas de fabricación sin un mecanismo de balance común. |
| `assemble` | El inventario se descontaba **antes** de crear y validar completamente la entidad, aunque los controles de piezas y grafo se ejecutaban previamente. |
| `modify` y `dismantle` | `ensure_object` materializaba componentes/revisiones en el **original** antes de comprobar todas las condiciones. Un rechazo podía dejar cambios; el debitado, recuperación y actualización del objeto se realizaban por separado. |
| `salvage` | Recuperación estimada por estado y hash de IDs válida en su criterio, pero acreditada tipo por tipo sin comprobar previamente todos los saldos de destino. |
| `use`, `excavate` | Reglas de herramienta y excavación mezcladas con el dispatcher. Se acreditaba piedra directamente al inventario al despejar obstáculos. Una etiqueta ambigua podía seleccionar arbitrariamente el primer objeto coincidente. |
| `use/llenar` | Un recipiente con **contenido sólido** podía perderlo por sobrescritura con agua. |
| `mechanics.test_assembly` | Las magnitudes no finitas (`NaN`, infinito) podían llegar al cálculo. `possible_uses.transmision` se anunciaba incluso sin forma móvil o unión articulada. |
| `design` y propuestas | **Ya no ejecutan física por sí mismas**: `design_materials_error` valida composición material, y una propuesta aprobada no instala capacidades. Este contrato se conserva. |
| `interact` sobre contenidos/cargas | Registro cerrado y versionado de capacidades. Las transferencias sólidas ya emplean `transfer_units` desde etapa 10; líquidos conservan sus unidades fraccionarias. No se duplicaron estas leyes. |

## 2. Propietarios y reglas de implementación

### Transformaciones de materiales

**`nilo_runtime/worlds/resources.py`** incorpora `material_counts`, `check_materials` y `exchange_units`: se validan **todas** las cantidades enteras, sus claves y las reservas antes de acreditar o debitar la primera unidad. Una excepción no deja un descuento parcial. `exchange_units` devuelve saldos previos y posteriores, consumo y producción, separados del relato del LLM.

**`nilo_runtime/worlds/fabrication.py`** es propietario único de `combine_action` y `fabricate_action`. `world.execute_action` solo despacha; no mantiene el cuerpo de transformación. Un compuesto consume los lotes originales y recibe **una** unidad resultante; sus atributos derivan de propiedades declaradas en el catálogo/estado y de una regla física acotada. `craft/build` comprueban materiales y ficha de diseño, preparan geometría, componentes y objeto, y descuentan los lotes **al publicar** el artefacto u obra. Una intención `design` nunca crea materia ni capacidades físicas por sí sola. El reloj mantiene sus fases de preparación, trabajo y efectos.

**`mechanics.py`** comparte `check_materials` y `exchange_units`; valida materiales, piezas y grafo antes de construir, y debita unidades luego de preparar el ensamblaje. La transmisión potencial requiere una unión móvil y una pieza con geometría adecuada; no indica que se haya verificado su funcionamiento. Las pruebas de carga y energía rechazan magnitudes no finitas o negativas, sin presentar el dato inválido como fallo físico.

### Modificaciones y recuperación

**`nilo_runtime/worlds/intervention.py`** se encarga del preflight y la publicación aislada de `modify/dismantle`. Antes de crear componentes reales revisa localización, objeto, modo, pieza, presupuesto, condiciones, contenido de recipientes y cargas estructurales. La evaluación prepara una copia del **objeto y de los inventarios/listas afectados**, no una copia del mapa territorial. Solo ante éxito reemplaza el estado del objeto y las reservas, preservando la identidad de sus referencias en la UI y el cuaderno.

**`construction.py`** conserva cálculos técnicos, componentes/revisiones y ejecución interna en `_apply_intervention_mutating`, usada **únicamente sobre el borrador**. La API pública `apply_intervention` llama a `execute_prepared`. `salvage` conserva su recuperación determinista y probabilística por lotes completos, pero acredita el conjunto en una única transacción. Nunca recupera más componentes de los existentes.

**`nilo_runtime/core/identity.py`** incorpora `staged_identity`, reversible dentro de una `EntropySession`: si una reforma fracasa después de preparar IDs de componentes históricos, restaura contador de UUID, contador físico y RNG exclusivo de identidades; si se publica, confirma los IDs. No toca el RNG de decisiones ni la ruta histórica sin `EntropySession`.

### Uso físico y ensayos

**`nilo_runtime/worlds/tool_use.py`** es propietario de `use_action`, `adjacent_rock` y `dig_with_tool`. Calcula capacidad según forma, resistencia y durabilidad, más vecindad y reservas. Corte y excavación acreditan madera/piedra solo si ocurrió una extracción concreta; mover una roca elimina el obstáculo y acredita **una sola vez** su unidad. La roca no puede abrirse ni cambiarse de terreno si el inventario de destino no admite el crédito de piedra. Se conserva la física de contención y flotación de `nilo_runtime/physics/materials.py`.

El uso antiguo `llenar` comprueba contenido preexistente: no pisa sólidos con agua. Una búsqueda de herramientas por etiqueta que coincida con varias exige **ID único**. Los ensamblajes con durabilidad agotada no pueden probarse como activos. `world.py` reexporta `adjacent_rock` y `dig_with_tool` para compatibilidad con consumidores históricos.

### Frontera de evaluación

El registro cerrado de `capabilities.py` sigue separando `verified_success`, `precondition_failed` y `no_evaluable` por los contratos previos. `phenomena.missing_physics` registra un intento cuando falta el modelo sin convertirlo en capacidad real, síntoma corporal o derrota del dispositivo. La evidencia de resultados pertenece a `action_results.py` y al motor de eventos de etapa 03. El catálogo de formas sigue independiente de los nombres narrativos, según etapa 11.

## 3. Regresiones y compatibilidad

`tests/test_interacciones_12.py` incorpora **32 pruebas focalizadas**: intercambio de lotes con prevalidación, mezcla, fabricación y gasto exacto, fichas incompatibles, ensamblaje conexo, rechazo sin mutación de objetos legados, modificación con nuevas revisiones, desmontaje y salvamento, cargas y contenidos previos, acciones de herramienta, corte, excavación acumulativa, movimiento de rocas, no duplicación de piedras, desambiguación de identificadores, cifras físicas inválidas, mecanismo roto y restauración de la secuencia de IDs tras un fallo.

`tools/auditar_interacciones_12.py` inspecciona propietarios por AST, evita volver a introducir cálculos en `world.py`, controla la dependencia por callback, la delegación de reformas y la vigencia del rollback de identidades. `.github/workflows/validacion.yml` ejecuta la auditoría y pruebas específicas antes de la suite completa, escenarios físicos, replays, ZIP portable y pruebas de identidad entre procesos. `MANIFIESTO_SHA256.json` y `tools/verificar_paquete_07.py` incluyen `fabrication.py`, `intervention.py` y `tool_use.py`; las trazas del laboratorio apuntan a los propietarios actuales.

**CI del código final [#42020647740](https://github.com/mxlzz/Nilo_public/actions/runs/42020647740): SUCCESS**, **815 pruebas ejecutadas, una omitida, cero fallas**, 32 casos específicos de etapa 12. Pasaron auditoría estructural, escenarios físicos, validación de identidad/RNG, comparación de eventos, reproducción entre procesos, ZIP portátil extraído e importado y ausencia de claves sensibles. La huella del replay se mantuvo idéntica entre procesos con semillas de hash distintas: `9c4d43a5815fb042e06e32789b7dc6606023c3eb0634fe08dd7ad90616dc5c24`. El código probado corresponde al commit `e307d0ee44ff4c37ed277034dce62104e3a36fe2` (commits posteriores solo documentales con `[skip ci]`). **Histórico [#42020647714](https://github.com/mxlzz/Nilo_public/actions/runs/42020647714): success**, seis SQLite sintéticas de generaciones anteriores importadas en copias; originales intactos. No se utilizaron saves personales.

## 4. Alcance deliberadamente pospuesto

- **Etapa 13 · Necesidades corporales y descanso:** el alivio, abrigo y seguridad deben surgir de condiciones físicas verificadas. La categoría textual `habitaculo` todavía influye en `shelter_condition` y no debe usarse como evidencia científica automática.
- **Etapa 14 · Observación del entorno:** proyecciones para usuario y LLM de solo lectura y acceso a conocimiento material realmente percibido. Los catálogos internos no se transmiten automáticamente.
- **Etapa 18 · Persistencia:** escenarios de restauración/replay de partidas completas, sin modificar v5 ni inventarios privados durante etapa 12.
- **Etapa 23 · Evaluación conductual:** estos tests físicos sintéticos no prueban mejores decisiones autónomas con Gemini/Groq ni eliminación de bucles de investigación.
- **Física avanzada 0.8:** termodinámica, potabilización, evaporación, maquinaria compleja y efectos de escala real requieren modelos y mediciones que no se inventan en 0.7.

**Puerta de salida superada:** suite completa y específica, seis saves históricos sintéticos, escenarios, replay y ZIP portables confirmados en verde; seguimiento e informe cerrados en #74/PR #77. No fusionar el PR ni publicar 0.7.0 hasta completar la etapa 24. **Próxima etapa 13 · Necesidades corporales y descanso.**
