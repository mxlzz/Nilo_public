# Catálogo modular de Nilo · primera etapa (0.5.9.3.16)

Esta es una **extracción conservadora de datos** del entorno `isla_v1`, no un sistema de extensiones dinámicas. Los valores originales y las reglas del motor se conservan para no alterar las corridas ni los replays. No equivale todavía a la arquitectura integral 0.6 (#30).

## Archivos

- `catalog/materiales.json`: propiedades físicas del motor para los siete materiales existentes (`world`: dureza, resistencia, peso, combustible, brillo; `physics`: densidad/permeabilidad; `recoverability`: recuperación al desmontar).
- `catalog/terrenos.json`: símbolos, etiquetas, yacimientos, fuentes, alias de inspección/recolección y transitabilidad del escenario isla.
- `catalog/objetos.json`: palabras y formas reconocidas por la implementación actual, geometrías de piezas y tipos de uniones. **No es un catálogo cerrado de invenciones ni un recetario.**
- `catalogo.py`: lectura y validación tipada de estos tres archivos, conversiones compatibles con las antiguas constantes y creación de copias independientes por partida.

`world.py`, `physics.py`, `mechanics.py`, `construction.py` y `environments.py` consumen este catálogo. Los nombres de variables conservan sus interfaces históricas para facilitar las pruebas y la migración.

## Contratos y límites

1. **Solo archivos confiables del paquete:** el agente no puede editar rutas, instalar código ni elegir un JSON arbitrario. Cualquier versión del catálogo requiere pruebas y una nueva entrega revisada.
2. **Propiedades reales ≠ conocimiento de Nilo:** estos valores se aplican internamente y no se vuelcan al prompt como mediciones. Nilo debe seguir descubriendo propiedades mediante observación, experimentación y evidencia.
3. **Sin nuevos fenómenos:** cambiar un número puede alterar la física; esta entrega conserva los anteriores. No se añaden leyes, materiales, especies ni recetas de invención.
4. **Instancias distintas:** las partidas reciben copias de los materiales. Modificar materiales aprendidos o sintetizados dentro de una partida no cambia el catálogo global ni otras partidas.
5. **No cargar catálogos incompatibles silenciosamente:** el cargador rechaza campos físicos ausentes, números no finitos, IDs de material no existentes, símbolos inválidos, entradas duplicadas y esquemas distintos a `schema:1`.
6. **Compatibilidad conservada:** replays y pruebas de escenario validan que el mismo estado y secuencia de decisiones resulten iguales. Las partidas anteriores mantienen sus materiales históricos; no se reconstruyen desde los nuevos JSON.

## Qué queda para 0.6 (#30, #8, #5)

- Un **registro de capacidades** con `validate → prepare → execute → verify → ActionResult` sin modificar varios archivos centrales por operación.
- Manifiestos con versiones, dependencias, compatibilidad y activación por partida, más migraciones no destructivas.
- Un primer módulo físico vertical, preferentemente **transferencia entre recipientes**, con conservación real del contenido y pruebas de resultados.
- Reemplazar los efectos físicos atribuidos a **nombres/categorías** de objetos o refugios por propiedades geométricas y composicionales verificables.
- Separar entidades vivas/organismos cuando haya estados y operaciones biológicas realmente modelados. Crear ahora un JSON vacío de organismos no proporcionaría funcionalidad.
- Asegurar que el segundo módulo nuevo pueda incorporarse sin editar el dispatcher de `world.py`, el prompt de `brain.py` ni el bucle de `nilo.py`.

## Cómo extender con seguridad

Para incorporar un nuevo material **no alcanza con sumar un nombre al JSON**: deben existir referencias consistentes, reglas de aparición, descubrimiento, fuentes de recolección y ensayos que puedan medir su comportamiento. No es un procedimiento disponible directamente para Nilo. Los cambios son revisión de desarrollo y se comparan en una **copia aislada de una partida**.

El alcance se seguirá en [issue #30](https://github.com/mxlzz/Nilo_public/issues/30). El ciclo de propuestas de Nilo se desarrolla aparte en PR `referencia privada #72` (`referencia-historica-privada-pull-72`) y no se integra sin su propia evaluación.
