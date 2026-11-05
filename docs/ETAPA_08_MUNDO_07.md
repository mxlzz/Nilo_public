# Nilo 0.7 · Etapa 08 — Mundo, topología y generación

**Fecha:** 4 de noviembre de 2026. **Rama:** `refactor/0.7`. **Estado: COMPLETADA.** CI integral `referencia privada #41901014954` (`referencia-historica-privada-actions-runs-41901014954`): **success, 735 pruebas (1 omitida), 8 tests de mundo y 9 del orquestador, escenarios, auditorías, ZIP y replay histórico intacto**. CI histórico `referencia privada #41900978760` (`referencia-historica-privada-actions-runs-41900978760`): **success, 6/6 saves sintéticos y seis semillas de referencia**. [Plan de 25 etapas](PLAN_REESTRUCTURACION_NILO_07.md) · [Etapa 07](ETAPA_07_ORQUESTADOR_07.md) · PR `referencia privada #155` (`referencia-historica-privada-pull-155`).

## 1. Auditoría y alcance

Antes de esta etapa, `world.py` contenía 1.160 líneas (~65 KB) con responsabilidades superpuestas: generación de islas, niveles, consultas geométricas, revelado, BFS, navegación, extracción/forraje, fabricación, excavación y pruebas físicas. El método `new_world(seed)` (a partir de línea 127) generaba un mapa de **37 × 21** celdas en dos niveles (`0` y `-1`) utilizando exclusivamente `random.Random(seed)`, ruido trigonométrico y reglas fijas. El mismo RNG decidía, en un **orden dependiente del recorrido**, vegetación, roca, galerías subterráneas y cantidades de los depósitos. Modificar el orden de estas llamadas cambiaría la partida aunque la semilla se mantuviera.

Además de `new_world`, estaban en `world.py` las primitivas `tile_key`, `valid`, `tile`, `set_tile`, `reveal`, las dimensiones `W/H`, las cuatro direcciones `DIRS` y el conjunto de terreno `PASSABLE`. Sus consumidores usan explícitamente la API `from world import ...`; retirarla habría roto el motor físico, la navegación, las vistas, escenarios y laboratorios.

La generación inicial ubica un refugio en **(15,10,0)**, cueva en **(23,7,0)** y ruinas en **(12,7,0)**, además de un pasillo hacia la entrada a la cueva y una salida real en **(23,7,-1)**. Los depósitos toman sus símbolos de `catalogo.YIELDS`, leído desde `catalog/terrenos.json`. El generador antes **redefinía** `PASSABLE` con la cadena `".,Tocrs=h:vse"`, cuyo conjunto coincide exactamente con el catálogo. Se detectó esa definición duplicada y se eliminó: el origen es ahora el catálogo validado, del que se toma una **copia independiente** para preservar el aislamiento previo entre la pasabilidad efectiva del mundo y el set mutable del catálogo.

**Límite de esta revisión:** los valores de física de `materiales.json`, `objetos.json` y las propiedades efectivas de objetos/ensambles seguirán revisándose en la etapa 11. La navegación, BFS, exploración, paso por niveles, extracción, minería y construcción corresponden a etapas 09–12. No se modifican anticipadamente sus leyes ni se confunden con la topología inicial.

## 2. Estructura implementada

| Propietario | Responsabilidad / contrato |
| --- | --- |
| `nilo_runtime/worlds/contracts.py` | `WorldDefinition` inmutable (entorno, versión de generador, ancho/alto, niveles, símbolos de terreno, de tránsito y de recursos, sitios). `WorldGenerator` como puerto tipado `definition + generate(seed)` para un entorno futuro **sin crear una segunda implementación** |
| `nilo_runtime/worlds/island.py` | Generación única de `isla_v1`, `new_world`, `reveal` inicial, consultas/edición básica de celdas, `W/H/PASSABLE/DIRS`, `ISLAND_DEFINITION`, `ISLAND_GENERATOR` y validador de generación inicial |
| `world.py` | Reexporta los nombres anteriores y conserva navegación/acciones heredadas; **no define otra función `new_world`** |
| `environments.IslandEnvironment` | `make_world(seed)` delega al generador registrado; `world_definition` ofrece metadatos al observador/laboratorio, sin inyectarlos como conocimiento del personaje |
| `catalogo.py` + `catalog/*.json` | Catálogos versionados de símbolos, materiales, depósitos, fuentes, pasabilidad y propiedades físicas. El generador consume `YIELDS/TERRAINS/PASSABLE`; no carga rutas definidas por el LLM ni por las partidas |
| `nilo_runtime/application/bootstrap.py` | Crea estado nuevo mediante `environment.make_world(seed)` y el agente inicial del escenario; sigue generando exactamente el **save v5**, sin añadir `WorldDefinition` al snapshot |

