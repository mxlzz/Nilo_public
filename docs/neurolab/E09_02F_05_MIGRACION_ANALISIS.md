# E09.02f.5 — mapa preliminar de migración de dendritas C1

**Fecha:** 2026-11-21. **Estado:** ingeniería inversa estática de las dos rutas de migración; **no hay módulo ejecutable ni prueba de equivalencia aún**.

**Fuente:** `Creatures.exe` PE32 aportado por el usuario; SHA-256 `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7`. Direcciones virtuales del binario específico, no de otros ejecutables. No se ejecutó ni se distribuyó el archivo.

## 1. Condiciones previas a la migración

En el bucle neuronal principal (VA `0x40467A–0x4047E2`), la SVRule de pérdida puede decrementar la fortaleza de la dendrita. Al llegar a cero, se borran susceptibilidad, STW y LTW y se incrementa un contador de conexiones agotadas. El bucle revisa el tipo de migración configurado genéticamente (en una estructura de clase dendrítica); después existen dos rutas:

- `migration_type=1`: el bucle invoca **VA 0x404A80** para neuronas/entradas activas en la fase posterior.
- `migration_type=2`: el bucle invoca **VA 0x404B90**, que opera sobre fuentes conjuntivas con restricciones adicionales.

El `dad1.gen` original tiene Decision con tipo 1 y Concept con tipo 2. Las rutas diferenciadas **están en el ejecutable**; no son reglas inventadas del proyecto.

## 2. Tipo 1 — ruta de reemplazo de fuente (0x404A80–0x404B8A)

Observaciones directas de instrucciones:

1. Evalúa condiciones de actividad de la neurona receptora, existencia de fuente y presencia de una dendrita sin fortaleza (`strength=0`) en el conjunto.
2. Usa el generador de números aleatorios del motor para elegir entre neuronas candidatas del lóbulo de origen correspondiente.
3. Comprueba la fuente candidata contra las conexiones existentes del mismo conjunto; **si coincide con otra fuente, sale sin conectar esa candidata** (la rutina vista no contiene reintentos iterativos dentro de ese camino).
4. Cuando acepta un nuevo origen, escribe un puntero hacia la neurona fuente en el slot desconectado.
5. Inicializa **STW y LTW al mismo valor aleatorio dentro del rango genético configurado**, y **strength** según su rango genético; actualiza un contador de migración/agotamiento.
6. No modifica la cantidad de slots de dendrita, sino que reutiliza un slot; no se observó creación irrestricta de nuevas neuronas.

**Límite:** no se ha inferido aún el valor exacto/criterio de todos los flags en llamadas ni el contrato del PRNG de Creatures. No afirmar equivalencia de la selección de fuentes.

## 3. Tipo 2 — ruta para combinaciones de conceptos (0x404B90–0x404EA1)

Observaciones directas:

1. Obtiene el conjunto de neuronas fuente disponible y **reordena aleatoriamente candidatos** por intercambios de índices.
2. Construye conjuntos de entradas a partir de candidatos, con **controles de repetición** de fuentes dentro de la combinación.
3. Calcula una **firma derivada de sumas y productos** de los punteros fuente (con reducción parcial a16 bits), y la compara con firmas de otras unidades de la misma familia para impedir duplicaciones exactas según su criterio implementado. Esta estructura es una reconstrucción por lectura del flujo máquina; no es una función matemática especificada públicamente.
4. Si encuentra una combinación admisible, asigna fuentes y vuelve a inicializar **STW/LTW y fortaleza** dentro de rangos del genoma.
5. Existen rutas de fallo/no-reemplazo que ponen a cero los pesos y la fortaleza y mantienen la falta de conexión.
6. La búsqueda es finita y su comportamiento depende del PRNG, del orden de fuentes y de las firmas calculadas.

**Límite:** todavía no se han reconstruido formalmente todos los bucles, las condiciones de desempate, los códigos de fallo y los estados de neuronas implicadas; no crear una implementación “fiel” basada solo en esta interpretación de alto nivel.

## 4. Comparación con E07 y mínimos para implementación

En el ensayo E07 propio dos slots se reemplazaban por reglas simples de atrofia/uso, y rendían igual que una caché LRU. **Eso NO reproduce estas dos rutinas**: la versión histórica está condicionada por actividad, conjuntos de fuentes candidatos, restricciones de duplicados, rangos genéticos y un PRNG.

Antes de escribir un migrador C1:

- [ ] Determinar estructura y significado completo de los argumentos de `0x404A80` y `0x404B90`.
- [ ] Identificar el PRNG x86 utilizado y su estado; decidir si emular semilla exacta o inyectar una fuente de azar verificable en laboratorio.
- [ ] Crear ejemplos canónicos de reemplazo, duplicado y ausencia de candidatos, con resultado manual y direcciones que lo soporten.
- [ ] Aislar la regla para cambiar fuente sin violar conteos genéticos por lóbulo y tipo.
- [ ] Mantener modelado explícito de condiciones donde la migración no ocurre (fuente duplicada, inactividad, slot ocupado).
- [ ] Si no puede verificarse byte a byte, implementar como **variante H aproximada** y etiquetar las condiciones en las que diverge.

**Siguiente trabajo:** E09.02f.5a especificación operacional rigurosa y oráculos de ambas rutas; f.5b implementación solo tras satisfacer esos prerequisitos. **G00-H y G09 aún abiertas.** No requiere nuevas subidas de archivos.
