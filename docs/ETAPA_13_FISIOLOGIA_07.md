# Nilo 0.7 · Etapa 13 — Necesidades corporales y descanso

**Fecha:** 5 de noviembre de 2026. **Rama:** `refactor/0.7`.  
**Estado: COMPLETADA.** [Validación integral #42025565724](https://github.com/mxlzz/Nilo_public/actions/runs/42025565724): **success**, 844 pruebas ejecutadas (1 omitida). [Compatibilidad histórica #42025565421](https://github.com/mxlzz/Nilo_public/actions/runs/42025565421): **success**, seis partidas sintéticas.  
**Base protegida:** `main` y `VERSION` conservan 0.6.4. No se modificó esquema SQLite v5, ni partidas personales.

## 1. Alcance auditado y hallazgos

Se revisaron `survival.py`, `bodily_policy.py`, `nilo_runtime/application/clockwork.py`, `nilo_runtime/application/session.py`, `island_views.py`, `experiment_log.py`, `construction.py`, `inventions.py` y `laboratorio_motor.py`. Se contrastaron las pruebas de percepción, umbrales, autocuidado voluntario, restauración histórica, ensayos de descanso y el [issue #75](https://github.com/mxlzz/Nilo_public/issues/75).

1. La fisiología y sus palabras perceptivas permanecían en un archivo raíz; el reloj conocía por duplicado los umbrales de inconsciencia y recuperación. El cálculo de fatiga no trataba explícitamente NaN/Inf.
2. El motor distinguía `rest` de `wait` como acción, pero **`wait` aún ganaba energía pasivamente** (+1,2 puntos/h sobre un drenaje basal de 0,4). La espera sin descansar no podía medirse como control negativo.
3. Un objeto clasificado `habitaculo` por su nombre o propósito y con cuatro componentes/resistencia suficiente recibía `shelter_condition`. Tanto el reloj como el módulo de experimentos convertían esa **categoría narrativa** en ventaja fisiológica.
4. `inventions.record_design_test` vinculaba una recuperación de energía bajo la celda de refugio inicial a un diseño de obra colocada allí. Eso confundía una mejora ambiental preexistente con una capacidad construida.
5. Las consultas `needs_summary`/`perceived_needs` migraban estado y añadían registros a `person`; observar al personaje tenía efectos secundarios. El tratamiento de tiempo o reserva no finita tampoco era estricto.
6. `abrigo` y `seguridad` carecen de clima y amenazas simulados. No existe un modelo de cubierta, aislamiento térmico o cerramientos que permita acreditar una construcción como protección; simular ese efecto a partir de una palabra sería inventarlo.

## 2. Arquitectura

### Núcleo corporal único

`nilo_runtime/physiology/needs.py` concentra tasas físicas, límites, sensaciones y proyecciones. `nilo_runtime/physiology/policy.py` concentra duración de descanso/espera, multiplicador de fatiga y umbrales de colapso/recuperación. Las fachadas `survival.py` y `bodily_policy.py` mantienen las importaciones de los consumidores antiguos sin duplicar fórmulas.

El **autocuidado automático** de versiones históricas sigue en la fachada `survival.py` mediante un callback a `motivation.record_maintenance` activado únicamente con `legacy_autocare=True`. En las partidas modernas, ni agua próxima ni alimentos almacenados producen acciones automáticas de comer/beber: Nilo debe ejecutarlas o delegarlas explícitamente. La física no importa ni llama a un LLM.

Los valores corporales conservan escala 0–100, y el contexto perceptivo sigue enviando descripciones cualitativas de sed, hambre y cansancio. `needs_summary` y `perceived_needs` son de **solo lectura**; `ensure_needs` permanece como API explícita de inicialización/migración. Se rechazan intervalos NaN/Inf y reservas invalidas antes de aplicar tasas; no se normaliza silenciosamente un estado corrupto.

### Descanso, espera e inconsciencia

`rest` conserva recuperación basal estimada en **7 puntos/h al aire libre** y **11 puntos/h en la celda inicial de refugio**, menos drenaje de inactividad 0,4/h; son **unidades abstractas de simulación**, no rendimientos biomédicos. `wait`, en modo moderno, permite la evolución de sed, hambre y energía sin recuperación energética. La inactividad sin una acción `wait` conserva la recuperación leve ya modelada; esa distinción se ensaya, no se reinterpreta como un comando.

Se conservan las transiciones involuntarias a energía **≤5** (inconsciencia) y recuperación a energía **≥40**. El reloj consulta `policy.should_collapse`/`can_wake` y nunca solicita a Nilo que elija conscientemente caer o despertar. Una pérdida de conciencia interrumpe la acción pendiente sin producir materiales. `rest_minutes` y `wait_minutes` validan duraciones 1–1440 min; la ruta histórica mantiene sus contratos temporales previamente registrados.

Las reservas de `abrigo` y `seguridad` no se consumen ni regeneran sin fenómenos físicos; ninguna celda cambia mágicamente esas magnitudes.

### Resguardo independiente de nombres

`nilo_runtime/worlds/shelter.py` es el propietario único de `shelter_properties(world,position)` y `sheltered`, consultados por `island_views.survival_conditions` **y** `experiment_log.sheltered`.

- La **celda `h` preexistente** del mapa se reconoce como refugio por un dato topológico explícito: `status=verified`, `source=terrain`. Se conserva el comportamiento anterior y el replay de mundos con ese sitio inicial.
- Toda obra **nueva** o previamente importada, mientras no exista un modelo físico de cubierta, produce `status=no_evaluable`, `sheltered=False`, independientemente de `name`, `purpose`, `category` o un `shelter_condition` heredado. Las etiquetas históricas persisten para consulta, pero no conceden protección. Una propiedad `verified` autodeclarada en el dict de la obra tampoco basta.
- `construction.py` deja de inferir o regenerar `shelter_condition` a partir de la categoría. No se borra el dato antiguo de saves ya existentes.
- El registro de diseños ya no puede acreditar **eficacia de una construcción** solo porque el descanso ocurrió sobre la celda `h`: distinguir la fuente `terrain` de una futura fuente `structures` exige evidencia estructural del motor.

Por falta de ley física de cubierta, la ventaja de descanso de **obras construidas** queda suspendida hasta contar con soporte medible; no se inventa esa ley a partir de una ficha de diseño o una conversación. La categoría `habitaculo` sigue siendo útil como etiqueta organizativa, no como prueba material.

## 3. Pruebas y compatibilidad

**29 pruebas focalizadas** en `tests/test_fisiologia_13.py`: invariancia ante cambio de nombre/categoría de refugio, equivalencia de evaluación del reloj/medición, lectura pura, validación `no_evaluable`, preservación de `h`, fabricación sin cubierta gratuita, proyecciones sin cifras ni mutaciones, sed/hambre/fatiga, diferencias `rest/wait`, cap temporal, autocuidado histórico vs moderno, límites de inconsciencia y valores NaN/Inf.

`tools/auditar_fisiologia_13.py` verifica mediante AST propietarios sin dependencias invertidas, fachadas sin duplicación, consulta de resguardo única y que `construction` no vuelva a fabricar protección desde etiquetas. `tools/auditar_arquitectura.py` registra la nueva capa `physiology` con importaciones permitidas hacia `core` y la propia capa. Se revisaron las pruebas antiguas `test_v0581.py` y `test_v059328.py`: sus expectativas dependían explícitamente de conceder protección por nombre y de vincular un descanso en `h` a una obra. Se actualizan para exigir evidencia física, sin borrar casos históricos ni introducir excepciones especiales para `habitaculo`.

`MANIFIESTO_SHA256.json`, `tools/verificar_paquete_07.py` y la traza real de `laboratorio_motor.py` incorporan `physiology/__init__.py`, `physiology/needs.py`, `physiology/policy.py` y `worlds/shelter.py`. La workflow de validación ejecuta auditoría y tests antes de la suite integral, replay, escenarios físicos y smoke test del ZIP.

**CI final confirmada:** [Validación Nilo #42025565724](https://github.com/mxlzz/Nilo_public/actions/runs/42025565724) **success**, 844 pruebas (843 aprobadas y 1 omitida), 29 focalizadas, auditorías físicas y de arquitectura, escenarios, replay determinista y arranque del ZIP extraído. Huella de replay idéntica entre dos procesos: `9c4d43a5815fb042e06e32789b7dc6606023c3eb0634fe08dd7ad90616dc5c24`. [Compatibilidad histórica pública #42025565421](https://github.com/mxlzz/Nilo_public/actions/runs/42025565421) **success**, seis partidas sintéticas importadas sobre copias. Ambos workflows verificaron el commit `38b325c40d3a0bacd84eb39fec4dcf9444fe594d`. Los cambios de cierre son exclusivamente documentales (`[skip ci]`).

## 4. Límites explícitos y siguientes etapas

- El modelo de abrigo/salud **no incluye** temperatura, viento, lluvias, aislamiento ni riesgo sanitario de agua; por lo tanto no se otorga protección construida hasta implementar y comprobar esa física. Esto responde a la premisa del [issue #75](https://github.com/mxlzz/Nilo_public/issues/75); la resolución queda condicionada a CI final verde.
- **Etapa 14 — Observación del entorno:** consolidar instantáneas de solo lectura, separar datos internos del motor y percepción del agente, revisar la exposición de `shelter_properties` y evidencias.
- **Etapa 18 — Persistencia:** restauración/compatibilidad completa de partidas reales bajo los contratos actuales, sin tocar saves privados.
- **Etapa 23 — Conducta:** probar con proveedores LLM si los estados cualitativos y el descanso voluntario producen mejores decisiones autónomas. Las pruebas físicas **no** demuestran ausencia de bucles.
- **Futuras leyes físicas:** cobertura, aislamiento y ambientes representables requieren un modelo explícito y pruebas de estructuras, sin cambiar resultados retroactivamente por denominación.

**Condición de salida superada:** auditoría integral, pruebas, replay entre procesos, ZIP y seis partidas sintéticas en verde; seguimiento actualizado en master #74, issue #75 y PR #77. **La etapa 13 queda cerrada; etapa 14 · Observación del entorno habilitada.** No publicar ni fusionar 0.7.0 hasta finalizar etapa 24.
