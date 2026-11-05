# Auditoría técnica previa a Nilo 0.6 — 2 de noviembre de 2026

**Estado:** revisión de arquitectura completada, **sin cambios de motor**. **Referencia revisada:** `main`, Nilo **0.5.9.3.35** (PR `referencia privada #124` (`referencia-historica-privada-pull-124`)). Guía de planificación: [FUTUROS_CAMINOS.md](FUTUROS_CAMINOS.md). La prioridad y el alcance de una implementación futura pueden revisarse por evidencia.

## Pregunta y dictamen

**¿Hace falta una nueva versión de preparación antes de 0.5.9.4 y 0.6?**

**Dictamen:** **no se identificó un bloqueo técnico que obligue a publicar otra versión previa a `0.5.9.4`**. El trabajo previo a 0.6 puede cerrarse como **auditoría y diseño de criterios de aceptación**. Recomendar pasar a **0.5.9.4** para capturar una referencia conductual anterior al salto físico y luego comenzar **0.6 por cortes verticales comprobables**, sin convertir las propuestas `0.5.9.3.36` y `.37` en puertas de acceso obligatorias.

Esto **no** significa que 0.6 esté lista para lanzarse ni que toda la física actual sea composicional. Los problemas enumerados abajo deben diseñarse y corregirse **durante las primeras entregas de 0.6**, o aislarse de modo verificable, antes de declarar resueltos sus objetivos. No fijar `0.5.9.3.40` por continuidad numérica.

## Método y límites de evidencia

