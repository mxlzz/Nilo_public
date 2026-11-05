# Nilo 0.7 · Etapa 11 — Materiales, objetos y componentes

**Fecha:** 5 de noviembre de 2026. **Rama:** `refactor/0.7`.  
**Estado:** implementación y pruebas específicas completadas; cierre documental sujeto a CI del último commit.  
**Base:** `0.6.4` conservada en `main`, sin cambiar `VERSION`, partidas privadas ni esquema SQLite v5.

## 1. Reauditoría y hallazgos

Se inspeccionaron `catalogo.py`, los tres JSON de `catalog/`, `physics.py`, `world.py`, `construction.py`, `mechanics.py`, los consumidores de capacidades, el sistema de identidad, el laboratorio y las pruebas de compatibilidad.

| Hallazgo | Riesgo concreto | Decisión |
| --- | --- | --- |
| `world.infer_form` extraía «filo», «punta», etc. del **nombre** del objeto; `make_item` lo hacía también al fabricar objetos nuevos sin `form` | La etiqueta «hacha» podía conferir capacidad de corte sin declarar su geometría | Separar explícitamente clasificación histórica y creación de artefactos nuevos; `physical_item` exige `form` declarada para conferir capacidad |
| `build` determinaba portabilidad mediante el nombre | El texto de un artefacto podía convertir una obra fija en herramienta transportable | `craft` crea objeto portátil; para `build` solo una forma explícita del catálogo habilita ese destino |
| `construction.ensure_object` usaba `obj.setdefault('components',_components(...))` | Python evalúa `_components(...)` aun si existen componentes: se generaban IDs descartados y se desplazaba el flujo de identidades deterministas | Materialización **perezosa**, solo cuando faltan componentes; conserva IDs existentes |
| `construction.recompute` importaba `world.item_effects` | Dependencia invertida entre construcción y dispatcher físico | Import directo de `worlds.objects.item_effects`; no queda una segunda implementación |
| Validación de piezas y uniones repetida en `mechanics.create_assembly` y `test_assembly` | Divergencia de criterios, aceptar bool como índice y validar conexiones por caminos distintos | `worlds.components` como dueño único de normalización y conectividad |
| `catalogo._validated_objects` descartaba silenciosamente nombres de forma inválidos en JSON | Catálogo mal formado podía cargarse parcialmente | Rechazo explícito de claves vacías/no textuales |
| `physics.properties` prefería siempre el catálogo base incluso frente a mediciones explícitas almacenadas | Los materiales medidos no podían alterar densidad/permeabilidad en el motor físico | Preferencia por datos numéricos explícitos y finitos; fallback al catálogo para partidas sin mediciones |
| Casco hueco de **cero materiales** recibía volumen y capacidad, y el cuerpo vacío podía flotar | Objetos sin componentes podían originar capacidad gratuita | Desplazamiento/capacidad cero para objetos sin materiales |
| `item_effects` atribuía «contener» a cualquier objeto `form=recipiente`, incluso con geometría **maciza** | Discrepancia con `physics.evaluate_containment` | Si existe geometría medida, `contener` exige `shape=hueco`; el legado sin geometría conserva inferencia temporal |

## 2. Modelo implantado

**`nilo_runtime/worlds/objects.py`** es el propietario de `infer_form` (interpretación exclusivamente heredada), `declared_form`, `physical_item`, `make_item`, `item_effects`, `is_portable` heredado, clasificación visual de estructuras y `component_summary` puro. `world.py` importa y reexporta las APIs anteriores: no mantiene versiones duplicadas. La identidad física sigue viniendo de `nilo_runtime.core.identity.physical_suffix` (etapa 04).

Para un objeto **nuevo**, `name` y `purpose` son datos narrativos. La forma debe ser un valor explícito de `FORMS` para dar `golpear`, `cortar`, `excavar`, `mover` o `contener`. Sin forma declarada, `simple` carece de esas capacidades. La aptitud efectiva sigue necesitando ensayo real: una capacidad potencial no equivale a función verificada.

Para un objeto **legado**, `infer_form(name, form)` continúa resolviendo los nombres tradicionales cuando no se conoce su forma. `migrate_portable_structures` conserva esa heurística histórica para importar partidas viejas, sin reescribir retrospectivamente lo que ya se había guardado. Un cambio de nombre en un nuevo objeto no cambia la resistencia, densidad, flotación, geometría o capacidades si su definición física es idéntica.

