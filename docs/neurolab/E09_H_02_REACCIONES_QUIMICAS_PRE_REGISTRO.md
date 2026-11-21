# E09h.2 — preregistro de cinética de reacciones químicas C1

**Fecha:** 2026-11-21. Registrado después de una lectura exploratoria de x86 `0x42203F..0x4221CD` y del genoma original, antes de codificar el módulo de reacciones aisladas. No es un preregistro ciego de la hipótesis histórica.

## Fuente y alcance

Ejecutable SHA256 `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7`; genoma CD SHA256 `e2bb4ccf6a4081a128c6c9ffc6eb233452d416717ceef47e78820ca3a152ddd4`. El binario fue revisado localmente; nunca se publica. La lista de 58 genes de reacción ya puede recuperarse con `c1_reaction_inspector.py`.

Se reconstruirá **solo** el subpaso de reacción dentro de `0x421E70`, sin fingir que se tiene la bioquímica completa: emisor, receptor, decaimiento global de 256 químicos y rutas de actualización alternativa se tratan aparte.

## Hipótesis técnica exacta basada en instrucciones

El registro de reacción posee nueve bytes: `qtyA,chemA,qtyB,chemB,rate,qtyC,chemC,qtyD,chemD` **NO**: el orden efectivo del genoma fue confirmado como `qtyA,chemA,qtyB,chemB,qtyC,chemC,qtyD,chemD,rate` en el archivo, pero la rutina en memoria usa `[esi+4]=rate` y los pares de productos en `[esi+5..8]`. **La posición interna de tasa difiere del cuerpo del genoma; debe probarse el trasvase durante carga, nunca pasar directamente los nueve bytes como layout runtime.**

Si ID A/B es cero, ese reactivo no limita el máximo; si ambos existen, la capacidad inicial es `min(255, floor(pool[A]/qtyA), floor(pool[B]/qtyB))`. Los genes CD inspeccionados nunca contienen cantidad cero con ID de reactivo no nulo.

El código alrededor de `0x4220AC` llama a `0x419E40` con capacidad, tasa y tick; la magnitud de reacción aparente es `capacity - decay(capacity, rate, tick)`. Se restan `qty*extent` a los reactivos, saturando en cero, y se suman a productos, saturando a 255. Los genes se procesan en orden y usan el mismo pool ya actualizado; por lo tanto dos reacciones pueden encadenarse dentro del mismo tick. Esta es una hipótesis de transcripción directa que exige oráculos locales.

## Fixtures congelados

- Para reacción 71 del genoma (ID33 + ID1 → ID49, tasa8), pool[33]=10 y pool[1]=15 en tick0: capacidad10, decay10@8=1, extent9, remanentes1 y6, Reward49=9.
- Para reacción111 (Reward49 → Reinforcement51+Echo54, tasa16), pool49=20: capacity20, decay20@16=8, extent12, termina pool49=8, pool51=12 y pool54=12.
- Cadena 71→111 en **el mismo tick**, en el estado inicial del primer fixture: tras 71 el Reward49=9; reacción111 transforma 5, deja Reward49=4, Reinforcement51=5 y Echo54=5. Invertir el orden 111→71 NO debe producir51/54 en el mismo tick. Esta comprobación decide si la ejecución es secuencial.
- Genes 57 y112, de Punishment50, deben cumplir exactamente los campos publicados en E00, además de 71/111.
- Fixtures de saturación química (0 y255), reactivo ausente y conservación de entrada por copia; no ejecutar binario bajo CI.
- Se probará coherencia contra la función `c1_decay_math.decay` existente, sin cambiar sus tablas/hashes.

## Puertas de aceptación

1. Parsear las 58 reacciones del genoma y verificar índices 57,71,111,112; distinguir layout serializado y layout runtime, sin asumir equivalencia de ambos.
2. Los fixtures numéricos anteriores pasan, y el resultado en cadena depende de orden. Estado de pool de entrada no debe mutar.
3. Los tests históricos de NeuroLab siguen pasando; comparar siempre solo la etapa aislada, sin inferir emisión o recepción cerebral completas.
4. Antes de cerrar fidelidad de reacciones, investigar la asignación del struct en runtime y sus posibles excepciones. En caso de incertidumbre, clasificar **implementación candidata**, no reproducción histórica confirmada.

## Interpretación y decisión

La mejora de conocimiento buscada es comprender cómo nacen y se transforman los químicos Reward/Punishment/Reinforcement y cuándo pueden ser observados por los receptores del cerebro. No añadir neuronas, reglas de crédito artificial ni retocar las pruebas g.10b/c. G00-H, G05 y G09 siguen abiertos.
