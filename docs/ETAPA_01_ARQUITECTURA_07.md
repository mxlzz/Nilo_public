# Nilo 0.7 · Etapa 01 — Auditoría de dependencias y arquitectura objetivo

**Fecha:** 4/11/2026. **Rama de trabajo:** refactor/0.7. **Referencia del código:** 0.6.4, commit e7229ebf9cf6a9f45a44a4ca184c12795535c843. **Tipo de entrega:** definición y verificación estructural, sin migrar reglas físicas ni alterar partidas. Plan maestro: [PLAN_REESTRUCTURACION_NILO_07.md](PLAN_REESTRUCTURACION_NILO_07.md). Seguimiento: [ESTADO_REESTRUCTURACION_07.md](ESTADO_REESTRUCTURACION_07.md).

## 1. Trabajo efectivamente realizado y límites

Se inspeccionó el árbol completo de Git de main y se leyó el código fuente de los **63 archivos Python de raíz** (excluyendo tests) para relevar funciones de primer nivel y dependencias locales, incluidos imports dentro de funciones. Se inspeccionaron además las rutas principales de los módulos extensos (métodos y responsabilidades), la definición de CI, el empaquetador, los HTML principales y los catálogos de datos del árbol. Los tres JSON y cuatro HTML quedaron identificados en el inventario, sin realizar en esta etapa pruebas DOM ni auditoría línea por línea de su comportamiento. Se contrastó con los **21 hallazgos** de la [auditoría previa](AUDITORIA_ARQUITECTURA_NILO_07_2026-11-04.md).

La comparación Git entre el commit de referencia y main identificó **solo tres cambios documentales**; por tanto la revisión de imports corresponde al código auditado de 0.6.4. **No se ejecutó una corrida nueva, CI, replay ni pruebas de compatibilidad en esta etapa de diseño**; esos resultados no deben inferirse del relevamiento estático. Los 646 tests de CI mencionados en el informe previo son resultados anteriores, no pruebas ejecutadas aquí.

El grafo de importación es un relevamiento de dependencias Python literales de módulos locales (incluso cuando están dentro de una función); no equivale a una prueba de ausencia de dependencias dinámicas, referencias por cadenas, mutación compartida o importaciones nativas/externas. Los números permiten localizar acoplamiento, no medir por sí solos la calidad del software.

## 2. Grafo actual y focos comprobados

- **63 módulos Python** de raíz y **155 aristas de importación local** en el relevamiento textual, contando una sola vez cada par de módulos.
- Mayores emisores: **nilo.py** (37 módulos locales), **brain.py** (18), **laboratorio_motor.py** (13), **world.py** (8).
- Mayores receptores: **world.py** (15 módulos lo importan), **physics.py** (10), **brain.py** (9), **construction.py** (8), **action_contracts.py** y **survival.py** (7 cada uno).
- **Tres componentes cíclicos**, agrupando múltiples ciclos internos:
  1. **Física / acciones (8 módulos):** action_contracts, capabilities, construction, inventions, mechanics, structural_loads, vessels y world. Casos mínimos: world ↔ construction, construction ↔ structural_loads y world → inventions → action_contracts → world.
  2. **Cognición (2):** brain ↔ cognitive_projection. El proyector importa una función interna de brain, al mismo tiempo que brain depende de la proyección.
  3. **Aplicación / laboratorio (3):** nilo, historical_lab y laboratorio_casos. historical_lab y laboratorio_casos dependen de nilo, que importa historical_lab; el laboratorio se acopla así al ejecutable.

**Concentración interna relevante:** Simulation en nilo.py empieza en la línea 142 y acumula migración de saves (migrate, línea 198), guardado, resúmenes del observador, planificación (plan_ready, línea 671), deliberación (think, 946), bucle (tick, 1055; _tick_slice, 1092), vista pública y servidor HTTP (Handler, 1901). world.py concentra generación (new_world, 125), rutas (pathfind, 196), exploración (exploration_frontier, 383) y ejecución (execute_action, 713). brain.py concentra construcción de contexto (context_for, 278), comunicación (request_llm, 209) y parseo (normalize_decision, 557). Esto obliga a separar casos de uso y dependencias, no solamente archivos.

### Riesgos de arquitectura adicionales identificados en etapa 01