El traslado se comprobó **literalmente** contra el último `world.py` de la etapa 07 (commit `9dd4a5bdf5f3bbbcc51950fcb9515b88e4132d6b`): el bloque original de **2.886 caracteres** que implementaba las seis funciones `tile_key/valid/tile/set_tile/new_world/reveal` coincide sin modificación con el bloque movido a `worlds/island.py`. El validador y el contrato se agregaron **fuera** del algoritmo, por lo que no consumen valores de RNG. La forma de los diccionarios y el orden de las claves de `new_world` son los mismos que en 0.6.4.

## 3. Semilla, topología, datos y validación

- `new_world(seed)` conserva el único `random.Random(seed)` **local** para dibujar superficies, galerías y depósitos. Seis semillas permiten verificar mundos diferentes sin estado global, sin UUID y sin depender del orden de hashes de Python. Las mutaciones sobre un mundo no afectan a otro, aunque comparta semilla.
- `WorldDefinition` declara una ABI informativa del entorno `isla_v1`, versión de generador **1**, niveles `("0","-1")`, dimensiones y símbolos tomados de catálogo. `describe()` crea copias simples para inspección; **no modifica la partida ni revela conocimiento al LLM**.
- `IslandWorldGenerator.generate(seed)` construye la topología y ejecuta `validate_generated_world` **sobre mundos recién generados**. El validador comprueba capas, anchura/altura, símbolos, sitios, alineación de cueva/salida, correspondencia exhaustiva de depósitos con terrenos productivos, reservas iniciales **2–6**, y coordenadas de celdas reveladas. No arregla en silencio datos inválidos ni genera más RNG.
- El validador estricto **no se aplica a partidas ya existentes**. Una partida avanzada puede tener estructuras, roca excavada, agua alterada, recursos agotados, niveles migrados o depósitos a cero. Tratarla como un mundo *recién generado* sería un error; sigue usando el guardado/migración de la etapa 02 y sus invariantes históricos.
- La frontera `Environment.make_world` continúa permitiendo nuevos entornos que implementen el puerto `WorldGenerator` y su propio adaptador, sin registrar un segundo mundo de prueba ni modificar el escenario de Nilo. `register_environment` y `get_scenario` conservan sus contratos.
- `world.py` conserva `reveal` como alias exacto: el orden inicial de descubrimiento no se recalcula desde `set`. El análisis de qué observa Nilo se hará en la etapa 14; aquí solo se fija la topología verdadera.

## 4. Pruebas y huellas de referencia

