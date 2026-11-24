# E09.02f.3 — preregistro de la transición sináptica parcial de C1

**Fecha:** 2026-11-21. Se establece antes de implementar y ejecutar la fase f.3.

**Fuente primaria:** desensamblado estático de `Creatures.exe` PE32 del CD suministrado, SHA-256 `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7`. No ejecutar ni almacenar el binario en GitHub.

**Objetivo:** reconstruir las cuatro fases observadas en la dendrita **susceptibilidad → efecto químico sobre STW → relajación de STW → consolidación LTW**. Es un componente **aislado** de sinapsis, no la reconstrucción completa del motor: excluye cambios de strength, atrofia, migración, y la evaluación interna completa de SVRule y química ambiental.

## Evidencia y operaciones

- **0x4042C9–0x404306:** si el resultado de la regla SVRule de susceptibilidad supera el valor actual, `susceptibility` aumenta **4** por operación de byte (`(sus+4)&255`). Si no, decae usando la tasa genética. La suma de byte puede **desbordar** de 255 a 0 en niveles altos; no sustituir por clamp sin comprobar.
- **0x404311–0x404424:** el motor evalúa una SVRule genética de refuerzo, cuyo resultado es un byte `chemical_rule_output`. En esta primera fase **se recibe el resultado como entrada**, evitando simular lo que aún no se ha reconstruido.
- **0x40442B–0x4044A1:** `effect=(chemical_rule_output*susceptibility)>>8` (si la susceptibilidad es no nula). Si effect>0 y `effect > (STW - LTW)` con diferencia firmada, el motor escribe `STW = min(255,LTW+effect)`; de lo contrario conserva STW.
- **0x4044A1–0x4044E8:** llama a rutina `relax` C1 ya implementada y validada, tasa de STW por gen, hacia LTW.
- **0x4044EF–0x40451B:** si `STW != LTW` y tasa LTW no cero y `tick % rate == 0`, mueve LTW **una unidad** en dirección a STW.
- Tasas del genoma Decision `dad1.gen` de referencia para la clase elegida: susceptibilidad decay **48**, relajación STW **80**, LTW rate **128**.

**No confundir CHEM0/1:** estas variables son el **resultado de la regla de refuerzo**. Las concentraciones Reward49 / Punishment50 son las rutas genéticas para las dos familias de sinapsis, pero el mapeo receptor→regla y la dinámica química completa quedan fuera de esta prueba de cálculo.

## Estado y contrato de cálculo

Estado inmutable de una dendrita: `sus` / `stw` / `ltw` en 0..255.
Entradas numéricas por tick: `susceptibility_rule_output` (0..255), `reinforcement_rule_output` (0..255), tick entero no negativo.
Configuración: `sus_decay=48`, `stw_relax=80`, `ltw_rate=128` en el ejemplo Decision; permitir otros valores0..255 con validación.
No usar una variable `correct_action`, `target` semántico ni `reward=±1` como sustituto de las dos salidas genéticas.
Invocar las funciones de E09.02f.2 tal como fueron verificadas; no duplicar tablas ni reinterpretarlas.

## Oráculos previos

1. Comienzo (sus0,STW0,LTW0), entradas (255,255), tick1: **(4,3,0)**.
2. Desde (4,3,0), entradas (255,255), tick7: sube susceptibilidad8, `effect=(8*255)>>8=7`, STW tras relax=6; final **(8,6,0)**.
3. Desde (8,6,0), entradas (0,0), tick7: suceptibilidad baja a `(8*0xF35C)>>16=7`, STW baja a `(6*0xF999)>>16=5`, LTW0: **(7,5,0)**.
4. Desde (0,200,100), entradas (0,0), tick127: STW se relaja a **197**, LTW permanece100; tick128: no se aplica relajación STW (rate80 máscara7) y LTW pasa **101**.
5. Si sus=253 y salida de regla=255, entonces `add bl,4` produce **1**, no 255. Este comportamiento byte se registra como consecuencia observable de x86 para este binario.
6. Si hay química0, jamás aumentar STW mediante refuerzo; STW puede seguir acercándose a LTW por la rutina de relajación.
7. Valores0..255 y ticks válidos; entradas inválidas y estado incompatible se rechazan.
8. Checkpoint con el estado y configuración conserva continuación exacta con secuencia de entradas y ticks reproducible.
9. 20 secuencias pseudoaleatorias reproducibles; todas conservan límites.
10. E01–E09e y E09f.1/f.2 mantienen regresiones, sin modificarse.

**Gate E09.02f.3:** pasar tests y oráculos anteriores. Solo certifica el **fragmento numérico de actualización de una dendrita** de este ejecutable; no éxito de G09 ni conocimiento completo de la dinámica genómica.

**Próxima etapa E09.02f.4:** reconstruir SVRule de susceptibilidad y refuerzo a partir de inputs neuronales y variables químicas C1, strength y migración, y luego un microcircuito H. Evitar saltar directamente a una mente de 952 neuronas o al Nilo existente.
