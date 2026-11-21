# E09h.6a — flujo condicional del scheduler C1 (resultado parcial)

**Fecha:** 2026-11-21. **Estado:** ramas de ejecución comprobadas estáticamente; frecuencia real G-H6-CLOCK ABIERTA. No se ejecutó el juego.

## Procedencia y método

- EXE PE32 original aportado por el usuario, SHA-256 548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7, 387072 bytes.
- Inspección directa con **24 firmas x86** y **8 llamadas directas** verificadas contra los bytes originales; fuente [preregistro](E09_H_06_SCHEDULER_PRE_REGISTRO.md), [verificador](../../experiments/neurolab/e09_historical_scheduler_audit.py), [tests sintéticos](../../experiments/neurolab/tests/test_e09_historical_scheduler_audit.py) y [JSON reducido](resultados/e09h6a_flujo_original.json). Sin redistribuir EXE.

## Hallazgos por ruta

**Regular, VA 0x407540:**
- Si Norn+0x2CBC es no-cero, 0x40754B sale sin cerebro, química, conducta ni incremento de contador.
- Si Norn+0x2CBC es cero y Norn+0x2CCC es cero: cerebro 0x403BB0 → química 0x421E70 → comportamiento 0x40A4B0 → incremento del contador Norn+0x2C20 en 0x4075AB. Cerebro y química reciben el **mismo contador previo al incremento**.
- Si Norn+0x2CCC es no-cero, **omite cerebro y comportamiento pero conserva química e incremento**. No todo tick químico actualiza cerebro.

**Alternativa, VA 0x4075C0:** el segundo recorrido global por las criaturas llama esta función mediante 0x4248C3. Esta ruta actúa únicamente cuando Norn+0x2CBC es no-cero. Según Norn+0x2CB8 y estado en Norn+0x2C68, puede reestablecer un estado, actualizar el contador sin química, o llamar a 0x405D20 desde 0x40764B. Esta última subruta procesa **química 0x405D32 → cerebro 0x405DAF**, con un incremento de contador en 0x407657–0x40765E. No afirmar que se trate de un segundo tick regular de la criatura.

**Bucle global VA 0x4247B0:** un pase selectivo lee fase en dirección 0x43EAAC, recorre la lista desde ese índice con stride4 y llama a 0x407540 en 0x424884. La fase avanza de 0 a 4 (luego se reinicia a 0). Un segundo pase recorre la lista completa y llama 0x4075C0. Contador global 0x43BBB0 se incrementa al terminar el bucle.

**Advertencia estructural de interés:** cuando existen índices 4,8,…, el algoritmo de fase0 y fase4 los incluye en sus respectivos pases con stride4. Esto es un solapamiento de índices en la lectura estática, **no prueba de un error conductual real**: faltan datos de frecuencia de llamada, estado de la lista y ejecución de cada criatura. Una fase de cinco valores NO determina cinco Hz ni segundos por tick.

## Puertas

- **G-H6-FLOW:** verificado como **subconjunto acotado de rutas directas**; no exhaustivo frente a callbacks virtuales y otros eventos.
- **G-H6-CLOCK:** **ABIERTA**. Se localizaron invocadores de 0x4247B0 en 0x418966, 0x424C98 y 0x426894 pero no se conoce aún su origen temporal, ritmo de eventos o interacciones con pausa.
- **G00-H / G05 / G09:** permanecen abiertas.

**Próxima E09h.6b:** investigar origen de cadencia y controles de los tres invocadores de 0x4247B0; no inventar tiempo de tick. Sin aumentar neuronas ni tocar Nilo 0.7, main o merge del PR #103.
