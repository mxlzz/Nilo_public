# Revisión exploratoria estructurada de alternativas para un mundo ambiental autónomo y emergente

**Corte documental:** 21-11-2026. **Versión:** R1.0. **Objeto:** mundo físico/ambiental, su generación, evolución autónoma, fenómenos materiales y emergencia estructural. **Fuera de alcance:** cerebro, Norns, LLM, NeuroLab, genética neuronal, personajes e interfaz final.

**Tipo de documento:** revisión técnica exploratoria con evidencia primaria y recomendaciones condicionadas. **NO** es una revisión sistemática exhaustiva ni artículo revisado por pares. No llamar "probado" a algo inspeccionado en documentación. No implementar mientras se investiga.

## Resumen ejecutivo

Se evaluaron **42 artefactos o proyectos identificables** (aplicaciones, motores, bibliotecas, herramientas científicas, modelos académicos y estándares). No son 42 motores equivalentes y algunos son componentes del mismo ecosistema de software. La principal conclusión es que debemos **dejar de buscar un motor universal** y distinguir: (a) generador de condiciones iniciales; (b) procesos ambientales acoplados; (c) reglas locales que producen organización; (d) protocolo de estado, tiempo, unidades, persistencia y auditoría.

Tres familias merecen prioridad de investigación:
- **Candidatos al núcleo ambiental / ejemplos de ciclos causales:** Shanhai, AgroEcoSim, Landlab; Ecosystem Explorer como referencia funcional sin licencia de código verificada.
- **Candidatos al estado inicial:** WorldEngine y LibreTerrain. Infinigen es un generador geométrico/visual, no una simulación ambiental sostenida.
- **Investigación de organización no predefinida:** Particle Life, Lenia/Flow-Lenia y ALIEN; complementarios, no sustitutos de erosión, clima e hidrología.

**Hallazgo de arquitectura no considerado antes:** CSDMS Basic Model Interface (BMI), PyMT y eWaterCycle ya abordan interfaces de simuladores heterogéneos: initialize/update/get_value/set_value, variables, mallas y tiempo. Es prioritario evaluar *compatibilidad de modelos* antes de diseñar un motor propio.

