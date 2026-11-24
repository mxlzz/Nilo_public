# E09.02i-I3c.2 — preregistro de invocadores históricos de migración

**21/11/2026.** Inspección exploratoria anterior a la implementación del auditor; el EXE original sigue siendo fuente primaria: 387072 bytes, SHA256 548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7, PE32 image base 0x400000. Se documenta el alcance acotado, **no** se afirma fidelidad general.

## Hipótesis a falsar mediante firmas reales

- H2.1: dentro del flujo neuronal posterior a WTA (región 0x404911..0x4049E9) se procesan dos clases con marcador de tipo 1 en 0x404922, y cada célula recibe migración tipo1 sólo cuando el campo byte+2 no es cero, mediante la llamada directa 0x40494C a 0x404A80.
- H2.2: en la fase siguiente, marcador tipo2 (0x404992) y selección de índice guardado en arreglo temporal (0x404997). El valor -1 cancela, otro valor calcula registro neuronal con stride16 y llama desde 0x4049C2 a 0x404B90.
- H2.3: el fragmento de WTA 0x4048CC..0x404911 antecede a estas puertas y selecciona la salida de una célula, pero no se reconstruye aquí el estado de todos los otros callers ni el RNG del EXE.
- H2.4: las llamadas usan el mismo código de migración que el módulo C1 derivado previamente, pero **las condiciones del scheduler, identidad de punteros y random global** siguen siendo requisitos separados para integración.

## Evidencia/falsación y límites

- Auditar sobre el EXE hash-verificado las firmas x86 exactas de puertas de tipo, selección de célula/índice y cálculo de stride, y las dos llamadas E8 relativas. Toda firma alterada debe producir fallo. CI prueba un FakePE sintético con cambios adversariales, jamás redistribuye EXE.
- Un test del scheduler estático no es una simulación: no predice cuándo una célula tendrá salida no cero, ni prueba el número real de migraciones en C1, ni define aún la semántica de migrar una conexión en C1ContextBrain reducido.
- Preservar la evidencia derivada, errores y estado canónico. **G-I3c2-CALLSITE** cerrará sólo si las firmas coinciden con el EXE auténtico y el auditor es reproducible; G-HISTORICAL-SCHEDULER y G05/G09 seguirán abiertas.
- No usar datos nuevos de aprendizaje, no cambiar la arquitectura ni crear un migrador nuevo.
