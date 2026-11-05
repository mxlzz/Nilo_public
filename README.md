# Nilo — documentación técnica

**Repositorio público:** [issues y validación de la migración](docs/MIGRACION_PUBLICA_ETAPA_03.md).
`main` conserva Nilo 0.6.4; el desarrollo de 0.7 continúa en `refactor/0.7`,
con etapas 00–08 completadas y etapa 09 pendiente.

**Última versión: Nilo 0.6.4 — laboratorio de escenarios más accesible, con solicitud LLM íntegra, ayudas y resultados desplegables; sin cambios en las reglas físicas.** Las construcciones fijas ahora pueden ensayar cargas y almacenar o devolver materiales reales mediante un segundo módulo de capacidades independiente (`structural_loads.py`), y sus límites dependen de piezas, resistencias y geometría en vez de nombres. [Historial de cambios](docs/CAMBIOS.md). Conserva el sistema de evaluación de 0.5.9.4, que incluye `evaluar_corridas.py`, que analiza copias SQLite sin modificar las partidas, métricas de acciones y autonomía, comparación descriptiva con advertencias de comparabilidad y huella del estado inicial y semilla efectiva por sesión. [Protocolo de evaluación](docs/PROTOCOLO_EVALUACION_0594.md). La exploración dirigida de la .35 se conserva íntegra. No se modifican necesidades ni física.

**[Auditoría técnica previa a 0.6 (2/11/2026)](docs/AUDITORIA_PRE_06_2026-11-02.md)** — revisión de la arquitectura de la 0.5.9.3.35 y contraste con dos runs anteriores. Conclusión: no se necesitó una versión intermedia; se publicó **0.5.9.4** para reunir evidencia antes de comenzar 0.6 por cortes verticales.

**[Protocolo de evaluación 0.5.9.4](docs/PROTOCOLO_EVALUACION_0594.md)** — cómo comparar partidas, registrar las condiciones iniciales y distinguir medidas físicas de afirmaciones causales.


### Laboratorio explicativo y solicitud completa · 0.6.4

En **Escenarios**, catálogo y condiciones comparten la columna izquierda; a la derecha, el primer desplegable es **«Qué recibe el LLM»**, con opciones **Antes/Después** y **Gemini/Groq**. Muestra valores de contexto, instrucciones literales, contratos de acciones y cuerpo JSON completo construido con la misma función que envía Nilo, pero **sin realizar solicitudes**. Diferencia explícitamente el estado interno del motor del contexto proyectado que recibiría el personaje. Las secciones de mediciones, resultados, ejecución y diagnósticos ahora son desplegables, y los iconos (?) explican el significado de cada etapa. [Guía](docs/LABORATORIO_ESCENARIOS.md).

### Laboratorio histórico · 0.6.3

El botón **Partidas históricas** del laboratorio abre `http://127.0.0.1:8766/historico`. Cargá una partida `.sqlite3` o consultá la de esta carpeta, recorré las decisiones y acciones con un **slider**, seleccioná un punto y examiná su orden y registros. Desde esta versión, Nilo almacena checkpoints comprimidos antes de cada deliberación y acción para reproducir el procesamiento **en SQLite temporal**, mostrar las líneas ejecutadas y comparar efectos. Podés cambiar la orden de manera experimental sin alterar la partida original.

**Partidas previas:** se pueden consultar en la línea temporal, pero no reejecutar exactamente si carecen de estado anterior. Los UUID/relojes reales/eventos externos no están completamente reproducidos. El replay utiliza el motor instalado, **sin llamadas LLM**. El registro histórico aumentará el tamaño del SQLite con el tiempo. [Manual y limitaciones del depurador](docs/LABORATORIO_HISTORICO.md).

### Laboratorio de escenarios · 0.6.2

En Windows, ejecutá **`ABRIR_LABORATORIO.bat`** (o `python laboratorio_motor.py`). Abre **http://127.0.0.1:8766**. El modo principal es un **catálogo de 68 escenarios** —de órdenes simples a ciclos completos de varias deliberaciones—, y muestra para cada uno entrada, validación, código ejecutado con líneas desplegables, resultado, mediciones, variaciones físicas y contexto cognitivo antes/después. Las decisiones de prueba reemplazan la salida del LLM, **sin consultar Gemini ni Groq**.

El **sandbox de botones** permite elegir cualquiera de las 26 operaciones, parametrizarlas por opciones, combinarlas en un plan (hasta 12) y pasarlas por el mismo `Simulation.plan_ready` y `Simulation.tick` de la partida. Todos los ensayos ocurren en **SQLite temporal**, sin tocar tu `nilo_mundo.sqlite3`. El laboratorio de acciones físicas 0.6.1 continúa como modo legado en `/sandbox`.

[Manual y cobertura del laboratorio](docs/LABORATORIO_ESCENARIOS.md). El catálogo incluye rechazos esperables (como `go` hacia piedra o árbol por nombre, que sigue pendiente), fallos físicos, construcción, herramientas, investigación, proyectos y recuperación de registros. **No pretende enumerar infinitas combinaciones ni reproducir el comportamiento autónomo real de un proveedor LLM.**

**[Plan de desarrollo vigente y revisable](docs/FUTUROS_CAMINOS.md)** — **referencia para decidir las próximas versiones** (revisión: 2/11/2026). Distingue próximos incrementos, el hito de evaluación `0.5.9.4`, dependencias reales y el salto funcional `0.6`. El plan puede modificarse ante nuevos runs y prioridades documentadas; **no es un calendario rígido**.

**[Roadmap técnico histórico](docs/ROADMAP_0571.md)** — registro de decisiones y arquitectura desde 0.5.7. Las referencias antiguas a «próxima versión» no reemplazan el plan vigente.

**[Atlas interactivo de Nilo](docs/atlas_interactivo.html)** — explorador visual del personaje, mundo, mecánicas, arquitectura y memoria (HTML autocontenido, 0.5.9.3.14).

**[Referencia técnica integral (motor, decisiones, reglas, archivos, datos y mecánicas)](docs/REFERENCIA_TECNICA.md)** — documento único para estudiar cómo funciona Nilo, auditado contra la serie 0.5.9.3.13.

---

## Nilo 0.5.9.3.28 · Continuidad experimental y diseños verificables (1/11/2026)

- **Fichas de diseño:** al fabricar o construir con `design_id` válido, el objeto conserva físicamente ese identificador. El motor relaciona la ficha con el ID real fabricado y la medición, pero **fabricar no acredita función**.
- **Pruebas de herramientas:** los usos exitosos sobre el objeto vinculado pueden verificar una función mediante su método explícito `expected_test` o, si no se especificó, un método reconocible con el propósito declarado. Exige ensayo real de la revisión vigente; no basta mencionar el ID del diseño en otra herramienta.
- **Refugios:** una recuperación efectiva de energía en un habitáculo con cobertura física válida se vincula al diseño de esa construcción. Su estado será **función parcialmente comprobada**, porque no demuestra seguridad ni ventaja causal frente al exterior. No se atribuyen funciones retroactivamente a objetos históricos sin relación física identificable.
- **Bucle energético:** el contexto entrega el umbral de energía y duración exigidos por la comparación de descansos (≤60 inicial, menor a 74,9 final y 15 min mínimo), número de pruebas recientes no comparables, estado real del abrigo de construcciones y recordatorio de que `wait` no reduce energía. Se preservan estos datos incluso con contexto compacto de Groq.
- **Cierre de proyectos:** el rechazo del motor conserva su razón concreta y proyecto de origen para la siguiente deliberación, sin cerrarlo ni asignar nuevos objetivos. Descansos no comparables cuentan como pasos informativamente infructuosos **solo en investigaciones explícitas de descanso**; no se prohíbe descansar.
- **Recipientes (corrección de .27):** la vía tipada principal `action_results.py` y las variables autorizadas de predicción ahora coinciden con el laboratorio: `capacidad_util_agua`. Las etiquetas de mediciones históricas permanecen legibles; no existe pérdida de agua en el tiempo.
- **Interfaz:** apartado de diseños muestra funciones comprobadas con IDs de medición y aclara la diferencia con prototipos. Continúa sin cambiar las reglas físicas de sueño o seguridad.

**Límites:** no es todavía la evaluación integral de autonomía del issue #2; la semántica de objetivos abiertos sigue dependiendo de la deliberación autónoma de Nilo. La prueba prolongada con modelos reales continúa pendiente.

---

## Nilo 0.5.9.3.27 · Espera voluntaria y claridad de interfaz (2026-11-01)

**Cambios de comportamiento y presentación, sin cambiar reglas de capacidad física ni borrar mediciones históricas.**

- **Nueva acción `wait`:** Nilo puede esperar voluntariamente de 1 a 1440 minutos simulados (30 por defecto), sin ejecutar otra acción ni declarar un ensayo de descanso. La evolución corporal sigue siendo la de inactividad (aprox. +0,8 energía/h), diferente de `rest` (+6,6/h a la intemperie o +10,6/h en refugio). **No existe `sleep` como operación separada y esperar no reduce la energía para un experimento.** No se genera actividad ni logro automáticamente; el reloj avanza y las condiciones diferidas siguen evaluándose. Colapso fisiológico independiente e inalterado.
- **Recipientes:** «retención estimada %; puede perder líquido» se reemplaza por **«capacidad útil estimada»**, que ya incorpora el factor estático de permeabilidad. No se simula evaporación ni filtración a lo largo del tiempo. Los nuevos ensayos registran `capacidad_util_agua` como métrica observada; el antiguo `retencion_pct` y `agua_retenida` siguen siendo legibles en archivos históricos con etiquetas aclaratorias, sin modificar ni interpretar retrospectivamente sus resultados.
- **Proyectos:** se muestra el vínculo más reciente por categoría física/documental y se pliegan las referencias anteriores de cada familia en «Ver anteriores (N)», cerrados inicialmente. Se mantiene la exposición completa de vínculos en el Cuaderno. La nueva agrupación usa `seq` del índice histórico, sin confundir estado `new/updated` con recencia.
- **Mapa:** el borde de referencias pasa de arriba a debajo de todo el desplegable.
- **Márgenes:** el layout deja de imponer 1800px de ancho máximo; margen exterior de 12px por lado, alineado con encabezado y pie.
- **Compatibilidad:** no hay cambios en esquema SQLite, velocidad ni reglas físicas; se conservan mediciones, objetos, diarios y replays anteriores. Pruebas nuevas comprueban validaciones de duración, diferencia entre esperar/descansar/actividad, ejecución de acción en simulación con persistencia, presentación de vínculos en JS real, terminología y CSS.

**Alcances pendientes:** el nuevo indicador «capacidad útil» es una capacidad estática calculada; una simulación temporal de fugas sería una física distinta y requeriría reglas y evidencia nuevas. La comprobación visual humana con partidas grandes en Windows queda fuera de las pruebas automáticas.

---

## Nilo 0.5.9.3.26 · Cuaderno, vínculos completos y verificación de interfaz (2026-11-01)

**Tercera etapa acordada: #38, #51, #52, #53, #54.** Basada en 0.5.9.3.25, sin modificar reglas de autonomía, física corporal, tiempos de las acciones ni sus datos históricos.

- **#38 — Relaciones del Cuaderno:** `recordLinks` muestra TODOS los registros relacionados directamente, agrupados por familia sin subtítulos ni separadores, con prioridad de fase y orden histórico dentro de cada grupo; se elimina el control «Ver N relaciones más».
- `History.relations_for`, `relations_batch` y `Simulation.public_state` dejan de truncar vínculos a 40/25/32 por registro. La consulta individual `/api/record` también devuelve el grafo completo. Se deduplican referencias por entidad y se conserva la procedencia de las mediciones vinculadas al cuaderno.
- Los cortes de indexación de evidencias y `entity_links` (80/100/150) también se retiran. Migración `indexed_v2_full` reconstruye los índices de IDs explícitos una sola vez en bases existentes, sin reinterpretar texto, inventar relaciones ni modificar las partidas.
- **Integración con #49:** las transferencias, recargas, consumos, descargas y almacenamientos de recipientes ahora enlazan las herramientas u obras reales por ID, y distinguen origen/destino cuando hay evidencia tipada de éxito. La narración sin efecto físico o una operación rechazada no crea vínculo. Se conservan las variaciones de inventario como registros de material, sin inventar objetos.
- **#51–#54:** conservar las ayudas corporales vigentes, popovers flotantes, filtros y motivos de Investigaciones/Proyectos, y contorno del objetivo físico en el mapa. Esta versión agrega regresiones de arranque e integración contra el nuevo motor; no afirma verificación visual en Windows sin prueba humana.
- Pruebas de relaciones con más de 150 entidades por categoría, reconstrucción de índices históricos, ausencia de vínculos por texto, orden/presentación ejecutados en Node, simulación de transferencia con persistencia/reapertura SQLite; también se ejecutan pruebas y replays históricos.

**Pendiente de observación:** confirmar visualmente el comportamiento de ayudas, filtros, contorno y navegación/lectura del Cuaderno en una partida real; en acciones instantáneas el contorno puede no permanecer en pantalla. La cobertura futura de vínculos con terreno o fichas navegables de materiales depende de identidades físicas todavía no instrumentadas.

---

