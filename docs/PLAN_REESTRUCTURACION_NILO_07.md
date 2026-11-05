# Nilo 0.7 — Plan de reestructuración integral por etapas

**Estado vigente al 5/11/2026:** etapas **00–15 completadas** en `refactor/0.7`;
etapa **16 · Memoria, investigación y evidencias** pendiente. El seguimiento actual está en
[ESTADO_REESTRUCTURACION_07.md](ESTADO_REESTRUCTURACION_07.md) y el cierre de la
migración pública en [MIGRACION_PUBLICA_ETAPA_03.md](MIGRACION_PUBLICA_ETAPA_03.md).
La descripción de propuesta que sigue se conserva como registro del plan original.

**Decisión de versión (4/11/2026):** reservar `0.7` para el resultado integrado de la reestructuración de Nilo. La base comparativa es `0.6.4`. Esta hoja es una **propuesta de ejecución detallada**, todavía sin implementación ni fecha de publicación. La nueva física térmica queda fuera de `0.7` y se considera para `0.8`. Referencias: [auditoría 0.6.4](AUDITORIA_ARQUITECTURA_NILO_07_2026-11-04.md), [#74](https://github.com/mxlzz/Nilo_public/issues/74).

## Principio de trabajo

No reescribir el sistema entero de una vez ni dejar dos motores permanentes. Trabajar en `refactor/0.7` (a crear al comenzar la ejecución) mediante entregas internas y verificables; **no publicar versiones parciales `0.7.x`**: `0.7.0` es el release final. En cada etapa:

1. **Reauditar el alcance**: inventariar archivos, funciones, dependencias entrantes/salientes, estado mutado, fuentes de verdad, tests, deuda no observada en la primera auditoría y comportamiento real (incluidos límites conocidos).
2. **Especificar la responsabilidad y los contratos**: quién puede leer, decidir, mutar, persistir, observar; qué se conserva, corrige o retira de manera explícita.
3. **Reformular y reescribir**, migrando al paquete dueño de la responsabilidad, sustituyendo duplicaciones y adaptando el código consumidor. Evitar limitarse a mover archivos, introducir wrappers sin retirar duplicados o añadir un parche sobre el legado.
4. **Probar antes/después**: tests unitarios, invariantes, escenarios reales, pruebas diferenciales contra `0.6.4` y fixtures de partidas cuando corresponda. Toda desviación se clasifica como cambio deliberado, corrección o regresión; no cambiar silenciosamente la línea base.
5. **Cerrar e integrar**: documentación del contrato, decisiones y riesgos; CI verde, prueba del programa arrancando y funcionando, commit reversible, eliminación de rutas legadas cuando ya no tengan consumidores. No pasar a la etapa siguiente con regresiones conocidas sin justificar.

## Secuencia propuesta: 25 pasos de alcance acotado

### A. Referencia, modelo y motor

| Paso | Revisión profunda y reescritura | Puerta de salida |
|---|---|---|
| **00 · Congelar la referencia** | Identificar commit, distribución, catálogos, configuración, fixtures SQLite de diferentes generaciones, manifest y resultados; crear paquete de comparación con hashes y restauración. Sin reescritura de comportamiento. | `0.6.4` reproducible, partida de prueba recuperable, mediciones iniciales. |
| **01 · Arquitectura definitiva de paquetes** | Volver a estudiar todos los imports y ciclos, las 63 fuentes, HTML, scripts, datos, tests y flujos completos. Fijar propietarios de reglas, dependencias permitidas y estructura mínima de `core/worlds/physics/agent/cognition/storage/app/lab`. | Matriz archivo viejo → propietario nuevo y contratos; grafo sin dependencias circulares de dominio. |
| **02 · Estado de dominio** | Auditar `self.s`, `person`, mundo, marcadores, defaults, datos de UI y mezclas entre hecho, hipótesis y percepción. Reescribir esquemas tipados/versionados y validación en límites. | Esquemas estables y fixtures con serialización equivalente; proyecciones no mutan estado. |
| **03 · Eventos y resultados** | Reauditar tuplas antiguas, `ActionResult`, eventos y consumidores de texto; reemplazar cadenas interpretadas por eventos tipados, procedencia, causalidad, errores y efectos explícitos. | Un resultado contractual común, sin inferir éxito ni evidencia por la narrativa. |
| **04 · Identidades y aleatoriedad** | Rastrear `uuid4`, RNG global, semillas, IDs físicos/lógicos y serialización de estados. Centralizar identidad y secuencias reproducibles (#69). | Reanudar desde save preserva RNG e IDs; replays repetibles en el alcance declarado. |
| **05 · Reloj y ejecución temporal** | Revisar minutaje, `tick`, fases, pausas, interrupciones, velocidad y actividades automáticas. Rehacer contrato de duración prevista/transcurrida y fases (#67/#142). | Viaje/trabajo/acreditación coherentes; ningún efecto futuro se acredita antes de tiempo. |
| **06 · Registro y validación de acciones** | Revisar manuales, contratos, parseo LLM, planificador, `ACTION_DURATIONS` y dispatchers. Un registro tipado produce documentación, requisitos y validación. | Una única definición de operación para LLM/planificador/ejecución/laboratorio; se elimina el dispatcher duplicado. |
| **07 · Núcleo orquestador** | Desarmar `nilo.py` y `Simulation`: vida de sesión, reloj, cola, deliberación, acciones, UI, migraciones y servidor. Reescribir coordinación pequeña por casos de uso. | Motor ejecutable sin HTTP/UI, integrable por API, con escenarios pasando por la misma ruta. |

### B. Mundo físico y percepción

| Paso | Revisión profunda y reescritura | Puerta de salida |
|---|---|---|
| **08 · Mundo y generación** | Revisar topología, niveles, generación, semillas, catálogos y pertenencia de propiedades al entorno. Extraer `worlds/island` sin reglas cognitivas. | Mismo mundo inicial por semilla y contrato para otro entorno sin implementarlo todavía. |
| **09 · Navegación y exploración** | Revisar BFS, frontera, revelado, rutas, ascenso/descenso, `go/explore`, errores de accesibilidad y complejidad. Rehacer índices y consultas deterministas. | Rutas válidas, información solo conocida, menor costo medido, pruebas de no progreso (#2). |
| **10 · Recursos e inventario** | Auditar `gather/forage`, depósitos, transferencia, límites, consumo, extracción remota, mensajes y regresiones de materiales. Rehacer operaciones de conservación y fases. | Conservación y no-negatividad; extracción imposible sin trabajo; resultados sin parsing textual. |
| **11 · Materiales, objetos y componentes** | Revisar catálogos JSON, `catalogo`, `physics`, identidades, forma, uniones y `setdefault` con efectos. Definir propiedades físicas por datos/mediciones, no nombres. | Consistencia catálogo/motor, invariancia frente a etiquetas y objetos legados compatibles. |
| **12 · Interacciones y construcción** | Auditar `craft/build/modify/design/interact/use`, recipientes, cargas, mecanismos, proyectos materiales y efectos no evaluables. Rehacer handlers por capacidad física y resultados probables/medidos. | Ensayos comparables; propiedades no comprobadas no se convierten en capacidades; sin duplicación de física. |
| **13 · Necesidades corporales y descanso** | Revisar fisiología, acciones voluntarias vs involuntarias, umbrales, sueño, refugio/seguridad, tiempo y efectos físicos. Reescribir política física aislada de decisiones del personaje. | Sensaciones coherentes, descanso y condiciones verificables; renombrar refugio no cambia protección (#75). |
| **14 · Observación del entorno** | Auditar `island_views`, snapshots, percepción local, campos ocultos, visualizaciones y efectos secundarios. Rehacer proyecciones de solo lectura diferenciadas para usuario y agente. | Hash del estado idéntico antes/después de leer/renderizar; cero conocimiento oculto (#76). |

### C. Agente y cognición

| Paso | Revisión profunda y reescritura | Puerta de salida |
|---|---|---|
| **15 · Deliberación y proveedores LLM** | Auditar `brain`, `providers`, prompts Gemini/Groq, presupuestos y validación de salida. Separar gateway, prompt estable, proyección y parseo; un contrato común genera variantes compactas. | Payloads exactos inspeccionables; sin diferencias de reglas no documentadas; identidad del personaje conservada. |
| **16 · Memoria, investigación y evidencias** | Revisar `recall`, episodios, hipótesis, ensayos, comparaciones, conocimiento comprobado y vínculos por ID. Rehacer recuperación justificada y separación entre observación, creencia y evidencia. | No se inventa recuerdo ni resultado; procedencia consultable y continuidad comprobada. |
| **17 · Proyectos, agenda, hábitos y reconsideración** | Reauditar transición de estados, completitud, prioridades, bloqueo, actividades delegadas y bucles. Reescribir un modelo de proyectos y estrategia con evidencias/condiciones tipadas. | Sin cierres por coincidencia de palabras; no se imponen misiones; cambios de estrategia evaluables. |

### D. Datos, aplicaciones y laboratorios

| Paso | Revisión profunda y reescritura | Puerta de salida |
|---|---|---|
| **18 · Persistencia, migración e historial** | Revisar `archive`, WAL, snapshots, relaciones, versión de esquema y sincronizaciones completas. Rehacer repositorios y migraciones transaccionales por esquema, con escrituras incrementales donde aporten. | Partidas históricas importadas con IDs/historial intactos, backups restaurables y benchmarks documentados (#32). |
| **19 · Servidor, API y observatorio** | Revisar rutas HTTP embebidas, interfaces de lectura/escritura, errores, versiones y datos privados/configuración. Extraer `app/server` y proyecciones API con contratos. | La API no altera leyes al consultar; pruebas de operaciones/errores y compatibilidad explícita. |
| **20 · Interfaz principal** | Auditar `interfaz.html` (~175 KB), JS/CSS embebido, handlers inline, solapas, enlaces, estados, ayudas, preferencias y actualización. Separar assets y renderizadores sin rediseño visual innecesario. | Paridad funcional y pruebas de navegación/lectura; UI no modifica mundo accidentalmente. |
| **21 · Laboratorio unificado y centro de ajustes** | Auditar los tres laboratorios, `MotorLab` paralelo, replay, configuración y propuesta #70–#73. Unificar sobre el motor real; perfiles validados, diff, backups y restore **sin** escritura directa arbitraria a código Python. | Mismas reglas/acciones en simulación y laboratorio; experimentos aislados; aplicar/restaurar sin corromper partidas. |

### E. Verificación, reducción de legado y publicación

| Paso | Revisión profunda y reescritura | Puerta de salida |
|---|---|---|
| **22 · QA transversal y rendimiento** | Reevaluar huecos de los 646 tests/68 escenarios; ampliar tests unitarios, integración, metamórficos, cambios de estado, estáticos, UI, cargas largas y cobertura; auditar deuda surgida durante la migración. | CI verificable, benchmark SQLite/navegación, matriz de cambios intencionales vs baseline. |
| **23 · Evaluación autónoma real** | Comparar partidas Gemini/Groq con semillas, snapshots, presupuestos y condiciones registrados. Examinar bucles, continuidad, curiosidad, consumo LLM y hechos medibles; revisar anomalías y corregir solo lo atribuible. | Informe conductual reproducible, sin declarar mejoría por impresión o por tests sintéticos. |
| **24 · Limpieza final y release 0.7.0** | Auditoría final del árbol: imports y módulos huérfanos, compatibilidad residual, rutas alternativas, documentación, empaquetado, seguridad, migración y rollback. Eliminar adaptadores temporales sin uso. | Instalación nueva e importada correctas, reversión probada, manifest y release `0.7.0`; sin segundo motor legado permanente. |

## Criterios que no se negocian durante la migración

- Nilo mantiene decisiones e intereses propios; el motor no propone misiones ni inyecta investigación privilegiada.
- **Motor = consecuencias verificables; LLM = intenciones**, con evidencia por ID y `no_evaluable` cuando falte física.
- Las reglas físicas no dependen de nombres o del estilo narrativo. Las vistas son puras.
- Las partidas antiguas y su historia no se reescriben retrospectivamente. La compatibilidad de archivos se demuestra con fixtures.
- El laboratorio no tiene física paralela. La restauración de configuración y de partida son procesos separados.
- No incorporar termodinámica, clima ni segundo mundo en 0.7: primero consolidación y equivalencia, luego nuevas leyes.
- Los pasos son unidades de trabajo **internas**, no una obligación de versiones públicas o commits monolíticos. Se pueden subdividir si una auditoría local descubre dependencias nuevas.

## Renumeración de hitos (decisión 4/11/2026)

- **0.7.0** — consolidación arquitectónica descrita arriba.
- **0.8** — termodinámica y ciclos ambientales por fases separadas, antes #9/0.7.
- **0.9** — autonomía prolongada/procedimientos, antes #10/0.8; alcance revisable según lo que quede resuelto en 0.7.
- **0.10** — transferencia entre mundos, antes #11/0.9; el identificador 0.10 es posterior a 0.9 en versionado por componentes, aunque su asignación sigue tentativa.
- **1.0** — horizonte de estabilidad de runs prolongados, sujeto a evaluación; no desplazado mecánicamente.

Las anotaciones en `ROADMAP_0571.md` conservan la numeración histórica; el orden vigente se establece aquí y en `FUTUROS_CAMINOS.md`.
