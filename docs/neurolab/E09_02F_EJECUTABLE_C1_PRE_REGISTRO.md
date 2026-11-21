# E09.02f — preregistro de aritmética C1 verificada mediante ejecutable

**21/11/2026.** Fuente primaria aportada: `Creatures.exe` extraído por el usuario de la imagen original de CD. Solo inspección estática, **sin ejecutarlo ni subirlo** al repositorio.

**PE32 (x86)**, tamaño 387072 bytes, SHA-256 `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7`; timestamp de encabezado 1997-08-06 19:48:28 UTC; FileVersion/ ProductVersion de la estructura VS_FIXEDFILEINFO = 1.0.0.1. No atribuir equivalencia a la compilación inicial de 1996.

## Evidencias binarias previamente localizadas

| Dirección virtual x86 | Observación | Implicación |
|---|---|---|
| 0x401737–0x40177d | Reserva 0xC8C, construye 16 registros x 0xC8 desde offset+8 | CBrain tiene capacidad estática para 16 lóbulos, **no** indica 16 genes presentes |
| 0x4032e0–0x4034b9 | Recorre genes de lóbulos y reserva neuronas/dendritas | El genoma configura topología que instancia el motor |
| 0x403f2f–0x403f8f | Acumula (source.output × dendrite.weight) >> 8, limita 255, aplica (total × attenuation) >> 8, y AND bloquea si una fuente no disparó | Calcular TYPE0/1 y ANDTYPE0/1 usando escala 256, no 255 |
| 0x403fc2–0x4040b6 | Despacha SVRules opcodes 22–27 con tabla en 0x404a04 | Operaciones en orden sobre byte acumulador |
| 0x404000–0x404031 | Opcode 23 PLUS suma y satura en 255 | Saturar *en cada operación* |
| 0x404033–0x404061 | Opcode 24 MINUS resta, trunca resultado negativo a 0 | Saturar *en cada operación* |
| 0x404063–0x40408f | Opcode 25 TIMES, multiplicación entera y desplazamiento 8 | (a×b)//256, truncamiento entero |
| 0x404091–0x40409d | INCR/DECR saturados | No desbordar/underflow byte |
| 0x4040b6–0x404110 | Escribe nuevo estado y salida = max(estado − umbral, 0) | Resuelve disputa de fórmula **para este binario** |
| 0x4048cc–0x404911 | Comprueba flag de exclusividad competitiva y conserva salida máxima | Winner-takes-all concreto |

**Limitación:** las interpretaciones se basan en el flujo de instrucciones mostrado y en correlacionar layouts de genes y estructuras. No se ha terminado de desensamblar toda la transición de dendrita (susceptibilidad, STW/LTW, fortaleza y migración) ni de comprobar los ticks de forma dinámica. No inventar ecuación exacta de aprendizaje.

## Plan matemático mínimo E09.02f.1

Crear el **módulo nuevo** `c1_runtime_math.py` independiente del simulador E09e, sin tocar `c1_svrule_subset.py` ni sus datos históricos de laboratorio.

- `plus(a,b)=min(255,a+b)`.
- `minus(a,b)=max(0,a-b)`.
- `times(a,b)=(a*b)>>8`.
- `incr(a)=min(255,a+1)`, `decr(a)=max(0,a-1)`.
- `eval_rule` interpreta exclusivamente las 3 reglas neuronales existentes del dad1.gen: Decision=STATE+TYPE0-TYPE1, Attention=STATE+TYPE0+TYPE1, Concept=ANDTYPE0, usando operaciones **secuenciales** y saturadas.
- `dendrite_signal`: para entradas ya vinculadas, `sum((source_output*stw)>>8)` limitado a255; `type=(sum*attenuation)>>8`, `anded=type` si todos los source outputs no son cero, sino0. Para ausencia total de dendritas, el valor de AND queda por determinar con comparación de motor y NO se implementa aquí.
- `neuron_output= max(0,state-threshold)`; sin añadir relajación del estado, que se prueba separadamente.

## Oráculos manuales congelados antes del código

| Ensayo | Esperado con ejecutable x86 | Modelo anterior |
|---|---:|---:|
| Decision STATE80+TYPE0 240−TYPE1 200 | 55 | 120 (saturación solo final) |
| Decision STATE80+TYPE0 110−TYPE1 30 | 160 | 160 |
| Attention STATE250+TYPE0 30+TYPE1 30 | 255 | 255 |
| TIMES 255×255 | 254 | No implementado como operador independiente |
| TYPE0 fuente100 STW128, fuente80 STW128, attenuation255 | 89 | 90 |
| TYPE0 fuente255 STW128 dos veces, attenuation255 | 253 | 255 |
| ANDTYPE0 si fuente100, otra 0 (STW128 ambas) | 0 | 0 |
| Estado80, umbral24 → output56 | 56 | Modelo neuronal anterior no siempre aplica umbral posterior |

Incluye invalidaciones de bytes fuera de 0..255, determinismo para 20 seeds de casos sintéticos, y comparación explícita contra modelo previo sin cambiarlo.

**Puerta E09.02f.1:** pasar todos los oráculos y comprobar conservación regresiva de E01–E09e. Esto valida la parte aritmética del flujo máquina inspeccionado, **no** el aprendizaje C1.

## Siguientes subtareas

1. **E09.02f.2:** localizar rutinas exactas de susceptibilidad, refuerzo y relajación de STW en el mismo binario; identificar del genoma las tasas relevantes.
2. **E09.02f.3:** localizar actualización LTW, fortaleza y eventos de migración; separar hipótesis de pruebas directas.
3. **E09.02f.4:** integrar un microcerebro H con aritmética corregida y pruebas funcionales, compararlo en **nuevas semillas** contra E09e y baselines sin sobrescribir resultados.
4. **E09.02f.5:** publicar la tabla de divergencias por componente entre binario, documentación, genes y modelos anteriores, con confianza y direcciones precisas.

No sumar cuerpo, mundo ni LLM.
