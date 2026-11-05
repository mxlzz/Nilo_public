> **Actualización de planificación · 4/11/2026:** Se reservó **0.7.0** para la reestructuración integral de arquitectura, a partir de **0.6.4**, sin versiones públicas intermedias. El [plan de 25 pasos](PLAN_REESTRUCTURACION_NILO_07.md) incluye auditoría específica, reformulación de cada subsistema y pruebas por etapa; la implementación no comenzó. Por este cambio, termodinámica pasa tentativamente a **0.8** (issue #9), autonomía prolongada a **0.9** (#10), y transferencia entre mundos a **0.10** (#11). **1.0** sigue como horizonte sujeto a evaluación. Las menciones y discusiones anteriores de 0.7 como hito térmico son históricas y quedan reemplazadas por esta decisión; el roadmap histórico no se altera.

# Nilo — plan vigente y futuros caminos

> **Fuente principal de planificación, revisable:** revisión del **3 de noviembre de 2026**, con versión publicada **0.6.4** (primer corte físico 0.6.0, seguido de laboratorios de prueba 0.6.1–0.6.4) ([historial de cambios](CAMBIOS.md); la evaluación conductual con nuevas partidas continúa pendiente).
> Este documento expresa la **prioridad actual**, no un calendario fijo ni autorización automática de implementación. La historia técnica está en [ROADMAP_0571.md](ROADMAP_0571.md), los cambios ya publicados en [CAMBIOS.md](CAMBIOS.md) y los alcances detallados en sus issues.

## Auditoría estructural · 4 de noviembre de 2026 — posible base modular 0.7

**Estado: propuesta fundada, pendiente de aprobación del alcance. Sin cambios de motor.** La revisión de la versión **0.6.4** inspeccionó la estructura de **63 módulos/scripts Python** y rutas críticas de simulación, mundo, acciones, física, memoria, proyectos, SQLite, proveedor LLM, UI, laboratorio y migración. La [auditoría de arquitectura](AUDITORIA_ARQUITECTURA_NILO_07_2026-11-04.md) clasifica **20 hallazgos** por evidencia, severidad y responsabilidades actuales, e incluye una estructura propuesta de paquetes.

**Puntos centrales:** separar `Simulation` y `world.execute_action` de presentación, migración y registro; mantener una sola descripción estructurada por acción y un contrato de tiempo por fases; identidad/RNG persistentes; distinguir estado del mundo de percepción del personaje; migración versionada del SQLite y replays de paridad; conservar libertad de intereses del agente.

**Problemas nuevos identificados:** [#75](https://github.com/mxlzz/Nilo_public/issues/75) (categorías construidas desde nombres influyen en la condición de refugio) y [#76](https://github.com/mxlzz/Nilo_public/issues/76) (la lectura del mapa puede enriquecer/mutar estructuras). Sumados a [#67](https://github.com/mxlzz/Nilo_public/issues/67), [#68](https://github.com/mxlzz/Nilo_public/issues/68) y [#69](https://github.com/mxlzz/Nilo_public/issues/69) y a los límites cognitivos/archivísticos ya abiertos, justifican una reestructuración con pruebas diferenciales, no una ampliación de parches. **El resultado de 646 pruebas aprobadas no demuestra ausencia de estas inconsistencias.**

**Secuencia de diseño planteada, no aprobada:** establecer baseline/backup; normalizar tiempos, acciones, RNG y modelos de estado; extraer dominios de física/mundo; separar memoria/cognición y proveedores; migrar archivo, UI y laboratorio a los contratos nuevos; validar 68 escenarios, partidas antiguas, invariantes y LLM reales con condiciones documentadas. Se debe publicar solo con importación de saves y rollback comprobados.

**Numeración a decidir:** [#9](https://github.com/mxlzz/Nilo_public/issues/9) tenía **0.7** como nombre tentativo para termodinámica. Si se reserva 0.7 para consolidación arquitectónica, termodinámica deberá trasladarse expresamente a una etapa posterior, sin mezclar ambos cambios en la misma validación. Issue maestro [#74](https://github.com/mxlzz/Nilo_public/issues/74).

---

## Auditoría estructural · 4 de noviembre de 2026 — posible núcleo modular 0.7

**Estado: análisis documentado, sin implementación aprobada.** La revisión de 0.6.4 cubre la distribución de **63 módulos/scripts Python**, la interfaz principal HTML (~175 KB), los HTML del laboratorio, catálogos JSON y las rutas críticas del motor. El [informe de arquitectura](AUDITORIA_ARQUITECTURA_NILO_07_2026-11-04.md) recoge **21 hallazgos** distinguiendo defectos reproducidos, inconsistencias observables en código y deudas de modularidad. **Issue principal [#74](https://github.com/mxlzz/Nilo_public/issues/74).**

Los problemas de organización más inmediatos son el ciclo largo en nilo.py, el dispatcher físico en world.py, el esquema mutable compartido, la dispersión entre guía/validador/duraciones/ejecutor de cada acción, la generación de IDs/RNG, la sincronización del archivo SQLite y el acoplamiento entre prompt, proyección, memoria y mundo. Dos casos concretos nuevos: [#75](https://github.com/mxlzz/Nilo_public/issues/75) (clasificación narrativa de construcciones afecta condición de refugio) y [#76](https://github.com/mxlzz/Nilo_public/issues/76) (la lectura de mapa puede mutar entidades).

**Arquitectura propuesta:** paquetes core/worlds/physics/agent/cognition/storage/app/lab, con modelos de estado y resultados tipados, identidades/reloj reproducibles, observaciones sin mutación y una única ruta de ejecución también para el laboratorio. En vez de reemplazar todo el código de golpe: línea base 0.6.4 → contratos/RNG/timing → extraer mundos/física → cognición/proyectos → archivo/API/laboratorio → migración/test de partidas antiguas y evaluación conductual LLM comparable. **No alterar la autonomía ni añadir objetivos de manera encubierta.**

**Numeración en discusión:** [#9](https://github.com/mxlzz/Nilo_public/issues/9) había reservado tentativamente el rótulo «0.7» para termodinámica. Un 0.7 de consolidación estructural puede sustituir esa etiqueta **solo mediante decisión explícita**; las nuevas leyes térmicas conviene introducirlas después del cambio de base para atribuir correctamente las diferencias de comportamiento. No publicar 0.7 antes de verificar saves, replays y restauración.

---
## Propuesta abierta · 4 de noviembre de 2026 — laboratorio como centro de ajustes

**Estado: propuesta documentada, no aprobada ni implementada. No tiene versión comprometida.** El laboratorio actual (última publicación **0.6.4**) permite inspeccionar escenarios, replays y el payload LLM con valores; la propuesta amplía su función hacia un **centro de experimentación, configuración y restauración reversible**. No altera por sí misma la física, los prompts en uso, la memoria de Nilo ni sus partidas.

**Diseño central:** no modificar directamente archivos Python al mover sliders o checkboxes. Trabajar con **perfiles experimentales declarativos y validados**, ejecutarlos en el motor verdadero con SQLite temporal, comparar con el baseline y solo después habilitar una acción expresa para aplicar al motor instalado. Separar **checkpoint de ajustes** de **checkpoint del mundo**; restaurar reglas **nunca debe retroceder automáticamente la partida**.

| Etapa propuesta | Alcance | Issue |
| --- | --- | --- |
| **A · Experimentar (primera prioridad)** | Editor versionado de prompts Gemini/Groq; seleccionar datos enviados al LLM por checkboxes (sin modificar física ni memoria); parámetros configurables con tipo/rango/dependencia; guardar/cargar perfiles; ejecutar y comparar escenarios desde el mismo estado/semilla sin aplicar cambios a Nilo. | [#71](https://github.com/mxlzz/Nilo_public/issues/71) |
| **B · Aplicar y recuperar** | Backups automáticos antes de aplicar, checkpoint de configuración con nombre, diff, hashes, validaciones, aplicación atómica, botones para guardar/cargar/aplicar/restaurar; copia coherente de SQLite solo cuando se solicite un checkpoint completo de la partida. | [#72](https://github.com/mxlzz/Nilo_public/issues/72) |
| **C · Comparación avanzada** | Extracción gradual de parámetros físicos hoy fijos en Python, experimentos comparativos y deliberaciones reales LLM explícitas con medición de costos, resultados e invariantes. | [#73](https://github.com/mxlzz/Nilo_public/issues/73) |

**Referencia y condiciones de aceptación:** [issue maestro #70](https://github.com/mxlzz/Nilo_public/issues/70) y [especificación](LABORATORIO_CENTRO_AJUSTES_PROPUESTA.md). La herramienta no debe convertirse en un motor paralelo ni permitir ejecución de código arbitrario desde la interfaz. Todo cambio aplicado ha de tener respaldo recuperable y registro verificable. Conservar pruebas deterministas y distinguirlas de evaluación conductual real de Gemini/Groq ([#3](https://github.com/mxlzz/Nilo_public/issues/3)); mantener ligados el selector de contexto a [#31](https://github.com/mxlzz/Nilo_public/issues/31)/[#63](https://github.com/mxlzz/Nilo_public/issues/63) y la persistencia a [#32](https://github.com/mxlzz/Nilo_public/issues/32).

**Orden tentativo A → B → C, revisable.** Registrar esta propuesta en Github **no autoriza su implementación** ni desplaza automáticamente las prioridades vigentes de corrección del motor (#67, #68, #69).

---

## Verificación técnica y prioridades vigentes · 3 de noviembre de 2026

**Publicaciones verificadas.** 0.6.0 (`referencia-historica-privada-releases-tag-v0.6.0`) incorporó física composicional de cargas; 0.6.1 (`referencia-historica-privada-releases-tag-v0.6.1`) agregó laboratorio de acciones; 0.6.2 (`referencia-historica-privada-releases-tag-v0.6.2`) incorporó un banco de **68 escenarios** que recorre el orquestador real, y 0.6.3 (`referencia-historica-privada-releases-tag-v0.6.3`) agregó línea temporal de partidas y checkpoints previos a deliberación/acción. **Ninguna de las tres actualizaciones de laboratorio corrigió las leyes físicas pendientes.**

**Pruebas que efectivamente se ejecutaron:** la validación de la 0.6.3 (`referencia-historica-privada-actions-runs-41663032997`) pasó **634 tests (1 omitido)**, el catálogo de 68 escenarios sin desajustes esperados, los escenarios físicos deterministas y dos replays desde procesos independientes con huellas coincidentes. Empaquetado/release (`referencia-historica-privada-actions-runs-41663032926`) aprobado. El estudio de integración de **0.6.1** también ejecutó un orquestador demo de hasta 5,69 días, pero esa elección de acciones no proviene de Gemini/Groq; por lo tanto **no es evaluación conductual autónoma**. El informe y los ensayos se integraron en PR `referencia privada #138` (`referencia-historica-privada-pull-138`): [AUDITORIA_INTEGRAL_MOTOR_2026-11-03.md](AUDITORIA_INTEGRAL_MOTOR_2026-11-03.md). Las pruebas agregadas allí deben distinguirse de la batería original del release.

### Correcciones fundamentadas antes de seguir ampliando reglas físicas

| Prioridad de discusión | Hallazgo o dependencia | Estado |
| --- | --- | --- |
| **Alta** | [#67 — Contrato temporal](https://github.com/mxlzz/Nilo_public/issues/67): distinguir minutos previstos, desplazamiento, ejecución, transcurridos e interrumpidos en `ActionResult`, mediciones y planificación. | Defecto confirmado; **pendiente de corrección**. |
| **Alta** | [#68 — `gather` remoto](https://github.com/mxlzz/Nilo_public/issues/68): la acción que viaja hasta una fuente acredita extracción sin sumar su duración de trabajo. | Defecto reproducido; **pendiente**. |
| **Alta** | [#69 — Identidad y RNG](https://github.com/mxlzz/Nilo_public/issues/69): obras generan parte del ID con RNG global, fuera de la secuencia determinista explícita del mundo. | Defecto reproducido; **pendiente**. |
| **Alta, cognitiva** | [#2 — exploración agotada](https://github.com/mxlzz/Nilo_public/issues/2): `explore` fallido no cuenta siempre para reconsideración; el contexto no debe imponer intereses ni notificar nuevos sitios. | Evidencia en run real; conducta mejorada **no demostrada**. |
| **Media-alta** | [#13 — objetivos y cierres](https://github.com/mxlzz/Nilo_public/issues/13), [#20 — memoria](https://github.com/mxlzz/Nilo_public/issues/20), [#63 — percepción](https://github.com/mxlzz/Nilo_public/issues/63): continuidad y evidencia verificable entre deliberaciones sin inyectar objetivos. | Diseño/evaluación abiertos. |
| **Condición de validación** | [#3 — corridas comparables](https://github.com/mxlzz/Nilo_public/issues/3), [#32 — historial largo](https://github.com/mxlzz/Nilo_public/issues/32): comparar replays y nuevas corridas LLM, medir el crecimiento del SQLite por checkpoint y los límites de exactitud histórica. | Instrumentación parcial publicada, evaluación longitudinal pendiente. |

**Secuencia sugerida para discusión, no autorización de cambios:** corregir coherencia de los tiempos y `gather`; resolver identidad/RNG y compatibilidad de referencias; medir las consecuencias sobre detección de estancamiento y continuidad de proyectos; después revisar decisiones conceptuales abiertas de percepción 5×5, `recall`, `go` por nombres y extracción manual. **Sin cambios en los objetivos autónomos de Nilo y sin agregar avisos espontáneos sobre el mapa.** Las mejoras más amplias de física composicional #8/#62 continúan vigentes, sin fecha obligatoria.

**Laboratorio histórico 0.6.3:** reejecutar desde checkpoints de partidas **nuevas** bajo el motor instalado, comparar resultados físicos, inspeccionar el recorrido. Las partidas anteriores pueden consultarse pero no reproducirse exactamente cuando falta el estado anterior; cambiar UUID, versión, reloj real o datos archivados no capturados impide afirmar igualdad bit a bit. La base con checkpoints crece sin política de compactación: [manual y límites](LABORATORIO_HISTORICO.md), #32. La interfaz y su funcionamiento no deben confundirse con una mejora del motor autónomo.

---

## Diseño en proceso · 3 de noviembre de 2026 — percepción, memoria y acciones

**Estado: acordado como dirección conceptual, no implementado ni asignado a una versión.** Este bloque tiene precedencia sobre las ideas históricas de recuperación automática de alternativas y sobre cualquier formulación anterior que suponga notificar a Nilo cambios del mundo. Se originó en el análisis de la corrida 0.6.0 de 13 días/607 deliberaciones, con exploraciones repetidas y pérdida de continuidad de proyectos. No se altera código ejecutable por documentarlo.

### Percepción visual, hitos y autonomía de la atención

- **Campo visual 5×5 (radio 2):** enviar casillas y elementos observables detallados cuando el presupuesto permita; con contexto saturado, enviar una descripción local con posiciones de lo relevante. Si Nilo permanece inmóvil y no hay novedades, puede usarse una síntesis breve. No confundir compresión de texto con reducción física de lo visible. La oclusión avanzada, bosques/montañas como agrupaciones y pérdida de precisión de recuerdos con el tiempo quedan para más adelante.
- **Hitos memorables:** sitios singulares descubiertos (p. ej. entrada a cueva, ruinas, ventilaciones raras), construcciones propias y lugares personalmente significativos. La rareza se evalúa sobre el conocimiento de Nilo, nunca sobre el mapa secreto. Registro automático más posibilidad de que Nilo marque un lugar; **identidad física estable para no duplicar hitos**. Recuerdo de ubicación aproximada espontáneo y coordenadas exactas solo cuando estén documentadas y se consulten.
- **Separación funcional:** el motor conserva el mapa revelado para rutas; el LLM recibe percepción inmediata, continuidad de intención y recuerdos *justificados por reconocimiento*. **No enviar cada árbol o roca del mapa global en cada llamada**.
- **Memoria bajo demanda:** propuesta de operación `recall` (o nombre a precisar), búsqueda local por entidades, lugares, ensayos, ubicaciones, proyectos y cantidades documentadas; sin nueva consulta LLM obligatoria. Resultados con IDs y procedencia. Diferenciar recuerdo aproximado de recuento exacto documentado.
- **Evitar intervención de intereses:** revisar/eliminar recuperación histórica proactiva que introduce alternativas no pedidas (p. ej. priorizar la cueva al estancarse). Mantener continuidad del trabajo presente y reconocimiento disparado por lugares/objetos reales. La recuperación espontánea de temas lejanos queda **aplazada**, porque seleccionar qué recordar puede orientar artificialmente sus objetivos.

**Issues existentes actualizados:** [#4 — percepción](https://github.com/mxlzz/Nilo_public/issues/4), [#20 — memoria](https://github.com/mxlzz/Nilo_public/issues/20), [#63 — proyección cognitiva](https://github.com/mxlzz/Nilo_public/issues/63), [#31 — presupuesto y contexto](https://github.com/mxlzz/Nilo_public/issues/31).

### Navegación, fronteras y cambios del mundo

- **[`go` por recurso, hito o entidad conocida #64](https://github.com/mxlzz/Nilo_public/issues/64):** `go target=piedra` lleva a una fuente revelada y alcanzable sin recolectar; `go target=cueva` llega a su entrada sin descender; `go target=obra-ID` localiza una construcción propia. Conservar coordenadas y agua actuales. No convertir la localización en una extracción, ni forzar consulta `recall` previa. Resolver nombres ambiguos por ID; nunca elegir un homónimo arbitrariamente.
- **Exploración sin bucle #2:** `explore` fallido debe contribuir al reconocimiento del estancamiento según condiciones (sector, ruta, frontera, descubrimiento), hoy no aumenta `no_progress_steps` por su vía principal. Información sobre accesibilidad puede calcularse a partir del mapa *conocido* cuando Nilo explora o consulta; no afirmar conocimiento total del mundo.
- **Sin notificaciones de actualizaciones:** si aparecen sectores nuevos o cambian navegación/obstáculos, actualizar internamente rutas y validez de conclusiones; **no enviar mensajes espontáneos** del tipo «el mundo cambió» ni «tenés regiones nuevas». Cómo revisa Nilo una convicción espacial antigua sin aviso dirigido **queda pendiente**.

Relacionado: [#2](https://github.com/mxlzz/Nilo_public/issues/2), [#4](https://github.com/mxlzz/Nilo_public/issues/4), [#64](https://github.com/mxlzz/Nilo_public/issues/64).

### Acciones físicas y manual

- **[#65 — piedra y herramientas](https://github.com/mxlzz/Nilo_public/issues/65):** propuesta inicial de `gather piedra` a mano con 33 % de extraer **una** unidad y 67 % de fallo sin extracción. La eficacia con herramientas debe depender de propiedades físicas comprobables; diferenciar extraer fragmentos (`gather`) de excavar y potencialmente abrir una casilla (`excavate`). Por revisar: ruinas frente a roca maciza, probabilidades y compatibilidad. **No está aprobado como ley física definitiva ni implementado.**
- **[#66 — catálogo LLM](https://github.com/mxlzz/Nilo_public/issues/66):** hoy las 26 operaciones se reenvían en cada deliberación; reducir a un índice breve pero completo, con contratos detallados consultables cuando haga falta. No ocultar opciones arbitrariamente, no convertir el selector en un sistema que sugiera intereses, y evitar nuevas llamadas al LLM para consultar parámetros triviales. Coordinar con [#31](https://github.com/mxlzz/Nilo_public/issues/31) y [#30](https://github.com/mxlzz/Nilo_public/issues/30).

### Qué falta decidir / cómo verificarlo

1. Forma de la matriz 5×5 y sus versiones compactas por proveedor; qué terreno se identifica por percepción y cuál requiere inspección; oclusión compleja pospuesta.
2. Identificación y deduplicación de hitos importados; esquema de `recall`, resultados/procedencia y condiciones de reconocimiento situacional sin inyectar alternativas.
3. Revisión de conocimiento cartográfico cuando cambia el entorno **sin avisos espontáneos**; no inventar accesibilidad ni convertir una observación antigua en verdad atemporal.
4. Semántica de `go target` ante homónimos y niveles distintos, y separación estricta de desplazamiento/extracción.
5. Distribución de recolección manual vs herramienta, conservación de recursos, RNG/replay; contenido íntegro del catálogo de acciones y recuperación voluntaria de detalles.
6. Pruebas deterministas de física, migración/compatibilidad y evaluación conductual con corridas comparables [#3](https://github.com/mxlzz/Nilo_public/issues/3), especialmente repetición de `explore`, desvíos inducidos por memoria y consumo de tokens.

**Secuencia tentativa sin versión asignada:** (A) percepción/hitos y continuidad sin sesgo, (B) consultas `recall` y `go` por nombres, (C) semántica de extracción/manual de operaciones, (D) evaluación longitudinal. Se puede ajustar si una dependencia técnica real exige otro orden. Los siguientes cortes de física 0.6 no quedan cancelados ni subordinados automáticamente a este diseño.

## Decisión de secuenciación · 2 de noviembre de 2026

Conservar los **hitos originales de desarrollo 0.6, 0.7, 0.8, 0.9 y 1.0**, sin convertir cada mejora intermedia detectada en un requisito para llegar a 0.6. Las versiones incrementales de 0.5.x sirven para corregir límites verificados, preparar dependencias y medir resultados, **no para posponer indefinidamente** la física composicional.

El **hito 0.5.9.4 (comparación de corridas, #3)** ya estaba contemplado en la hoja de ruta antes de la discusión sobre los parches recientes. No es sinónimo de `0.5.9.3.40`. **No hay una versión `0.5.9.3.40` aprobada** como hito. Tampoco se deben confundir `0.5.9.3.35` (parche propuesto) y `0.5.9.4` (hito de evaluación).

La secuencia preferida **hoy** es:

| Orden preferido | Estado a 2026-11-02 | Alcance y criterio | Issues |
| --- | --- | --- | --- |
| **0.5.9.3.35** | **Publicada; seguimiento conductual pendiente** | Exploración orientada por dirección y región conocida; `explore` genérico compatible, frontera alcanzable, recorrido gradual y cardinales reales registrados. Evaluar su efecto en partidas, sin declarar resueltos problemas narrativos no reproducidos. | [#60](https://github.com/mxlzz/Nilo_public/issues/60), [#26](https://github.com/mxlzz/Nilo_public/issues/26); pruebas para [#3](https://github.com/mxlzz/Nilo_public/issues/3) |
| **Preparación acotada de 0.6** | **Auditoría completada; sin nueva versión obligatoria** | [Auditoría del 2/11/2026](AUDITORIA_PRE_06_2026-11-02.md): separación de entornos y módulo de recipientes existentes; faltan segundo módulo, reconocimiento gradual, invariancia ante nombres y consumidores tipados. Un run anterior tiene 24 mediciones archivadas fuera de la memoria operativa. **No se detectó un bloqueo que impida iniciar 0.5.9.4**. Resolver dependencias físicas en cortes de 0.6; recuperación por ID cuando se necesite, sin imponer FTS5. | [#4](https://github.com/mxlzz/Nilo_public/issues/4), [#5](https://github.com/mxlzz/Nilo_public/issues/5), [#30](https://github.com/mxlzz/Nilo_public/issues/30), [#20](https://github.com/mxlzz/Nilo_public/issues/20), [#32](https://github.com/mxlzz/Nilo_public/issues/32), C.1/C.2 |
| **0.5.9.4** | **Infraestructura de evaluación implementada; estudio conductual pendiente** | Corridas comparables desde estados y semillas documentados. Evaluar autonomía, bucles, decisiones corporales y exploración con trazabilidad del modelo, proveedor y origen de la acción. Separar regresiones deterministas de conducta real del LLM. Punto de evaluación antes del gran cambio físico, sin prometer una causalidad que los datos no permiten. | [#3](https://github.com/mxlzz/Nilo_public/issues/3), [#2](https://github.com/mxlzz/Nilo_public/issues/2), [#50](https://github.com/mxlzz/Nilo_public/issues/50) |
| **0.6** | **Primer corte funcional publicado; física composicional en expansión** | Física composicional y arquitectura modular: propiedades, forma, materiales, uniones y mecanismos acreditan resultados independientemente del nombre que les dé Nilo. Distinguir percepción, identificación, hipótesis y comprobación. La modularidad ya tiene un primer corte, no se considera terminada. | [#8](https://github.com/mxlzz/Nilo_public/issues/8), [#30](https://github.com/mxlzz/Nilo_public/issues/30), [#4](https://github.com/mxlzz/Nilo_public/issues/4), [#5](https://github.com/mxlzz/Nilo_public/issues/5) |

**Decisión tras la auditoría del 2/11/2026:** se avanzó a **0.5.9.4**, sin publicar una .36/.37 solamente por preparación. Los prerrequisitos que sí son reales para conseguir los objetivos de física composicional se implementarán dentro de los primeros cortes de 0.6. La consulta histórica de mediciones por ID está justificada por una partida con 204 mediciones archivadas y 180 activas, pero no exige FTS5 ni una versión previa a .4. Documento de evidencia: [AUDITORIA_PRE_06_2026-11-02.md](AUDITORIA_PRE_06_2026-11-02.md).

**Después de publicar 0.5.9.4:** [protocolo de evaluación](PROTOCOLO_EVALUACION_0594.md) disponible; recolectar corridas verdaderamente comparables con LLM antes de inferir efectos sobre autonomía, necesidades y exploración dirigida. **Próxima gran meta técnica: 0.6**, empezando por modularidad y física composicional según la auditoría. Si hay hallazgos de los runs que obliguen a ajustar el rumbo, revisar esta guía, sin generar parches por rutina.

**La ubicación de 0.5.9.4 antes de 0.6 era una preferencia metodológica revisable**, no una condición irrevocable. Si aparecen evidencias que aconsejan adelantar una parte de la física o postergar un experimento, discutir y documentar ese cambio.

### Hallazgo de corrida y hotfix conductual 0.5.9.4.1 · 2/11/2026

En una corrida real de .4 el agente construyó un refugio en un proyecto, lo modificó en otro y luego repitió inspección/descanso sin prueba funcional. La corrección .4.1 (PR `referencia privada #128` (`referencia-historica-privada-pull-128`)) da continuidad a la evidencia por **ID físico**, diagnostica objetivos de protección no instrumentados y conserva antecedentes de pausas en el contexto. El sistema no inventa abrigo comprobado ni fuerza a Nilo a cambiar de interés. **Pendiente evaluación conductual con LLM comparable (#3)** y física composicional de refugios (#8) en 0.6.

### Auditoría del contexto cognitivo — 2/11/2026 · primer corte 0.5.9.4.2 implementado

[Informe técnico de payloads y observabilidad](AUDITORIA_CONTEXTO_LLM_2026-11-02.md), con auditor reproducible `auditar_contexto_llm.py` y pruebas de Gemini/Groq/compatible. Hallazgos prioritarios: `proyecto_actual.progress` numérico subjetivo enviado al LLM; `condicion_abrigo` esquemática confundible con protección verificada; exposición de propiedades calculadas de herramientas; memoria de pausas potencialmente descartable al comprimir; diferencias entre proveedores al conservar campos no compactados. La falta de progreso de `explore` fallido permanece fuera de algunos contadores.

**Primer corte de implementación:** 0.5.9.4.2 (PR `referencia privada #131` (`referencia-historica-privada-pull-131`)), sobre [#63 — Proyección perceptiva unificada](https://github.com/mxlzz/Nilo_public/issues/63). Falta corroboración conductual y trabajo incremental en trazabilidad/recuperación (#31/#47/#17, protocolo #3).

**Orden acordado de trabajo:** (1) representación cognitiva tipada/perceptiva y protección de memoria relevante; (2) reconsideración basada en resultados de exploración, sin misiones impuestas; (3) `interact` ambiental modular y física 0.6. Conservar cifras de inventario, coordenadas y ensayos realmente medidos. La corrección perceptiva se publicó con pruebas, no por el informe en sí. Evaluar con #3 antes de declarar mejora conductual.

### Primer corte funcional 0.6.0 · Cargas estructurales físicas

La 0.6 comenzó por un **segundo módulo instalable** (`cargas_estructurales`): las obras fijas pueden probar, almacenar y recuperar lotes materiales sobre superficies con capacidad física acotada por geometría, componentes y material. El nombre de la obra no altera ese resultado. Las reformas están sujetas al contenido realmente depositado y se conservan las evidencias por revisión. Véase [CAMBIOS.md](CAMBIOS.md). Este corte **no** implementa todavía un sistema completo de esfuerzos, clima, construcción de pasarelas o conexiones ambientales; continúan los objetivos de #8/#62/#16/#17, y la observación espontánea con LLM debe evaluarse por #3. En las siguientes etapas de 0.6 se priorizarán consecuencias espaciales y mecanismos, no más informes generales de contexto.

### Ajuste de presentación acordado para la próxima entrega con UI (pendiente)

**[Issue #51 — Necesidades compactas por sensaciones](https://github.com/mxlzz/Nilo_public/issues/51).** En lugar de porcentajes y barras, mostrar solamente la sensación cualitativa **idéntica a la que recibe Nilo** (`survival.perceived_needs`), con un indicador cromático discreto y accesible. Ayudas (?) reducidas exclusivamente a los **intervalos internos de cada sensación**, respetando el caso de inconsciencia. Para **Abrigo** y **Seguridad**, usar estados neutros «sin exposición simulada» y «sin amenazas simuladas» mientras no existan clima/amenazas activos; no afirmar protección física comprobada.

**Secuencia:** agrupar con el **próximo lanzamiento que modifique la interfaz**, preferentemente una entrega inicial de **0.6**, **sin parche independiente de interfaz** ni condicionar el inicio de física composicional. Es un cambio **pendiente**, puramente de presentación: las cifras siguen en el motor, las mediciones y el observatorio de corridas de .4. La etiqueta final y su ubicación pueden ajustarse según la implementación; #51 es la especificación vigente. **No se declara publicada por anotarla aquí.**

### Mejoras incrementales sugeridas pero no comprometidas

- **`0.5.9.3.36` (etiqueta tentativa):** índices de consulta histórica en SQLite, posiblemente FTS5, recuperación por IDs y relaciones [#20](https://github.com/mxlzz/Nilo_public/issues/20), [#32](https://github.com/mxlzz/Nilo_public/issues/32). **FTS5 no es automáticamente prerrequisito de 0.6**. Antes de asignarle versión, demostrar qué caso actual lo exige y comprobar si el archivo existente lo resuelve.
- **`0.5.9.3.37` (etiqueta tentativa):** consolidación de conocimiento y recuperación bajo demanda [#20](https://github.com/mxlzz/Nilo_public/issues/20), [#31](https://github.com/mxlzz/Nilo_public/issues/31), [#5](https://github.com/mxlzz/Nilo_public/issues/5). Determinar qué es dependencia del nuevo motor y qué puede incorporarse después sin pérdidas de evidencia.
- **No se fijan `0.5.9.3.38`, `.39` ni `.40`** por completar una secuencia numérica. Que un issue siga abierto tampoco obliga a crear un parche.
- **0.5.9.3.34.1 ya implementada:** percepción corporal cualitativa para decisiones del agente, manteniendo reservas internas numéricas y resultados medidos consultables [#62](https://github.com/mxlzz/Nilo_public/issues/62), [#50](https://github.com/mxlzz/Nilo_public/issues/50). **Pendiente comprobar efecto conductual** mediante #3; no confundir pruebas unitarias con evaluación longitudinal.

## Hitos mayores recuperados: orientación de largo plazo

| Hito histórico | Estado | Dirección funcional |
| --- | --- | --- |
| **0.6 — física composicional / modularidad** | Primer corte publicado; alcance de ampliaciones abierto | Capacidades físicas verificables derivadas de materiales, geometrías y uniones; reconocimiento y conocimiento empírico del mundo. [#8](https://github.com/mxlzz/Nilo_public/issues/8), [#30](https://github.com/mxlzz/Nilo_public/issues/30) |
| **0.7 — termodinámica y ambiente** | Propuesto, sin fecha | Primero fenómenos térmicos medibles, después variación ambiental y ciclos. [#9](https://github.com/mxlzz/Nilo_public/issues/9) |
| **0.8 — autonomía prolongada** | Propuesto, parcialmente anticipado en 0.5.x | Procedimientos y estrategias reutilizables con menor dependencia de llamadas LLM; no duplicar hábitos ya implementados. [#10](https://github.com/mxlzz/Nilo_public/issues/10) |
| **0.9 — transferencia de Nilo A entre mundos** | Propuesto, sin fecha | Conservar identidad y memoria ante un segundo entorno físicamente diferente; estudiar qué conocimientos se transfieren y cuáles hay que recomprobar. [#11](https://github.com/mxlzz/Nilo_public/issues/11) |
| **1.0 — observación de larga duración** | Horizonte exploratorio | Runs recuperables de semanas o meses, estabilidad y evaluación; criterios de publicación aún abiertos. `referencia privada #25` (`referencia-historica-privada-issue-25`) registra su recuperación histórica, no una implementación. |
| **Nilo B** | Experimento separado, largo plazo | Agente con conocimiento inicial mínimo; no confundir con el traslado de Nilo A a otro entorno. [#7](https://github.com/mxlzz/Nilo_public/issues/7) |

La secuencia 0.6→1.0 conserva **las ideas acordadas**, pero esos números son rótulos históricos revisables: ni plazos ni obligaciones de lanzar todas esas versiones.

## Cómo se usa esta guía a partir de ahora

**Fuente de verdad y estados.** Este apartado inicial de `FUTUROS_CAMINOS.md` es el plan vigente. `ROADMAP_0571.md` y la recuperación histórica más abajo documentan decisiones anteriores, incluso cuando su terminología «siguiente versión» haya quedado superada. `CAMBIOS.md`, `VERSION` y las releases determinan qué está **realmente implementado**. Los issues describen alcance y pendientes, no trabajo hecho por el mero hecho de estar escritos.

**Antes de decidir una implementación**, contrastar:
1. Qué limitación está demostrada por código, pruebas o un run (separar observación de hipótesis).
2. Qué mejora concreta se busca, dependencias verificadas, alternativas, esfuerzo, riesgos de compatibilidad y coste de oportunidad respecto de 0.6.
3. Si conviene parchear ahora, agrupar con el próximo hito, reservar para más adelante, reducir alcance o descartar.
4. Cómo verificarlo: pruebas físicas/deterministas, replays, mediciones de coste y, para mejoras cognitivas, corridas observadas con LLM sin atribuir efectos sin comparación.
5. Qué decisión tomó el observador: versión **tentativa** o **aprobada**, alcance y motivo. No adjudicar números definitivos sin esa decisión.

**Cuando cambie el rumbo**, editar primero esta guía (fecha, orden, motivos y enlaces), luego ajustar los issues afectados. Registrar explícitamente qué se adelanta, pospone, divide, fusiona o descarta y **por qué**. No reescribir el registro histórico como si la decisión nueva hubiera existido siempre. Tras publicar, enlazar PR, release, pruebas y límites reales; evitar declarar «completado» un objetivo cognitivo por haber pasado CI.

**Principio del proyecto:** Nilo elige intereses y acciones dentro del mundo y puede proponer ampliaciones a partir de evidencias. El observador decide y autoriza cambios de software; una propuesta de Nilo o un issue no instala leyes, módulos ni parches automáticamente. Mantener compatibilidad y trazabilidad de partidas.

---

## Antecedentes y decisiones anteriores (registro histórico, no calendario vigente)

## Recuperación de la hoja de ruta 0.6–0.9 (27 de octubre de 2026)

Las conversaciones previas planteaban **0.6 física composicional → 0.7 termodinámica y entorno dinámico → 0.8 autonomía prolongada → 0.9 transferencia entre mundos**, con **1.0 como horizonte de experimentos largos**. Eran una **propuesta evolutiva**, no versiones comprometidas. Se registra el contenido recuperado, no se fijan fechas ni se promete que esas funciones deban coincidir con esos números.

### 0.6 · Que los objetos funcionen por sus propiedades, no por su nombre

- Geometrías, materiales, combinaciones y mecanismos con consecuencias físicas calculadas, incluidos objetos y usos que no fueron programados como recetas.
- Propiedades compuestas y, como línea posterior, variación entre muestras. Mantener **separados** los cambios de física, variación y conocimiento para identificar por qué mejora o empeora el comportamiento.
- El planteo reciente incorpora una dependencia: primero diferenciar **lo percibido, lo identificado, lo sabido conceptualmente y lo comprobado experimentalmente** ([#4](https://github.com/mxlzz/Nilo_public/issues/4), [#5](https://github.com/mxlzz/Nilo_public/issues/5)). La variación excepcional, incluido el ejemplo ilustrativo del 1 %, permanece aplazada ([#6](https://github.com/mxlzz/Nilo_public/issues/6)).
- **Validación a diseñar:** que una modificación real de geometría o material cambie una medición física, sin depender del nombre declarado ni de la narración.

### 0.7 · Más leyes, introducidas una a una

- Temperatura y transferencia de calor, humedad, cambios de estado, evaporación y condensación; después día/noche, iluminación, clima y recursos que cambien con el entorno.
- La secuencia anterior distinguía **termodinámica aislada** y **mundo dinámico posterior**. No introducir ambos a la vez si eso impide atribuir los efectos observados.
- **Validación a diseñar:** fenómenos reproducibles y variables medibles; los resultados `no_evaluable` siguen sin considerarse fracasos del agente.

### 0.8 · Aprender procedimientos para actuar con menos deliberación

- Reutilizar procedimientos comprobados, parámetros y condiciones; hábitos y planes condicionales; revisión autónoma de intentos que dejan de funcionar.
- Parte de esta idea ya entró en la serie 0.5.x (agenda, hábitos, operaciones en espera). La revisión estratégica [0.5.9.3](https://github.com/mxlzz/Nilo_public/issues/2) y las corridas comparativas [0.5.9.4](https://github.com/mxlzz/Nilo_public/issues/3) adelantan otras piezas.
- **Pregunta abierta:** qué capacidades *faltan realmente* y cuáles serían duplicaciones. El objetivo no es automatizar por automatizar, sino demostrar aprendizaje conductual y medir llamadas LLM reales.

### 0.9 · Probar si los conocimientos sobreviven al cambio de entorno

- Un segundo entorno que sea físicamente distinto, no únicamente otro mapa o prompt; Nilo A conserva identidad, memoria y resultados con su procedencia, pero **no** recibe automáticamente como universales las leyes locales del lugar anterior.
- Observar **transferencia, generalización y necesidad de recomprobación**. Comparar con un agente sin esa experiencia previa en condiciones documentadas.
- Esta línea es distinta de Nilo B ([#7](https://github.com/mxlzz/Nilo_public/issues/7)): Nilo B plantea otro punto de partida epistemológico; la 0.9 probaría a un mismo Nilo A ante un mundo nuevo.
- La separación de escenarios y entornos iniciada en 0.5.8 es una base de software, **no** prueba todavía de transferencia.
- **Validación a diseñar:** uso efectivo de conocimientos adquiridos y capacidad para reconocer sus límites. El calendario de observación puede incluir distintas duraciones, no depende de una cantidad fija de días.

### Criterio de revisión constante

- Revisar al comienzo de **cada etapa** si el comportamiento buscado ya existe, sigue siendo interesante o debe replantearse, fusionarse, dividirse o descartarse.
- El número **0.6, 0.7, 0.8 o 0.9 es una etiqueta histórica de la idea**, no una restricción del orden de trabajo ni una promesa de versión.
- Mantener las hipótesis del diseño separadas de los hechos observados en runs; comparar versiones/semillas/modelos y registrar qué variable del motor o del agente cambió.
- Toda ampliación de física o capacidad requiere diseño, pruebas, control del observador y documentación; una Issue no autoriza implementar por sí sola.

## Decisiones de diseño conservadas

### 2026-10-27 — Entre percepción, reconocimiento y propiedades

1. **Al descubrir un elemento:** Nilo obtiene indicios perceptibles reales, no necesariamente la identidad de clase ni las propiedades avanzadas.
2. **Inspección voluntaria por coordenadas:** Nilo decide qué estudiar. Si el motor permite identificarlo, registra que ese tipo de elemento corresponde a un objeto/material reconocible. Nilo A conserva su conocimiento conceptual contemporáneo, pero no conoce automáticamente todas las equivalencias del mundo.
3. **Reconocimiento transferible:** después de identificar un tipo, Nilo reconoce nuevos ejemplares equivalentes sin repetir la inspección básica; no deduce por ello que todos sean físicamente idénticos.
4. **Experimentos voluntarios:** la dureza, resistencia, porosidad, efectos de calor o agua, etc., siguen siendo desconocidas salvo por evidencia obtenida mediante métodos que el motor pueda ejecutar o medir. Si una variable no está modelada, declarar ese límite, no inventar el resultado.
5. **Nuevos elementos futuros:** añadir un material al motor no lo añade retrospectivamente a la memoria de Nilo; podría descubrirlo, identificarlo e investigarlo por decisión propia.
6. **Expresión natural frente a ejecución estructurada:** en deliberaciones que ya existen, el LLM puede elegir IDs estables de objetos/materiales conocidos o coordenadas. No introducir un segundo LLM obligatorio para traducir sinónimos. `gather` sigue incluyendo desplazamiento y extracción verificada.
7. **Excepciones por muestra:** cuando la física pueda soportarlo, propiedades distintas de un mismo tipo pueden contradecir regularidades aprendidas. Las variaciones deben ser persistentes, reproducibles por semilla/identificador y **no** reveladas gratuitamente por reconocer la clase.

**No se decide aún:** exactitud de la percepción previa a inspección, formato de IDs/clases, métodos de análisis por propiedad, migraciones de mundos previos, distribución estadística de excepciones, ni cronograma. Las Issues correspondientes conservan esas decisiones abiertas.

## Pendientes técnicos arrastrados de etapas previas

Mantener visibles en `docs/ROADMAP_0571.md` además de las nuevas Issues:

- **C.1:** reproducción fiel de partidas reales con estados, reloj, RNG, intervención humana y traza ordenada; ya existe replay determinista para escenarios guionados.
- **C.2:** completar migración desde resultados legados y texto narrativo hacia `ActionResult` estructurado en todos los consumidores.
- **Separación de entornos:** probar transferencia del mismo agente/memoria a un segundo entorno pequeño sin prometer que los mundos sean ya intercambiables.
- **Métricas y regresión:** ejecutar comparaciones multisemilla, aparte de las pruebas aisladas y las huellas SHA de replay.

Estos pendientes **no se declaran terminados** por haber implementado versiones intermedias; hay que verificar su estado antes de trabajar en ellos.

## Mantenimiento de este registro

Cuando surja una idea nueva o retomemos una anterior:

1. **Registrar la pregunta y la razón**, separando observación, hipótesis y decisión.
2. Crear o actualizar una Issue, enlazarla aquí e indicar estado y dependencias. Evitar duplicados.
3. Antes de implementar, revisar qué depende de qué, acordar alcance y versión; luego rama de trabajo, pruebas, replay y aprobación del observador.
4. Al publicar, enlazar PR, commit/release y resultado observado. No equiparar pruebas unitarias con calidad cognitiva demostrada en un run real.

Este índice es una memoria del **proyecto**, no un conjunto de órdenes para Nilo ni un mecanismo de evolución autónoma del software.
