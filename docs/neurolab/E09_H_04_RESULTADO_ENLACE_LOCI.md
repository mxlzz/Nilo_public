# E09h.4 — enlace receptor genético → CHEM → SVRule de C1 (verificación estática)

**Fecha:** 2026-11-21. **Estado:** G-H4-ADAPTER y G-H4-X86 verificadas en su alcance delimitado. G00-H/G05/G09 global siguen abiertas.

## 1. Fuente primaria y procedencia

El usuario adjuntó de nuevo el ejecutable original, leído **directamente** como PE32 x86 sin instalarlo ni ejecutarlo.

- Tamaño: 387.072 bytes.
- SHA-256: 548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7, **idéntico** al EXE de E09f/h.1–h.3.
- Se verificaron frente a bytes reales **31 firmas de instrucciones x86**, una dirección de vtable y **cuatro entradas de tabla de saltos** con sus desplazamientos byte a byte. Inspección local: 31/31 firmas correctas.
- [Verificador reproducible](../../experiments/neurolab/e09_historical_locus_audit.py), [tests sintéticos](../../experiments/neurolab/tests/test_e09_historical_locus_audit.py), [fixture derivado del original](resultados/e09h4_inspeccion_estatica_original.json). **No se publicó ni EXE ni desensamblado completo.**
- Los **seis genes de receptor** proceden de [E09h.3](resultados/e09h3_receptores_genoma_original.json), previamente verificados contra el GEN original. No se volvió a recibir GEN en esta intervención.

## 2. Cadena de punteros verificada en el ejecutable

1. **Objeto cerebral:** en 0x40AF89 se almacena CBrain en Norn+0x2C18. CBrain instala una vtable de loci en brain+4 (0x401788, valor 0x43302C); su primera entrada apunta a **0x4030E0**.
2. **Lectura de genes receptores:** 0x421970 carga los campos órgano/lóbulo/locus. Con órgano 0, 0x421A09..0x421A18 usa Norn→brain+4 y despacha por vtable con parámetros (kind=0, lobe, locus).
3. **Resolver de lóbulo:** 0x4030E0..0x403103 reduce el lóbulo módulo el número de lóbulos y calcula brain+8+200*lobe (stride 0xC8). La tabla en 0x403128/0x40312E elige el caso por **número de locus genético**.
4. **Desplazamientos exactos:** receptor loci **13,14,15,16** saltan a **0x403183, 0x40318B, 0x403193, 0x40319B**, respectivamente, y cada caso agrega el desplazamiento **+0xC3,+0xC4,+0xC5,+0xC6** relativo al inicio del lóbulo. Estos cuatro bytes son CHEM0..CHEM3 de ese lóbulo, no concentraciones del pool global.
5. **Enlace de escritura:** 0x421A6F guarda el puntero resuelto dentro del registro de receptor (campo +8); 0x42200C..0x42200F obtiene el puntero y escribe el byte receptor. **No recalcula el locus genético en cada tick.**
6. **Lectura por SVRule:** 0x403E2C/0x403E38/0x403E42/0x403E4C leen las cuatro variables del lóbulo al crear la tabla local; se copian en stack +0x45..+0x48. El intérprete 0x403FD1 usa stack[0x40+opcode], por lo que **opcode5=CHEM0, 6=CHEM1, 7=CHEM2, 8=CHEM3**.

Se verifica el destino efectivo del byte receptor y su lectura por SVRule **en el flujo estático de esta versión exacta**. Corrobora [CDN/LCUS](https://lisdude.com/cdn/76.html) y [C1 Brain Guide](https://zenzoa.com/creatures/c1-brains.html), pero ya no depende exclusivamente de esas fuentes secundarias.

## 3. Hallazgo adicional: inicialización con valor nominal

En 0x421AC6..0x421ACF, si se obtiene un locus válido, el cargador de receptores escribe **nominal** en el destino antes de ejecutar las fases de química. Esto es diferente de la posterior transferencia desde concentración.

Con los seis genes originales de E09h.3 y un estado inicial de ceros, el enlace de genes deja:

- **Decision, lóbulo 6:** CHEM0..3 = (0,0,16,16).
- **Concept, lóbulo 8:** CHEM0..3 = (0,4,0,0).

Tras el pool artificial de E09h.3 (49=12,50=12,52=5,53=12), los receptores dejan Decision=(11,11,5,16) y Concept=(0,0,0,0). **Son oráculos estáticos y sintéticos, no valores observados durante el juego.** Se agregó [inicialización de nominales](../../experiments/neurolab/e09_historical_locus.py) y sus tests.

**Duplicados:** 0x421A26..0x421A5D busca un registro con el mismo puntero resuelto y lo reutiliza; los genes posteriores sobrescriben campos. Nuestro adaptador sigue **rechazando deliberadamente colisiones** como convención conservadora de laboratorio: no se demostraron todas las rutas de conflictos ni hay colisiones entre estos seis receptores.

## 4. Puertas y limitaciones

- **G-H4-ADAPTER:** mapeo y tests sobre seis genes, aislamiento de lóbulos, valores nominales y SVRules.
- **G-H4-X86:** **verificada estáticamente** para el SHA del EXE recibido: resolver, saltos, inicialización, escritura de receptor y lectura SVRule.
- **CI previo:** [run 44947076331](https://github.com/mxlzz/Nilo_public/actions/runs/44947076331), 339 tests y dos expectedFailure históricos; los nuevos tests de auditor y nominales requieren una nueva CI para finalizar.
- **Sin extrapolaciones:** todavía no hay Norn ejecutado ni trazas de concentraciones en tiempo real, reloj global exhaustivo, emisores completos, cruce de todas las rutas condicionales, ni aprendizaje neuronal integrado. **G00-H/G05/G09 siguen abiertas**.

El primer intento de leer el EXE desde la Biblioteca fracasó por permisos, pero **el bloqueo desapareció** al adjuntarse de nuevo el archivo con bytes accesibles. Se conserva este antecedente para trazabilidad.

## 5. Próximo eslabón del plan

**E09h.4 se cierra solo en su alcance de enlace estático.** Para completar el camino químico histórico antes de volver al problema de crédito causal, el paso siguiente será preregistrar y verificar **emisiones genéticas** hacia el pool químico, incluyendo valores iniciales, muestreo y condición de escritura, sin añadir neuronas ni tunear g.10.

**PR #103 draft; no merge a main ni cambios a Nilo 0.7.**
