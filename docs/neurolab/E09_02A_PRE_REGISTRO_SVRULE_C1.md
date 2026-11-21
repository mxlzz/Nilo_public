# NeuroLab — E09.02a: reconstruir el núcleo de SVRules C1 antes de integrar la mente

**Pre-registro fechado 21/11/2026, antes de programar este componente.** Línea histórica H (reglas de genes reales) + pruebas propias N (cálculo numérico). No implica emulación completa de Creatures 1 ni modifica el Nilo existente.

## Motivación y evidencia

El usuario aportó `dad1.gen` de su imagen de CD C1. Su SHA256 y la comparación con el parche están documentados en [E00_GENOMA_ORIGINAL_COMPARACION.md](E00_GENOMA_ORIGINAL_COMPARACION.md).

Tres genes neuronales codifican SVRules **no vacías**:
- **Decision (lóbulo 6):** bytes `09 17 0C 18 0D 00 00 00` = `STATE PLUS TYPE0 MINUS TYPE1`.
- **Attention (lóbulo 7):** bytes `09 17 0C 17 0D 00 00 00` = `STATE PLUS TYPE0 PLUS TYPE1`.
- **Concept (lóbulo 8):** bytes `0E 00 00 00 00 00 00 00` = `ANDTYPE0`.

**Estas reglas son datos del genoma, no fórmulas inventadas.** Aun así, el ejecutable determina aritmética saturada, orden temporal y significado de TYPE0/1, incluidos sus límites. No afirmar equivalencia temporal hasta validarlo.

## Unidad implementable mínima

Una función determinista para evaluar **solo esas tres SVRules completas** sobre un estado abstracto:
- `state` byte0..255.
- `type0` byte0..255 y `type1` byte0..255.
- `and_type0` byte0..255: el valor de TYPE0 cuando todas las dendritas de clase0 están activas; cero si alguna está inactiva.
- El resultado de evaluación se satura a byte 0..255. Se fija como **convención propia N** la saturación **al final**, no entre operadores, hasta tener mejor evidencia.
- No agregar química, recurrencia, refuerzo, cuerpo, mundo ni ejecuciones de estado continuas.
- El módulo falla de manera explícita ante reglas desconocidas en lugar de sustituirlas por un cálculo genérico incorrecto.

## Oráculos previos al código

1. Decision `state=80,type0=110,type1=30` → 160.
2. Decision `state=80,type0=20,type1=130` → 0 (saturación).
3. Attention `state=0,type0=50,type1=30` → 80.
4. Attention `state=250,type0=30,type1=30` → 255.
5. Concept `and_type0=90` → 90.
6. Concept `and_type0=0` aunque `type0=90` → 0, porque una dendrita está inactiva.
7. Para todos los opcodes inválidos/longitudes no8, generar excepción con causa; no corregir genoma silenciosamente.
8. 20 secuencias pseudoaleatorias con misma semilla deben reproducir resultados; no pueden cambiar pesos ni parámetros del NeuroLab anterior.
9. Comprobar que las tres reglas se leen literalmente del `dad1.gen` del usuario mediante el inspector externo, y que los 9 lóbulos del archivo del CD y del parche son iguales; ese contraste ya se hizo fuera de CI y quedó documentado. CI solo ejecutará fixtures sintéticos y las reglas fijas comprobadas, **no alojará el archivo del juego**.

**Puerta de salida E09.02a:** interpretar correctamente reglas genéticas demostrables con oráculos independientes, preservar regresiones E01–E08, y documentar ambigüedad de aplicación histórica. No equivale a «mente integrada» (G09 continúa abierta).

**Siguiente paso E09.02b:** conectar señales y estados entre las tres reglas bajo un reloj explícito de laboratorio; evaluar circuito mínimo de cinco o seis neuronas vs el E02 simplificado, sin afirmar que ya emula C1.