[`tests/test_mundo_08.py`](https://github.com/mxlzz/Nilo_public/blob/refactor/0.7/tests/test_mundo_08.py) incorpora hashes **externos al nuevo generador**, calculados con el algoritmo original de 0.6.4 sobre `json.dumps(world, ensure_ascii=False, separators=(",",":"))`. Abarcan absolutamente todo el dict: niveles, depósitos, sitios, estructuras vacías, campos auxiliares y secuencia de celdas conocidas al inicio.

| Semilla | SHA-256 del mundo completo |
| ---: | --- |
| `0` | `0ee59a26fe2eb4baa3ca65867e5972a10572459f59832729db46f43359f3f0e4` |
| `1` | `17b55dfe193b4b3895e03d9d8816d53ce88eabab49c0b4555cc0f8b561580cb4` |
| `42` | `663457a9a0213eca8629be1b605f61dfda03d9e94864afe51cc067855df7cb4c` |
| `7321` | `ae1b04e016a93c1b2bad5ec0ce9297aab78f1ef828fb6fa0df93aab2409d39f9` |
| `9821` | `7b6e50aa927118c3e4b4ab50ef09e90b928adef33929e08fa80b8541376e88ce` |
| `987654321` | `9bf53ad60377ea7e8dabb0b31e57f420f0b4c61b065fcc7ca8a30df3193325d0` |

Las pruebas comparan tres accesos a la topología (`world.new_world`, `ISLAND_GENERATOR.generate`, `IslandEnvironment.make_world`) y `initial_state` para las mismas semillas; comprueban dos procesos Python con `PYTHONHASHSEED` y `random.seed` diferentes; confirman correspondencia completa de depósitos con el catálogo y que `reveal` no añade duplicados. Incluyen mutaciones sintéticas de generaciones nuevas inválidas (nivel ausente, dimensiones, símbolo sin catálogo, cueva desalineada, sitio desplazado, recursos faltantes/imposibles y revelaciones fuera del mapa) que deben fallar sin alterar el objeto.

La auditoría AST [`tools/auditar_mundo_08.py`](https://github.com/mxlzz/Nilo_public/blob/refactor/0.7/tools/auditar_mundo_08.py) impide un `new_world` duplicado en `world.py`, el uso de RNG global o imports hacia cognición, HTTP, aplicación o los handlers físicos desde `nilo_runtime/worlds`. Verifica además que la pasabilidad, símbolos productivos y terrenos declarados coincidan con `catalogo`.

El [workflow de validación](https://github.com/mxlzz/Nilo_public/actions/workflows/validacion.yml) ejecuta el auditor y las regresiones focalizadas antes de la suite completa. El ZIP portable incluye `worlds/__init__.py`, `contracts.py`, `island.py` y verifica dentro de su carpeta **extraída** la huella `7321`.

**Puerta de salida superada.** Run integral `referencia privada #41901014954` (`referencia-historica-privada-actions-runs-41901014954`), **success** sobre el commit definitivo de código+tests `a8594a118b8cc85fc99e330519562049874d0cd5`: **735 pruebas ejecutadas (1 omitida)**, 8 focalizadas de generación y 9 de orquestador, auditorías de arquitectura/identidad/acciones/núcleo/mundo, escenarios físicos, ZIP extraído, continuidad RNG/IDs entre procesos y replay con fingerprint exacto `9c4d43a5815fb042e06e32789b7dc6606023c3eb0634fe08dd7ad90616dc5c24`. Run histórico `referencia privada #41900978760` (`referencia-historica-privada-actions-runs-41900978760`), **success** tras el aislamiento final de `PASSABLE`: **seis SQLite sintéticas** de 0.5.9.4.2/0.6.0/0.6.4 importadas en copias sin alterar originales y seis semillas comparadas con 0.6.4. Los hashes topológicos y el bloque fuente de generación permanecen idénticos. No quedan condiciones de CI pendientes.

## 5. Qué se preserva y qué falta

Se conserva el escenario de Nilo, los puntos iniciales, la posición del refugio, el pasillo de acceso a cueva, los signos del mapa, recursos y cantidades por semilla, orden inicial de descubrimiento, catálogo de materiales, las dos capas originales, el save v5, navegación y física heredadas. El motor no necesita reasignar metas ni introducir necesidades nuevas para poder cargar un mapa.

La extracción deja preparadas las siguientes responsabilidades sin anticiparlas: **09** navegación, BFS y accesibilidad; **10** depósitos mutables e inventarios; **11** materiales/objetos; **12** capacidad física de interacciones; **14** proyecciones de percepción y privacidad de casillas. El hecho de que `world.py` siga agrupando estos handlers es deuda temporal explícita, no un segundo generador.

**Etapa 08 cerrada. Siguiente: 09 · Navegación y exploración, habilitada y aún no iniciada.** `main`, `VERSION`, release 0.6.4 y partidas personales no se modifican en esta etapa.
