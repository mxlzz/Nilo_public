# E09.02f.6 — preregistro: intérprete completo de SVRules C1 y snapshot por dendrita

**21/11/2026. Antes de codificar.** Fuente primaria: flujo de instrucciones del `Creatures.exe` PE32 del usuario, SHA256 `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7`.

## Evidencia estática

- Las reglas neuronales usan intérprete x86 VA `0x403FAF–0x4040B6`.
- Las de susceptibilidad, refuerzo, ganancia y pérdida de fortaleza usan **la misma semántica de operadores** en fragmentos en VA `0x4041C2–0x4047C4`.
- Los valores para **una dendrita** se copian a una tabla local antes de evaluar sus SVRules: `input` = source.output (índice16), `susceptibility` (18), `stw` (19), `ltw` (20), `strength` (21). En x86 se leen desde `[dendrite+0x6..0x9]` y quedan almacenados en posiciones relativas de la tabla `[esp+0x50..0x55]`.
- El cálculo de susceptibilidad y STW cambia bytes de la dendrita posteriormente, pero las reglas genéticas de **ese mismo ciclo** leen la **tabla originalmente capturada**, no los valores nuevos, salvo recarga que se identifique explícitamente. Las tasas, el tiempo y el resultado químico de cada regla son independientes.
- Operandos genéticos 0..21 según la [C1 Brain Guide](https://zenzoa.com/creatures/c1-brains.html) (la fuente secundaria ayuda a nombrar los índices). Byte0 termina la regla.
- `TRUE` (22) aborta la SVRule con resultado0 si el acumulador actual es0, o permite continuar (x86 `0x403FF3–0x403FFB`).
- `PLUS` 23 y `MINUS`24 consumen el **siguiente byte** como ID de variable y saturan 0..255 por operación.
- `TIMES`25 consume el siguiente ID y usa `(acc*var)>>8`.
- `INCR`26 y `DECR`27 son saturados, no leen operandos adicionales.
- El intérprete de laboratorio rechazará opcodes desconocidos o reglas sin terminador: **contrato de validación seguro**, no afirmación de que el EXE original se comportaba así ante genes corruptos.

## Interfaz y oráculos

Crear `C1SVTable` con las 18 variables genéticas y químicos CHEM0..3 como bytes; la tabla local es **inmutable**. `evaluate(rule:bytes, table)` devuelve byte0..255 y, opcionalmente, traza de opcodes/resultados sin modificar el input.

**Fixtures establecidos antes del código:**
1. `OUTPUT TRUE INPUT` (10,22,16,0...) con OUTPUT80 e INPUT127 → **127**; con OUTPUT0 → **0**.
2. `SUSCEPT TRUE CHEM0 TRUE STW` (18,22,5,22,19,0...) con SUSCEPT4, CHEM0=255, STW30 → **30**; con cualquiera de SUSCEPT/CHEM0 en cero → **0**.
3. `OUTPUT TRUE CHEM0` con OUTPUT90 CHEM0=51 → **51**, OUTPUT0 →0.
4. `CHEM2` → valor químico de índice7 (p. ej. 45).
5. `STATE PLUS TYPE0 MINUS TYPE1`, datos80/240/200 → **55**, no120 (saturación intermedia).
6. `CONST255 TIMES CONST255` → **254**; `CONST64 PLUS CONST255`→255; `CONST0 DECR`→0; `CONST255 INCR`→255.
7. `C1SVTable` con valores fuera 0..255, rule con operador incompleto y reglas sin terminador → excepción explícita.
8. **Snapshot:** si la dendrita comienza SUSCEPT0/STW0, una regla de gain `SUSCEPT TRUE CHEM0 TRUE STW` da0 aunque después de otro cálculo dentro del mismo tick la dendrita llegue a SUSCEPT4/STW3; su resultado en ese tick sigue0. Un *nuevo snapshot del tick siguiente* puede dar3.
9. Reproducibilidad con 20 semillas y regresiones E01–E09f.5.

**G f.6:** pasar oráculos, publicar manejo literal de `TRUE` y preservar variables capturadas; **no equivale todavía a integración neuronal ni a bioquímica ambiental completa**.

**Siguiente E09.02g:** paso integrado de dendrita usando `C1SVTable` congelada y las transiciones ya verificadas, seguido de un microcerebro de cinco neuronas con modelos experimental e histórico separados. Registrar antes de implementar y probar.