## Nilo 0.5.9.3.25 · Capacidades físicas y recipientes (2026-11-01)

**Segunda etapa acordada: #59, #39, #30 y #49.** Esta versión añade un primer módulo operativo completo, pero NO presupone que toda la arquitectura de plugins futuros esté terminada.

- **#59:** fabricación de objetos blandos y duplicados materiales independientes; sin veto universal por resistencia media inferior a 3 ni pérdida automática de materiales por ese veto. La resistencia sigue representada para evaluar usos. Se conserva el límite de componentes y las restricciones de obra fija superpuesta.
- **#30:** registro cerrado y versionado de capacidades físicas en `capabilities.py`, con despacho genérico `interact` y módulo `vessels.py`; se registra la versión de contenidos en el mundo al primer uso, y la evidencia de cada operación incluye ID y versión. Las partidas anteriores no cambian de leyes hasta ejecutar una operación nueva; si una partida requiere otra versión o la capacidad está deshabilitada, la operación se rechaza. No se cargan paquetes arbitrarios ni se habilitan propuestas automáticamente. Quedan pendientes activación explícita por instalación, migraciones entre versiones incompatibles y generación de otros módulos.
- **#49:** recipientes esquemáticos pueden llenarse parcialmente desde agua ambiental contigua, transferir cantidad comprobable entre dos objetos, descargar al entorno, beber explícitamente del contenido, guardar y retirar sólidos del inventario. Se valida capacidad, disponibilidad, cercanía, material compatible, integridad y cantidad sin duplicaciones. El agua ambiental aún no tiene un balance de depósito finito; descargar no produce charcos modelados. Los recipientes llenos no pueden desmontarse ni modificarse de manera que el contenido exceda la capacidad final sin vaciarlos o transferirlos previamente. La acción histórica `use/llenar` permanece para compatibilidad; el módulo nuevo utiliza `interact/rellenar`.
- **#39:** métodos físicos reconocidos por registro y diagnóstico tipado de la ausencia de método, con alcance, variables no evaluables e ID de evidencia. Los rechazos del módulo por precondición se distinguen de fallos físicos medidos y de `no_evaluable`. No se reinterpreta el historial anterior, ni se infiere filtración/potabilidad a partir de contención.
- Continúan sin cambiar los contratos corporales #55–#58, la autonomía del personaje, la física geométrica detallada y la interfaz del run anterior. Replays históricos preservados.
- Tests nuevos de conservación de contenidos, duplicados, intentos rechazados sin efectos, consumo explícito, cambios de capacidad, diagnóstico y arranque. Se complementan con la suite y replays de CI.

---

## Nilo 0.5.9.3.24 · Casilla de intervención en mapa (2026-11-01)

- #54: marca con un contorno interior discreto la casilla concreta de una intervención física durante una acción pendiente, sin modificar símbolos, rastro ni geometría. Disponible en superficie y cueva, y en mapas cercano y general.
- El motor expone `active_intervention` de solo lectura: `x,y,z,op`, exclusivamente si puede identificar una casilla observada y real. No se escribe en SQLite ni modifica memoria, acciones, tiempos o necesidades.
- Inspección: admite terreno por coordenadas, terreno/obra inequívocos y omite herramientas portátiles. Excavación: valida roca adyacente y herramienta con capacidad. Recolección: muestra fuente real cuando ya se trabaja allí, no casilla de apoyo; `forage` utiliza el selector físico compartido. Obras fijas: se distingue de modificaciones de herramientas portátiles.
- Durante una navegación, incluso si ya hay fuente seleccionada, no se anticipa el contorno: aparece solo durante intervención física, si ese estado dura hasta el próximo refresco. En operaciones que se ejecutan instantáneamente al terminar un trayecto, puede no ser visible; no se introducen esperas artificiales para forzar animaciones.
- Si se cancela la acción, se pierde conciencia, cambia de nivel o el terreno no está revelado, no aparece marca. Pueden comprobarse estos casos con pruebas de contrato y ejecución de mapa JavaScript.
- Basada en la corrección de arranque 0.5.9.3.23.1. Sin cambios de #38, #39, #30, #49 o de supervivencia.

---

## Nilo 0.5.9.3.23.1 · Corrección de arranque de interfaz (2026-11-01)