1. Lectura estática de `main`: `environments.py`, `world.py`, `capabilities.py`, `vessels.py`, `action_results.py`, `nilo.py`, `brain.py`, `physics.py`, `mechanics.py`, `construction.py`, `catalogo.py`, `episodic_memory.py`, `inventions.py`, `archive.py`, `experiment_log.py`, `laboratory.py`, `goal_evidence.py` y contratos de operación; contraste con issues [#8](https://github.com/mxlzz/Nilo_public/issues/8), [#30](https://github.com/mxlzz/Nilo_public/issues/30), [#4](https://github.com/mxlzz/Nilo_public/issues/4), [#5](https://github.com/mxlzz/Nilo_public/issues/5), [#20](https://github.com/mxlzz/Nilo_public/issues/20), [#32](https://github.com/mxlzz/Nilo_public/issues/32) y [#3](https://github.com/mxlzz/Nilo_public/issues/3).
2. Inspección **solo lectura** de dos bases de partidas anteriores disponibles al observador; no se modificaron, migraron ni ejecutaron. La procedencia exacta fue comprobada en `engine_sessions`. Los resultados de sus partidas son observaciones, **no** ensayos controlados.
3. La CI de **0.5.9.3.35** había pasado al publicar su PR y release. **Esta auditoría no ejecuta un run nuevo con LLM**, ni una prueba funcional nueva de física. Las consecuencias previstas de modificaciones arquitectónicas siguen siendo hipótesis hasta su implementación y evaluación.

### Contraste reproducible con los runs disponibles

| Dato | `nilo_mundo(20261101-234332).sqlite3` | `nilo_mundo(20261102-004605).sqlite3` |
| --- | ---: | ---: |
| Versiones registradas en `engine_sessions` | 0.5.9.3.26 → .27 → .29 | 0.5.9.3.30 → .31 → .32 |
| Tiempo total simulado | 2,88 días | 1,45 días |
| Mediciones presentes en `history` de SQLite | 204 | 123 |
| Mediciones en `person.measurements` | 180 | 123 |
| Mediciones archivadas fuera de la memoria activa | **24** | 0 |
| Mediciones `explore` en la ventana activa | 78 | 98 |
| Investigaciones con estado `abierta` | 15 | 6 |

**Verificación directa:** en el primer run, las tres mediciones más antiguas archivadas ya no figuran en `person.measurements`; por ejemplo `med-46b91c256315`. El código actual `experiment_log.measure` conserva **180** muestras activas y `laboratory.compare` busca IDs exclusivamente en esa lista. Por tanto, un ensayo puede **persistir en SQLite** y quedar **fuera del alcance operativo de `compare`**; no se atribuye pérdida física de datos. `archive.History.get(category,item_id)` permite consulta puntual, pero `compare` todavía no la utiliza.

**Límite de interpretación:** estos runs se generaron **antes** de los cambios perceptivos de .34.1 y de exploración de .35. Los 78/98 registros de `explore` **no demuestran** cómo se comporta Nilo con exploración dirigida, ni prueban por sí solos bucles patológicos o una mejora causal de motivación.

## Hallazgos y alcance recomendado

### A. Arquitectura de entorno y extensiones: base presente, integración incompleta

- **Hecho:** `environments.Environment` expone interfaz de percepción, recorrido, validación y acciones; `IslandEnvironment` la implementa. El registro habilitado contiene **solo `isla_v1`**. No se ha probado un segundo entorno físico y todavía existen dependencias directas de topología, cueva, `W/H` y símbolos de la isla en `brain.context_for` y `world.py`.
- **Hecho:** `capabilities.Capability` y `dispatch` permiten registrar métodos bajo `interact`; el primer módulo es **`contenidos` v1.0.0** (`vessels.py`). Declara versión por mundo y bloquea desajustes. **No hay un segundo módulo independiente en el registro**.
- **Límite adicional:** la descripción de métodos `ACTION_GUIDE['interact']` sigue enumerando manualmente los métodos del módulo de recipientes. El mecanismo de ejecución es ampliable, pero la **exposición de capacidades al LLM aún no deriva íntegramente del registro**.
- **Criterio para el primer corte 0.6:** añadir un **segundo módulo físico independiente**, con validación de precondiciones, efectos y métricas; comprobar que se registra, ejecuta, comunica, versiona y persiste **sin retocar `world.execute_action`, la lógica de despacho de `nilo.py` ni una lista de métodos escrita a mano en `brain.py` o el contrato de `interact`**. Si se requieren adaptadores centrales, declararlos como refactorización inicial única y medir que la siguiente extensión no los repita. Compatibilidad con partidas antiguas obligatoria.

### B. Física composicional: hay modelos útiles, pero también efectos por clases/nombres

- **Hecho:** `physics.body_physics` y las evaluaciones de contención/flotación combinan material, tamaño, forma y propiedades. `mechanics` modela conexiones, carga y transmisión en un conjunto limitado. `construction` permite piezas, reformas, daño/recuperación.
- **Límite concreto:** `world.infer_form` puede **deducir la forma a partir del nombre**, `item_effects` concede operaciones según el campo `form`, `world.classify_structure` asigna `habitaculo` a partir del nombre/propósito y `construction.recompute` usa `category=='habitaculo'` para determinar cobertura. Hay usos físicos correctamente medidos, pero **no se garantiza todavía invariancia general ante renombrado**.
- **Límite de datos:** `physics.properties` consulta primero el catálogo global `MATERIAL_PHYSICS`; para materiales base, los valores `density/permeability` de una instancia en `person.materials` no tienen precedencia sobre el catálogo. Esto **importa si 0.6 pretende cambiar propiedades por instancia** o introducir muestras distintas: el cálculo físico debe obtener propiedades de una fuente definida y persistente, no de prioridades accidentales. No se declara un fallo observado en los dos runs.
- **Decisión:** diseñar esto **dentro de 0.6**, partiendo de una capacidad medible concreta. Tests exigidos: dos objetos con estado físico equivalente y nombres distintos producen el mismo resultado; una variación física representada cambia el resultado solo cuando una ley lo justifica; modificar un objeto preserva versiones/evidencias anteriores. No intentar simular todas las formas ni todas las leyes simultáneamente. [#8](https://github.com/mxlzz/Nilo_public/issues/8), [#30](https://github.com/mxlzz/Nilo_public/issues/30).

### C. Percepción e identificación: faltan estados epistémicos estructurados

- **Hecho:** `brain.context_for` usa `world_view`, que entrega `TERRAINS` como etiquetas conocidas; `world.inspect_target` informa directamente la identidad de un terreno revelado; recolección e inventario usan identificadores del catálogo. `experiment` almacena resultados por clave `material|método`, con una base real de comprobación, pero **no una separación sistemática de desconocido → observado → identificado → propiedad probada**.
- **Consecuencia de diseño:** el descubrimiento de materiales o capacidades nuevas no podría presentarse fielmente como aprendizaje gradual si se filtra la identidad del motor antes de la inspección. No se deduce de ello que Nilo A carezca de conocimientos conceptuales modernos.
- **Decisión:** definir en la **primera fase de 0.6** una identidad estable de ejemplar/tipo y evidencias de identificación; distinguir cualidades perceptibles, propiedades reales y mediciones aprendidas. Mantener compatibilidad perceptiva de partidas antiguas y no revelar tipos futuros retrospectivamente. No obliga a un parche previo a la evaluación 0.5.9.4. [#4](https://github.com/mxlzz/Nilo_public/issues/4), [#5](https://github.com/mxlzz/Nilo_public/issues/5).

### D. Evidencia tipada: transición parcial que necesita completar los nuevos caminos

- **Hecho:** `ActionResult` tiene `status`, `success`, `facts` y `physical` estructurados. `IslandEnvironment.perform_result` envuelve la operación legada; `ActionResult.as_legacy` mantiene compatibilidad con las antiguas tuplas. Navegación, diseño y ciertas acciones del coordinador siguen entrando por rutas específicas.
- **Límite verificable:** `goal_evidence.check_goal` todavía consulta fragmentos de `verified_facts` para algunos requisitos (`recipiente`, `explore`, `agua`), aun cuando se conserven IDs y mediciones. Cambiar redacción o sumar nuevas capacidades requerirá criterios de evidencia basados en identidad/variables físicas, no en frases del motor.
- **Decisión:** hacer que **cada capacidad añadida en 0.6** emita efectos tipados verificables y que predicción, laboratorio y cierre del objetivo pertinente consuman esas variables con procedencia. Migrar consumidores legados gradualmente y conservar la lectura de historiales antiguos. No condicionar toda la versión 0.6 a reemplazar de golpe cada operación histórica. [#8](https://github.com/mxlzz/Nilo_public/issues/8), C.2 del [roadmap histórico](ROADMAP_0571.md).

### E. Memoria y evidencia antigua: limitación real, pero FTS5 no es requisito inmediato

- **Hecho:** `episodic_memory.recall_relevant` revisa **todo `person.life_history`** en cada selección; es costoso potencialmente en partidas largas, sin medición de coste a escala de meses. `nilo.write` persiste el estado completo en el snapshot y sincroniza el archivo histórico.
- **Hecho contrastado:** al menos una partida tiene 24 mediciones archivadas inaccesibles a `compare`; la solución funcional mínima es **consulta por ID en SQLite**, usando `History.get`/un repositorio de evidencias y pruebas de versiones/IDs, sin búsqueda textual plena. `record_links` ya indexa relaciones explícitas.
- **Decisión:** documentar la recuperación puntual como **necesaria para experimentación longitudinal de 0.6**, pero **no crear automáticamente .36** ni instalar FTS5 antes de tener un caso que requiera búsqueda léxica. La consolidación de memoria bajo demanda y el perfilado de rendimiento pueden quedar para después, con una intervención más temprana si un run reproducible lo exige. [#20](https://github.com/mxlzz/Nilo_public/issues/20), [#32](https://github.com/mxlzz/Nilo_public/issues/32), [#31](https://github.com/mxlzz/Nilo_public/issues/31).

### F. Evaluación de autonomía: no confundir correcciones de código con efectos conductuales

- **Hecho:** el motor ya distingue decisiones del modelo, algunas rutinas, eventos físicos y mediciones con procedencia; la .34.1 cambió percepción corporal y la .35 añadió exploración orientada. No hay aquí evidencia longitudinal posterior a esos cambios.
- **Decisión:** **0.5.9.4 (#3)** debe registrar estado inicial, versión exacta, proveedor/modelo, semilla, eventos, decisiones y uso de recursos; medir repeticiones, continuidad de investigaciones, resultados verificables, ingestas/descansos y exploraciones por intención, sin declarar que «más acciones» sea necesariamente mejor. Comparar muestras realmente homologables, reconociendo que un LLM externo no se hace determinista por fijar la semilla.
- **No se imponen nuevos objetivos a Nilo.** La observación de autonomía no requiere más llamadas LLM automáticas por defecto.

## Orden de implementación recomendado

| Momento | Alcance delimitado | Condición para avanzar |
| --- | --- | --- |
| **Ahora** | **Cerrar auditoría** y conservar las dos partidas como evidencia histórica previa a .35; no cambiar motor ni inventar versión de preparación. | Informe revisado y enlazado en la guía e issues. |
| **Siguiente entrega: 0.5.9.4** | Instrumentar/evaluar corridas comparables; identificar qué cambios cognitivos realmente produjeron una diferencia. | Protocolo y límites documentados, métricas reproducibles, ningún resultado atribuido causalmente sin control adecuado. |
| **0.6, corte 1** | Probar segundo módulo independiente; contratos físicos/visibilidad de operaciones y primera separación de percepción e identidad. | Una capacidad nueva se instala y comunica sin reescribir lógica central; evidencia tipada trazable; los objetos antiguos siguen funcionando. |
| **0.6, corte 2** | Reemplazar al menos un caso de forma/función inferidas por nombre con propiedades del objeto, geometría y componentes; ensayos de modificación con variantes. | Invariancia por nombre, diferencias físicas justificadas y resultados medidos; no acreditar una propiedad solo por fabricarla. |
| **0.6, según necesidad** | Resolver consultas de mediciones antiguas por ID y reducir dependencias de texto en validación experimental; mejorar memoria/perfilado cuando exista evidencia. | Ensayo archivado fuera de las últimas 180 muestras recuperable por ID auténtico, sin incorporar conocimiento falso al agente. |

Estos cortes son **propuestas de diseño internas a 0.6**, no versiones o PRs aprobados automáticamente. La secuencia puede cambiar si aparecen problemas reales.

## Riesgos y precauciones explícitos

- Reestructurar estados epistémicos sin migración puede cambiar lo que Nilo «sabe» de una partida antigua: definir semántica de importación, no reinterpretar retroactivamente pruebas.
- La ampliación modular no permite instalar módulos creados por el personaje sin revisión humana; el registro debe seguir cerrado y versionado.
- Los dos runs inspeccionados prueban disponibilidad de evidencia y distribución de acciones de **versiones previas**, pero no la evolución conductual de 0.5.9.3.35.
- Una guía o una prueba automática no sustituye la evaluación física real de una nueva capacidad.
