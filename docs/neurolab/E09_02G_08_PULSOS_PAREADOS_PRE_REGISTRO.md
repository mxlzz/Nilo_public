# E09.02g.8 — pre-registro de supresión pareada de pulsos temporalmente desalineados

**Fecha:** 2026-11-21. Registrado después del ledger g.7 y **antes de escribir el runner g.8**. Estudio de intervención de laboratorio, **NO una corrección de C1** ni un experimento independiente de g.5: reutiliza sus 20 semillas y bloques por trazabilidad.

## Pregunta e hipótesis

El ledger g.7 encontró 652 desalineaciones `Concept usado por la acción anterior != Concept usado por la plasticidad actual` en 10.200 pulsos comparables: prácticamente todas en **posición 1** (segundo tick) de un bloque de estímulo distinto, incluidas fronteras entre fases. ¿Contribuye esa desalineación al rendimiento pobre de ciertas semillas, o sería equivalente quitar cualquier pulso en un momento próximo?

**Hipótesis direccional:** si la actualización en posición 1 de cada bloque *con cambio de contexto* es perjudicial, suprimir solo ese pulso mejorará la precisión steady del holdout respecto de suprimir un pulso adyacente en posición 2, manteniendo el mismo número de oportunidades de feedback. Una mejora puede ser específica del reloj de este banco y no demuestra necesariamente que cada sinapsis esté corrigiendo una causalidad.

## Diseño congelado

Para cada semilla `0..19`, se reconstruye desde cero E09g.5, con 6 unidades, 8 sinapsis, Concept y Decision C1 reducidos, el mismo flujo de recompensa externa del evaluador y **dos fases de 32 bloques×8 ticks** balanceados aleatorios, con reversión A→B. Se retienen el pulso pendiente y estado neuronal/sináptico de A al comenzar B. Holdout de 16 bloques×8 ticks por fase, **sin plasticidad**, midiendo total, primeros 2 ticks y steady (últimos 6 ticks). Se ejecutan tres brazos independientes:

1. **C (control original):** químico `pending` en todos los ticks, igual a g.5.
2. **G (gated):** solo si hay cambio de contexto respecto del bloque anterior, se entrega `ZERO` en **posición 1** de ese bloque, ignorando ese pulso; todos los demás se entregan normalmente.
3. **S (sham temporal):** en el **mismo bloque y transición**, se entrega `ZERO` en **posición 2**, un tick después, y no en posición 1. Controla número y distribución de bloques con supresión pero difiere el instante.

Un cambio de contexto entre el **último bloque de A y el primero de B** también activa la regla; el primer bloque de A no. Toda supresión se define por calendario sensorial, no por si la acción fue acertada o por el resultado de holdout. No insertar información de decisión correcta en `C1ContextBrain`. Los tres brazos usan exactamente el mismo número de ticks y estímulos. Se registrarán pulsos realmente omitidos, incluidos casos en que `pending=ZERO`; si G y S no omiten el mismo número de pulsos efectivos, se informará la diferencia sin declararlos perfectamente equiparados.

## Evaluación y límites

- Primario: media de precisión **steady fase B** de G vs S, con pares por semilla, y distribución de los deltas G-C, S-C, G-S.
- Secundarios: steady fase A, precisión total y `early` de ambas fases, semillas con ≥0.90 steady en ambas fases para cada brazo, degradaciones y mejoras en las 8 semillas originalmente fallidas.
- Indicador práctico preregistrado **no equivalente a prueba de causa:** `mean_steady_B(G) - mean_steady_B(S) >= 0.03` sin degradación de A mayor que 0.02 frente a S. Si no se cumple, clasificar efecto limitado o adverso. Se reportarán igualmente todos los resultados.
- Control obligatorio: C debe reproducir g.5 **12/20** semillas y sus promedios steady A `0.9671875`, B `0.9302083333333333` (tolerancia 1e-12); las pruebas de g.5 siguen intactas.
- No alterar después de resultados tasas del genoma, WTA, bloques, semillas, evaluación steady ni política de supresión. Reportar cantidad exacta de pulsos omitidos y métricas por semilla incluso si el experimento no mejora.

**Limitación crucial:** G y S son oráculos **externos** que conocen el borde temporal del estímulo. No son nuevas facultades del Norn, no sustituyen a un sistema interno de atribución causal y no cierran G05. Aun si G supera S, el siguiente paso requiere diseñar un circuito realmente capaz de manejar crédito temporal sin información externa, y compararlo con una tabla simple antes de considerar complejidad adicional. No incorporar mundo, cuerpo, LLM ni motor Nilo.
