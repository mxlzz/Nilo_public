# Nilo 0.7 · Etapa 14 — Observación del entorno

**Fecha:** 5 de noviembre de 2026. **Rama:** `refactor/0.7`.  
**Estado: COMPLETADA.** [Validación integral #42043576562](https://github.com/mxlzz/Nilo_public/actions/runs/42043576562): **success**, 854 pruebas, una omitida. [Compatibilidad histórica #42042227634](https://github.com/mxlzz/Nilo_public/actions/runs/42042227634): **success**, seis partidas SQLite sintéticas reabiertas en copias.  
**Baseline protegido:** `main` / 0.6.4, esquema save SQLite v5, partidas personales intactas. [Plan](PLAN_REESTRUCTURACION_NILO_07.md) · [Seguimiento](ESTADO_REESTRUCTURACION_07.md) · [PR #77](https://github.com/mxlzz/Nilo_public/pull/77) · [Issue #74](https://github.com/mxlzz/Nilo_public/issues/74) · [#76](https://github.com/mxlzz/Nilo_public/issues/76).

## 1. Auditoría del alcance

Se relevaron `island_views.map_snapshot/survival_conditions`, `world.world_view/inspect_target`, `brain.context_for/known_site_routes`, `cognitive_projection.project_context`, `nilo_runtime/application/records.public_state`, `worlds/shelter.py`, el catálogo y las pruebas de las versiones 0.5–0.6.4.

| Hallazgo verificable | Efecto anterior | Resolución |
| --- | --- | --- |
| `map_snapshot` mostraba `" "` en terreno no revelado pero proyectaba **todas** las estructuras en `structure_layers` y `structure_cell_lists`. | Una vista podía exponer nombres, IDs, coordenadas y materiales ocultos por sus metadatos JSON. | `visible_structures` filtra por `revealed` y retorna copias; todos los niveles y listas de celdas comparten el mismo filtro. |
| `brain.context_for` obtenía vecinos mediante `tile(w,…)` incluso sin `revealed` y sus últimas 12 obras desde `w["structures"]`. | Un LLM podía conocer terreno adyacente o una obra que el personaje nunca observó. | `adjacent_terrain` presenta `" "` para vecinos no revelados y `construcciones_fijas` usa solo obras observadas. |
| `records.public_state` devolvía `w["structures"]` y las incluía entre los registros enlazables. | El JSON de interfaz filtraba estructuras que no aparecían sobre el mapa. | Proyección UI de obras visibles; sus vínculos de construcción se restringen al mismo conjunto. |
| `world.inspect_target` buscaba por nombre/ID en todas las estructuras, incluidas remotas y no descubiertas. | El fallo de distancia podía revelar existencia, ubicación e ID de un elemento desconocido. | Inspección espacial filtra obras observadas. Si una casilla lejana fue revelada, sigue informando «fuera de alcance». |
| `inspect` informaba durabilidad numérica mientras el contexto cognitivo ya usaba desgaste subjetivo. | Incoherencia de la experiencia perceptiva según la vía de acceso. | `desgaste_observable` único; sin porcentajes en el texto de inspección. Las mediciones reales registradas siguen siendo consultables. |
| `world_view` y transformación cualitativa de desgaste vivían en módulos con responsabilidades físicas/cognitivas mixtas. | Dos lugares de cambio potenciales y separación incompleta de observación. | Propietarios únicos en `nilo_runtime/perception/island.py` y `objects.py`; compatibilidad por reexportación. |

El problema original de efectos secundarios de `enrich_structure` sobre estructuras históricas ya había comenzado a corregirse en etapa 02 usando `deepcopy`. Aquí se afianza y cubre también la revelación espacial y las rutas cognitivas; no se reclama la creación de un segundo estado del mundo.

## 2. Contrato y propiedad del código

**Verdad física:** `nilo_runtime/worlds` y `worlds/shelter.py` siguen siendo propietarios de topología, terreno, construcciones, estado, recursos y abrigo verificable. Leer o renderizar no cambia terrenos, inventarios, registros ni RNG.

**Proyección de isla:** `nilo_runtime/perception/island.py` implementa `visible_structures`, `world_view`, `adjacent_terrain`, `survival_conditions` y `map_snapshot`. `island_views.py` mantiene la importación histórica, sin copiar los algoritmos. La UI conserva el contrato del mapa (`maps`, `structure_layers`, `structure_cell_lists`, `trail_layers`, etc.) y el enriquecimiento de objetos antiguos se realiza exclusivamente sobre copias.

**Agente y proveedores:** `brain.context_for` utiliza el filtro espacial común; los sitios y rutas siguen exigiendo evidencia revelada. No se envía automáticamente el catálogo completo ni las estructuras ocultas. `cognitive_projection` conserva la separación entre valores internos y sensaciones; `perception/objects.py` concentra el lenguaje de desgaste. El contrato completo de prompts/proveedores queda reservado a la etapa 15.

**Interfaz:** `RecordsUseCases.public_state` conserva su estructura de salida y solo expone en `structures` y vínculos del mapa las obras reveladas. Los documentos, mediciones y proyectos históricos propios siguen siendo registros, sin afirmar que un registro de diseño demuestre funcionamiento físico.

**Inspección:** la presencia de una estructura se consulta entre obras observadas, no en todo el estado. Estar registrado lejos de Nilo permite el mensaje de alcance solo si se trata de una casilla conocida. Nombres, etiquetas o `shelter_condition` no dan abrigo: el terreno `h` es el único resguardo verificado por la física actual.

## 3. Validación y diferencias respecto del legado

- Diez pruebas en `tests/test_observacion_14.py`: estructura oculta en ambos niveles, metadatos y UI, copias desprendidas, contexto para LLM, vecino sin revelar, revelación posterior, inspección por nombre, desgaste cualitativo, pureza repetida y 40 lecturas simultáneas con seis workers.
- Auditoría AST `tools/auditar_observacion_14.py`: propietario único y ausencia de rutas directas a estructuras ocultas. Se actualizaron las auditorías transversales de arquitectura y resguardo; el pipeline `.github/workflows/validacion.yml` ejecuta la auditoría y los tests específicos antes de la suite general.
- Tres expectativas antiguas quedaron **reformuladas intencionalmente**, no silenciadas: una obra remota solo es «conocida» si la casilla está revelada; un ensayo cognitivo añade esa casilla conocida a su fixture; la inspección informa «desgaste leve» en lugar de `85%`. Se corrigió también un `NameError` al referenciar `tile_key` en el contexto de salida de cueva.
- **CI integral [#42043576562](https://github.com/mxlzz/Nilo_public/actions/runs/42043576562): success** sobre commit `e201ed899b649f46ab47968191d5f9a4ff049b94`. `854 tests` (1 omitida), escenarios físicos deterministas, replay, auditorías estructurales y ZIP portátil verificados. Los replays entre procesos reproducen el fingerprint histórico `9c4d43a5815fb042e06e32789b7dc6606023c3eb0634fe08dd7ad90616dc5c24`.
- **Compatibilidad histórica [#42042227634](https://github.com/mxlzz/Nilo_public/actions/runs/42042227634): success**; seis SQLite sintéticas de generaciones anteriores reabiertas sobre copias durante la entrega inicial de esta etapa, sin modificar originales. Las correcciones posteriores de imports/fixtures fueron comprobadas en la suite integral final; el flujo histórico **no se ha relanzado para cada commit posterior**.
- No se han creado migraciones de esquema, leyes físicas nuevas, automatismos corporales ni reescrituras retrospectivas de partidas. `main` y `VERSION` permanecen en 0.6.4.

## 4. Límites y etapa siguiente

La distinción entre percepción actual, memoria personal e historial persistido se formalizará todavía más en **etapa 16 · Memoria, investigación y evidencias**. La separación de instrucciones, payloads, límites de proveedores y parseo corresponde a **etapa 15 · Deliberación y proveedores LLM**. La evaluación de autonomía real mediante Gemini/Groq, sesgos de decisión y posibles bucles pertenece a **etapa 23**, no puede inferirse de pruebas sintéticas de lectura.

**Puerta de salida superada:** las consultas y visualizaciones ensayadas no cambian el hash del estado persistible; estructuras y terrenos no revelados no aparecen en las proyecciones del agente ni de mapa; CI integral verde, replay idéntico, ZIP y compatibilidad histórica sintética confirmados. PR #77 continúa en borrador, sin merge ni release 0.7.0. **Próxima etapa 15.**