**`nilo_runtime/worlds/components.py`** contiene `normalize_parts`, `normalize_joints` y `connected_parts` sin efectos. Se exige forma del catálogo, material conocido, extremos de unión válidos y grafo conexo; no se considera un ensamblaje funcional solo por sus etiquetas. `mechanics.py` utiliza esas funciones tanto para construir como para verificar el aparato, manteniendo las reglas de consumo existentes bajo control de etapa 12.

**`physics.py`** conserva la API y los valores base de `MATERIAL_PHYSICS` cuando no hay mediciones nuevas. Un material nuevo o medido utiliza `density`/`permeability` del estado, si son finitas y dentro de límites físicos existentes; de lo contrario conserva el catálogo/fallback. No hay nueva ley térmica, CFD ni dinámica 3D.

**`construction.py`** mantiene la representación 2.5D y la historia de revisiones. `ensure_object` solo crea componentes si realmente faltan, sin consumir identidades en lecturas repetidas de un objeto ya equipado. `component_summary` ofrece una proyección **no mutante**, incluso para objetos con listas antiguas de materiales. `recompute` utiliza al propietario de capacidades en vez del dispatcher de acciones.

## 3. Pruebas y evidencia

- **18 tests focalizados** en `tests/test_objetos_11.py`: fuentes únicas, forma vs. etiquetas, propiedades medidas vs. catálogos, recipientes huecos/macizos, vacío material, control de NaN/Inf, identidad estable e idempotencia de migración, JSON inválido, uniones válidas e inválidas, inventario sin gasto ante ensamblaje desconectado y fabricación real.
- `tools/auditar_objetos_11.py`: valida AST de propietarios, ausencia de duplicación/ciclos, no consumo eager de IDs y dependencia de `craft` respecto de `physical_item`.
- `laboratorio_motor.py` registra y enlaza trazas reales de `objects.py` y `components.py`; prueba de fabricación en `tests/test_laboratorio_motor.py` verifica propietario y URLs.
- `MANIFIESTO_SHA256.json`, `tools/verificar_paquete_07.py` y `.github/workflows/validacion.yml` incluyen ambos módulos, con prueba de arranque desde ZIP extraído.
- [CI integral sobre código anterior a la última actualización del laboratorio #42013249799](https://github.com/mxlzz/Nilo_public/actions/runs/42013249799): **success**, 781 tests (1 omitida), ZIP importable, replays idénticos y escenarios físicos. La última CI, que añade prueba del laboratorio, debe verificarse separadamente.
- [Compatibilidad histórica pública #42012878554](https://github.com/mxlzz/Nilo_public/actions/runs/42012878554): **success** con seis SQLite históricas sintéticas y seis semillas; originales sin modificar. No se emplean partidas personales.

### Cambios intencionales

La clasificación de **herramientas nuevas** pasa a depender de `form` declarada. `craft(name='hacha')` sin `form='filo'` no produce una herramienta capaz de cortar. Los artefactos existentes siguen siendo leídos mediante inferencia histórica. `build` sin forma declarada crea estructura incluso cuando el nombre sugiere «martillo»; la decisión explícita de portabilidad ya no queda delegada al texto.

Los valores de masa/permeabilidad proceden de datos de materiales, y una geometría vacía deja de conferir volumen positivo. Esta corrección puede cambiar resultados de artefactos incompletos; no se oculta como igualdad universal de comportamiento.

## 4. Fronteras y deuda expresamente registrada

- La **clasificación visual `habitaculo`** sigue derivando de etiquetas históricas y en el código vigente influye en `shelter_condition`/descanso mediante `island_views.surroundings`. Es un acoplamiento pendiente: no se lo confunde con una propiedad física validada de cubierta ni se atribuye a esta etapa la solución. **Etapa 13** revisará abrigo y necesidades, junto con una condición de refugio que dependa de evidencia física.
- Los consumos de `combine`/`craft`/`assemble`/`build` y `construction.apply_intervention`, las recuperaciones `salvage`, las reformas y los efectos antes de terminar validaciones siguen sujetos a **etapa 12 · Fabricación e interacciones físicas**. Esta etapa 11 no los declara transaccionales ni elimina la deuda existente.
- La evolución de ley térmica y procesos físico-químicos complejos sigue fuera de 0.7. El objetivo aquí es coherencia del contrato y fuentes de verdad, no inventar física faltante.

**Condición de cierre:** CI final verde tras trazas del laboratorio, pruebas focalizadas y generales, seis saves sintéticos históricos compatibles, escenario y ZIP importable, replay RNG exacto, registro del issue #74/PR #77 y ningún merge a `main`. La etapa 12 se habilitará al cerrar esta condición.
