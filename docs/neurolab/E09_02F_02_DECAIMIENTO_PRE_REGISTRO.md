# E09.02f.2 — preregistro de decaimiento y relajación C1 x86

**21/11/2026. Fuente primaria:** análisis estático de `Creatures.exe`, aportado por el usuario, SHA-256 `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7`. No ejecutar ni distribuir el binario.

**Módulo separado de la E04 experimental.** No revisar retroactivamente sus resultados. El presente protocolo fija tests antes de escribir el nuevo código.

## Evidencia directa del binario

| VA x86 | Rutina / datos | Lectura |
|---|---|---|
| 0x419E40–0x419E83 | `decay` | rate>>3 selecciona índice; `tick & mask` controla actualización; nuevo byte = `(factor*current)>>16` |
| 0x419E90–0x419F08 | `relax` | mismo índice y máscara; mantiene fracción del valor respecto al destino; no necesariamente modifica en cada tick |
| 0x43A0E8 | `factor[32]`, uint32 | primeros coeficientes 0, 0x32A5, 0x71DD, 0xAABB, 0xD110, 0xE758, 0xF35C, 0xF999; 8–30 también 0xF999; 31 es 0xFFFF |
| 0x43A168 | `mask[32]`, uint32 | índices 0–7=0; índice 8=1, 9=3, 10=7, ..., 31=0xFFFFFF |
| 0x4042C9–0x404306 | susceptibilidad de dendrita | si la meta supera la susceptibilidad, aumenta cuatro unidades; si no, invoca decay (rate configurado por el gen) |
| 0x4044A1–0x4044E8 | STW | invoca relax con LTW como destino y tasa genética; guarda nuevo STW |
| 0x4044EF–0x40451B | LTW | si STW ≠ LTW y `rate > 0`, cuando `tick % rate == 0` LTW se mueve **una unidad** hacia STW |

**Estabilidad de la evidencia:** las direcciones solo valen para el ejecutable identificado por SHA. Las tablas se transcriben como números (datos derivados), sin almacenar el juego.

## Regla matemática E09.02f.2

```
index = rate >> 3
mask = MASK[index]
factor = FACTOR[index]
if (tick & mask) != mask:
    return current
decay(current,rate,tick) = (current * factor) >> 16
relax(current,rate,target,tick) =
    target + floor((current-target)*factor/65536)   si current > target
    target - floor((target-current)*factor/65536)   si current <= target
```

La fórmula de arriba es una **lectura del código máquina**. En `relax`, solo se usa factor para la distancia absoluta; no es una tasa lineal «restar 6» como en E04.

`ltw_toward` se aislará con la regla de incremento/decremento de 1 cuando tick divisible por rate. Una tasa de 0 implica no actualizar LTW; en Python **no** se realiza división por cero.

## Oráculos manuales preregistrados

- Decay rate48: `factor=0xF35C`, máscara0, `current=200→190` en cualquier tick.
- Decay rate80: `factor=0xF999`, máscara7, `current=200`, tick6→200 (sin actualizar), tick7→194.
- Relax rate80, current255, target0: tick6→255, tick7→248.
- Relax rate48, current0, target200: tick0→10.
- LTW: desde120 hacia STW200, rate128, tick127→120, tick128→121. Desde120 hacia STW50, rate128, tick128→119.
- Factores/máscaras exactos para los 32 índices; repetir con tasas 0 y255.
- Entradas byte fuera de0..255, tasas inválidas, ticks negativos o bool deben rechazarse.
- Constancia para 20 semillas de secuencias de rate/tick/value.
- Regresiones E01–E09e no deben modificar sus resultados.

**No se afirma** que este módulo solo reproduzca el aprendizaje químico de un Norn. Falta conectar reglas SVRule de susceptibilidad/refuerzo/fortaleza y el ciclo completo de actualización del motor.

**Próximo E09.02f.3:** integrar susceptible+refuerzo STW y consolidación LTW con señales químicas provenientes del genoma, con pruebas que contrasten el código máquina y las tasas reales, incluyendo el problema de crédito diferido E05.
