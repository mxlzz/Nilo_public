# E09.02f.4 — preregistro: cambios de fortaleza y desconexión C1

**Fecha:** 2026-11-21; se registra antes del código f.4.

**Fuentes:** análisis estático de `Creatures.exe` del usuario (SHA-256 `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7`) y genes de dendritas de `dad1.gen`. No se ejecuta el binario ni se almacena en GitHub.

## Hallazgos verificados por instrucciones x86

- **0x40451E–0x40467A, ganancia:** si `gain_strength_rate>0`, la fortaleza actual es menor que255 y `tick%gain_strength_rate==0`, el motor evalúa la SVRule de ganancia y establece `strength=max(strength,gain_rule_output)`. No es aumento fijo de una unidad; guarda directamente la salida de la regla cuando ésta supera strength.
- **0x40467A–0x4047C4, pérdida:** si `lose_strength_rate>0`, strength>0 y `tick%lose_strength_rate==0`, evalúa SVRule de pérdida. Si su salida es **no nula**, **decrementa la fortaleza 1**.
- **0x4047C4–0x4047E2, agotamiento:** si strength pasa de 1 a 0, el motor limpia susceptibilidad, STW y LTW de la dendrita y otros dos bytes en una estructura neuronal relacionada, y incrementa un contador de conexiones agotadas. La interpretación completa del objeto neuronal y la política de migración posterior **quedan por investigar**; no simularlas por suposición.
- Las tasas vienen de los genes, pero sus valores concretos difieren por lóbulo y clase. En el experimento aislado las tasas se entregarán explícitamente, sin inventar un promedio.

## Contrato de módulo f.4

Entrada: estado de dendrita `DendriteState(susceptibility,stw,ltw)` de f.3 + `strength` byte; tasas `gain_rate`, `lose_rate` bytes; `gain_rule_output` y `lose_rule_output` bytes; tick entero>=0.
Salida: nuevo estado de dendrita, nueva fortaleza, bandera **lost_connection** (un solo evento en el tick).
Reglas: ganancia antes de pérdida; salida de regla externa (no ejecutar toda la SVRule química en esta fase). Si la fortaleza decrece hasta 0, se ponen a 0 los tres campos de la dendrita; **no reconectar automáticamente**.

## Oráculos previos a ejecutar

1. Strength2, gain_rate2, gain_rule_output80, tick2 → strength80. El mismo caso tick1 →2.
2. Strength10, lose_rate3, lose_rule_output1, tick3 →9; tick2 →10.
3. Strength2, gain_rate2, gain_output80, lose_rate3, lose_output1, tick6 →79 (ganancia primero, pérdida después).
4. Strength1, sus8/STW6/LTW2, lose_rate1, lose_output1, tick1 → strength0, sus=STW=LTW=0, **lost_connection=True**.
5. Misma configuración del punto4 con lose_output0: no se pierde nada.
6. Strength255 ignora salida de ganancia, pero aún puede decrementar por pérdida.
7. Rates0 desactivan sus respectivas operaciones; si el `tick` no es múltiplo, no actualizan.
8. En todas las pruebas se conserva [0,255], se rechaza entrada inválida, eventos repetibles bajo 20 semillas y no se modifica E09f.1–f.3.
9. El módulo no toma `correct_action`, objetivos del evaluador, mundo, cuerpo ni químicos inventados.

**Gate:** comprobar oráculos anteriores sin añadir reconexiones. El éxito certifica solo **ganancia/pérdida de fortaleza y señalización de conexión agotada** según este binario. **No certifica la migración, que es la etapa siguiente.**

**Próximo E09.02f.5:** estudiar funciones que consumen el contador de conexiones agotadas, y verificar el proceso real de migración Decision-style y Concept-style. Después, con todas las piezas verificadas, integrar un microcerebro histórico y comparar contra E09e (modelo experimental).