**Decisión de proceso:** no justificar código físico nuevo ni adoptar un solo motor hasta pruebas comparativas por función. Mantener \`matter_v0.py\` como spike histórico y no ampliar sus reglas.

## 1. Pregunta y criterios de revisión

**Pregunta:** qué bases técnicas, sistemas completos y antecedentes científicos permiten construir un territorio inicial, pequeño, consistente y persistentemente cambiante, donde agua, terreno, clima, materiales y eventualmente sistemas vivos se condicionen entre sí, y donde puedan aparecer nuevas configuraciones sin diseñar cada objeto final.

Decisiones acordadas: estrategia híbrida, estado inicial generado y posterior evolución autónoma, búsqueda de estructuras no prescritas, territorio inicialmente pequeño, progreso independiente de la observación. **Ninguna de estas decisiones implica simular la emergencia de nuevas leyes físicas.** Las leyes del motor son definidas; lo que aspiramos a dejar abierto son las configuraciones y organizaciones producidas.

Se distinguen cuatro capacidades a menudo confundidas:
1. **G (generación):** produce estado inicial parametrizado o por semilla.
2. **D (dinámica):** ejecuta evolución posterior desde ese estado.
3. **C (acoplamiento):** procesos se realimentan a través de variables físicas compartidas.
4. **O (organización):** interacciones locales generan formas/estructuras no especificadas como plantillas.
Además: **R** reproducción, observación y persistencia, **I** integración/documentación, **L** licencia, **M** madurez.

**Jerarquía de evidencia:**
- **P:** artículo científico/doc oficial, describe un método/capacidad pero no prueba nuestra integración.
- **R:** repositorio primario inspeccionado, metadatos de licencia/último push y/o README. Fecha de push no equivale a salud.
- **T:** ejecución de prueba en nuestro CI con artefactos y condiciones rastreables.
- **D:** demostración pública observable sin acceso al código. No equivale a una prueba con controles.
- **?:** evidencia insuficiente, no atribuir propiedad ni licencia.

**Método:** búsquedas cruzadas por familias (world generation, geofísica/hidrología, ecosistemas, autómatas y organización, herramientas de acoplamiento); comprobación de URL primaria, objetivo y tipo de modelo; para repositorios principales, fecha de último push y licencia declarada en metadatos; lectura de documentación y trabajos académicos. No se auditaron íntegramente los 42 códigos ni se ejecutaron 42 motores. No se establecieron puntajes artificialmente precisos.

**Exclusión:** herramientas de rendering puro sin generación causal, IA cognitiva de agentes, software sin fuente identificable, copias sin procedencia, herramientas no vinculadas a la pregunta. Se permiten excepciones de visualización/generación señaladas explícitamente por sus limitaciones, nunca como si ya resolvieran evolución ambiental.

## 2. Catálogo de 42 alternativas

**Clave:** «licencia n/v» significa licencia de reutilización no verificada en esta investigación; no significa propietario ni automáticamente libre. «Push» es fecha de último cambio publicado según GitHub, comprobada al corte; tampoco confirma soporte de largo plazo. Los detalles funcionales son evidencia documental salvo donde se indica prueba.

### Grupo A. Mundos/ambientes integrados y referentes funcionales (8)

**01 — Ecosystem Explorer** · https://www.ethanjhulbert.org/ecosystem-explorer/ · Documentación https://www.ethanjhulbert.org/ecosystem-explorer/about/ · [D/P]. Terreno inicial por semillas y presets; clima, agua superficial/subterránea, sedimentos, vegetación, fuego, lava y evolución por pasos; permite intervenir y examinar celdas. **Muy alto ajuste como referencia de lo que debería sentir el sistema completo.** Código/licencia del programa no identificados; reglas simplificadas, sin prueba de evolución abierta. Prioridad: **ALTA para benchmark funcional, NO como biblioteca copiable**.

**02 — Shanhai** · https://github.com/aruis/Shanhai · MIT · push 2026-05-17 · [R]. Workbench Eco-CA semi-3D con hidrología, humedad, nutrientes, crecimiento vegetal, degradación/recuperación y validaciones documentadas; escenarios controlados 64×64. **El candidato abierto más directamente alineado para experimentar un circuito ambiental acoplado y auditable.** Es un prototipo pequeño/reciente y habrá que ejecutar los tests; no afirmar que implementa geomorfología real ni estructuras abiertas. Prioridad **ALTA**.

**03 — AgroEcoSim** · https://github.com/cg-tuwien/AgroEcoSim · BSD-3-Clause · push 2026-11-16 · [R]. Simulador de crecimiento vegetal, clima procedural y difusión de humedad de suelo; CLI y servidor headless con interfaz HTTP, además de visualización. Muy útil para **submodelo de crecimiento y un contrato computacional desacoplado de la UI**. No ofrece por sí mismo tectónica ni evolución abierta. Prioridad **ALTA/MEDIA**.

**04 — BiomeSimulator** · https://github.com/andrenepomuceno/BiomeSimulator · Apache-2.0 · push 2026-04-25 · [R]. Mundo 2D con terreno, ríos, estaciones, vegetación y animales; posee suite de regresión y profiling declarados. Las especies/tipos de organismo están predefinidos; no confundir simulación demográfica con organización material emergente. Útil para examinar separación simulación/rendering y continuidad. **MEDIA**.

**05 — Evo Plants Sim 3D** · https://github.com/Bradorez/evo_plants_3d · licencia n/v en metadatos · push 2026-05-20 · [R]. Terreno, flujo hídrico, erosión, estaciones, suelos y poblaciones vegetales; 3D en Babylon.js; declara núcleo TypeScript a paso fijo. Interesante **referente de acoplamiento y visualización**; proyecto pequeño y licencia sin verificar: NO reutilizar código sin aclararla. **MEDIA**.

**06 — Madingley General Ecosystem Model** · https://madingley.github.io/ y https://github.com/Madingley/C-sharp-version-of-Madingley · código libremente descargable pero licencia de redistribución no confirmada aquí; repositorios históricos (último push en versión C# 2018-05-04) · [P/R]. Ecología mecanística de productores y consumidores a gran escala. Excelente antecedente de principios ecológicos y restricciones de energía; no motor de terreno mutable de escala local. **MEDIA, solo línea ecológica posterior**.

**07 — Permaculture Network (Gary Zhexi Zhang y Agnes Cameron)** · https://agnescameron.info/permaculture/ · [P/D], licencia de código no identificada. Antecedente 2019 que modela relaciones ecológicas como conversación entre agentes ambientales. Confirmado como inspiración expresamente citada por Ecosystem Explorer. Valioso para diseño conceptual de causalidad comprensible, no base de motor disponible. **MEDIA como antecedente conceptual**.

**08 — ALIEN (Artificial Life Environment)** · https://github.com/chrxh/alien · BSD-3-Clause · push 2026-11-21 · [R]. Sistema de partículas y enlaces materiales 2D acelerado por GPU, energía, organización y mutación. Encaja **muy bien en el frente de autoorganización**, no es simulador de relieve/hidrología realista ni justifica incorporar cerebros a este proyecto. Evitar afirmaciones de complejidad indefinida garantizada. **ALTA para investigación de organización, no núcleo ambiental**.

### Grupo B. Generadores de territorio, geografía y formas (11)

**09 — WorldEngine** · https://github.com/Mindwerks/worldengine · MIT · push 2026-11-16 · [R+T]. Placas, relieve, precipitaciones, erosión, temperatura, biomas y exportación. **Generador inicial**, no motor ambiental continuo. Nuestro CI generó 32×16 celdas, validó elevaciones y roundtrip Protobuf; el resultado dependió del estado RNG global NumPy además de la semilla de generación. Prueba: https://github.com/mxlzz/Nilo_public/actions/runs/44944136887 . **ALTA para benchmark de estado inicial**, con corrección/encapsulación de aleatoriedad.

**10 — LibreTerrain** · https://libreterrain.org/docs/ · Código https://gitlab.com/libreterrain/libreterrain · MIT/Apache-2.0 declaradas por documentación · [P]. Editor nodal abierto, motor Rust + Godot 4, terreno, erosión, agua, vegetación y salida de datos. La documentación 2026.1 declara primer release estable y semilla reproducible. **Alternativa moderna para producir datos iniciales y estudiar componentes geomorfológicos**; es authoring, no demostración de mundo autónomo persistente. **ALTA como generador alternativo**.

**11 — WorldSmith (Gravitas40E)** · https://github.com/Gravitas40E/WorldSmith · Apache-2.0 · push 2026-08-09 · [R]. Motor planetario Rust que declara evolución de interiores, tectónica, clima y reproducibilidad; proyecto recién creado (julio 2026, 0 estrellas en revisión). No validar tales promesas sin tests ni asumir madurez. **MEDIA exploratoria**.

**12 — Worldsmith (TheDatawiz-dot)** · https://github.com/TheDatawiz-dot/Worldsmith · MIT · push 2026-08-16 · [R]. Generador web de relieve, clima, ríos, lagos, biomas y exports. Determinista según documentación. **Generador de geografía**, no dinámica continua; no confundir con #11 por similitud de nombre. **MEDIA**.

**13 — SoilMachine** · https://github.com/weigert/SoilMachine · README indica MIT; GitHub no detectó SPDX formal · push 2023-06-11 · [R]. Terreno multicapas, erosión hídrica/eólica, transporte de sedimentos, distintos tipos de suelo. Cubre una necesidad más precisa que Sandspiel para **materiales geomorfológicos**. Riesgo de mantenimiento e integración C++/TinyEngine; confirmar licencia real del artefacto. **ALTA para estudiar representación; MEDIA para adopción inmediata**.

**14 — Demiurge** · https://github.com/owenyuwono/demiurge · MIT · push 2026-08-20 · [R]. Planeta por placas Voronoi, elevación, erosión, clima, visualización de escala grande a local. Predomina la **generación funcional por posición/semilla**; no prueba relieve permanentemente erosionándose. **MEDIA**.

**15 — Neural-Earth** · https://github.com/dunkean/neural-earth · licencia n/v en metadatos · push 2026-11-12 · [R]. Generación tectónica y refinamiento por modelos de difusión; clima, suelo e hidrología en la cadena de generación. Refuerzo visual aprendido no significa causalidad física; riesgo de costo GPU y licencia. **MEDIA/BAJA para primera etapa**.

**16 — Infinigen** · https://github.com/princeton-vl/infinigen · BSD-3-Clause en repositorio actual · push 2026-11-11 · [R/P]. Generación 3D procedural de terreno, vegetación, objetos y materiales desde reglas, basado en Blender. **Muy valioso para geometría y presentación futura**, pero no sistema de agua/vegetación/erosión persistentes con causalidad mutua. Literatura 2023 describía estado/licencia de esa fecha; prevalece licencia del repositorio actual para versiones concretas. **ALTA para render futuro, BAJA como núcleo**.

**17 — HeightForge Engine** · https://github.com/DuskforgeStudios/heightforge-engine · MIT · push 2026-07-21 · [R]. Núcleo de altura, erosión, ríos, ruido y terreno por chunks. Pequeño/reciente; objetivo de generar heightmaps, no ecología autónoma. **MEDIA**.

**18 — rworld** · https://github.com/daver64/rworld · MIT · push 2026-08-21 · [R]. Librería header-only C++ de terreno, precipitación, temperatura, biomas y suelos. Reutilización técnica potencial; no demostrar evolución continua solo porque se presenta como «living world». **MEDIA**.

**19 — torusworld** · https://github.com/lmsh7/torusworld · licencia n/v en metadatos · push 2026-07-22 · [R]. Generación toroidal sin costuras con continentes, erosión, ríos y vegetación; salida de tiles. Útil si se exige continuidad topológica sin fronteras, **pero todavía no la exigimos** y no resuelve dinámica ecológica. **BAJA por ahora**.

### Grupo C. Modelos científicos de procesos físicos y ambientales (11)

**20 — Landlab** · https://github.com/landlab/landlab · MIT · push 2026-11-19 · [R/P]. Biblioteca de procesos para dinámica de la superficie terrestre: escorrentía, erosión, sedimentos, laderas, agua subterránea y componentes ecohidrológicos, con interfaces y mallas compartidas. **Posible base científica más sólida para nuestro núcleo ambiental**, dado que ofrece piezas acoplables y no un sandbox cerrado. Requiere selección responsable de ecuaciones y escalas; no garantiza desempeño de videojuego ni autoorganización abierta. **PRIORIDAD MUY ALTA**.

**21 — Fastscape** · https://github.com/fastscape-lem/fastscape · BSD-3-Clause · push 2026-11-02 · [R/P]. Componentes de evolución topográfica para modelos rápidos mediante xarray-simlab. Orientado a evolución de paisaje, no agua a escala de segundo ni organismos. **ALTA como alternativa geológica**.

**22 — Badlands** · https://github.com/badlands-model/badlands · LGPL-3.0 · push 2026-05-01 · [R/P]. Erosión, transporte sedimentario, evolución de cuencas a escalas geológicas grandes. Documentación y artículos científicos. Escala y tiempos distintos de interacción inmediata. **MEDIA como referencia geomorfológica**.

**23 — pyDeltaRCM** · https://github.com/DeltaRCM/pyDeltaRCM · MIT · push 2026-10-21 · [R/P]. Formación y evolución de deltas, canales y sedimentos en modelo de complejidad reducida; ciencia reproducible y extensibilidad documentada. **ALTA para fenómeno específico de ríos/deltas, NO para todo el mundo**.

**24 — GeoTaichi** · https://github.com/Yihao-Shi/GeoTaichi · GPL-3.0 · push 2026-11-18 · [R]. Física de suelo, materiales granulares, deformables y fluidos con esquemas MPM/DEM/FEM y acoplamientos, GPU Taichi. Potente pero pesado para la prueba mínima; requisitos/licencia/costo de adopción. **MEDIA para módulos especializados futuros**.

**25 — SPlisHSPlasH** · https://github.com/InteractiveComputerGraphics/SPlisHSPlasH · MIT · push 2026-10-28 · [R/P]. Fluidos SPH 2D/3D; CLI y scripts de simulación. Referente de fluido local, no hidrología de cuenca ni clima. Usarlo solo si el nivel de detalle lo exige. **MEDIA**.

**26 — climlab** · https://github.com/climlab/climlab · MIT · push 2026-07-23 · [R/P]. Modelado climático por procesos mediante clases composables. Útil para simplificaciones de radiación/energía y modelos globales; desproporcionado para un único valle inicial si no se justifica. **MEDIA/BAJA para etapa 1**.

**27 — SpeedyWeather.jl** · https://github.com/SpeedyWeather/SpeedyWeather.jl · EUPL-1.2 · push 2026-11-21 · [R/P]. Modelo de circulación atmosférica global en Julia, interactivo/extensible y con parametrización. Escala planetaria; no justifica su inclusión en un terreno de decenas de celdas. **BAJA al inicio, ALTA solo si se decide clima de planeta**.

**28 — Helios** · https://github.com/PlantSimulationLab/Helios · LGPL-2.1 · push 2026-11-20 · [R/P]. Simulación de física y fisiología de plantas/ambiente, balance energético y radiación. **Candidato fuerte si queremos crecimiento vegetal con costos/beneficios físicos**, no generador de cadenas montañosas. **MEDIA futura**.

**29 — PyHelios** · https://github.com/PlantSimulationLab/PyHelios · MIT del wrapper, dependencias del núcleo Helios bajo sus propias licencias · push 2026-11-16 · [R]. Interfaz Python para la suite #28; instalación Python y opciones CPU/GPU. **No contarlo como segundo motor independiente**; se conserva en inventario porque cambia drásticamente la integración. **MEDIA**.

**30 — OpenAlea L-Py** · https://github.com/openalea/lpy · licencia CeCILL según README; metadatos de GitHub NOASSERTION · push 2026-11-18 · [R/P]. Modelado de morfogénesis y arquitectura vegetal con gramáticas L-systems + Python. **Genera formas por reglas y condiciones**, pero sigue imponiendo una familia de gramáticas; por sí mismo no demuestra nuevas clases biológicas no definidas. **MEDIA/ALTA para estructuras vegetales futuras**.

### Grupo D. Reglas locales, materia y autoorganización (8)

**31 — Sandspiel** · https://github.com/MaxBittker/sandspiel · MIT · push 2026-09-10 · [R+T]. Automata celular 2D de «falling sand», tipos y reglas implementados por especie. En nuestro CI: **4/4 ensayos de caída, barrera, repetición y control de viento**, tras normalizar a 126 el campo de viento (constructor solo arranca ceros y la rutina interpreta ese valor como fuerza). https://github.com/mxlzz/Nilo_public/actions/runs/44944136887 . Útil para movimiento local; **no** API de materiales generales ni geología. **MEDIA**.

**32 — Sandspiel Studio** · https://github.com/MaxBittker/sandspiel-studio · MIT · push 2026-10-11 · [R]. Editor de reglas/elementos por bloques, apropiado para explorar cambios en dinámicas celulares. Parte de código depende de \`Math.random()\` global y de estado de app; documentación interna advierte de esquemas de update problemáticos con tamaños variables. **MEDIA como laboratorio, no motor validado**.

**33 — The Powder Toy** · https://github.com/The-Powder-Toy/The-Powder-Toy · GPL-3.0 · push 2026-11-21 · [R]. Arena, líquidos, gases, calor, presión, electricidad y gravitación; Lua, snapshots y manipulación de partículas. Más maduro y amplio que Sandspiel; catálogo de elementos predefinidos y arquitectura C++/SDL. No hay todavía ejecución comparativa en nuestra rama: **pendiente**. **ALTA para baseline de materiales, MEDIA para núcleo**.

**34 — Particle Life** · https://github.com/hunar4321/particle-life · MIT · push 2024-08-29 · [R]. Partículas que se atraen/repelen entre tipos, con patrones y estructuras autoorganizadas. Experimento conceptual simple que aísla el fenómeno de **interacciones locales → estructuras**. No es mecánica de suelo ni ecología realista; útil para pruebas de formación/estabilidad y controles negativos. **ALTA para emergencias mínimas**.

**35 — Lenia** · https://github.com/Chakazul/Lenia · MIT · push 2024-07-19 · [R/P]. Autómata celular continuo con patrones estables, móviles y autoorganizados. No resuelve conservación física general ni hidrología. **ALTA como referencia teórica y de prueba de patrones**.

**36 — Flow-Lenia** · https://github.com/erwanplantec/FlowLenia · licencia n/v en metadatos · push 2026-10-09 · [R/P]. Extiende Lenia con **conservación de masa** y parámetros locales, buscando coevolución de patrones; implementación JAX según INRIA. Es el referente conceptual **más pertinente para combinar estructura, masa y dinámica local**, pero no licencia para integración confirmada. **PRIORIDAD MUY ALTA para método, no copiar hasta verificar derechos**.

**37 — Sensorimotor-Lenia Search** · https://github.com/flowersteam/sensorimotor-lenia-search · MIT · push 2024-04-11 · [R/P]. Búsqueda de reglas que permiten estructuras estables y móviles frente a obstáculos; aporta metodología de **descubrimiento y evaluación**, no un mundo completo. **MEDIA/ALTA metodológica**.

**38 — Golly** · https://golly.sourceforge.io/ · proyecto abierto, licencia específica no comprobada en esta revisión · [P]. Laboratorio consolidado para autómatas celulares y reglas de crecimiento locales. Bueno para analizar sensibilidad a reglas y patrones, pero no infraestructura para geomorfología y balances de materia. **MEDIA como banco experimental**.

### Grupo E. Infraestructura para acoplar modelos (4)

**39 — CSDMS Basic Model Interface (BMI)** · https://github.com/csdms/bmi · MIT · push 2026-11-16 · [R/P]. Estándar probado para controlar y consultar simuladores: \`initialize\`, \`update\`, \`get_value\`, \`set_value\`, unidades, rejillas y tiempo. **Posible contrato de interoperabilidad**, no un motor de mundo; adoptarlo exige demostrar compatibilidad real de variables y escalas. **PRIORIDAD MUY ALTA**.

**40 — PyMT** · https://github.com/csdms/pymt · MIT · push 2024-10-22 · [R/P]. Toolkit Python CSDMS para ejecutar/acoplar modelos BMI. Ahorra programación de adaptadores en algunos casos; costo de dependencias y compatibilidad de versiones pendientes. **ALTA como alternativa a orquestador propio**.

**41 — eWaterCycle** · https://github.com/eWaterCycle/ewatercycle · Apache-2.0 · push 2026-09-16 · [R/P]. Plataforma para hidrología reproducible y acoplamiento de modelos BMI. Más cercana a investigación académica hidrológica que juego persistente; lecciones importantes de reproducibilidad, contenedores y control de estados. **MEDIA/ALTA como precedente de integración**.

**42 — BMI_pyDeltaRCM** · https://github.com/DeltaRCM/BMI_pyDeltaRCM · MIT · push 2022-05-22 · [R]. Adaptador BMI para el modelo de deltas del candidato #23. **Ejemplo concreto de puente**, no segundo motor ni producto dinámico en sí. **MEDIA como plantilla de interoperabilidad**.

## 3. Síntesis de resultados por pregunta

### ¿Existe un proyecto que ya haga exactamente lo que buscamos?
En este conjunto **no se verificó un producto que simultáneamente**: produzca automáticamente un territorio plausible, lo haga evolucionar indefinidamente con balances y realimentación físicamente consistentes, permita formas estructurales verdaderamente abiertas, ofrezca interfaz de lectura/acción y exponga código reusable con costo razonable. Esto es **ausencia de una coincidencia demostrada en la muestra**, NO prueba de inexistencia universal.

El referente funcional más cercano es **Ecosystem Explorer** (sistemas ambientales, ciclo e intervención), pero sin licencia de fuente confirmada. El referente abierto más cercano para **simulación ecosistémica local y pruebas causales** es **Shanhai** (hidrología → suelo/vegetación), con alcance aún experimental. **Landlab** es el candidato más sólido como plataforma de procesos geológicos/hídricos. **ALIEN/Flow-Lenia/Particle Life** son los referentes de organización emergente; ninguno puede sustituir todo el modelo terrestre.

### ¿Qué es emergencia aquí?
No equiparar:
- **Variedad por semilla**: diversidad de mapas parametrizados.
- **Autonomía**: actualización sin usuario.
- **Feedback causal**: una variable altera otra que a su vez transforma la primera.
- **Emergencia estructural**: patrones funcionales causados por interacciones locales sin instrucciones directas de construir ese patrón.
- **Novedad abierta sostenida**: cambios de estructura/función a lo largo del tiempo sin agotar el repertorio; desafío científico aún sin garantía general.

El éxito temprano debería ser demostrar **feedback y estructuras persistentes** con controles negativos. No comprometerse a lograr evolución abierta del universo entero como criterio de aceptación de la primera versión.

### ¿Cómo permitir lo emergente sin simular átomos?
Abordaje híbrido con variables **físicamente significativas pero agregadas**: topografía, agua superficial, humedad de suelo, sedimento, composición de suelo, energía y cobertura. No son leyes microscópicas emergentes, sino fenómenos macroscópicos aproximados. Un campo puede cambiar por otras leyes y causar efectos recíprocos. Una zona deja de ser «bosque porque el generador lo dijo», si la dinámica de plantas, agua, luz/suelo y perturbaciones modifica su existencia.

**Precaución:** esto permite formas e interacciones emergentes, **no** garantiza la aparición de materiales o reglas físicas nuevos. Para ese objetivo distinto se necesita laboratorio separado de autoorganización y especificación de novedad.

### ¿Por qué no elegir Sandspiel solo?
Su sistema de tipos materiales es basado en especies con funciones update concretas, adecuados para caídas/combustión, menos para lluvia-cuenca-sedimento-suelo con variables continuas por celda. Sería sesgo de arquitectura convertir un juego de arena en fundamento universal solo por haber conseguido 4 tests positivos.

### ¿Por qué no elegir WorldEngine solo?
Genera condiciones iniciales. El mundo generado no contiene por sí solo un motor persistente. Además el RNG global exige control explícito para repetición reproducible. Es un **componente potencial**, no el «corazón».

### ¿Por qué evaluar Landlab primero?
La combinación de modelos de superficie ya es su propuesta central y está documentada en literatura científica. Ofrece componentes, interfaces y datos observables. La pregunta pendiente no es si existe: es si su rendimiento, escalas y licencia de dependencias encajan con los experimentos del mundo.

### ¿Cómo conectar componentes?
Separar **estado del mundo** de **solvers especializados**. Empezar investigando si BMI puede servir para: declarar entradas/salidas por componente, unidades, malla, paso temporal y consulta/mutación, sin código especial del motor principal. No suponer que es plug-and-play automático; aún habría que garantizar **quién es dueño de cada variable**, conservación al cruzar límites, interpolación entre resoluciones, estabilidad numérica y compatibilidad de pasos temporales.

## 4. Recomendación y orden de pruebas (etapa 0, aún abierta)

**Decisión recomendada con confianza moderada:** continuar con **reutilización-primero y evaluación modular**, no motor físico propio. Las herramientas a ejecutar prioritariamente en pruebas **distintas y apropiadas a sus dominios**, no bajo un test universal inaplicable:

**Línea A — Ambiente acoplado:** Shanhai y AgroEcoSim. Controlar escenario lluvia/suelo/vegetación, cambio de parámetros y ablación causal. Ecosystem Explorer como **benchmark funcional de caja negra** (sin copiar código), misma hipótesis observable si su UI lo permite.

**Línea B — Terreno inicial y cambio geomorfológico:** WorldEngine o LibreTerrain para exportar altura/material/agua; Landlab para simular erosión/transporte posterior. Para comparaciones geológicas incluir Fastscape en escenario que corresponda. El ensayo importante es **si el dato generado puede continuar evolucionando en otro modelo sin contradicción**, no cuál produce la imagen más bonita.

**Línea C — Formación de estructuras sin plantillas:** Particle Life y, para formulaciones de conservación/flujo, Flow-Lenia; evaluar licencia antes de reutilizar. ALIEN como base física alternativa si necesitamos partículas y enlaces. No incluir su cerebro/agentes en este proyecto.

**Línea D — Integración:** comprobar la interfaz BMI con un caso de dos procesos que comparten estado y paso temporal, y comparar contra un adaptador mínimo explícito. No programar orquestador general antes de ver si PyMT resuelve el problema.

**Criterio para cerrar la etapa 0:** (1) especificaciones observables y métricas acordadas antes del ensayo; (2) ejecución de al menos dos alternativas realmente comparables en cada función candidata; (3) costo medido de ejecución/adaptación e implicaciones de licencia; (4) dictamen por componente «usar / adaptar / descartar / desarrollar», con código/commit, logs, semillas, condiciones y control negativo; (5) plan actualizado por ADR si la decisión cambia las fases. No autorizar diseño definitivo por valoración de README.

**Escenarios candidatos con pruebas y controles:**
- **S1 Generación:** mismas semillas/condiciones → estados iguales; seeds distintos → variación medible; elevaciones finitas y redes de drenaje topológicamente coherentes. Registrar unidades y resolución.
- **S2 Agua:** ingreso, escorrentía, infiltración, evaporación y salida con balance; sin lluvia/fuente, observar comportamiento de control. Una imagen de río no cuenta.
- **S3 Erosión:** transporte altera realmente el relieve y el almacenamiento sedimentario; sin erosión el relieve debe mantener la variable relevante; comparar balance interno/salida y estabilidad.
- **S4 Feedback:** alteración de humedad cambia biomasa/cobertura; cobertura modifica infiltración/erosión en un retorno causal medible; comparar ablación de un eslabón.
- **S5 Organización:** aparición de agregados sin plantilla; medir componentes conectados, persistencia temporal, distribución de tamaños y respuesta a perturbaciones; comparación con reglas aleatorias sin interacción significativa.
- **S6 Tiempo/persistencia:** guardar/reanudar no modifica trayectoria dentro de tolerancia, registrar fuentes pseudoaleatorias y parámetros; iniciar/finalizar componentes independientemente del observador.
- **S7 Rendimiento:** evaluar al menos tamaños 64×64 y 256×256 (cuando correspondan) con CPU, RAM, tiempo por tick y coste de transferencias entre componentes. No inventar umbral de FPS antes de medir ni exigir misma resolución a solver geológico y autómata.
- **S8 Compatibilidad:** probar conversión de un estado generado a uno dinámico con unidades, conservación y límites documentados. Si los estados no son convertibles sin perder el objetivo, no combinar por conveniencia.

## 5. Riesgos, limitaciones y controles metodológicos

1. **Escalas incompatibles:** tectónica en millones de años frente a caídas por segundo. Una simulación multiescala puede necesitar integraciones discontinuas y garantías de conservación, no un único timestep.
2. **Plantillas disfrazadas de emergencia:** muchos generadores deterministas ofrecen variación enorme pero ninguna estructura nueva fuera de categorías predefinidas.
3. **Física aparente:** visualizaciones que cambian colores sin modificar inventarios o topografía efectivos. Auditar variables y flujos.
4. **Modelos científicos inapropiados:** mayor realismo ecuacional no significa mejor experiencia ni costo computacional aceptable.
5. **Acoplamiento ingenuo:** dos ecuaciones correctas pueden producir contradicciones al combinarse; exigir dueño de estado, fronteras, transferencia de cantidades y tests negativos.
6. **Licencias:** MIT/BSD/Apache suelen facilitar integración con obligaciones propias; GPL/LGPL/CeCILL/EUPL tienen requisitos distintos. El uso real requiere revisar archivos de licencia y forma de distribución, no una etiqueta sola. Ausencia de licencia verificable **no autoriza copiar**.
7. **Madurez:** popularidad, commits recientes y despliegue web no son pruebas de estabilidad; solicitar pruebas de integración y reproducibilidad.
8. **Sesgos de investigación:** las herramientas identificadas no equivalen a universo de toda solución posible; están sobrerrepresentadas GitHub/documentación en inglés. Se deben revisar candidatos cuando cambia el alcance.
9. **Sin benchmark universal:** un generador planetario no se debería reprobar por no ejecutar físicas de arena; cada clase requiere pruebas adecuadas.
10. **Objetivo sobredimensionado:** la evolución abierta sostenida es problema científico, no capacidad garantizada de Flow-Lenia o ALIEN. Tomar como preguntas observables diversidad funcional, adaptabilidad a perturbaciones y no agotamiento temprano, sin extrapolar.

## 6. Bibliografía académica mínima (fuentes primarias)

- Hutton, Piper & Tucker (2020), *Basic Model Interface 2.0*, JOSS: https://doi.org/10.21105/joss.02317 .
- Tucker et al. (2022), *CSDMS: a community platform for numerical modeling of Earth surface processes*, GMD: https://gmd.copernicus.org/articles/15/1413/2022/ .
- Moodie et al. (2021), *pyDeltaRCM: a flexible numerical delta model*, JOSS: https://doi.org/10.21105/joss.03398 .
- Salles et al. / Badlands project and methods: https://github.com/badlands-model/badlands and https://www.sciencedirect.com/science/article/pii/S0098300416300851 .
- Raistrick et al. (2023), *Infinite Photorealistic Worlds Using Procedural Generation*, CVPR: https://openaccess.thecvf.com/content/CVPR2023/papers/Raistrick_Infinite_Photorealistic_Worlds_Using_Procedural_Generation_CVPR_2023_paper.pdf .
- Plantec, Hamon, etc., *Flow-Lenia: Emergent Evolutionary Dynamics in Mass Conservative Continuous Cellular Automata*: https://arxiv.org/abs/2506.08569 y https://pubmed.ncbi.nlm.nih.gov/40298480/ .
- Mordvintsev et al. (2020), *Growing Neural Cellular Automata*: https://distill.pub/2020/growing-ca/ ; relevante a morfogénesis local, no incorporar cerebro al mundo.
- Boudon et al. (2012), *L-Py: An L-System Simulation Framework for Modeling Plant Architecture Development*: https://pmc.ncbi.nlm.nih.gov/articles/PMC3362793/ .
- *Towards origins of virtual artificial life: an overview* (2025): https://pmc.ncbi.nlm.nih.gov/articles/PMC12489504/ .
- Revisión de modelos de evolución topográfica (2026): https://onlinelibrary.wiley.com/doi/10.1002/esp.70400 ; referencia secundaria de contrastes de escalas y métodos, no sustituto de sus manuales.
- eWaterCycle y acoplamiento de modelos hidrológicos: https://gmd.copernicus.org/articles/15/5371/2022/ .
- *Self-Organization and Artificial Life* (2020): https://pubmed.ncbi.nlm.nih.gov/32697161/ .

## 7. Control del estudio y siguientes decisiones

- **Dejar sin efecto como recomendación** el supuesto previo de que había que desarrollar una física propia de «caja cerrada» o de que Sandspiel era el candidato principal para el motor.
- No borrar experimentos anteriores: conservar su historia como antecedente de una decisión que luego fue cuestionada.
- **Etapa 0 no cerrada:** esta revisión proporciona corpus/criterios y prioridades, no evidencia de integración real de todas las piezas.
- No iniciar etapas de motor propio ni trabajo de NeuroLab.
- La ubicación en rama de \`Nilo_public\` es estrictamente provisional: no constituye integración de sistemas ni permiso para mezclarlos.
- Para alterar orden/criterios, crear ADR con justificación, riesgo, comparación, plan de prueba y gate; dejar versión anterior auditable.

**Dictamen:** abandonar la estrategia de diseñar materiales primero y «buscar después» un mundo. Evaluar primero sistemas ambientales integrados y su capacidad de recibir un terreno inicial; reservar los sistemas de autoorganización para probar la parte realmente abierta.