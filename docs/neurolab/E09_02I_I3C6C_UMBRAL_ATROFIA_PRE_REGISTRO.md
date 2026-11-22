# NeuroLab I3c.6c — preregistro del umbral funcional de inhibición de atrofia

**21/11/2026 · prueba matemática ANTES del nuevo código; no ensayo conductual.** Basado en los resultados aislados [I3c.6a](E09_02I_I3C6A_RESULTADO_REALIMENTACION_ATROFIA.md) e [I3c.6b](E09_02I_I3C6B_RESULTADO_UMBRAL_QUIMICO.md).

## Problema distinto al de I3c.6b

I3c.6b verificó que `locus=3` basta para cambiar un receptor original `CHEM2/CHEM3` de16 a15. **Eso no prueba menor atrofia**, porque la SVRule genética de pérdida Decision es `CHEM2` / `CHEM3` y el motor `update_strength` sólo reduce la fortaleza si el valor de la regla es **DISTINTO DE CERO** en ticks habilitados de tasa5. Hay que determinar el **primer valor del locus que hace cero la señal de pérdida**, en lugar de interpretar cualquier cambio analógico como alteración de conducta.

## Experimento congelado

- Reusar `authentic_receptors()`, `EMITTER_GENES`, `emitter_tick`, `receptor_value`, `C1SynapticInput`, `update_c1_synapse`, `DECISION_EXCITATORY_GENE/DECISION_INHIBITORY_GENE`. No nuevas reglas ni parámetros.
- Recorrer `locus=0..32`, `pool` cero, un único tick de emisor0, receptores127/128 (CHEM2/3 nominal16). Para cada salida CHEM, pasarla como único químico relevante en una dendrita artificial con **strength4, STW0, LTW0, susceptibilidad0, source_output0, owner_state80, owner_output0**, a `update_c1_synapse(tick=5)`. Confirmar que la SVRule de pérdida devuelve la concentración CHEM correspondiente y la strength final es3 si CHEM>0, o4 si CHEM=0.
- Calcular por ambas parejas el umbral receptor `locus>=3` (ya I3c.6b) y por separado el **primer locus que inhibe efectivamente la pérdida**. **Predicción falsable:** requiere `locus>=18`; no asumir antes de computar. Confirmar extremos 0,1,2,3,17,18,32.
- Analizar implicación de topología: `C1ContextBrain` 2 dendritas por clase/neurona, `DynamicContextBrain` 1, original Decision128 por clase. Por ser agregación Type1 MIN de conexiones sueltas en registros neuronales procesados, **18 contactos por clase es sólo una cota inferior estructural** para poder alcanzar la señal, no una garantía de que se alcance durante un recorrido real ni de que el cerebro aprenda.
- Registrar las curvas completas e intervalos de x, preservar el resultado negativo; el ensayo es de función de fuerza y compuerta, NO de entrenamiento ni retención. No modificar `main`/Nilo0.7/PR draft.

## Puertas y decisión

- **G-I3c6c-LOSS:** recorrer 33 inputs×2 pares, verificar identidad `lose_strength_rule_output=CHEM2/3`, fortaleza tras tick5, el primer x que evita la pérdida y test de borde. Reportar incluso si la predicción18 falla.
- **G-I3c6c-SCALE:** capacidad fija2, dinámica1, original128; afirmar únicamente imposibilidad de alcanzar esa realimentación por esta ruta en modelos reducidos (sin otras químicas).
- **G05/G09/G00-H ABIERTAS**. No recomendar arquitectura con3 conexiones como solución de autorregulación: sólo lograría reducir un número CHEM15 que sigue induciendo pérdida completa a cada tick habilitado. Comparar alternativas en un documento de decisión después de medir.