- La versión 0.5.9.3.23 intentaba ejecutar `stored('nilo.researchView.v1',...)` **antes de inicializar `const stored`**, provocando un `ReferenceError` de JavaScript durante el arranque de la página.
- La 0.5.9.3.23.1 corrige el orden de las declaraciones sin cambiar las reglas del motor, el formato de partidas ni los filtros.
- Se añadió una prueba de ejecución real de la secuencia de inicialización con Node.js; `node --check` no detectaba este fallo en tiempo de ejecución.
- No contiene cambios del mapa (#54): la 0.5.9.3.24 quedó suspendida hasta resolver y verificar el arranque.

---

## Nilo 0.5.9.3.23 — Lectura de registros (2026-11-01)

- #51: ayudas de hidratación, alimentación y energía actualizadas conforme a las reglas efectivamente publicadas en 0.5.9.3.22 (sin ingestas por umbral; descanso libre y colapso).
- #52: ayudas contextuales de Ensayos y otras secciones como popup flotante en `body`, sin desplazar registros; cierre por Escape, clic exterior, scroll y cambio de solapa.
- #53: filtro **independiente** de investigaciones por estado, incluyendo integradas; motivos registrados de pausas, abandonos y cierre en fichas, sin inferir razones ausentes.
- El filtro de Proyectos se conserva exactamente como en 0.5.9.3.22.
- No incluye agrupación de relaciones del Cuaderno #38 ni resaltado de casillas de intervención #54; ambos requieren pruebas específicas y quedan para otra versión.

---

## Nilo 0.5.9.3.22 — Autonomía corporal y agenda

- #55: `rest(minutes)` permite descansar de 1 a 1440 minutos simulados (30 por defecto). Al caer a energía ≤5, el estado inconsciente interrumpe la acción; se recupera a energía ≥40 sin deliberar durante el colapso.
- #56: no hay ingesta ni provisiones automáticas por umbrales del motor. Comer, beber, descansar y recolectar requieren decisión de Nilo o delegación verificable.
- #57: la agenda no bloquea acciones por sed, hambre o energía mediante umbrales generales; se siguen comprobando precondiciones físicas por operación.
- #58: las rutas y acciones físicas aplican un factor consistente de fatiga al iniciar la acción; la calibración dinámica durante rutas largas queda para evaluación posterior.
- Las reglas históricas pueden reproducirse sin transformar sus consumos ni descansos anteriores. No incorpora cambios de interfaz #38/#96–#54 ni nuevas capacidades de recipientes #49.

---

## Nilo 0.5.9.3.21 — QMP global, lectura compacta y descanso sin misión obligatoria

- QMP: «¿Qué me perdí?» queda en un pie fijo de la columna de registros, fuera de la franja de lectura por solapa, sin cambio de función ni de historial.
- Barra superior: Marcar como leído, filtro e Indicador quedan juntos sin el botón QMP que provocaba desplazamiento horizontal.
- Necesidades: ayudas (?) con información vigente de energía hasta 100, sin versión anterior ni leyenda redundante; Abrigo y Seguridad atenuados, recuperan contraste al enfocar.
- Actividad: porcentaje y tiempos simulados y reales en una línea.
- Cuaderno (#38): se verificó el flujo de relaciones físicas creado en 0.5.9.3.20, con movimientos de inventario y herramientas/obras por ID cuando constan en las mediciones y sus relaciones.
- Autonomía (#50): sin misión de investigar descanso; conservar recuperación física, mediciones y ensayos elegidos por Nilo. Prompt y contexto no priorizan el estudio refugio/intemperie; dejan de producirse conclusiones automáticas atribuidas a él. Una comparación explícita con evidencia sigue disponible.
- Proyectos opcionales: acción sin_proyecto para deliberar/actuar sin abrir proyecto. No se modifican las reglas de pausa ni de recordatorios.
- Compatibilidad: las reproducciones antiguas conservan la conducta física y la comparación automática de sus reglas históricas; no se borran resultados pasados al importar una partida.
- Seguimiento abierto: verificar vínculos visuales en runs nuevos (#38) y autonomía real del personaje (#50).

---

## Nilo 0.5.9.3.20 — Lectura compacta y recuperación completa de energía

- **Energía (#48):** la recuperación deja de interrumpirse al cruzar 75. Una pausa, reposo en refugio o inactividad pueden reponer energía hasta el límite natural de la escala (100); siguen existiendo consumo por actividad, hidratación y nutrición. El criterio experimental `rest_comparable` continúa exigiendo mediciones controladas: no convierte en válida una prueba saturada. El replay histórico conserva reglas antiguas; nuevos guiones pueden seleccionar `"ruleset":"0.5.9.3.20"`.
- **Cuaderno — Registros relacionados (#38, primer corte):** sin tocar una palabra del texto de Nilo, el archivo reúne movimientos de inventario medidos (por ejemplo, madera +2 / piedra −1) y herramientas/construcciones identificadas por ID real, versión o uso en acciones. Los materiales son saldos de inventario, no objetos individuales. Para las partidas antiguas se muestran deltas físicos existentes; las asociaciones nuevas con instancias solo existen si hay snapshots identificables. **Quedan para el desarrollo del catálogo 0.6:** fichas navegables y otras relaciones con el entorno.
- **Desplegables (#42):** abrir otro registro del mismo grupo cierra el anterior. Un ensayo y una predicción, o diseños y obras, son grupos independientes; los detalles técnicos anidados permanecen disponibles.
- **Ayuda contextual (#43):** las tarjetas de explicación pasan a botones (?) en Ensayos, Creaciones, Hallazgos, Investigaciones (predicciones), Propuestas y Agenda. En Ensayos se ubica junto a «Todas las mediciones»; conserva el estado dinámico de comparación de descansos en la ayuda.
- **Pestañas (#47):** un clic sobre la pestaña activa o una distinta vuelve al registro más reciente, sin reiniciar filtros ni redirigir saltos explícitos a registros históricos. En Chat, el gesto lleva al mensaje más reciente al final.
- **Conducta (#21):** los registros de habilidades tienen fondo/borde de novedad visible cuando activan el indicador de la solapa.
- **Compatibilidad:** sin cambios en `agenda.py`, en la selección de pausas/recordatorios (#40), ni en la estructura física del mundo. El empaquetado contiene `physical_links.py` y las pruebas de regresión. Se conserva importación de partidas y la verificación determinista histórica.
- **Otros issues:** #26 (direcciones narradas), #39 (matriz de capacidades), #30 (registro modular), #37 (planilla maestra), #33 (síntesis episódica) y las expansiones de física requieren trabajo separado; no se cierran artificialmente.

---

## Nilo 0.5.9.3.19 — Cierre verificado de reconocimiento y hallazgo de agua

- **#13, bug confirmado en run de día 2:** el proyecto «Reconocimiento del terreno y hallazgo de agua.» quedaba al 95 % pese a que Nilo solicitó `completar` 23 deliberaciones consecutivas y había exploraciones, agua observada e inspecciones con mediciones reales. El evaluador de objetivos ignoraba las palabras «reconocimiento» y «hallazgo» y no podía aceptar sus propias pruebas.
- **Validación específica y conservadora:** para ese tipo de objetivo, el motor exige evidencia de exploración del terreno y hallazgo comprobado de agua (observación real durante exploración, llegada a orilla o inspección), junto con una referencia auténtica en `prueba_cierre`. Los resultados de `conclude`, las frases del cuaderno o el simple nombre de una construcción **no** acreditan esos hechos.
- **Referencia pertinente:** cuando Nilo cita una medición válida, el verificador puede elegirla en vez de comparar contra una muestra histórica distinta. Ante un intento de cierre sin cita pertinente, explica qué IDs sí acreditarían ese objetivo.
- **Seguridad epistémica:** localizar agua **no** prueba que sea potable. La comprobación de potabilidad/purificación continúa exigiendo una métrica física específica.
- **Partidas existentes:** pueden continuar desde una copia de la versión anterior; no se modifican leyes, inventario, objetos, supervivencia ni se cierra de oficio ningún proyecto. Nilo debe decidir pedir nuevamente el cierre. No se alteran decisiones históricas.
- **Pruebas:** evidencia combinada, ausencia de agua, ausencia de exploración, citas no pertinentes, no confusión con ruinas ni potabilidad, cierre de proyecto integrado y retrocompatibilidad de replays.
- **Interfaz:** las dos ideas de futuras mejoras se registraron en [#42](https://github.com/mxlzz/Nilo_public/issues/42) (un desplegable por sección) y [#43](https://github.com/mxlzz/Nilo_public/issues/43) (ayudas (?) en lugar de tarjetas descriptivas). No se incluyen en este parche de bloqueo cognitivo.

---

## Nilo 0.5.9.3.18 — Recordatorios condicionados y filtros de estado

- **#40 · Recordatorios autoestablecidos:** Nilo puede declarar en la Agenda un recordatorio sin pasos físicos (`"modo":"recordatorio"`) asociado al proyecto que decide pausar, con una condición verificable como `energia < 60`. Al cumplirse, aparece una sola señal y el recordatorio vuelve al contexto de deliberación; Nilo decide si retoma la investigación. **No se ejecuta automáticamente** una prueba ni se declara logrado el objetivo.
- **Agenda y Proyectos:** desplegable de estado junto a «Indicador», con «Vigentes», «Agendados», «Finalizados», «Bloqueados» y «Todos», manteniendo los controles en una sola línea (desplazamiento horizontal cuando el espacio no alcanza). El filtro se recuerda por solapa, no altera el historial ni las marcas de lectura. Los recordatorios se distinguen visualmente de las tareas ejecutables.
- **Conservación:** tareas delegadas previas, progreso, replays históricos y reglas físicas mantienen comportamiento. Las condiciones no satisfacen por sí mismas los criterios de éxito experimental. La agenda anterior sigue siendo válida sin `modo`.
- **Alcance:** esta versión implementa el primer tramo de #40, pero **no** la clasificación centralizada completa de capacidades físicas (#39/#62), que permanece pendiente. La conducta del LLM con el recordatorio debe medirse en un run.
- **Pruebas:** normalización y deduplicación, evento único al cruzar umbral, pausa y reconocimiento al retomar, visibilidad en contexto compacto, compatibilidad de render y controles.

---

## Nilo 0.5.9.3.17 — evidencias de diagnóstico y navegación conocida

- **#29, PR `referencia privada #72`:** integrado `diagnostic_support.py`. `propose` y `report_issue` conservan el origen y la pertinencia de cada evidencia. IDs inexistentes o ensayos ajenos al fenómeno no se convierten en pruebas; una revisión humana llega a las deliberaciones posteriores sin atribuirle condición de evidencia física. Nilo sigue eligiendo libremente si presenta solicitudes.
- **#20:** el contexto LLM conserva la navegación hacia **lugares realmente revelados**, incluso cuando un proveedor aplica `compact_context`. Informa coordenadas, nivel del mapa y el estado de una ruta conocida (`en_destino`, `ruta_conocida`, `sin_ruta_conocida`, `otro_nivel`). Si no existe ruta conocida, **no concluye que el sitio sea inaccesible**. Los lugares no descubiertos nunca se exponen.
- **Compatibilidad:** la simulación física, los mapas y las acciones `go` y `inspect` permanecen intactos. El nuevo campo informa, pero no ordena desplazamientos ni modifica proyectos o recuerdos históricos.
- **Verificación:** tests deterministas de la selección de evidencia de `propose` y `report_issue`, revisiones humanas, rutas conocidas y ocultas, contexto compacto, escenarios y replay. Las decisiones efectivas del LLM deberán compararse con runs.
- **Pendientes:** reconsideración de descansos improductivos (#2), modelo modular de operaciones (#30), memoria longitudinal general (#20/#65), planilla maestra de definiciones. No se incluyen todavía en esta entrega.

---

## Nilo 0.5.9.3.16 — primer catálogo modular y correcciones

- **Catálogo físico separado**: `catalog/materiales.json`, `catalog/terrenos.json` y `catalog/objetos.json`, leídos y validados por `catalogo.py`; `world.py`, `physics.py`, `construction.py`, `mechanics.py` y `environments.py` conservan sus contratos y propiedades anteriores. Cada partida recibe copias independientes de los materiales.
- **×80 funcional**: la ruta HTTP `/api/settings` y el motor comparten velocidades `×1/×10/×60/×80`; se rechazan `×300` y `×600`, que habían quedado obsoletos.
- **Consultas LLM**: mínimo global configurable de **15 segundos** por defecto en instalaciones nuevas, validado entre 10 y 300 segundos. Las instalaciones actualizadas conservan su `config.env` anterior (por ejemplo, 60 segundos) y el valor efectivo aparece en **Configuración → Modelo y consultas**. No se eluden cooldowns/429 ni cuotas de proveedor.
- **Límites**: esta extracción no constituye todavía un registro de operaciones instalables, ni física composicional general, ni un sistema de organismos. No se agregaron efectos físicos ni objetivos a Nilo. El diagnóstico autónomo del PR `referencia privada #72` sigue separado.
- **Pruebas y paquete**: catálogo incluido en el ZIP portable, pruebas unitarias de compatibilidad, simulación determinista y prueba HTTP de ×80. [Contrato y pendientes 0.6](docs/CATALOGO_MODULAR.md).

---

## Nilo 0.5.9.3.15 — mapa, recursos y nuevos temas monocromáticos

- **Mapa:** un botón alterna entre mostrarlo u ocultarlo; las referencias se despliegan con un `details` independiente, dentro del mapa. La opción histórica «Solo mapa» se migra a mapa visible con las referencias plegadas. Ocultar el mapa deja visibles las solapas de recursos.
- **Recursos:** Materiales, Herramientas y Obras comparten espacio en tres solapas. Se conservan los accesos a las fichas y los conteos se actualizan con el mundo.
- **Color:** dos nuevos temas neutros, **Grises oscuros** y **Grises claros** (fondo casi blanco), además de Bosque, Grafito y Terracota. El estado elegido se conserva como preferencia visual portable.
- **Navegación:** eliminado el botón «Volver a conexión anterior» de la columna de registros (#34). Se conserva «← Volver» dentro del diálogo histórico y sus relaciones verificadas.
- **Alcance:** solo cambios de presentación y preferencias visuales; motor, proyectos, evidencias, físicas y partidas sin modificaciones. El PR de diagnóstico autónomo `referencia privada #72` sigue separado y pendiente de evaluación.

---

## Nilo 0.5.9.3.14 — corrección de auditoría y regresiones verificables

- **Recolección sin LLM:** `record_skill` acredita `gather` mediante el material canónico solicitado y el incremento real del inventario; deja de depender de la frase textual de `world.py`. Compatible con alias y recolección de una sola unidad; el registro histórico conserva su lector heredado.
- **Cierre de proyectos:** la ruta genérica por coincidencia de palabras ya no declara demostrados objetivos sin criterio físico instrumentado. `terminado` requiere evidencia pertinente; `pausado` y `abandonado` siguen disponibles. Se conservan las validaciones explícitas de fabricación, contención, descanso, etc.
- **Navegación:** `move()` ejecuta exclusivamente rutas por casillas ya reveladas; `explore` continúa apuntando a fronteras conocidas y revelando al llegar.
- **Pruebas:** regresiones reales `execute_action → record_skill → choose_wait_action`, resultados tipados, cierres falsos por coincidencia léxica y rutas con atajo oculto.
- **Alcance:** no se implementan criterios universales de objetivo, física composicional, índices de memoria ni refactorización completa a `ActionResult`. La referencia técnica original describe la 0.5.9.3.13; esta sección documenta el delta de mantenimiento.

---

## Nilo 0.5.9.3.13 — validez de cierres, investigaciones y QMP

**Hallazgos del run de 14,6 días y alcance de esta entrega:**

- **Cierre de proyectos (#13):** una prueba exitosa perteneciente a un proyecto ya no basta para completarlo. El cierre debe citar uno de los IDs que acreditan los criterios físicos del objetivo: fabricación, contención de un material concreto, recuperación de energía, desplazamiento o exploración. Los objetivos compuestos necesitan pruebas de cada requisito instrumentado. Si el motor no mide pérdida cero, estanqueidad, potabilidad o planificación futura, la conclusión permanece sin verificar. La decisión de pausar/abandonar sigue disponible. Esto es un validador conservador, **no** una comprensión semántica universal de cualquier objetivo.
- **Investigación y continuidad (#20):** las nuevas preguntas registran IDs de proyectos de origen; al pausar o abandonar un proyecto solo se modifican estados de investigaciones con vínculo explícito, conservando el historial. Cuando el mismo tema se retoma, se puede reabrir el mismo ID. No se reasignan investigaciones antiguas por parecidos textuales y archivar no demuestra una hipótesis.
- **QMP:** páginas de acontecimientos diversificadas por categoría con hasta 12 hechos principales; una serie administrativa de proyectos deja de desplazar siempre los ensayos y descubrimientos. «¿Qué más?» vuelve a buscar pendientes dentro del snapshot, en lugar de excluirlos por un techo de relevancia. Se conserva la confirmación de lectura únicamente de referencias presentadas o evaluadas y las vinculadas expresamente.
- **Pruebas (#3):** casos sintéticos derivados de cierres indebidos del run, revisión de una investigación asociada a proyecto y continuación de QMP. No se adjunta ni altera la partida original.

**Pendientes conocidos:** la interpretación general de objetivos con propiedades físicas arbitrarias, la indexación de investigaciones antiguas y una síntesis verdaderamente basada en episodios (no fichas, **#33**) requieren diseño adicional. La estructura modular sigue en #30.

---

## Nilo 0.5.9.3.12 — navegación y precisión al excavar

- **Volver a conexión anterior**: conserva solapa, filtro de registros y posición de lectura; funciona para vínculos desde el cuaderno, registros archivados, mediciones y resúmenes. Se mantiene una pequeña pila de navegación; no se altera el estado del mundo.
- **Pie redundante**: eliminado el texto fijo de la interfaz que repetía explicaciones de arquitectura.
- **Excavación**: al retirar una roca, el motor sigue convirtiendo la casilla en transitable y recuperando las piedras correspondientes, pero ahora informa que **despejó la casilla**. Ya no afirma que abrió un paso o una ruta sin haber comprobado conectividad o ventaja de recorrido.
- **Pruebas**: regresión donde una roca rodeada de suelo transitable se excava sin afirmar que abrió un pasaje; validación de botones y sintaxis JS.

Esta versión no introduce cálculo topológico de rutas antes/después ni modifica memoria, física o decisiones autónomas.

---

## Nilo 0.5.9.3.11 — relaciones legibles y lectura coherente del resumen

- **Registros relacionados:** cada vínculo conserva su categoría y recibe un símbolo y tono discreto. En Cuaderno se distingue `Nuevo` cuando la procedencia explícita o una marca de creación coincide con la entrada, `Actualizado` cuando existe un cambio documental verificable, y `Relacionado` atenuado como contexto. Si los datos históricos no lo permiten, no se afirma novedad.
- **Navegación:** se mantienen los enlaces de retorno existentes en «Registros relacionados». No se introduce botón adicional «Volver al Cuaderno».
- **«¿Qué me perdí?»**: descripción breve; «¿Qué más?» e historial de resúmenes se muestran **después** del texto y referencias, visibles al llegar al fondo de la ventana.
- **Lecturas:** una entrega puede incluir hasta 12 registros destacados y hasta 12 fuentes **directamente relacionadas**, en caso de que estuvieran pendientes y se muestren como «Registros vinculados revisados»; se marcan sus variantes en todas las solapas al confirmar el resumen. El resto mantiene su condición de no leído para «¿Qué más?», junto con los registros posteriores a la captura de la entrega.
- **Validación:** regresiones para distinguir creación de continuidad, comprobar enlaces directos y preservar registros nuevos y pendientes. Ningún cambio en física, decisiones autónomas ni LLM.

---

## Nilo 0.5.9.3.10 — cierre de proyectos, mediciones y memoria operativa

- **Decisiones del personaje:** completar requiere pruebas primarias pertinentes; abandonar y pausar son alternativas expresas que preservan el historial y no simulan logros. Completar, abandonar o pausar no crea un proyecto idéntico en el mismo turno. Se cancelan o suspenden tareas diferidas vinculadas y se evita la reactivación involuntaria.
- **Diagnóstico:** distinguir resultados físicos fallidos de interacciones `no_evaluable` y evitar conclusiones universales por métodos sin modelo. Nilo sigue eligiendo si solicita o no una ampliación.
- **Ensayos:** `compare` admite tasas medidas de descanso en refugio e intemperie, solo con muestras no saturadas y comparables. El contexto del LLM recibe pares reales aptos para `compare`; no se inventan valores.
- **Memoria:** ante estancamiento de exploración superficial, se recupera una transición a cueva previamente comprobada solo si la entrada es conocida. No se inventa ruta actual ni se obliga a viajar.
- **Versión y distribución:** `VERSION` y encabezado muestran 0.5.9.3.10. El manifiesto del paquete se actualiza para incluir las dependencias recientes y verificar los archivos actuales.
- **Compatibilidad:** los proyectos activos de partidas existentes conservan su historial. Los estados nuevos solo aparecen cuando Nilo toma una nueva decisión.

Este release **no completa** todo el #29 ni implementa el sistema modular #30. El próximo paso de evaluación (#3) será comparar estos cambios con el run observado, con sus limitaciones metodológicas.

---

## Nilo 0.5.9.3.9 — Resumen por acontecimientos, diagnóstico y controles de tiempo

- **«¿Qué me perdí?»**: apartados temáticos breves, extensión adaptada al número e importancia de novedades, pasajes más narrativos solo para hitos destacados. Agrupación de referencias por tipo con enlaces directos. La primera página analiza hasta 12 acontecimientos destacados; «¿Qué más?» conserva el resto de prioridad suficiente.
- **Lectura de resúmenes**: una vez que la interfaz recibe el resumen confirma tanto las fuentes destacadas de la página como las fuentes evaluadas de menor prioridad en el mismo snapshot. Se preservan sucesos posteriores y acontecimientos relevantes que esperan otra página. Cada resumen conserva referencias auditables, incluso cuando no requiere LLM porque solo había rutina.
- **Diagnóstico autónomo**: señales estructuradas y agrupación de intentos repetidos por operación, objetivo y estado, con IDs originales. Distingue uso incorrecto, fallo físico, fenómeno no evaluable y posible contradicción del contrato. Nilo elige si experimentar, cambiar de estrategia, reportar o proponer; ninguna regla física se modifica automáticamente.
- **Construcciones (#27 y #28)**: al pulsar una obra del mapa o lista se abre la ficha completa en «Creaciones». Desaparece el panel intermedio. Los planos históricos exponen los lotes, materiales, cambios entre revisiones y estados de piezas preservados.
- **Velocidades**: ×1, ×10, ×60 y ×80. Las partidas con ×300 o ×600 se migran a ×80. La escritura se mantiene limitada a ×2. Ninguna velocidad modifica las cuotas ni el intervalo mínimo real del LLM.
- **Sin cambios en el estado físico por cambiar de interfaz**. Se mantienen pruebas de replay y migración. Se recomienda conservar la carpeta/partida anterior antes de importar.

**Pendiente deliberadamente:** #26 requiere una reproducción concreta de la contradicción direccional, y el diagnóstico cognitivo #29 continúa siendo incremental; no se declara resuelto en su totalidad.

---

## Nilo 0.5.9.3.8 — Respaldo entre modelos Gemini y ajustes de interfaz

- **Gemini multinivel:** la misma API key intenta `gemini-3.1-flash-lite` y, si no está disponible, `gemini-3.5-flash-lite` y `gemini-3.8-flash` antes de pasar a Groq. El orden alternativo se configura en `GEMINI_FALLBACK_MODELS`; dejarla vacía desactiva los modelos alternativos. Solo se usan los modelos que el proyecto tenga habilitados; ninguno amplía automáticamente las cuotas que Google asigna.
- **Bloqueos independientes:** el cooldown de Gemini queda identificado por modelo y huella no reversible de la clave (la clave nunca se guarda en la partida). Cambiar de clave o de orden de modelos elimina la espera global anterior sin saltarse los límites reales de Google.
- **Configuración:** sin cambios en tus claves existentes. Si `config.env` no tiene `GEMINI_FALLBACK_MODELS`, se aplica la lista predeterminada. Se conserva el respaldo Groq y el contador interno de deliberaciones exitosas, que sigue siendo global.
- **Interfaz:** «¿Qué más?» e «Historial de resúmenes» quedan juntos sobre los registros de «¿Qué me perdí?», con regreso a la síntesis; se elimina la pestaña duplicada «Indicadores» de Configuración, conservando el selector por solapa y sus preferencias.
- **Pruebas:** regresiones de 429 por modelo, independencia de claves, orden de fallback y desactivación opcional.

**Notas:** un error 401/403 o una cuota de proyecto restringida no crea capacidad adicional. Las cuotas gratuitas dependen del modelo, la cuenta y el proyecto según Google AI Studio. No crear múltiples cuentas para rotar límites.

---

## Nilo 0.5.9.3.7 — Aceleración ×300/×600 y política de tiempo

- **Velocidades:** botones ×300 y ×600, disponibles en la interfaz y API. El motor divide el tiempo en tramos de hasta un minuto simulado y termina cada acción según su duración, sin saltarse rutas o pasos.
- **Consultando al LLM:** velocidad temporal efectiva ×1 mientras está deliberando, sin alterar la velocidad seleccionada ni los límites reales del proveedor.
- **Esperas:** la pausa automática (×0) incluye el intervalo ordinario entre llamadas si no quedan actividades útiles. Conserva el avance para rutinas seguras y tareas cuya condición depende del reloj simulado. El reintento LLM sigue gobernado por tiempo real.
- **Cuaderno:** en ×300 y ×600 se muestra el texto íntegro sin animación y se conserva la duración simulada de su escritura; ×1, ×10 y ×60 mantienen el modo anterior (×2 al escribir en modos acelerados).
- **Interfaz:** indica velocidad efectiva; las habilidades no leídas de Conducta reciben resaltado como los demás registros, solucionando #21. Por ahora no se cambia cuándo el contador de una habilidad genera una novedad.
- **Compatibilidad:** migración sin cambios en el mundo, reglas físicas o cuotas. Nuevo replay determinista con tiempos fraccionados y pruebas de regresión.

Relacionado: [#22](https://github.com/mxlzz/Nilo_public/issues/22) y [#21](https://github.com/mxlzz/Nilo_public/issues/21).

---

## Nilo 0.5.9.3.6 — memoria operativa y pruebas de cierre

- **Memoria contextual:** recupera experiencias verificadas de días anteriores según el objetivo y el lugar, con referencia a su ID y fecha. Una entrada conocida a una cueva permite recordar descensos y ascensos previos, aunque existan numerosos eventos más recientes. La selección no modifica la experiencia original y permanece en el contexto reducido de proveedores.
- **Evidencia primaria:** las operaciones `conclude` y `compare` ya no se reutilizan como mediciones físicas para otra conclusión. La repetición de la misma conclusión con idénticas pruebas no genera un nuevo hallazgo.
- **Cierre de proyectos:** no se utilizan registros de conclusión como avances físicos. Las pruebas que dicen «no está comprobada» o «sin funcionamiento verificado» no permiten cerrar un objetivo como si estuviera demostrado. La potabilidad requiere una medición física explícita, todavía ausente del escenario actual.
- **Compatibilidad:** conserva partidas anteriores y no altera retrospectivamente hechos históricos. Cambia únicamente la evaluación de nuevos pasos y decisiones. Se mantienen los límites del mundo físico y la libertad de Nilo para elegir proyectos.
- **Pruebas:** recuperación de la cueva tras actividad posterior, compactación de contexto, evidencia derivada y cierre de proyectos sin demostración.
- **Pendiente:** revisar los casos ya cerrados erróneamente sin cambiar la historia de la partida; probar corridas comparables (#3) y la calidad del ciclo de investigación (#5 y #13).

---

## Nilo 0.5.9.3.5 — «¿Qué me perdí?» por relevancia y «¿Qué más?»

- **Primera síntesis:** revisa todos los registros pendientes, no solo los 100 primeros; elige hasta siete acontecimientos según una clasificación editorial determinista, basada en tipo de hecho y contenido verificable, no en el orden de llegada.
- **Continuación:** «¿Qué más?» ofrece otras capas en orden de importancia no creciente, sin repetir los registros anteriores y sin incorporar eventos aparecidos después del inicio de ese resumen. El botón desaparece cuando solo queda actividad rutinaria.
- **Lectura exacta:** confirma únicamente los registros expresamente incluidos y enlazados en la respuesta, una vez montada la síntesis en pantalla. Los demás siguen sin leer; novedades nuevas no se pierden. Las distintas vistas de una misma conclusión conservan sus marcas de lectura.
- **Historial:** cada capa queda registrada como un resumen independiente, con fuentes trazables y fecha. El observador externo sigue sin intervenir en la memoria ni decisiones de Nilo.
- **Pruebas:** 150 eventos con un hecho importante en la posición 130, continuación sin repetición, sucesos nuevos durante la síntesis, deduplicación de hallazgos, ausencia de falsos marcados y conservación de actividad rutinaria.
- **Pendiente:** para estudiar el motor se propone un observatorio con métricas reproducibles [issue #19](https://github.com/mxlzz/Nilo_public/issues/19). Para un entorno urbano futuro: [issue #18](https://github.com/mxlzz/Nilo_public/issues/18).

---

## Nilo 0.5.9.3.4 — desplegables estables y lectura de enlaces internos

- **Desplegables:** todos los registros expandidos de Cuaderno, Novedades, Investigaciones, Ensayos, Creaciones, Propuestas, Agenda y demás solapas conservan su estado abierto al actualizarse los datos; incluye desplegables anidados y aparición de nuevos registros.
- **Lectura al navegar:** seguir un vínculo a un registro relacionado confirma como leído **el registro de origen**, no el de destino. Se mantiene la navegación, el estado persistente por solapa y el marcado explícito de toda la solapa. Soluciona [issue #15](https://github.com/mxlzz/Nilo_public/issues/15).
- **Pruebas:** regresión con Node.js para conservar un desplegable anidado cuando se insertan otros registros; comprobación de lectura de origen y compatibilidad con tarjetas y notificaciones anteriores.
- **Pendiente por separado:** [issue #16](https://github.com/mxlzz/Nilo_public/issues/16) recoge el rediseño de «¿Qué me perdí?» con relevancia decreciente y continuación «¿Qué más?». Este paquete **no altera** la selección ni las marcas de lectura de los resúmenes.

---

## Nilo 0.5.9.3.3 — contratos operativos y detección de limitaciones

- **Una sola fuente:** `action_contracts.py` documenta las 24 operaciones y genera la descripción que recibe el LLM; se elimina la acción redundante `manual` y el archivo `action_manual.py`.
- **Verificación automática:** las acciones `inspect`, `gather`, `use`, `experiment`, `build` y `modify` se contrastan contra una fotografía mínima del estado antes y después. El resultado queda asociado al ID original de acción: `conforme`, `uso_incorrecto`, `limitacion`, `posible_error` o `no_verificado`.
- **Diagnósticos trazables:** solo una contradicción comprobable puede generar automáticamente un informe en Propuestas → Diagnósticos; se adjunta la acción original y se evita duplicar solicitudes equivalentes. Los rechazos normales y los experimentos físicos negativos no se etiquetan como bugs. Los informes siguen sin modificar el código.
- **Autonomía preservada:** Nilo recibe códigos y resultados recientes; puede decidir investigar, replantear la operación o proponer una ampliación de la física. El motor no le revela recursos desconocidos ni recetas de fabricación.
- **Migración:** se descartan consultas `manual` pendientes de partidas 0.5.9.3.2, sin modificar construcciones, inventario o recuerdos. El historial previo no se reescribe.
- **Verificación:** nuevas pruebas de contratos, falsos positivos y trazabilidad; replay determinista actualizado para los nuevos metadatos de diagnóstico.

---

## Nilo 0.5.9.3.2 — manual, diagnósticos y correcciones del run

- **Manual operativo:** Nilo dispone de la acción `manual` (`{"op":"manual","target":"inspect"}`) para consultar instrucciones y límites reales sin revelar propiedades físicas desconocidas. Sin `target` ofrece el índice.
- **Inspección:** `inspect` identifica herramientas portátiles, construcciones fijas y terrenos por nombre, ID o coordenadas; distingue objetos fuera de alcance de elementos inexistentes. Ya no pierde terreno visible porque la percepción resumida muestre solo 18 hitos.
- **Proyectos:** `accion_proyecto="nuevo"` crea un ID nuevo aunque el modelo proponga uno anterior. El porcentaje de avance se puede revisar y no permanece forzosamente en 95 %. El cierre requiere evidencia real del proyecto y se advierte sobre varios ciclos de deliberación sin avances materiales.
- **Investigaciones y predicciones:** agrupación más sensible de preguntas relacionadas; el planificador identifica métricas que no puede medir antes de ejecutar un ensayo y comunica el límite sin cancelar la acción física. El descanso comparable permite verificar `energy_per_hour`.
- **Diagnósticos:** `report_issue` puede clasificar una anomalía como `uso`, `limitacion` o `error`, referenciar el manual y adjuntar acciones verificables. Propuestas tiene filtros Todas / Diagnósticos / Ampliaciones, sin nuevas pestañas ni cambios automáticos de código.
- **Repetición y archivo:** se evita seguir recolectando por encima de 12 porciones de alimento y se eliminan inserciones redundantes del historial SQLite. La secuencia histórica y las relaciones entre registros se conservan.
- **Compatibilidad:** instalá la nueva versión en otra carpeta, importá la partida anterior y conservá el respaldo. Los cambios se aplican a acciones futuras. Se actualizó el replay determinista porque el comportamiento de inspección y proyectos cambió de forma intencional.

---

## Nilo 0.5.9.3.1 — síntesis de pendientes y accesos rápidos

- **¿Qué me perdí?** genera mediante el LLM configurado una síntesis narrativa global de los registros **no leídos** del Cuaderno, Actividad y demás solapas. No utiliza la fecha del resumen anterior como punto de corte. El narrador es externo a Nilo y distingue creencias del personaje de mediciones físicas.
- **Lectura selectiva y segura:** el resumen se prepara sobre una selección inmutable de pendientes; solo tras mostrarlo se confirman como leídos exactamente los registros cubiertos. Cualquier novedad que aparezca mientras se genera sigue sin leer; si el LLM falla no se marca nada.
- **Historial:** los resúmenes se archivan en SQLite, con fecha, texto y referencias que permiten abrir fichas de origen. El historial no modifica el estado de lectura.
- **Lectura compartida:** los indicadores de las demás solapas se conservan en la partida (no exclusivamente en localStorage). Se migra la lectura anterior del navegador. Siguen funcionando tanto el clic individual en la tarjeta como «Marcar como leído» para toda la solapa; las conclusiones mostradas en Ensayos y Hallazgos comparten confirmación.
- **Interfaz:** se elimina el encabezado redundante «Archivo y pensamiento». «Resultados comprobados» pasa a «Conocimientos registrados» y cada conocimiento permite abrir su ficha en Hallazgos. Las herramientas de la columna central conservan sus datos y pasan a enlazar con su ficha concreta en Creaciones.
- **Compatibilidad:** los cambios afectan el historial del observador, no los pensamientos de Nilo ni las reglas de física. El resumen necesita un proveedor LLM configurado y consume una consulta del límite de chat; si no está disponible, los pendientes permanecen intactos.

---

## Nilo 0.5.9.3.0 — trazabilidad entre registros

- **Cuaderno:** se preserva íntegramente lo que escribió Nilo. Debajo aparecen enlaces únicamente a investigaciones, proyectos, predicciones, mediciones, diseños y propuestas vinculados por identificadores registrados, nunca por cercanía temporal o semejanza de texto.
- **Vínculos bidireccionales:** desde una prueba se puede volver al Cuaderno que originó su plan y desde una propuesta se puede recorrer su evidencia. Las relaciones se muestran en Investigaciones, Ensayos, Hallazgos, Propuestas, Creaciones y Proyectos.
- **Procedencia de las decisiones:** el motor añade a las acciones deliberadas el identificador de la entrada que dio lugar a ese plan. Las acciones automáticas, hábitos y tareas de agenda no se atribuyen a esa entrada sin motivo.
- **Archivo persistente:** SQLite mantiene índices de vínculos en ambos sentidos. `GET /api/record` recupera fichas antiguas incluso si ya no aparecen en la vista reciente, con su última revisión conservada y sin alterar el asiento original.
- **Compatibilidad:** en partidas previas solo se enlazan relaciones que ya tengan referencias explícitas; no se reconstruyen asociaciones especulativas. Las reglas físicas, necesidades y autonomía siguen funcionando como antes.
- **Validación:** pruebas de enlaces documentados, rechazo de coincidencias por fecha, origen real de decisiones, integridad de lecturas y reproducción determinista. El fingerprint de la partida de referencia cambia debido a los metadatos de procedencia.

---

## Nilo 0.5.9.2.9 — archivo organizado por procesos

- La columna de Archivo y pensamiento se reorganizó en **12 solapas visibles** y cuatro áreas: Vida (Cuaderno, Actividad, Memoria); Conocimiento (Investigaciones, Ensayos, Hallazgos, Creaciones); Autonomía (Proyectos, Agenda, Conducta); Interacción (Chat, Propuestas).
- **Actividad** reúne Novedades y Hechos mediante filtros Destacados/Todos. **Creaciones** reúne Inventos y Planos, manteniendo abiertos los saltos desde construcciones. **Investigaciones** incorpora Hipótesis y predicciones concretas. Versiones se consulta desde Configuración, sin perder historial.
- **Hallazgos** distingue conclusiones con mediciones y alcance declarado de las propiedades recientes registradas por el motor. No equipara toda observación con un conocimiento general probado.
- Memoria despliega los hitos conservados de cada etapa de 30 días y aclara que las preferencias son tendencias numéricas derivadas de reglas, no declaraciones personales.
- Proyectos muestra hitos, motivos, resultados recientes y si hay una estrategia por reconsiderar; los contadores ya dicen «últimos resultados conservados». Agenda prioriza pendientes y evita avisos duplicados por registros de sus mismos pasos. Conducta distingue las acciones realizadas sin nueva deliberación.
- Ensayos separa pruebas deliberadas de todas las mediciones mediante un filtro, preservando acceso contextual a registros históricos.
- **¿Qué me perdí?** ya no formula una pregunta genérica al chat: lista registros pendientes reales de la solapa elegida. En Cuaderno y Actividad consulta además el archivo SQLite histórico con `GET /api/unread`, sin cambiar marcadores de lectura. Las entradas antiguas fuera de la vista reciente pueden consultarse y marcarse individualmente.
- Se conservan partidas, registros, físicas, decisiones y propuestas. Cambia la presentación y se habilita lectura archivada; no se agregan mecánicas ni se altera la autonomía.

---

## Nilo 0.5.9.2.8 — navegación contextual y registros legibles

- **Construcciones → Planos:** «Ver plano, componentes e historial» abre la ficha de la construcción seleccionada y todas sus revisiones, con desplazamiento a ese registro; no obliga a buscarlo otra vez.
- **Barra de lectura:** se retira «Hay registros nuevos» / «Sin novedades nuevas»; «Marcar como leído» queda a la izquierda, «¿Qué me perdí?» centrado e «Indicador» a la derecha. El modo Discreto solo cambia los avisos de navegación: las tarjetas pendientes conservan el mismo fondo que en Normal.
- **Planos y Agenda:** desaparecen respectivamente «Identificadores técnicos» e «Información técnica». Los datos permanecen en la simulación, sin alterar el motor.
- **Referencias a mediciones:** se sustituyen códigos como `med-b3b051dd68ab` en proyectos, resultados de agenda, conclusiones, investigaciones y propuestas por enlaces descriptivos «Ver ensayo · ...». Al tocarlos se abre el ensayo exacto y, si ya no figura entre los últimos registros, se recupera del SQLite histórico mediante `GET /api/measurement?id=...` sin alterar la partida. Los IDs siguen disponibles dentro de la información técnica propia de Ensayos cuando sean necesarios para diagnóstico.
- **Cabecera del mundo:** se elimina el título redundante «Mundo conocido» y se compactan el nombre de nivel, las coordenadas y el selector de mapa en una línea cuando el ancho lo permite.
- **Mapa:** los símbolos de suelo, hierba, arena, sendero y galería se muestran al 50 % de opacidad, sin apagar el fondo del rastro ni los símbolos de construcciones y recursos.
- Cambios de presentación y consulta de archivos históricos; sin ajustes de física, conocimiento, decisiones autónomas ni reglas de Nilo.

---

## Nilo 0.5.9.2.7 — lectura directa, indicadores por solapa y mejor contraste del mapa

- **Lectura por tarjeta:** se eliminan las casillas y los botones ✓. Al hacer clic en una tarjeta pendiente se marca como leída; Cuaderno y Novedades conservan lectura individual en SQLite y las demás solapas continúan usando firmas locales. Abrir los desplegables de esas solapas no los cierra por culpa del marcado.
- **Marcar como leído:** las solapas que guardan marcas locales también retiran inmediatamente sus fondos de novedad. Antes podían conservarlos hasta otro cambio o navegación.
- **Indicadores:** el selector Normal / Discreto / Oculto aparece junto a «Marcar como leído» y modifica solo la solapa activa. Sigue sincronizado con Configuración → Indicadores y con las preferencias portables.
- **Mapa:** las piedras usan tonos de pizarra azulados para separarlas visualmente del rastro ámbar; se atenúan los símbolos de suelo y hierba en los tres temas.
- **Investigaciones:** «resultados vinculados» ahora se muestran como registros de acciones asociados a una investigación activa, con fecha y hechos concretos en un desplegable. Cuando existe una conclusión, se enumeran las mediciones citadas que siguen disponibles. La asociación no implica que la hipótesis esté comprobada.
- Solo cambios de interfaz, documentación y pruebas; no se alteran las reglas físicas, la cognición ni el contenido de la partida.

---

## Nilo 0.5.9.2.6 — Ensayos y Agenda legibles

- **Ensayos:** títulos que traducen códigos de operaciones a acciones comprensibles. Un `go` con posición final registrada aparece como **«Desplazamiento hasta (x, y)»**; si el desplazamiento no ocurrió, no afirma llegada. Un recorrido con tramos informados por el motor muestra «6 tramos recorridos · 18,13 min». Las acciones restantes utilizan nombres como «Registrar conclusión», «Recolectar · piedra» o «Descanso en refugio».
- **Separación entre ejecución e interpretación:** «Acción completada» describe el estado de la operación, no prueba la hipótesis estudiada. Los códigos `go`, `med-...` y otros campos operativos se conservan en el desplegable «Información técnica», sin modificar los registros.
- **Agenda:** condición de activación en lenguaje natural (p. ej. «Después de 60 min simulados desde que se programó»), objetivo declarado, pasos ejecutados y resultados efectivamente registrados por el motor en apartados separados. La indicación de tiempo **no significa una duración de descanso**.
- **Control de ambigüedad:** si una tarea de recuperación/descanso únicamente ejecutó `conclude` y no incluyó pasos `rest` ni `compare`, la ficha explica que «Secuencia completada» no acredita una comparación de descanso. Si las evidencias vinculadas visibles corresponden a otro tipo de ensayo, también lo informa.
- El JSON de condiciones, IDs y pasos sigue disponible en un detalle técnico desplegable; se conserva como fuente de diagnóstico. La clasificación de las mediciones y la partida SQLite permanecen intactas. **No se alteraron reglas de agenda, leyes físicas ni decisiones del LLM.**

---

## Nilo 0.5.9.2.5 — preferencias portables, novedades por registro y planos legibles

- **Preferencias junto con la instalación:** desde esta versión se guarda `preferencias_interfaz.json` en la carpeta de Nilo (solo opciones visuales, sin claves ni memoria del agente). Guarda tema, zoom Cerca/General, modo del mapa, nivel, rastro, notificaciones e indicadores por solapa. La página conserva las opciones de navegador; al abrir, combina ajustes locales con el archivo del servidor y sincroniza cambios, sin consultas al LLM. Durante el primer inicio o importación manual se importa ese JSON si la instalación anterior lo tenía y el destino no lo tiene.
- **Compatibilidad importante:** las versiones **anteriores a 0.5.9.2.5** solo almacenaban estos ajustes en el `localStorage` del navegador. Si se usa el mismo navegador y dirección/puerto, la nueva versión puede leerlos y crear la copia portable. Si se cambia de navegador, ordenador u origen, la importación de una carpeta antigua **no** puede recuperar automáticamente el antiguo `localStorage`: no existe un archivo del que copiarlo. Esas preferencias se pueden volver a configurar o recuperar abriendo primero la versión nueva en el navegador que aún las conserva.
- **Elementos nuevos y actualizados:** Cuaderno y Novedades muestran una tarjeta completa de fondo sutil para registros sin leer; cada entrada tiene una casilla individual de leído. Se elimina «Leído hasta aquí». Cuaderno usa lectura individual persistida en SQLite: marcar una nota no implica marcar otras.
- Las demás secciones muestran tarjetas de registros nuevos o actualizados según las firmas estables del seguimiento local, con un botón discreto para confirmar individualmente cada registro. La selección por solapa y la visualización de indicadores Normal/Discreto/Oculto siguen independientes de la lectura. La primera apertura en un navegador no inventa un histórico de novedades anterior.
- Las introducciones explicativas de Planos, Propuestas, Hipótesis, Ensayos, Agenda y Versiones quedan debajo cuando existen registros; **Memoria** conserva Etapas de vida y Preferencias desarrolladas arriba.
- **Construcciones del mundo** pasa a ser una ficha resumida de ubicación, estado y propósito con acceso a **Laboratorio → Planos**. Esta última conserva los componentes y las revisiones.
- En **Planos**, las herramientas portátiles ya no muestran la huella genérica del motor como metros cuadrados medidos. Los IDs de objetos y componentes pasan a un desplegable «Identificadores técnicos». Los esquemas de herramientas siguen siendo descripciones de piezas sin escala; se corrige «1 lote» en singular.
- No se modificaron la física, los efectos de las herramientas ni la partida SQLite. El modelo abstracto de dimensiones genéricas para herramientas continúa en el motor y requiere una revisión separada antes de atribuirles tamaño físico verificable.

---

## Nilo 0.5.9.2.4 — descarga versionada e importación desde otra carpeta

**Para descargar:** usá [GitHub Releases](https://github.com/mxlzz/Nilo_public/releases) y elegí el archivo `Nilo-0.5.9.2.4.zip`. Al descomprimirlo se crea una carpeta `Nilo-0.5.9.2.4` que contiene `INICIAR_NILO.bat`.

**Importante:** la función automática **Code → Download ZIP** de GitHub siempre genera `Nilo-main.zip` (y `Nilo-main/` dentro) cuando descargás la rama principal. Ese nombre lo elige GitHub; para tener el nombre de versión, descargá el ZIP de **Releases**. Una nueva versión que cambia `VERSION` y supera las pruebas crea/publica su propio paquete mediante el workflow `.github/workflows/paquete.yml`. Alternativamente, desde el código fuente es posible crear el mismo paquete con `python empaquetar_version.py`.

**Primer inicio:** el menú ahora muestra `0. Elegir otra carpeta (también sirve la letra O)`. Ambas opciones permiten pegar la ruta completa de una instalación anterior (por ejemplo `Nilo-main` o `Nilo-0.5.9.2.3`) y luego elegir si importar una copia de la base SQLite. El detector ya no usa una lista cerrada de nombres: reconoce carpetas `Nilo*` en ubicaciones cercanas y habituales. Si se elige importar, pero la ruta está vacía o se escribe una opción inválida, la configuración se cancela con un mensaje de error; **no** se inicia silenciosamente un mundo nuevo.

`N` sigue significando **nuevo mundo**, sin importar. El origen no se modifica ni se mueve. La selección de carpeta e importación se ofrece al **primer arranque de una carpeta nueva**, antes de crear el archivo de partida. El asistente no vuelve a solicitar una importación una vez configurada la instalación.

**Distribución sin datos personales:** los ZIP solo incluyen archivos declarados en `MANIFIESTO_SHA256.json`, sin `config.env`, claves, mundos `.sqlite3`, historiales privados, motores Python descargados ni respaldos. Se conserva `config.env.example` para la primera configuración. La generación usa solo Python estándar y los archivos necesarios del repositorio.

---

## Nilo 0.5.9.2.3 — columna única de mundo y avisos configurables

- **Columna Mundo conocido:** un único desplazamiento vertical para mapa, referencias, materiales, herramientas y construcciones. Se eliminan alturas y scrolls verticales independientes del mapa, las referencias y los recursos. El mapa puede seguir desplazándose **horizontalmente** cuando su tamaño excede el ancho disponible.
- **Vista del mapa:** selector persistente con tres modos: **Mapa y referencias**, **Solo mapa**, **Ocultar ambos**. Los recursos permanecen siempre visibles; se respeta la preferencia antigua de mapa oculto al migrar.
- **Botonera:** Cerca / General / Rastro / zoom y selector Nivel con tamaño compacto equivalente a los controles de velocidad.
- **Configuración → Indicadores:** cada subpestaña tiene preferencia independiente: **Normal** (punto rojo y señal en pestaña madre), **Discreto** (punto tenue sin activar la madre), u **Oculto** (ninguna señal). Solo cambia la presentación, no las lecturas ni el contenido; se guarda por navegador.
- **Una acción por solapa:** se elimina **Marcar todo como leído** y se unifica en **Marcar como leído**. Cuaderno y Novedades marcan solo esa categoría en el servidor; las otras pestañas guardan confirmación local. **Propuestas** se marca vista, pero ninguna decisión pendiente se acepta ni rechaza.
- **¿Qué me perdí?:** disponible en las pestañas de contenido; abre Chat con una pregunta previamente redactada que menciona la subpestaña de origen y pide separar hechos, hipótesis y pendientes. **No envía** la consulta automáticamente.
- **Sliders/barra de desplazamiento:** el color de las barras verticales y horizontales sigue las variables de tema Bosque, Grafito y Terracota en navegadores compatibles (scrollbar-color y WebKit).

Actualización de **interfaz solamente**: no cambian el motor físico, memoria SQLite, reglas de recolección ni comportamiento autónomo de Nilo.

---

**Próximas versiones e ideas todavía abiertas:** [Índice de futuros caminos](docs/FUTUROS_CAMINOS.md) · [Roadmap técnico](docs/ROADMAP_0571.md). Las ideas no equivalen a funcionalidades implementadas ni autorizan cambios automáticos.

---

## Nilo 0.5.9.2.2 — recolección comprobada y fuentes inequívocas

Corrección basada en el run 0.5.9.2 (seed **7321**) en el que `gather piedra` solo acercaba a Nilo a la roca en (5,17) sin entregar piedra, mientras `gather afloramiento mineral` extraía madera de una arboleda cercana.

- **Recolección con resultado real:** la navegación hacia una fuente no acredita por sí sola la extracción. Al alcanzar el punto de trabajo, la misma operación continúa con la extracción comprobada; solo entonces `gather` tiene estado de éxito. Cuando el camino se interrumpe o supera el tramo disponible, registra explícitamente que no recogió material.
- **Destinos precisos:** nombres de materiales y alias exactos de terrenos conocidos (`piedra`/`roca`, `mineral oscuro`/`afloramiento mineral`, `madera`/`arboleda`, etc.). Un nombre desconocido no extrae ningún material de un depósito vecino por defecto.
- **Inspección coherente:** `inspect piedra` encuentra una `roca` observable, sin inventar que haya entregado piedra.
- **Corrección de inferencias pasadas:** el contexto de la deliberación identifica resultados antiguos incompatibles con la cantidad de material realmente ingresado al inventario (por ejemplo, acercamiento sin extracción, o madera obtenida al solicitar afloramiento mineral). Se mantienen intactos esos resultados y la memoria autobiográfica; el motor no sustituye el juicio de Nilo.
- No se alteraron los rendimientos de depósitos, las propiedades materiales ni las condiciones de acceso. No se modifica la base SQLite al entregar la nueva versión.

Los tests ejercitan exactamente las posiciones **(5,17), (5,18), (7,14) y (7,15)** del seed 7321 y un ciclo real de navegación/ejecución. La partida original sirve como diagnóstico; no se incorpora ni se publica en el repositorio.

---

## Nilo 0.5.9.2.1 — ajustes de interfaz

- **Notificaciones discretas:** un punto rojo en la subpestaña con actividad nueva y en su pestaña madre. No se cambian los colores base de las solapas. Se conservan los marcadores persistentes del motor para **Cuaderno** y **Novedades**, y la condición `pendiente` de **Propuestas**; las demás secciones admiten «Marcar como revisada», una confirmación explícita, no desaparecen por solo abrir la pestaña. El seguimiento de estas otras secciones se almacena localmente en el navegador, con línea base inicial al abrir la versión para no inventar novedades antiguas.
- **Mapa opcional:** botón Mostrar/Ocultar mapa. Agrupa mapa, controles y referencias; mantiene materiales, herramientas y construcciones. La preferencia se conserva en el navegador.
- **Configuración:** ahora contiene dos subpestañas **Avisos** y **Modelo y consultas**. El estado abreviado de la conexión LLM permanece en «Nilo ahora»; el detalle de proveedores, tokens y botón de reintento pasó a Configuración.
- **Altura de la pantalla:** escritorio amplio (al menos 1181 px de ancho y 680 px de alto) ajusta las tres columnas a la altura disponible y conserva el desplazamiento dentro de paneles extensos, evitando que sea necesario desplazar la página completa. En móvil y ventanas estrechas se mantiene el desplazamiento normal.
- **Alcance:** exclusivamente frontend, sin cambiar persistencia SQLite, física, autonomía, decisiones del LLM, ni las reglas de revisión humana.

---

## Nilo 0.5.9.2 — hipótesis, predicción y contraste verificable

Nilo puede asociar a una operación de experimentación una predicción previa mediante el campo opcional `prediction` (`hypothesis`, `expected_effect`, y opcionalmente `metric`, `operator`, `threshold`). El motor registra la predicción **antes** de ejecutar el paso y después confronta el valor esperado únicamente con `ActionResult.physical.metrics`, sin interpretar hechos redactados. No modifica las leyes físicas ni añade llamadas obligatorias al LLM.

**Estados posibles:** `prediccion_coincide`, `prediccion_no_coincide`, `variable_no_medida`, `sin_modelo_evaluable`, `criterio_incompleto`, `prediccion_cualitativa`. La coincidencia de una métrica no prueba la causalidad ni confirma objetivos más amplios. Por ejemplo, medir `retencion_pct` de agua **no** comprueba pureza o retención de partículas; una predicción sobre `particulas_retenidas_pct` permanecerá **sin medir** si esa variable no es calculada por el motor.

Historial técnico y cognitivo accesible en **Laboratorio → Hipótesis**. Cada entrada enlaza a la medición y acción real, si existen, y conserva en `history_revisions` el registro previo a la ejecución. Nilo recibe un resumen limitado en la siguiente deliberación para reconsiderar la hipótesis sin exigirle que solicite nuevas leyes. Se mantiene el protocolo: Nilo investiga y propone; **el observador decide** qué implementar.

Los runs anteriores no reciben hipótesis retroactivas. Próximos hitos: 0.5.9.3 revisión estratégica bajo circunstancias significativas y 0.5.9.4 evaluación comparativa de runs.

---

## Nilo 0.5.9.1 — historia de versiones dentro de cada partida

Cada arranque registra una sesión real en la **misma base `nilo_mundo.sqlite3`**, tablas `engine_sessions` y `session_model_usage`. Contiene versión leída del archivo `VERSION`, UTC de inicio/último guardado/cierre normal, minutos simulados al comienzo y al final, escenario, entorno, commit Git (cuando exista) y SHA256 del manifiesto de archivos. También cuenta por sesión qué proveedor y modelo respondieron **efectivamente** en deliberaciones y conversaciones; el modelo configurado al inicio se registra por separado.

**Interfaz:** Diario → **Versiones**. Las partidas existentes empiezan a acumular historial cuando se abren con 0.5.9.1: no se inventa qué versión ejecutó las etapas anteriores. Si un proceso se interrumpe sin cierre registrado, el historial informa eso, sin afirmar un fallo. En ZIP sin metadatos Git el commit queda «no disponible» (no se infiere). Ninguna clave API, conversación ni mapa oculto se registra en estas tablas.

El historial es técnico: no cambia reglas físicas ni memoria del agente. Antes de abrir una partida valiosa con otra versión, respaldar la base desde los scripts existentes. Las pruebas verifican migración no destructiva, persistencia y replay. Próximo hito **0.5.9.2**: relación estructurada hipótesis → predicción → prueba → propiedades verificadas; luego **0.5.9.3** revisión estratégica y **0.5.9.4** comparación de runs. Las mejoras futuras no habilitan autoaprobación ni modificación de código por Nilo.

---

## Nilo 0.5.9.0 — autodiagnóstico y revisión

Nilo distingue la solicitud de **una nueva ley física** (`propose`) de una **posible anomalía** (`report_issue`). El motor revisa automáticamente ciertos invariantes inequívocos, como inventario negativo, necesidades fuera de rango, posición inválida o contradicción entre éxito y estado tipado. Solo abre una **solicitud pendiente de revisión**; no concluye que se trata de un bug ni lo corrige.

En la interfaz: **Vínculo → Propuestas → Exportar informe JSON**. El paquete adjunta únicamente evidencias registradas por el motor, contexto de revisión y un procedimiento orientativo. No contiene claves de API ni el mundo oculto. Su SHA256 verifica integridad de contenido, no su interpretación.

**Gobernanza acordada:** Nilo investiga y redacta solicitudes; el observador las lee y las discute con ChatGPT. Solo el observador decide si corresponde ampliar una ley física, investigar una anomalía o descartar la solicitud. Si decide modificar el programa, ChatGPT puede ayudar a diseñar y escribir los cambios **con su autorización explícita**, en una rama de trabajo, con tests y replay antes de integrarlos. **No se incorporará un agente desarrollador que examine, apruebe o modifique automáticamente el código.** Aceptar una propuesta en la interfaz es una decisión conceptual; no instala física ni autoriza por sí sola cambios de código. Véase `docs/PROTOCOLO_REVISION_HUMANA.md`.

Detalles, límites y ejemplos: `docs/DIAGNOSTICO_0590.md`.

---

## Nilo 0.5.8.3 — ActionResult

El motor comienza a emitir resultados tipados: estado de evaluación, hechos y, cuando corresponde, evidencia física derivada de pruebas registradas. Esta evidencia se archiva en `action_outcomes[*].action_result` y se incorpora al contexto de deliberación del LLM. Las entradas del cuaderno y los textos de narración siguen siendo texto libre, pero **no** otorgan propiedades ni medidas físicas.

Consulta `docs/ARQUITECTURA_0583.md` para el contrato, ejemplos y límites de la migración gradual.

---

## Nilo 0.5.8.2 — Módulos y apariencia

La validación física de planes y los filtros de acciones redundantes ahora pertenecen al entorno (`island_planning.py` para `isla_v1`) y se invocan mediante `Environment`. No cambian las leyes físicas ni el formato de las partidas.

**Mapa:** suelo/hierba discretos, muros/roca con más contraste para comunicar solidez y evitar confundir obstáculos con casillas transitables. Agua, minerales y señales conservan sus códigos de color.

**Colores de interfaz:** selector «Tema» en la cabecera, con **Bosque** (predeterminado), **Grafito** (neutro frío) y **Terracota** (cálido). Se recuerda por navegador sin afectar la simulación.

**Validación:** `python -m unittest discover -s tests -v`, `python validar_escenarios.py --seed 7321` y `python reproducir.py tests/fixtures/replay_basico.json`.

---

## Nilo 0.5.8.1 — Vista del mundo desacoplada

La simulación obtiene las **condiciones físicas locales** y la **proyección del mapa** a través de `Environment`, en lugar de interpretar estos detalles en el coordinador. Las reglas actuales de `isla_v1` están en `island_views.py`. No hay cambios de jugabilidad ni del formato de las partidas guardadas. Detalle de límites y contratos: `docs/ARQUITECTURA_0581.md`.

Las comprobaciones incluyen `python -m unittest discover -s tests -v` y los escenarios/replays de la CI. La separación de mundos es gradual: **aún no hay un segundo mundo jugable**.

---

# Nilo 0.5.8 — Separación inicial de Nilo y su mundo

La inteligencia, el escenario de partida y la implementación del mundo ya tienen módulos diferenciados: `agent.py`, `scenarios.py` y `environments.py`. El escenario por defecto conserva el mismo mundo, materiales, posición y equipo que la 0.5.7.3. Se agregó `territorio_sin_equipo` como condición inicial alternativa sobre la misma física.

El núcleo consulta el adaptador del entorno para deliberar, validar destinos, navegar y ejecutar efectos. La memoria del agente vive en `person` y no se reinicia al recargar su partida. Las partidas heredadas obtienen el escenario original de manera no destructiva.

**Límites:** el motor de necesidades, muchas validaciones, las migraciones y el mapa de la interfaz todavía dependen de `isla_v1`. Un mundo urbano, extraterrestre o social requerirá adaptadores y reglas físicas/sociales nuevas; no está implementado ni es seleccionable desde la interfaz actual.

En Python puede crearse una partida nueva con `Simulation(db_path="otra_partida.sqlite3", scenario_id="territorio_sin_equipo")` y ejecutarla de forma aislada. Si ya existe un snapshot, prevalece su escenario guardado. El replay admite el campo JSON `scenario_id` para ensayar inicios alternativos sin API.

---

# Nilo 0.5.7.3 — Cuaderno a ×2 temporal

Cuando el simulador está a ×10 o ×60, escribir se reproduce a ×2 (tanto la velocidad visible como el tiempo de Nilo), sin alterar la selección. En ×1 escribe normalmente. Al terminar, el tiempo vuelve a la velocidad seleccionada; pausar o cambiarla durante la escritura funciona de inmediato.

Las partidas y las leyes físicas siguen siendo compatibles con 0.5.7.2.

---

# Nilo 0.5.7.2 — Reproducción de decisiones y reloj controlado

Esta revisión continúa **sobre la versión 0.5.7 definitiva**. Permite comprobar el resultado de una secuencia de decisiones sin gastar créditos de un LLM.

- `reproducir.py`: carga un archivo JSON con respuestas del LLM, semillas del mundo/agente/UUID, reloj Unix inicial, tamaño de cada intervalo y cantidad máxima de ticks. Ejecuta el mismo `plan_ready` y `tick` que la aplicación.
- Aísla las pruebas en SQLite temporal. No utiliza `config.env`, el servidor web ni la base `nilo_mundo.sqlite3` del usuario.
- Emite hashes SHA256 del **estado completo**, del **archivo SQLite** y del conjunto de ambos. El atributo opcional `expected_fingerprint` permite detectar divergencias inmediatamente.
- Desde esta versión las deliberaciones reales posteriores quedan registradas en la categoría local `llm_decision` de SQLite (decisión normalizada, proveedor, modelo, minuto del mundo y huella del contexto).
- No se afirma todavía que estas pruebas reconstruyan una vida histórica real: haría falta conservar estado inicial, llamadas, intervenciones humanas y temporización efectiva. La reproducción actual comienza en un mundo controlado por semilla.
- No se alteran las reglas físicas, ni las partidas anteriores.

**Uso en Windows**, desde la carpeta descomprimida de Nilo: ejecutar
`python\\python.exe reproducir.py tests\\fixtures\\replay_basico.json`
una vez preparado el Python portable. También se puede usar `python reproducir.py ...` si Python ya está instalado. Para guardar el informe, añadir `--output reporte.json`.

**Validación:** `python -m unittest discover -s tests -v`, `python validar_escenarios.py --seed 7321` y el comando anterior. El workflow de GitHub ejecuta estas pruebas sin claves de API.

---

# Nilo 0.5.7.1 — Métricas verificables de actividad

Esta actualización se desarrolla **sobre la versión definitiva 0.5.7**, no sobre el primer intento `0.5.7-alpha.1`. La primera implementación se conserva en `archive/0.5.7-alpha.1`; la definitiva corresponde a `release/0.5.7` y sirve de base para `main`.

- Las acciones finalizadas alimentan `behavior.py`, que registra tipo de acción, origen (LLM / rutina / espera / agenda / motor), duración **sólo si hay medición**, novedad verificable, destinos revisados y cambios de proyecto.
- Los indicadores aparecen en **Autonomía → Hábitos** y llegan al LLM como contexto factual. No miden personalidad, interés ni creatividad; tampoco atribuyen razones que no hayan sido observadas.
- El registro arranca con esta versión: las partidas antiguas siguen intactas y las acciones previas no se inventan ni retrocalculan.
- Las verificaciones de herramienta que dispara el motor sin un nuevo LLM están señaladas como origen `motor`.
- Pruebas agregadas: `python -m unittest discover -s tests -v` y `python validar_escenarios.py --seed 7321`. La batería completa debe ejecutarse en una máquina con Python; el código publicado no constituye, por sí mismo, un resultado de ejecución.
- La 0.6 seguirá reservada al cambio general de física. Antes quedan pendientes la reproducción completa de deliberaciones y la eliminación de los módulos que todavía interpretan texto como resultado.

**Distribución:** el código de la 0.5.7.1 queda versionado en GitHub. Para una instalación local, descargá el código de esta versión en una carpeta nueva, ejecutá `INICIAR_NILO.bat` e importá una copia de tu partida anterior. No sobrescribas la base original.

---

# Nilo 0.5.7 — Consolidación técnica, mapa multicapa y pruebas reproducibles

Esta es una **versión de estabilización**, no el nuevo motor físico general planeado para 0.6.

- **Navegación honesta:** `go`, rutas a orillas, recursos y exploración no calculan caminos por casillas no descubiertas; las órdenes a coordenadas desconocidas informan incertidumbre sin filtrar si hay roca o suelo. La vuelta de la cueva mantiene las rutas conocidas.
- **Compuestos físicos:** los materiales combinados ahora conservan densidad y permeabilidad derivadas de sus ingredientes y el motor las usa al fabricar objetos. No se simula todavía transformación térmica ni porosidad dinámica; el dato previo de partidas antiguas usa valores de compatibilidad.
- **Contexto compacto:** mantiene identidad del proyecto y conclusiones incluso en el proveedor de respaldo. Puede superar el presupuesto orientativo de caracteres, pero no suprime silenciosamente esos hechos.
- **Planes:** si el modelo propone únicamente pasos descartados, el motor registra el bloqueo y solicita reconsideración, sin inyectar una exploración atribuida a Nilo.
- **Diagnósticos más estructurados:** los resultados nuevos incluyen estado tipado, deltas numéricos, posiciones y enlace al ID de medición, además del texto narrativo. Es una transición: todavía quedan módulos heredados que procesan cadenas; no se considera terminada la refactorización.
- **Archivo:** lectura masiva de identificadores y marcadores en vez de centenares de SELECT por sondeo. Los históricos conservan sus IDs y estado de lectura.
- **Interfaz:** selector para observar superficie/cueva independientemente de dónde esté Nilo; distingue la casilla `@` cuando contiene construcciones y conserva todas las obras superpuestas. Cuatro áreas de navegación (Diario, Laboratorio, Autonomía, Vínculo). Velocidades y pausa accesibles en la cabecera.
- **Validación:** `PROBAR_MOTOR.bat` ejecuta escenarios físicos deterministas sin usar credenciales ni cuotas de LLM. Es un arnés inicial de escenarios, **no un replay íntegro** de deliberaciones.

**Compatibilidad:** instalar en carpeta nueva e importar una copia de la base desde 05.6.3 o anteriores. No se migra ni altera el archivo de origen. Respetar las restricciones de ejecución del equipo Windows.

---

# Nilo 05.7 — Autonomía y planificación persistente

- **Agenda diferida:** cada deliberación puede añadir hasta seis tareas con pasos y condiciones verificables (tiempo, materiales o necesidad). El motor revisa los prerrequisitos antes de ejecutarlas y suspende la secuencia si alguna acción falla. Solo admite procedimientos seguros dentro del repertorio existente y rutas conocidas.
- **Reconsideración efectiva:** la reiteración de intentos sin progreso activa la memoria de estrategias agotadas. Los planes que solo repiten ese método se descartan; una nueva estrategia puede desbloquearlo si produce resultados. No se generan automáticamente ideas creativas.
- **Proyectos e investigaciones:** se vuelven a consolidar preguntas equivalentes sin borrar ninguna entrada. El objetivo inicial de explorar y localizar agua se cierra únicamente cuando hay agua observada, recorrido suficiente y acción de beber verificada; otras metas siguen siendo decisiones de Nilo.
- **Inspecciones exactas:** pedir agua no puede devolver una arboleda como resultado; si el objetivo no es visible, se informa el fallo.
- **Gestión de espera:** distingue descanso real de inactividad; al agotarse los proveedores, el tiempo simulado puede detenerse automáticamente cuando no hay tareas útiles. Las tareas futuras con hora pendiente mantienen el reloj en marcha. El sistema vuelve a consultar tras las esperas reales de API.
- **Reintento manual:** botón con límites de cuota/429, autorización, tamaño de solicitud e intervalo mínimo; no reinicia contadores. Se muestran intentos, éxitos y fallos por proveedor.
- Se preservan las funciones y la física de 05.6.2. La agenda **no simula creatividad sin LLM**: sigue exclusivamente procedimientos elegidos y comprobados en el mundo. No se introducen peligros, termodinámica ni recursos ficticios.

# Nilo 05.6.2 — Regreso de cuevas y física no implementada

- La salida de cueva aparece como `e` en el subsuelo (visible solo si está descubierta). Los mundos antiguos se migran sin restablecer terreno, inventario ni cuadernos.
- `ascend` desde una galería distante calcula el regreso por casillas **ya conocidas**; una ruta bloqueada no autoriza teletransporte ni ascenso. La vuelta puede planificarse junto con una búsqueda de agua posterior.
- Ante hidratación menor al 40 % y con fuerzas suficientes, los hábitos pueden escoger regresar de la cueva si conocen la ruta.
- Ensayos explícitos de condensación, evaporación o técnicas que no tienen modelo producen el resultado **FÍSICA NO IMPLEMENTADA**, no un fracaso físico. No se inventa agua. Se conservan registros y se pueden adjuntar a una propuesta de ampliación; solo la persona decide aprobarla.
- En el mapa se diferencia la salida, el piso de galería y la pared con contraste de fondo.
- No se incorporaron todavía las leyes de humedad, calor, evaporación y condensación.
- Edición portable: primer inicio descarga Python embebido si todavía no está en la carpeta; requiere Windows que permita ejecutar este tipo de programas y conexión inicial para obtener el intérprete.

# Nilo 05.6.1 — Laboratorio general y autonomía cotidiana (experimental)

- Laboratorio comparativo con `compare`: contrasta 2–6 ensayos cuantificados del mismo fenómeno y método. Únicamente se liberan métricas después de experimentos realmente ejecutados: dureza y resistencia de materiales; retención de recipientes; empuje/flotación; carga y transmisión de ensamblajes. Son unidades abstractas y las conclusiones **no prueban causalidad** ni física fuera del motor.
- Registros `measurement` y `conclusion` se guardan en SQLite y aparecen en Ensayos. Un LLM no puede introducir valores por narración; se exigen IDs de ensayos reales.
- Ritmos metabólicos menos invasivos; comer/beber desde reservas continúa mediante rutinas locales. Abrigo y seguridad no disminuyen por el mero paso del tiempo en ausencia de clima o riesgos simulados.
- Registro del tiempo dedicado a tareas repetitivas: Nilo recibe un resumen compacto de mantenimiento y puede decidir si investiga alternativas, sin imponerle inventos concretos.
- Compatible con la partida anterior: descomprimí en una nueva carpeta y recuperá una copia de la partida desde el asistente.
- Continúan fuera del alcance: agricultura, animales, ecología compleja y motor 3D.

## Nilo 05.5 · Ensayos medibles y cierre de investigaciones (2026-10-26)

- Recuperación energética **deliberada** al ejecutar `rest`: separada de la recuperación residual mientras Nilo espera, escribe o delibera. El motor sigue aplicando el mismo deterioro metabólico general.
- Toda acción física nueva registra valores iniciales/finales, posición, duración, inventario, delta corporal, éxito y hechos comprobados; los ensayos permanecen en `history` (SQLite) aunque la pantalla muestre un tramo reciente.
- Los descansos se consideran comparables solo si duran al menos 15 minutos, no llegan al límite de recuperación, se mantienen en un mismo sitio y permanecen en la misma condición de refugio o intemperie. Los casos que no cumplen los criterios también quedan archivados, identificados como no comparables.
- Una obra identificada como refugio sólo pasa de prototipo a «descanso observado» después de una prueba; la etiqueta «mejora de descanso comprobada» requiere comparación válida con descanso exterior. No demuestra otras propiedades (impermeabilidad o seguridad).
- Con datos adecuados de **ambas** condiciones se incorpora una conclusión descriptiva con las dos pruebas enlazadas, se cierra la investigación correspondiente y Nilo recibe la conclusión y la indicación de evitar repetirla sin nuevas variables. Si no hay muestras suficientes, recibe un diagnóstico de lo que falta, sin inventar resultados.
- Pestaña **Ensayos**: mediciones y conclusiones auditable; la pestaña Investigaciones identifica las conclusiones demostradas. El chat accede a mediciones recientes.
- Se mantienen la compatibilidad de partidas y la edición portable. El sistema no afirma causalidad universal ni generaliza a climas/terrenos que todavía no simula. No existe editor de leyes físicas.

## Nilo 05.4 · Propuestas de depuración y lectura al abrir

- `report_issue`: Nilo puede solicitar la revisión de una posible inconsistencia entre lo esperado y lo observado. El motor adjunta únicamente evidencias verificables de acciones ejecutadas; no inventa registros. Se puede presentar una sospecha aunque no haya evidencias, que queda explícita como tal.
- Evaluación humana: error confirmado pendiente de corrección, limitación válida, capacidad ausente, interpretación equivocada o necesidad de más evidencia. La clasificación se conserva en la base de datos y se proporciona a Nilo para reconsiderar hipótesis. No cambia el motor ni instala código.
- Resultados de acciones verificadas persistidos como diagnósticos; compatibilidad con partidas anteriores y seguimiento en el historial.
- Abrir el detalle de una Novedad la marca como leída automáticamente (avanzando el marcador cronológico), conservando su contenido y el desplegable abierto.
- No introduce el editor de nuevas leyes físicas ni modifica las reglas materiales.

## Nilo 05.3.1 · Orillas accesibles y novedades sin redundancia

- `go` admite `{"op":"go","target":"agua"}` para localizar la orilla **conocida y alcanzable** más próxima. Si se solicita una casilla de agua conocida por coordenadas, busca la orilla accesible de ese mismo cuerpo de agua. No permite caminar sobre agua ni implica que exista conexión subterránea.
- Los fracasos de navegación indican el motivo verificado (agua, roca, sin ruta) y evitan atribuir bloqueos a vegetación o arena que sí son transitables.
- Las Novedades separan título y hechos adicionales. Si no hay detalles nuevos, la entrada no se expande. Los registros anteriores también se muestran sin repetir el título.
- Compatible con las partidas 05.3 y anteriores; instalar en una carpeta nueva.

# Nilo — simulación de autonomía emergente

**Versión experimental `0.5.7.1`**. Aplicación local de Python 3.10+, interfaz web y partida persistente SQLite. La situación de Nilo A: una persona adulta con conocimientos culturales contemporáneos que debe resolver problemas concretos en un entorno desconocido.

> Aviso: la simulación sigue siendo un prototipo físico discreto y de unidades abstractas. No verifica termodinámica avanzada ni concede nuevas leyes simplemente porque una propuesta fue aprobada.

## Instalación nueva o actualización sin perder la partida

1. Descomprimir `Nilo_05_7_portable_Windows.zip` en una carpeta **nueva** `Nilo_05_7`.
2. Ejecutar `INICIAR_NILO.bat` (prepara Python embebible local en el primer inicio).
3. En el primer inicio elegir una instalación anterior, importar `config.env` y decidir por separado si copiar la partida. **No sobrescribe la instalación original**.
4. Para regresar a una versión previa, restaurar *también* el respaldo de la base compatible. Utilizar los scripts `RESPALDAR_PARTIDA.bat` y `RESTAURAR_PARTIDA.bat`.

Por privacidad, nunca subir `config.env`, `*.sqlite3` ni respaldos a GitHub. El repositorio contiene el **programa completo** bajo `source/`, no un parche.

## Funciones nuevas

- **Necesidades**: hidratación, nutrición, energía, abrigo y seguridad. Consumo acumulativo del tiempo del mundo. Rutinas deterministas para beber, comer y recuperar energía cuando el contexto lo permite; tienen coste en recursos y no gastan consultas al LLM. Efectos de fatiga sobre duración de las tareas.
- **Alimentos**: `forage` consume reservas locales limitadas de vegetación, con rebrote gradual tras 48 horas simuladas, `eat` consume una unidad real del inventario, `drink` requiere acceso físico al agua. Calidad sanitaria del agua aún desconocida, no verificada.
- **Inventos**: `design` crea una ficha con propósito, fundamento, piezas, uniones, procedimiento, predicción y método de prueba. Las versiones se conservan. `craft`, `build`, `assemble`, `use` enlazan resultados mediante `design_id`. Un diseño no es un artefacto físico. Una construcción no valida por sí misma la función prevista.
- **Mecanismos**: `assemble` consume materiales de piezas concretas, exige conexiones consistentes y crea un prototipo. `use` puede comprobar resistencia a carga y transmisión de movimiento mediante energía aplicada; ninguna prueba genera energía de la nada.
- **Bandeja de propuestas**: `propose` registra fenómeno no modelado, evidencia, limitación y prueba posible. El observador puede aprobar el estudio, pedir más detalles o rechazarlo, con justificación. Por seguridad física y técnica **la aprobación no instala código, no ejecuta fórmulas arbitrarias ni habilita un fenómeno nuevo**. Las aprobaciones aceptadas quedan pendientes de desarrollar en una versión probada.
- **Memoria de largo plazo**: registro de experiencias acumuladas sin truncar (`life_history`), etapas de 30 días y preferencias que evolucionan lentamente a partir de acciones verificadas. El contexto para el LLM es selectivo; preserva la historia aunque no toda pueda entrar en cada llamada.
- **Interfaz**: pestañas Inventos, Propuestas y Memoria, indicadores de necesidades. Conserva Novedades y su marcador de lectura, mapa y chat.

## Nilo 05.1 · Hábitos, espera y continuidad

- **Habilidades aprendidas** (`source/habits.py`): solo las operaciones con resultados materiales efectivos producen habilidades. Se guardan éxitos verificables y evidencias; la migración reconoce algunos registros comprobados de partidas antiguas sin inventar ubicaciones.
- **Actividades delegadas**: en sus deliberaciones, Nilo puede declarar una lista opcional `actividades_en_espera` de actividades conocidas (`forage`, `gather`, `rest`, `drink`, `craft`) con límites de stock, distancia y razones. Una lista vacía expresa que prefiere no delegar ninguna. No es obligatorio delegar.
- **Ejecución sin LLM**: cuando el modelo está esperando reintento o alcanzó el límite, el motor selecciona una acción breve y prudente solamente si puede justificarla con un procedimiento comprobado, necesidades y un recurso cercano. Sin acciones posibles, descansa. No inicia exploraciones desconocidas ni inventos nuevos.
- **Memoria auditada**: pestaña Hábitos muestra habilidades, prioridades elegidas y resultados de las acciones sin LLM. La historia queda persistida en SQLite e incluida como contexto compacto en decisiones futuras.
- **Sin editor de física**: las propuestas de expansión permanecen registradas, pero incorporar leyes físicas desde Ajustes se pospone.

## Nilo 05.1 · Hábitos, espera y continuidad

- **Habilidades aprendidas** (`source/habits.py`): solo las operaciones con resultados materiales efectivos producen habilidades. Se guardan éxitos verificables y evidencias; la migración reconoce algunos registros comprobados de partidas antiguas sin inventar ubicaciones.
- **Actividades delegadas**: en sus deliberaciones, Nilo puede declarar una lista opcional `actividades_en_espera` de actividades conocidas (`forage`, `gather`, `rest`, `drink`, `craft`) con límites de stock, distancia y razones. Una lista vacía expresa que prefiere no delegar ninguna. No es obligatorio delegar.
- **Ejecución sin LLM**: cuando el modelo está esperando reintento o alcanzó el límite, el motor selecciona una acción breve y prudente solamente si puede justificarla con un procedimiento comprobado, necesidades y un recurso cercano. Sin acciones posibles, descansa. No inicia exploraciones desconocidas ni inventos nuevos.
- **Memoria auditada**: pestaña Hábitos muestra habilidades, prioridades elegidas y resultados de las acciones sin LLM. La historia queda persistida en SQLite e incluida como contexto compacto en decisiones futuras.
- **Sin editor de física**: las propuestas de expansión permanecen registradas, pero incorporar leyes físicas desde Ajustes se pospone.

## Límites expresos

- No existe aún física universal. No hay presión, gas, ciclo termodinámico, válvulas, combustión cuantitativa, fluidodinámica ni fabricación de una máquina de vapor funcional.
- No hay mortalidad ni sistema completo de heridas/enfermedades, reproducción o herencia generacional. El límite de acciones y el mapa siguen siendo finitos.
- Las aprobaciones de nuevos principios *no autogeneran código* ni modifican el motor hasta implementarlas y probarlas.
- Las necesidades son abstractas; no representan modelos biomédicos o seguridad alimentaria real.
- `×60` acelera tiempo simulado, no consultas LLM. Los modelos pueden tener límites diarios externos.

## Arquitectura

- `source/nilo.py`: orquestación, servidor local, base SQLite y API
- `source/brain.py`: contexto LLM, JSON y planes
- `source/world.py`: terreno, acciones físicas, rutas y construcción
- `source/physics.py`: geometría, contención y flotación
- `source/mechanics.py`: ensamblajes y esfuerzos elementales
- `source/survival.py`: necesidades y autocuidado automático
- `source/inventions.py`: fichas técnicas, revisiones y propuestas
- `source/cognition.py`: investigaciones y relaciones
- `source/interfaz.html`: interfaz web con pestañas
- `tests/test_v05.py`: pruebas de migración y sistemas nuevos

## Pruebas

```bash
python -m unittest discover -s tests -v
```

## Desarrollo de Nilo B

Se conserva el motor independiente del perfil de conocimiento inicial. Nilo B será un experimento posterior, con epistemología restringida, generaciones y transmisión cultural. El simple hecho de cambiar el prompt no elimina los conocimientos implícitos del modelo LLM.


## Edición portable de Windows

Este paquete tiene lanzadores que usan `python/python.exe` local. El primer inicio descarga y verifica la distribución **oficial Python 3.12.10 embeddable x64**, SHA256 fijo, sin instalar Python en Windows ni cambiar PATH. Para distribuirlo sin conexión, copiá la carpeta `python/` ya preparada. Ver `LEEME_PORTABLE.txt`.


## Nilo 05.3 — Construcciones y herramientas que evolucionan

- **Obras con identidad persistente**: modificar un refugio no crea una estructura nueva. `modify` admite añadir, sustituir, retirar y reparar componentes consumiendo recursos físicos del inventario.
- **Desmontaje parcial o total** mediante `dismantle`, con recuperación parcial de materiales según su condición. Las obras retiradas permanecen en el registro histórico.
- **Planos de planta ASCII**: cada obra guarda una planta orientativa con dimensión, entrada, orientaciones y zonas de uso propuestas. Se crea desde el objeto existente, no desde una narración libre del LLM.
- **Geometría local 2.5D separada del minimapa**: las dimensiones y componentes son independientes de la resolución de las casillas. No se simula todavía un mundo tridimensional completo, interiores navegables ni mecánica estructural avanzada.
- **Pestaña Planos** y detalle de construcciones, con versiones y esquemas anteriores. Reformar invalida la demostración de funcionamiento de la versión nueva; deben ejecutarse pruebas nuevas.
- Se mantienen el archivo histórico, avisos, resumen de pendientes, zoom independiente y hábitos de 05.2.

Para actualizar, instalá 05.3 en una carpeta **nueva** e importá una **copia** de tu partida y configuración previa. No borres 05.2 hasta verificar la importación. La distribución portable descarga un intérprete oficial de Python en el primer inicio, salvo que ya se haya preparado en otra PC.

### Convenciones del motor

Las dimensiones son aproximaciones abstractas acotadas por recursos. Los rótulos de actividad (por ejemplo *dormir* o *almacenar*) indican uso previsto, **no demuestran** la existencia de muebles, tabiques o desempeño térmico. La recuperación de materiales se calcula por lote, sin duplicarlos. Los mecanismos compuestos mantienen sus uniones verificadas o registran piezas desconectadas después de intervenirlos.

## Nilo 05.2 — Historia, lectura, notificaciones y zoom independiente

- Se conserva un archivo histórico append-only en `nilo_mundo.sqlite3`, tabla `history`, con registros de diario, novedades, eventos, chat, experiencias y documentación. Las revisiones de diseños, investigaciones y proyectos se guardan en `history_revisions`. Los límites de la interfaz **no borran** estos registros.
- `reading_positions` guarda por separado el último registro leído de `journal` (Cuaderno) y `news` (Novedades). Desde cada pestaña podés marcar la sección o ambas como leídas sin eliminar mensajes.
- Preguntá en el chat `¿Qué me perdí?` o `Poneme al día`. Nilo recibe solo el contenido pendiente para resumir (hasta 80 entradas por lote) y explicita si hay más. Para continuar, preguntá `Seguí`. El chat **no cambia** los marcadores automáticamente: después de un resumen exitoso podés pulsar «Marcar lo resumido como leído», sin afectar entradas posteriores.
- `Avisos ⚙` abre los ajustes de notificaciones del navegador: aviso breve, texto completo o desactivadas; solo Cuaderno, solo Novedades o ambos. Requieren permiso y mantener la pestaña abierta. Funcionan mientras la ventana está minimizada; no hay servicio de notificaciones independiente del navegador.
- Los mapas `Cerca` y `General` conservan **zooms diferentes** en la configuración local de ese navegador, incluso tras cerrar la pestaña.
- El motor puede atender urgencias fisiológicas mediante rutinas comprobadas aun cuando el LLM funcione, hasta dos acciones antes de la siguiente deliberación; se muestran estadísticas de acciones autónomas/deliberadas.
- `EXPORTAR_HISTORIAL.bat` produce `exportaciones/Nilo_historial_YYYYMMDD_HHMMSS.jsonl` para consultar toda la historia sin tener que usar SQLite.
- Actualizá en una **carpeta nueva**, iniciá `INICIAR_NILO.bat` e importá una copia de tu partida. No borres la instalación anterior hasta comprobar el resultado.
- La distribución portable instala el intérprete embebible en la propia carpeta durante el primer inicio, como 05.1; **el ZIP descargado inicialmente no contiene Python**.