**R01 · Colisión de nombre de paquete (nuevo).** La propuesta inicial del informe usaba un paquete Python llamado **nilo/**, pero el proyecto ya tiene el módulo ejecutable **nilo.py**, importado mediante «import nilo / from nilo import Simulation» por replays, tests y herramientas. Crear un paquete con ese mismo nombre podría cambiar la resolución de imports y romper esos consumidores. **Decisión:** crear la nueva implementación bajo **nilo_runtime/**, conservar temporalmente el archivo nilo.py como interfaz/arranque compatible, y retirarle responsabilidades progresivamente. No crear nilo/__init__.py al lado de nilo.py.

**R02 · La distribución es por manifiesto (nuevo detalle operativo).** empaquetar_version.py toma la lista de rutas de MANIFIESTO_SHA256.json, no descubre automáticamente archivos nuevos. Crear paquetes Python o dividir interfaz HTML/CSS/JS sin modificar esa lista produciría un ZIP incompleto aunque los tests en el repositorio pasen. **Decisión:** la migración de cada etapa incluye actualizar el manifiesto y tests de instalación desde el ZIP cuando incorpore archivos de ejecución; revisar también BAT/PS1 y rutas relativas. El empaquetador no debe incluir secretos ni SQLite de usuario.

**R03 · Ramas de refactor no disparan CI al hacer push (nuevo).** .github/workflows/validacion.yml escucha push para main y work/**, pero no refactor/**; el evento pull_request sí está disponible. **Decisión:** habilitar explícitamente refactor/** para controles sobre la rama y comprobar el CI a través de un PR de integración.

**R04 · Entradas históricas y herramientas dependen de símbolos de raíz.** En particular reproducir.py, auditar_contexto_llm.py, laboratorio_casos.py y historical_lab.py importan nilo, brain o world. Una migración de módulos que solo actualice las llamadas del servidor podría dejar roto el replay sin afectar una prueba superficial de arranque. **Decisión:** inventariar las importaciones públicas antes de retirar cualquier símbolo; introducir adaptadores de compatibilidad con fecha de salida y tests concretos.

**R05 · La interfaz y el laboratorio son consumidores distintos de datos.** Los cuatro HTML principales del ejecutable (interfaz.html, laboratorio_motor.html, laboratorio_escenarios.html y laboratorio_historico.html) contienen JS/CSS propios. Las vistas de Nilo, datos físicos de depuración y proyección que recibe el LLM no deben utilizar el mismo objeto mutable ni tener idénticos permisos. **Decisión:** DTOs de lectura separados sobre un estado físico común; componentes JS reutilizables sin fusionar permisos ni hechos/creencias.

**R06 · La noción de arquitectura no basta para proteger semántica.** Separar imports no prueba que las acciones conserven duración, conservación de materiales, identidad ni decisiones autónomas. Cada etapa debe incorporar pruebas por dominio y diferenciales; el checker de dependencias solo previene una clase de regresiones.

## 3. Arquitectura de destino

**Raíz de paquete:** nilo_runtime/. Su estructura final se materializará gradualmente; las rutas siguientes identifican propietarios semánticos, no exigen crear un archivo por concepto desde el inicio.

~~~text
nilo_runtime/
  core/          # tipos de estado y evento, contratos, reloj, identidad, puertos mínimos
  worlds/
    island/      # generación, terreno, rutas, percepción espacial, fuentes/depósitos
  physics/       # materiales, objetos, construcción, capacidades, fisiología
  agent/         # memoria, investigación, proyectos, agenda, hábitos, preferencias
  cognition/     # proyección consciente, prompts, validación LLM, proveedores
  storage/       # SQLite, esquema/migraciones, historial, backups y checkpoints
  audit/         # invariantes, diagnósticos y trazabilidad del motor
  application/   # orquestación de turnos, sesión, transacciones y coordinación
  web/           # API HTTP, DTOs de presentación y assets estáticos
  lab/           # casos, ejecución sobre el motor real, replay, perfiles experimentales
tools/           # utilidades de instalación, respaldo, empaquetado y QA
nilo.py          # compatibilidad de arranque/imports, sin física ni implementación HTTP
tests/
catalog/         # datos versionados; traslado físico solo si hay prueba de empaquetado
~~~

**Revisión respecto de la estructura inicial:** application/ no es core/. El coordinador debe poder importar/ensamblar dominios; el contrato básico del core no puede depender de ellos. web/ está separado de application/ para impedir que HTTP se convierta en dependencia de la simulación. audit/ separa diagnósticos del conocimiento de Nilo. Son límites funcionales; un paquete no debe multiplicarse en microarchivos de una función sin necesidad.

### Reglas de dependencia

1. **core** no importa mundos, física, agente, cognición, almacenamiento, UI ni laboratorio. Contiene datos y contratos neutrales.
2. **physics** puede usar tipos puros de core y datos de materiales, pero no importar world, prompts, API, storage ni agent. Recibe la geometría/estado necesarios en parámetros tipados; no consulta por su cuenta el mapa global.
3. **worlds/island** usa core y llama capacidades físicas por puertos definidos (o por composición desde application). No permite que physics le importe de regreso. Las consecuencias espaciales son responsabilidad del mundo; las leyes materiales, de physics.
4. **agent** conserva proyectos, memoria, prioridades elegidas, agenda y evidencia; consume observaciones y resultados publicados. No altera directamente el mapa o leyes físicas. **cognition** proyecta y decide mediante contratos de lectura; ninguna de ambas capas invoca world.execute_action.
5. **storage** implementa repositorios, migraciones y registros atómicos; no importa el ejecutable nilo.py, servidores ni laboratorios. Un snapshot del mundo no equivale a la totalidad del archivo relacional; distinguirlos en el contrato.
6. **application** es la raíz de composición: valida intención, prepara, ejecuta fases, confirma efectos, registra evidencia y publica observaciones. Es la única ruta de ejecución para Nilo y laboratorio.
7. **web** y **lab** llaman a servicios públicos de application. No pueden ejecutar una física alternativa ni modificar estructuras persistentes al generar una vista; los cambios de configuración pasan por una API explícita y transaccional.
8. **tools** opera por interfaces públicas de storage/application cuando corresponde; no hereda estado desde importaciones del entrypoint.
9. Los imports circulares nuevos están prohibidos. Los ciclos antiguos se irán retirando al migrar sus dependencias; que un ciclo desaparezca es una condición estructural, no prueba de comportamiento equivalente.

### Contratos conceptuales que deben concretarse

| Contrato | Contenido mínimo | Dueño de la mutación |
| --- | --- | --- |
| GameState / ActorState / WorldState | Estado tipado, versión de esquema, entidades por ID; sin preferencias de navegador | Application mediante operaciones de dominio |
| ActionIntent / ActionSpec | Operación, argumentos validados, unidades, requisitos, fases y origen | Cognition propone; Application valida |
| ActionExecution / ActionResult | Tiempo previsto/transcurrido, fases, efectos físicos, fallo/no evaluable, enlaces a evidencia | Application ejecuta; Physics/World calculan consecuencias |
| Observation / CognitiveProjection | Información revelada y pertinente, procedencia, filtro de acceso, síntesis sin mutaciones | World produce observación; Cognition proyecta |
| Project / EvidenceRef | Estados/transiciones elegidas, criterios, referencias inmutables a medidas | Agent gestiona decisiones y proyectos |
| SaveSchema / SessionManifest | Versiones de motor/datos/acciones, RNG, configuración, identidad y copia coherente | Storage persiste por transacción |
| DeveloperExperiment | Perfil versionado, snapshot aislado, cambios de parámetros, diff y resultados | Lab usa Application; nunca ejecutor propio |

Se prefieren interfaces pequeñas basadas en datos/funciones y protocolos de Python donde aporten testabilidad. Evitar un framework extensible por anticipado a mundos que todavía no existen.

## 4. Inventario completo: archivos existentes y propietario previsto

Las flechas con varias rutas señalan **división real de responsabilidades** dentro del archivo heredado; cada archivo de origen figura una vez. Los propietarios no autorizan mover código sin su prueba correspondiente.

| Propietario principal | Fuentes actuales (63 en total) | Asignación o división prevista |
| --- | --- | --- |
| **core / contratos (4)** | action_contracts.py, action_results.py, timing.py, physical_links.py | Contratos/resultados/tiempo en core; snapshots de physical_links pasan a audit, con DTO común en core |
| **application y web (3)** | nilo.py, interface_prefs.py, observer.py | nilo.py se divide entre application/engine, agent/proyectos, storage/migración y web/servidor; preferencias y observador van a web y su almacenamiento asociado |
| **worlds (6)** | world.py, island_planning.py, island_views.py, environments.py, scenarios.py, intervention.py | world.py se divide entre mundos/generación/navegación/recursos y handlers físicos; interfaces de ambiente al límite core/worlds; vistas puras; escenarios iniciales |
| **physics (10)** | catalogo.py, physics.py, construction.py, capabilities.py, mechanics.py, vessels.py, structural_loads.py, survival.py, bodily_policy.py, phenomena.py | Datos/leyes/objetos/capacidades independientes del mundo; «no evaluable» como resultado, necesidades corporales y políticas físicas separadas |
| **agent (16)** | agent.py, cognition.py, episodic_memory.py, experiment_log.py, goal_evidence.py, goals.py, habits.py, inventions.py, laboratory.py, motivation.py, behavior.py, agenda.py, project_lifecycle.py, project_progress.py, research_cycle.py, strategy_review.py | Entidades y estado inicial, memoria, evidencia y proyectos; inventions.py distribuye diseños y propuestas diagnósticas; laboratory.py son ensayos realizados por Nilo (no laboratorio del desarrollador) |
| **cognition (4)** | brain.py, cognitive_projection.py, prompt_budget.py, providers.py | brain.py se separa en prompts, observaciones/contexto, parser, decisiones y gateway; proveedores no contienen leyes |
| **storage (5)** | archive.py, record_links.py, review_store.py, run_history.py, historical_lab.py | Historia, vínculos, sesiones, snapshots/replay; historical_lab.py se divide entre storage/checkpoints y lab/replay |
| **audit (3)** | diagnostics.py, diagnostic_guidance.py, diagnostic_support.py | Invariantes, diagnósticos y evidencia tipada, sin interpretar hechos físicos por similitud de palabras |
| **lab (7)** | laboratorio_motor.py, laboratorio_casos.py, laboratorio_contexto.py, reproducir.py, evaluar_corridas.py, auditar_contexto_llm.py, validar_escenarios.py | Runner, escenarios, análisis de contexto, evaluaciones y replays; laboratorio_motor.py se divide también con web/lab-api; eliminar MotorLab._execute paralelo tras comprobar equivalencia |
| **tools (5)** | gestionar_partidas.py, migrar.py, primer_inicio.py, empaquetar_version.py, exportar_historial.py | CLI de respaldo/importación/instalación/paquete/exportación; rutas públicas estables o wrappers compatibles |

**Inventario adicional no Python:** catalog/materiales.json, objetos.json y terrenos.json; cuatro interfaces HTML de ejecución/laboratorio (más docs/atlas_interactivo.html documental); .github/workflows/validacion.yml y paquete.yml; MANIFIESTO_SHA256.json y VERSION; ocho BAT y dos archivos de instrucciones TXT, PowerShell de instalación y config.env.example. Revisar cada launcher, asset y herramienta en pasos 19–24; evitar «mover un archivo» sin actualizar manifiesto y rutas externas.

## 5. Secuencia de corte de los ciclos (aplicación obligatoria de contratos)

1. **Core primero (02–06):** esquemas, resultados, reloj e IDs. El contrato de acción no puede importar world para poder documentar una operación.
2. **Orquestador pequeño (07) y mundo (08–10):** Application obtiene capacidades físicas por composición; worlds no debe importar cognitive projection. Extraer el dispatcher legacy de world únicamente cuando estén los handlers equivalentes.
3. **Construcción y capacidades (11–13):** convertir llamadas construction ↔ world, construction ↔ vessels y construction ↔ structural_loads en funciones sobre DTOs/puertos. Las capacidades físicas se registran sin importar el mundo.
4. **Observaciones y cognición (14–17):** eliminar brain ↔ cognitive_projection; la proyección consume datos del actor, no una función interna del módulo que llama al LLM.
5. **Persistencia y laboratorio (18–21):** cortar nilo ↔ historical_lab/laboratorio_casos y que los checkpointers no necesiten importar el CLI. El laboratorio usa application y no implementa una ruta paralela.
6. **Limpieza (22–24):** prohibición total de ciclos de paquetes y de imports físicos desde UI/cognición; compatibilidad con entradas históricas documentada y eliminada cuando corresponda.

## 6. Criterios de aceptación de arquitectura para las etapas siguientes

- No se renombra/retira una API heredada sin identificar y probar todos sus consumidores (incluidos scripts, pruebas y empaquetado).
- CI en rama refactor/** más pull_request y checker automatizado de grafo cuando se incorpore; prohibir **ciclos nuevos** desde ya y registrar reducción de los heredados.
- Al crear archivos ejecutables, manifest/ZIP se actualiza y se verifica el arranque **desde el ZIP empaquetado**, no solamente desde checkout.
- Cada etapa incluye listado de funciones movidas, duplicaciones eliminadas, pruebas, decisiones de cambio semántico y estado de rollback.
- Conservación de nombres/IDs históricos en SQLite; separación de engine_version, save_schema_version y action_schema_version; no confundir prueba de esquema con replay exacto.
- Ningún prompt ni objetivo del personaje cambia de manera incidental por mover código; la comparación de payload LLM se registra en etapa 15.
- No introducir segunda física en laboratorio, ni autorización automática para modificar el programa a partir de diagnósticos de Nilo.

## 7. Resultado y límites de cierre de etapa 01

**Diseño completado:** inventario 63/63, grafo de imports local, detección de tres componentes cíclicos, matriz de destino, contratos de lectura/escritura, política de compatibilidad y hallazgos operativos adicionales R01–R06. La arquitectura de destino es la referencia de implementación, **revisable ante evidencia real de las siguientes auditorías**.

**Todavía no hecho (no pertenece a la implementación de esta etapa):** extracción de archivos a nilo_runtime/, reescritura de engine, modificación de física, migración SQLite, corridas LLM, importación de partidas antiguas, pruebas desde ZIP. El paso 00 de fixtures/rollback completo permanece pendiente.

**Próximo paso material:** 02 — modelos de estado. Antes de implementarlo debe completarse la congelación reproducible del paso 00; el diseño aprobado aquí no sustituye ese respaldo.
