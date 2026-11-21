# E09.02f.5a — especificación operacional preregistrada de migración C1

**21/11/2026. Estado:** especificación previa a implementación `c1_migration.py`. Se extrajo inspeccionando directamente `Creatures.exe` (PE32 x86, SHA-256 `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7`). El archivo no se ejecutó ni se distribuye.

Se contrastó de forma independiente con [C1 Brain Guide, Migrating Dendrites](https://zenzoa.com/creatures/c1-brains.html). **La guía es secundaria**; las instrucciones y direcciones VA de este ejecutable son la evidencia primaria. No identificar esta compilación de agosto de 1997 con el primer motor de 1996.

## A. Datos de ejecución y fuente de azar

- Función importada por IAT `0x441088`: **`rand` de la CRT de Microsoft** (constatado en tabla de importaciones). Hay también `srand` en `0x4410A8`. No se reconstruyó el estado global del PRNG en la partida ni su semilla inicial.
- Las dos rutas usan el resultado de `rand()` mediante **módulo del número de candidatos/rango** (`cdq; idiv`). Esto implica selección con sesgo de módulo si el rango no divide el rango entero del PRNG.
- Para pruebas **inyectar secuencia explícita de valores devueltos por rand**, no usar `random.Random` de Python como sustituto del PRNG real.
- Modelo de `SourceNeuron`: puntero/identificador entero positivo (identidad que compara el binario), `exclusive_lobe` como byte en `neuron+0x0f`. No mezclar índice ordinal con puntero físico en la función checksum.
- Una clase de dendritas contiene slots con puntero fuente, STW, LTW, strength y susceptibilidad. Los rangos `initial_ltw_min/max` e `initial_strength_min/max` se toman del **genoma por clase**.

## B. Tipo 1 / Decision-style: VA 0x404A80–0x404B8C

1. Solo se llama desde bucle de migración para neuronas con `output>0` y clase con `migration_type=1`, después de actualizar conexiones.
2. Si no hay fuentes **activas** en el lóbulo origen, no hay migración.
3. Buscar la **primera dendrita con strength=0**, recorriendo la clase en orden. Si no hay, no migrar.
4. Elegir una candidata por `active_sources[rand()%n]` (**una extracción**). Si su puntero coincide con **cualquiera** de las fuentes existentes en la misma clase, **abortar sin reintento este tick** (VA 0x404B19–0x404B23).
5. Si no coincide, sobrescribir el puntero de la dendrita suelta. Sortear **una vez** LTW en el intervalo genético inclusivo y copiar ese mismo byte a STW (VA 0x404B4F/0x404B52). Sortear otra vez strength en el intervalo genético inclusivo y escribir (VA 0x404B6F). La susceptibilidad estaba en cero después de desconexión.
6. Se decrementa un contador de conexiones sueltas si era >0 (VA 0x404B72–0x404B7F). Para prueba aislada, representar como cambio de estado, **no fingir estructura del contador de toda la red**.

**Oráculos tipo1:** clase `[(A,stw=30,ltw=20,str=4), (B,stw=0,ltw=0,str=0)]`, pool activo `[A,C]`. Azar de fuente0→A duplicada, sin cambio ni reintento (una llamada a rand). Fuente1→C aceptada; con rango LTW 5..7, strength 2..4 y rand posteriores 1,2, resulta nuevo `(C,stw=6,ltw=6,str=4)`. Con output0 o pool vacío, no consumir azar ni cambiar conexiones.

## C. Tipo 2 / Concept-style: VA 0x404B90–0x404EA1

**Selección de neurona receptora (caller 0x40498E–0x4049E7):** hay una búsqueda con cursor descendente del índice más alto con actividad relevante y conexiones sueltas; el contador se restablece al agotar el recorrido. **No reconstruimos todavía la totalidad del scheduler ni la transición de WTA.** La función aislada recibe un destinatario explícitamente `selected`, nunca elige arbitrariamente un Norn.

**Dentro de la ruta:**
1. Guardar copia de los punteros antiguos de **todos los slots de la clase**.
2. Si `#active_sources < #slots`, no aplicar nueva combinación.
3. Reordenar **el arreglo activo de fuentes**: para i=0..n−1, j=`rand()%n` e intercambiar elementos i,j. La rutina x86 opera **in situ** sobre el arreglo de fuentes del lóbulo origen (VA 0x404C15–0x404C3D). La prueba debe exponer el orden resultante.
4. Intentar ventanas **contiguas** de longitud k (#slots) empezando en posición0, luego1, ... hasta n−k (VA 0x404C4A–0x404E34).
5. Si dos fuentes de una ventana tienen **el mismo campo `exclusive_lobe` NO CERO**, rechazar inmediatamente la ventana, sin sortear pesos (VA 0x404C6A–0x404CA6). Los grupos cero no se consideran conflictivos.
6. Para una ventana admisible, escribir los nuevos punteros de **todos** los slots y sortear para **cada** slot LTW inicial inclusivo, escribir STW=LTW y sortear strength (VA 0x404CCC–0x404D32).
7. Calcular firma de la combinación **sobre los punteros enteros**, NO sobre sus índices ordinales: `((sum(ptr_i) & 0xffff)<<16) | (product(ptr_i) & 0xffff)` (VA 0x404D5F–0x404D78). Suma y producto de máquina son 32 bits con overflow; la firma no es garantía de igualdad de combinaciones.
8. Comparar firma con la de otras neuronas **activas** de mismo lóbulo receptor y mismo número de conexiones de la clase (VA 0x404D9D–0x404DFD). Si coincide, rechazar la ventana **aunque las fuentes sean distintas** (colisión de checksum), continuar con la ventana siguiente. Las neuronas comparadas son suministradas por el caller y excluyen explícitamente al destinatario.
9. Si una ventana se acepta, conservar el recableado, actualizar cursor de migración del lóbulo y terminar.
10. Si se agotan todas las ventanas: **restaurar punteros anteriores** de todos los slots, pero limpiar STW, LTW y strength (VA 0x404E49–0x404E65). No afirmar que esa restauración los vuelva conexiones funcionales.

**Oráculos tipo2:** pool [A(1),B(1),C(2),D(0)], k=2. Usar draws fuente `[0,1,2,3]`, que dejan orden igual, para inspeccionar ventanas A-B (rechazada exclusividad), B-C (aceptada) con draws de dos pesos por cada slot. Debe devolver misma capacidad k=2. Si firma B-C aparece en otro concepto activo, descartar esa ventana y probar C-D. Cuando todas colisionan o incumplen exclusividad, restaurar punteros viejos pero dejar pesos/strength0. Si pool menor que k, no intentar combinaciones.

**Colisión real comprobable:** punteros (0x10000,0x20000) y (0x14000,0x1c000) son dos pares diferentes pero con la misma suma 0x30000 y producto bajo16=0; comparten firma. El motor podría rechazar una combinación diferente por este mecanismo de filtro.

## D. Qué podemos validar y qué no

**G f.5b:**
- [ ] tests oráculo Tipo1 y Tipo2, sin cambiar resultados preregistrados;
- [ ] fuente activa, rechazo duplicados/exclusividad/firma, ventanas, rangos inclusivos, número fijo de slots, restauración, consumo de rand y checkpoint del estado;
- [ ] variaciones de rangos y 20 secuencias reproducibles de rand inyectado;
- [ ] regresiones de NeuroLab E01–E09f.4.

**No afirmar por G f.5b:** que conocemos la secuencia global de rand, toda la planificación por cursor/actividad neuronal, la semántica de nacimiento, el orden completo de fases cerebrales o el comportamiento efectivo de C1 en tiempo real. Para un emulador bit a bit haría falta contrastar todos esos elementos, potencialmente mediante ejecución controlada del juego en un entorno aislado.

**Después:** E09.02g — comparar una variante de microcerebro histórico contra E09e de cinco neuronas, anotando qué conexiones y flujos químicos son supuestos experimentales y qué operaciones vienen del ejecutable.
