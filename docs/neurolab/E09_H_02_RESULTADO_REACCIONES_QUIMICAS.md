# E09h.2 — resultado de cinética aislada de reacciones C1

**Fecha:** 2026-11-21. [Preregistro E09h.2](E09_H_02_REACCIONES_QUIMICAS_PRE_REGISTRO.md) anterior al módulo. Fuentes **exclusivas** originales del usuario, identificadas por SHA-256: EXE `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7`, GEN `e2bb4ccf6a4081a128c6c9ffc6eb233452d416717ceef47e78820ca3a152ddd4`. Ambos inspeccionados localmente, ninguno redistribuido.

## Evidencia e implementación

- [Cálculo de reacción aislada](../../experiments/neurolab/e09_historical_reaction_math.py), [tests sin binarios propietarios](../../experiments/neurolab/tests/test_e09_historical_reaction_math.py) y [fixture derivado de genes del CD](resultados/e09h2_reacciones_genoma_original.json).
- [CI #44945152541](https://github.com/mxlzz/Nilo_public/actions/runs/44945152541), código comprobado hasta commit `9952bee39ac9d355938425a8cf00b139bd10774a`: **success, 325 tests, 2 expectedFailure históricos**. CI prueba aritmética con fixtures sintéticos; lectura directa de genes se verificó localmente.
- Del genoma del CD se recuperaron **58 reacciones** y se verificaron los campos originales de los genes 57,71,111,112, incluyendo las sustancias 49 Reward, 50 Punishment, 51 Reinforcement, 54/55 Echo.
- El cuerpo serializado de 9 bytes usa *pares de cantidades e identificadores* de dos reactivos y dos productos, luego tasa. En el ejecutable, la rutina de carga reorganiza esos campos: **tasa en struct+4**, productos después. No alimentar el runtime directamente con el layout del genoma.
- La operación computada por reacción es limitar `capacity` según disponibilidad y coeficientes de reactivos; aplicar la función de `decay` C1 verificada previamente a esa capacidad; usar `extent=capacity-decay(capacity,rate,tick)`; sustraer reactivos y añadir productos con saturación a byte 0..255. Las reacciones se ejecutan **en orden sobre un pool mutable**, copiado al inicio por nuestro módulo puro, que retorna uno nuevo.

## Oráculos numéricos reproducidos

1. Gene 71: cantidades químico33=10 y químico1=15, tick0 → `extent=9`; quedan 1 y 6, Reward49=9.
2. Gene111: Reward49=20 → `extent=12`; quedan Reward49=8, Reinforcement51=12, Reward Echo54=12.
3. **Cadena dentro del mismo tick**: ejecutar 71→111 con el estado del primer ejemplo produce Reward49=4, Reinforcement51=5, Echo54=5. Ejecutar 111→71, en ese orden, deja Reward49=9 y Reinforcement/Echo en 0. La dependencia de orden es material.
4. Gene112 Punishment50→Reinforcement51+Punish Echo55 se comprobó con fixture sintético consistente con los bytes del genoma original.

**Impacto temporal:** el orden químico documentado en [E09h.1](E09_H_01_RESULTADO_ORDEN_CEREBRO_QUIMICA.md) sitúa receptores **antes** que reacciones. Por tanto, Reward generado por una reacción y consumido por otra durante la misma invocación química no tiene por qué estar presente al muestreo del receptor. No deducir concentraciones ni comportamiento del Norn fuera de esta etapa local.

## Límite científico

**E09h.2: subetapa de aritmética de reacción implementada y testeada**, pero **no** se cierra la bioquímica completa ni se ha ejecutado Creatures para verificar trazas reales de concentraciones. Quedan emisores, receptores unidos a loci, tasa/frecuencia del reloj, otras rutas y condiciones del motor. La fórmula y orden se dedujeron por lectura estática de una versión PE32 identificada, no extrapolable sin contraste a todas las ediciones.

**Siguiente E09h.3:** verificar cómo concentraciones existentes se convierten a loci cerebrales por receptores genéticos; conservar intactas las redes C1-reducidas, g.10b/c y Nilo. G00-H/G05/G09 abiertas.
