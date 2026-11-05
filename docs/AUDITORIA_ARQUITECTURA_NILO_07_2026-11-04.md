# Nilo 0.6.4 — auditoría integral de arquitectura y propuesta de núcleo 0.7

**Fecha:** 4 de noviembre de 2026. **Código revisado:** main en commit `e7229ebf9cf6a9f45a44a4ca184c12795535c843`. **Estado:** diagnóstico y diseño; **no se modificó ninguna ley, prompt ni partida.** Issue principal [#151](https://github.com/mxlzz/Nilo/issues/151).

## 1. Alcance, metodología y límites

- Se inventariaron los 63 módulos y scripts Python de producción/herramientas fuera de `tests/` (796.824 bytes de fuente), los HTML principales y los tres catálogos JSON; se analizaron imports, funciones, clases y acoplamientos. Se revisaron en detalle las rutas críticas de `Simulation`, `world.execute_action`, `IslandPlanner`, acción tipada, contexto LLM, persistencia, respaldo, UI y replay.
- Se cotejaron `catalog/*.json`, `docs/AUDITORIA_INTEGRAL_MOTOR_2026-11-03.md`, el roadmap, los issues de física y cognición y los tests. El último CI de `main` ([ejecución 41839578058](https://github.com/mxlzz/Nilo/actions/runs/41839578058)) pasó **646 tests con 1 omitido**, más los pasos deterministas de escenarios/replay.
- **Distinción:** la auditoría es estructural/estática con apoyo de pruebas y runs previos; no es una inspección formal de todas las combinaciones de cada instrucción ni una nueva corrida de 13 días con LLM real. Se separa *defecto reproducido*, *defecto observable en la implementación*, *riesgo de arquitectura* y *diseño pendiente*.
- Se revisó el programa instalable, sus herramientas y documentación. El informe propone una migración controlada en lugar de sustituir 0.6.4 en un único commit.

## 2. Qué está bien y debe conservarse

- El agente propone operaciones, pero las consecuencias físicas se evalúan en Python, sin conceder capacidades solo por narración.
- Ya existe una frontera parcial por `Environment` y un registro de capacidades `interact`; los catálogos de materiales/terreno/objetos tienen validadores declarativos.
- El resultado `ActionResult`, las mediciones, los diagnósticos y los vínculos entre registros permiten auditar fallos; proyectos, hipótesis y conclusiones tienen controles de evidencia.
- SQLite usa WAL, snapshot y archivo relacional; las copias de partidas utilizan la API de backup de SQLite, evitando copiar a ciegas una base activa.
- Hay aislamiento por SQLite temporal, 68 escenarios y checkpoints antes de decisiones/acciones. Las pruebas de regresión constituyen una base útil, aunque parcial.
- Las decisiones de autonomía son parte del contrato del proyecto: el motor no debe asignar misiones ni convertir la memoria recuperada en instrucciones. Un nuevo núcleo debe preservar esta libertad.

## 3. Problemas confirmados y prioridades

| ID | Prioridad | Hallazgo y evidencia | Consecuencia / corrección en 0.7 |
| --- | --- | --- | --- |
| A01 | **Alta, arquitectónica** | `nilo.py` (~2019 líneas) importa más de 30 módulos y agrupa `Simulation`, reloj, proyectos, persistencia, servidor HTTP y estado de UI. | Separar bucle de simulación, caso de uso de deliberación, gestión de proyectos, capa web e infraestructura, con interfaces explícitas. |
| A02 | **Alta, arquitectónica** | `world.py` (~1158 líneas) concentra topología, recursos, búsqueda de rutas, desplazamiento, excavación, inspección y `execute_action` con ramificación por operación. | Extraer navegación y recursos por dominio; un único registro tipado de acciones reemplaza el despacho repartido. |
| A03 | **Alta, defecto reproducido** | Tiempo estimado, reloj y `ActionResult.duration_minutes` no representan siempre la misma magnitud. [#141](https://github.com/mxlzz/Nilo/issues/141). | Contrato temporal por fase y medición única del tiempo realmente avanzado. |
| A04 | **Alta, defecto reproducido** | `gather` remoto acredita extracción inmediatamente al terminar viaje, sin consumir su tiempo propio: 9 vs 22 minutos en ensayo anterior. [#142](https://github.com/mxlzz/Nilo/issues/142). | Acción gradual con viaje → trabajo → material transferido; interrupciones coherentes. |
| A05 | **Alta, determinismo** | IDs de obras/objetos dependen de `random.getrandbits` global o `uuid4`; al cargar partida `Simulation.__init__` reinicia `self.rng` desde `9821 + int(clock_minutes)` si no se pasa semilla, en vez de recuperar su estado exacto. [#143](https://github.com/mxlzz/Nilo/issues/143). | RNG persistido por sesión/mundo, fábrica de identidades, RNG externo controlado, comparaciones por IDs estables. El efecto de reiniciar una partida real requiere prueba específica. |
| A06 | **Alta, causalidad física** | `world.classify_structure(name,purpose)` asigna `habitaculo` por texto; `construction.ensure_object` deriva `shelter_condition` de categoría, y `island_views.survival_conditions` usa la categoría para condición de refugio. [#152](https://github.com/mxlzz/Nilo/issues/152). | Separar etiqueta narrativa de propiedades físicas, ensayo y protección representada. Prueba de invariancia ante renombrado; mantener `no_evaluable` cuando falte modelo. |
| A07 | **Alta, lectura/escritura** | `island_views.map_snapshot()` invoca `world.enrich_structure()`, que asigna `category/status/description` con `setdefault`; leer la vista puede mutar entidades. [#153](https://github.com/mxlzz/Nilo/issues/153). | Proyecciones puras; normalización/migración explícita en un único punto transaccional. |
| A08 | **Alta, contrato de acciones** | `action_contracts.ACTION_GUIDE` describe operaciones en texto; `brain.normalize_decision` convierte el JSON; `IslandPlanner` valida; `nilo.ACTION_DURATIONS` asigna tiempos; `world.execute_action` y `nilo._tick_slice` ejecutan; `ActionResult` adapta una 4-tupla histórica. | Un solo contrato estructurado por acción: campos, unidades, prerequisitos, fases, resultado, predicción y documentación generada. Conservar compatibilidad de entrada. |
| A09 | **Alta, modelo de estado** | Diccionarios mutables `self.s`/`person`/`world` se pasan por múltiples capas. Migraciones y consumo de código emplean numerosos `setdefault`, campos `_origin`, `_last_*` y marcadores de versiones dentro de estado operacional. | Esquema central tipado y validado, comandos que producen efectos; estados de ejecución y eventos de dominio separados de metadatos de UI/archivo. |
| A10 | **Media-alta, historial** | `Simulation.migrate()` adapta sucesivamente mapa, proyectos, notas, herramientas y tareas; `s['version']=5` no distingue evolución de esquema de publicación 0.6.4. | Versiones explícitas `engine_version`, `save_schema_version`, `action_schema_version`; migraciones ordenadas, puras, con fixture de cada generación de partida. |
| A11 | **Media-alta, acoplamiento cognitivo** | `brain.py` (~697 líneas) mezcla un prompt extenso, datos del mundo, compresión/contexto, API y normalización; `cognitive_projection.project_context` importa localmente `_cognitive_needs_context` desde `brain`, que a su vez importa el proyector. | Separar construcción de observaciones, proyección consciente, memoria recuperada, política de presupuesto, formato del mensaje y gateway LLM; resolver dependencia circular diferida. |
| A12 | **Media-alta, divergencia entre LLM** | `brain.SYSTEM` y `prompt_budget.GROQ_SYSTEM` son instrucciones diferentes; `action_contracts.ACTION_GUIDE` y `prompt_budget.SHORT_OPERATIONS` duplican descripciones. | Núcleo conceptual único; descripciones completas/compactas generadas de un registro de acciones, sin divergencia silenciosa. [#64](https://github.com/mxlzz/Nilo/issues/64), [#135](https://github.com/mxlzz/Nilo/issues/135). |
| A13 | **Media-alta, persistencia/escalado** | Cada `Simulation.write()` llama a `History.sync` sobre todas las colecciones en memoria y serializa el snapshot completo; cada checkpoint histórico comprime otro estado entero. La carga depende del crecimiento de mundo/experiencias, sin retención documentada de checkpoints. | Escrituras incrementales y unidades de trabajo, índices/consultas explícitas, benchmarks de tamaño/tiempo y política revisable para checkpoints sin perder evidencia. [#65](https://github.com/mxlzz/Nilo/issues/65). |
| A14 | **Media-alta, replay** | `historical_lab.replay` reproduce desde snapshot y RNG, pero no restituye todo el archivo relacional ni el contexto externo; utiliza el motor instalado y estado aleatorio global temporal. | Reejecución sobre snapshot coherente del conjunto de datos + motor/versiones registradas; no declarar igualdad bit a bit sin evidencia. |
| A15 | **Media-alta, proyectos** | Apertura/pausa/cierre, evidencia, agenda, bloqueo de estrategias y avance de proyecto se reparten entre `nilo.plan_ready`, `project_lifecycle`, `goal_evidence`, `goals`, `project_progress`, `strategy_review` y otros. Parte del criterio depende de palabras del título. | Modelar `Project` con estado/transiciones y criterios declarados por Nilo, con evidencia enlazada por ID y `unknown/no_evaluable` separados de fallo. Sin objetivos impuestos por motor. |
| A16 | **Media, escalabilidad espacial** | `world.pathfind(...known_only=True)` consulta `revealed` como lista dentro de un BFS; `choose_frontier()` calcula rutas para múltiples fronteras con búsquedas reiteradas. | Índice espacial en memoria con sets/mapas y una exploración BFS de alcanzables compartida cuando procede; conservar orden determinista de descubrimiento. |
| A17 | **Media, duplicación de configuración** | `catalogo.py` valida `PASSABLE` desde `catalog/terrenos.json`, pero `world.py` reasigna luego `PASSABLE` al literal `set('.,Tocrs=h:vse')`. Coinciden actualmente, pero una edición del catálogo podría no tener efecto esperado. | Única fuente de terreno transitable. Tests de consistencia con materiales, renders y precondiciones. |
| A18 | **Media, laboratorio** | `laboratorio_motor.MotorLab._execute` retiene el viejo ejecutor de acciones, aparte del banco que usa `Simulation.plan_ready/tick`. | Un solo ejecutor del motor real; laboratorio como adaptador de escenarios, variantes y observación. Retirar legado solo tras asegurar cobertura. |
| A19 | **Media, QA** | CI pasa 646 tests (uno omitido), escenarios y replay entre procesos; no incluye informe de cobertura por rama, lint/tipado continuo, propiedad metamórfica, pruebas completas de interfaz ni corridas autónomas repetidas LLM. | Añadir invariantes/diferenciales, cobertura, tests de migración SQLite, carga larga y protocolo de LLM comparable. No confundir 68 categorías esperadas con verificación de todas las leyes. |
| A20 | **Baja, síntoma de mantenimiento** | `construction.ensure_object(obj)` usa `obj.setdefault('components',_components(...))`; la expresión `_components` se evalúa aun si el objeto ya tiene piezas, generando UUID sin utilizarlos. | Inicialización condicional explícita y sin efectos secundarios; revisión automatizada de defaults costosos o mutables. |

### A21 — Interfaz principal monolítica y duplicación de UI (prioridad media-alta)

La auditoría de archivos no Python detectó que `interfaz.html` ocupa **175.412 bytes** (aprox. 2.034 líneas) e integra **un bloque CSS y uno JavaScript**, más HTML, con numerosos renderizadores y 27 atributos `onclick`. Las tres interfaces de laboratorio son otros HTML completos con scripts y estilos propios: `laboratorio_escenarios.html` (~35,6 KB), `laboratorio_motor.html` (~29 KB) y `laboratorio_historico.html` (~15,9 KB). No se usa compilador web ni módulos JS organizados por responsabilidad.

**Hallazgo estructural:** presentación, estado del navegador, HTTP, navegación de registros, formateo de mediciones y paneles de ayuda conviven dentro de un único archivo. Los laboratorios mantienen cada uno su presentación y manejo de API. No prueba un bug de render actual, pero dificulta pruebas DOM, reutilización y cambios pequeños.

**Propuesta 0.7:** separar HTML/estilos, `api-client.js`, `app-state.js`, renderizadores por sección y componentes reutilizables para laboratorio; producir un paquete estático ejecutable offline sin dependencias pesadas. Mantener las rutas y apariencia funcional de la UI actual. Agregar tests E2E de navegación, formularios, backups/restore y consistencia de datos visibles. No migrar a un framework por costumbre ni mezclar el rediseño visual con la reescritura física.
## 4. Revisión de la división de archivos (inventario de responsabilidades)

### Núcleo y orquestación

- **Hoy:** `nilo.py`, `timing.py`, `action_contracts.py`, `action_results.py`, `agent.py`, `scenarios.py`, `environments.py`, `island_planning.py`.
- **Propuesta:** mantener un `engine` pequeño responsable de reloj/colas y de dirigir comandos; extraer gestión de proyectos, servidor HTTP y migración. El contrato de acción vive en `core/actions`; `environments.py` solo es el adaptador del mundo, no importa `brain` ni decide modelos.

### Mundo, navegación y física

- **Hoy:** `world.py`, `catalogo.py`, `island_views.py`, `physics.py`, `construction.py`, `mechanics.py`, `capabilities.py`, `vessels.py`, `structural_loads.py`, `phenomena.py`, `physical_links.py`, `survival.py`, `bodily_policy.py`, `intervention.py`.
- **Propuesta:** separar datos del mapa y generación; navegación/rutas; depósitos y recolección; objetos/componentes; leyes de materiales; necesidades; resultados de capacidades. No fusionar `vessels` con `structural_loads`: representan fenómenos diferentes bajo un contrato común. La percepción del entorno pertenece a una interfaz de observación pura.

### Cognición, memoria, proyectos

- **Hoy:** `brain.py`, `providers.py`, `prompt_budget.py`, `cognitive_projection.py`, `cognition.py`, `episodic_memory.py`, `habits.py`, `behavior.py`, `motivation.py`, `strategy_review.py`, `agenda.py`, `goals.py`, `goal_evidence.py`, `project_lifecycle.py`, `project_progress.py`, `research_cycle.py`, `inventions.py`, `experiment_log.py`, `laboratory.py`.
- **Propuesta:** agrupar por responsabilidades estables: `llm_gateway`/`prompts`, `perception`/`memory`, `plans`/`projects`, `scheduler`/`habits`, `research`/`evidence`. `laboratory.py` mide experimentos **dentro del mundo**, distinto del laboratorio de desarrollador. Evitar el exceso de microarchivos que necesitan importarse unos a otros para una operación simple.

### Archivo, diagnósticos y presentación

- **Hoy:** `archive.py`, `record_links.py`, `diagnostics.py`, `diagnostic_guidance.py`, `diagnostic_support.py`, `observer.py`, `review_store.py`, `run_history.py`, `interface_prefs.py`.
- **Propuesta:** `persistence` (SQLite, migraciones, historial, backlinks, checkpoints), `audit` (invariantes, resultados, diagnósticos), `observer` (resumen y estado visible); las preferencias de interfaz no deberían residir en el estado físico del agente.

### Herramientas y operación

- **Hoy:** `laboratorio_motor.py`, `laboratorio_casos.py`, `laboratorio_contexto.py`, `historical_lab.py`, `auditar_contexto_llm.py`, `evaluar_corridas.py`, `reproducir.py`, `validar_escenarios.py`, `gestionar_partidas.py`, `migrar.py`, `primer_inicio.py`, `empaquetar_version.py`, `exportar_historial.py`.
- **Propuesta:** distribuir `lab/` (escenarios, replay, contextos, diferencias), `tools/` (comandos de importación/exportación/paquete), `web/` (API y HTML/JS) sin duplicar dominio. Configuraciones y backup/restore pendientes en [#146](https://github.com/mxlzz/Nilo/issues/146)–[#149](https://github.com/mxlzz/Nilo/issues/149).

## 5. Propuesta de estructura de Nilo 0.7

```text
nilo/
  core/
    engine.py              # ticks, estados de acción, interrupciones
    model.py               # GameState / ActorState / eventos
    actions.py             # registro de contratos y despacho único
    time.py                # tiempo simulado y duración por fase
    identity.py            # RNG persistido, IDs estables
  worlds/
    registry.py            # contratos de entornos
    island/
      generation.py        # mapa y depósitos iniciales
      navigation.py        # rutas, frontera, cambios de nivel
      resources.py         # gather/forage y conservación
      perception.py        # observaciones del entorno sin mutación
  physics/
    materials.py           # datos y propiedades
    objects.py             # objetos, geometría, componentes
    construction.py        # build/craft/modify/assemble
    interactions.py        # capacidades, recipientes, cargas
    bodily.py              # necesidades y descanso
  agent/
    planning.py            # planes del personaje
    projects.py            # transiciones y evidencias de cierre
    memory.py              # memoria y recuperación bajo demanda
    habits.py              # agenda y delegaciones voluntarias
    research.py            # ensayos, hipótesis, comparaciones
  cognition/
    observation.py         # información que puede conocer Nilo
    prompts.py             # identidad y contratos estructurados
    projection.py          # filtrado/budget del contexto
    decision.py            # parseo y validación de salida LLM
    providers.py           # Gemini/Groq/compatibles; sin física
  storage/
    sqlite.py              # unidad transaccional y repositorios
    migrations.py          # versiones separadas de datos
    history.py             # log, índices, relaciones
    checkpoints.py         # snapshots de replay
  app/
    server.py              # API local y servidor, sin lógica física
    views/                 # interfaz y observatorio
  lab/
    scenarios.py           # fixtures y escenarios reales
    replay.py              # reproducción y comparación
    profiles.py            # propuestas de configuración aislada
  compat/
    import_06.py           # migración desde .6 y casos históricos
tools/                    # scripts de empaquetado, respaldo y QA
tests/                    # unitarios, integración, propiedades y migración
```

Esta es una propuesta de **paquetes y propietarios de reglas**, no un compromiso de generar exactamente esos archivos. Debe ajustarse a dependencias reales; un módulo pequeño no es un problema por ser pequeño, sino si carece de límites propios y solo dispersa el flujo.

### Contrato de ejecución nuevo (invariantes)

1. **Entrada:** la salida LLM representa una intención y pasa por un único parseador/versionador de acciones. Un nombre no concede resultados.
2. **Planificación:** se comprueban requisitos y se preparan acciones sin modificar física. Las acciones dependientes de resultados previos se revalidan justo al ejecutarse.
3. **Ejecución:** una acción tiene fases con duración y resultado independientes (`preparar`, `viajar`, `trabajar`, `acreditar`). El reloj y los efectos se aplican juntos; un bloqueo no acredita resultados futuros.
4. **Evidencia:** emitir `ActionResult` y eventos estructurados con duración planeada/transcurrida, recursos, posición, medidas, motivos de fallo y origen del paso.
5. **Aprendizaje:** experiencia/proyecto/agenda solo consumen evidencias y observaciones autorizadas; no cambian la realidad física ni inventan objetivos.
6. **Observación:** vistas de usuario y contexto LLM son proyecciones **sin efectos secundarios** de la misma partida; cada cual recibe únicamente lo autorizado.
7. **Persistencia:** guardar eventos y estado coherente en una transacción versionada; checkpoint completo ocasional y replays con manifest de motor+RNG+configuración.

## 6. Migración: orden propuesto para evitar otra cadena de parches

| Etapa | Entrega técnica | Puerta de salida verificable |
| --- | --- | --- |
| 0. Congelar referencia | Código y ZIP 0.6.4, fixtures SQLite viejos y nuevos, hashes de payload/escenarios y métricas. | Línea base documentada, backup legible y rollback a 0.6.4. |
| 1. Estado, eventos, RNG, tiempos | Definir esquemas, reloj y result contract; corregir #141/#142/#143 con pruebas independientes. | Paridad del resto de operaciones; desviaciones físicas nuevas documentadas; reinicio determinista. |
| 2. Separar motor de mundo | `Simulation` reduce su tarea a coordinar; acciones e interacciones pasan a adaptadores/handlers. | 68 escenarios comparados entre motores con diffs por campo y sin duplicación de ejecutores. |
| 3. Física y nombres | Propiedades/identidades de objetos, materiales, estructuras, supervivencia y navegación en paquetes aislados. | Invariancia de nombres #152, conservación material, pureza de lectura #153 y pruebas por semilla. |
| 4. Cognición autónoma | Proyección/contexto LLM, prompt común, memoria, proyectos, agenda y validación de respuesta LLM separados del mundo. | Igual solicitud con baseline cuando se espera; cambios de prompt intencionados y medidos; sin objetivos externos. |
| 5. Persistencia, API, laboratorio | Migraciones estructuradas, archivo incremental, servidor separado y laboratorio con perfiles/restore. | Importación de partidas históricas, WAL/backup/replay, recuperación ante fallos; mismas acciones desde juego y laboratorio. |
| 6. Validación de release | Suite completa, tests nuevos de invariantes, benchmark, corridas reales comparables con proveedores. | Publicar 0.7 solo con migración probada y lista explícita de cambios de comportamiento. |

El orden es revisable; **no mezclar simultáneamente una corrección física, un rediseño de memoria y una novedad ambiental** si se pretende atribuir las diferencias observadas.

## 7. Pruebas indispensables para 0.7

- **Golden master:** para cada escenario existente, comparar 0.6.4 vs núcleo nuevo a partir de mundo, actor y decisión idénticos; normalizar campos no físicos irrelevantes (IDs temporales) solo de forma documentada.
- **Invariantes:** materiales conservados en fabricar, depositar, transferir, desarmar; recursos no negativos; coordenadas, niveles y rutas físicamente válidas; tiempo real/trabajo/navegación consistentes; ningún éxito antes de terminar la fase correspondiente.
- **Metamórficas:** renombrar una obra o herramienta sin cambiar materiales, geometría ni componentes no debe cambiar la física; leer mapa/estado varias veces no muta la partida; reinicio durante acción debe continuar desde el mismo estado RNG.
- **Migraciones:** 0.5.x, 0.6.0, 0.6.4 y backups actuales; historial/checkpoints/vínculos y proyectos intactos. Mantener copia anterior recuperable.
- **Cognitivas:** JSON de decisiones validado, independencia de intereses, memoria no invasiva, equivalencia del núcleo del prompt en Gemini/Groq; inspección de contextos **exactos** para cada proveedor.
- **Largas:** múltiples semillas, estados con muchos proyectos/registros y crecimiento del SQLite a semanas/meses; medir bytes por acción y duración de snapshot/sync/replay.
- **LLM reales:** tras los tests deterministas, usar runs comparables con modelos/semillas/estados/presupuestos documentados. Una mayor cantidad de acciones no demuestra mejor autonomía.
- **Desarrollo:** incorporar lint/tipado gradual, cobertura de ramas en subsistemas críticos y tests de la interfaz en un navegador real; el CI actual usa principalmente `unittest` y comprobaciones de sintaxis JS.

## 8. Riesgos, alcance y decisión de versión

- **Mayor riesgo:** diferencias semánticas introducidas inadvertidamente al migrar reglas históricas. Se necesita una matriz de comportamientos deliberadamente preservados, corregidos o retirados; no basta que todos los tests actuales den OK.
- **Segundo riesgo:** incompatibilidad con partidas largas y enlaces a objetos/mediciones; el plan debe mantener IDs originales y registrar versión de esquema.
- **Tercer riesgo:** sobreingeniería. No rehacer el motor como un framework general de simulación antes de tener un segundo mundo. Usar interfaces mínimas, tipos explícitos y paquetes con responsabilidades claras.
- **Cuarto riesgo:** modificar al mismo tiempo los prompts y las leyes. El núcleo conceptual del personaje debe quedar estable durante la migración física para evaluar continuidad.
- **Nomenclatura:** el issue [#22](https://github.com/mxlzz/Nilo/issues/22) proponía *0.7 termodinámica*, pero la numeración no era un compromiso fijo. Se propone reservar **0.7 para la base modular** y mover termodinámica a una versión ulterior **solo después de acordarlo**, no reasignarla unilateralmente.

## 9. Qué NO implica esta auditoría

- No es autorización para sobrescribir la instalación vigente, reescribir el prompt, alterar los objetivos del personaje o convertir Nilo en un simulador de ingeniería real.
- No representa un segundo motor en paralelo mantenido indefinidamente. El núcleo nuevo debe reemplazar progresivamente al actual con una ruta de salida para el código legado.
- No afirma que los 646 tests actuales cubran todas las situaciones ni que los problemas de creatividad sean únicamente fallos del motor. Esas hipótesis requieren observación LLM real.
- No asigna una fecha de lanzamiento. El resultado deseable es una base comprobable y fácil de extender, no un cambio de número de versión por sí mismo.

## Issues relacionados

Arquitectura base [#151](https://github.com/mxlzz/Nilo/issues/151); nombre/física [#152](https://github.com/mxlzz/Nilo/issues/152); lectura con efectos [#153](https://github.com/mxlzz/Nilo/issues/153); tiempos [#141](https://github.com/mxlzz/Nilo/issues/141)/[#142](https://github.com/mxlzz/Nilo/issues/142); RNG [#143](https://github.com/mxlzz/Nilo/issues/143); física composicional [#21](https://github.com/mxlzz/Nilo/issues/21); capacidades [#62](https://github.com/mxlzz/Nilo/issues/62); proyectos y bucles [#31](https://github.com/mxlzz/Nilo/issues/31)/[#14](https://github.com/mxlzz/Nilo/issues/14); contexto [#64](https://github.com/mxlzz/Nilo/issues/64); persistencia [#65](https://github.com/mxlzz/Nilo/issues/65); laboratorio editable [#146](https://github.com/mxlzz/Nilo/issues/146); termodinámica propuesta [#22](https://github.com/mxlzz/Nilo/issues/22).
