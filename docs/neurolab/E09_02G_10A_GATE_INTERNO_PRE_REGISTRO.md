# E09.02g.10a — preregistro de factibilidad de filtrado interno mínimo

**Fecha:** 2026-11-21. Registrado después de g.9, **antes de codificar g.10a**. Esta es una **prueba de equivalencia funcional del mismo banco**, no una nueva prueba de superioridad cognitiva, ni un mecanismo verificado del ejecutable Creatures 1.

## Pregunta

El filtro de feedback dirigido `G` de g.8/g.9 dependía de un reloj de bloques externo. ¿Podemos reproducirlo usando solo señales que ya existen *dentro* de la microred y una traza mínima de la decisión anterior?

## Modelo candidato y límites de información

- **IG, compuerta intrínseca experimental**: envoltura de estado `(ContextBrainState, last_choice_concepts)` en torno a la clase `C1ContextBrain` original, **sin modificarla**. `last_choice_concepts` retiene la pareja de salidas de Concept que efectivamente leyó la decisión inmediatamente anterior (`ContextTick.old_concepts`), o `None` antes del primer paso.
- En cada tick, el módulo recibe **exactamente** `(estado interno, estímulo corriente, pulso químico pendiente)`. **Prohibido** consultar lista de bloques, posición dentro del bloque, mapeo correcto, `changed_context` externo, tiempos de premio, `seed` como oráculo, o un reloj contextual adicional.
- Si hay pulso químico no nulo, ambas parejas (`last_choice_concepts` y `ContextBrainState.concept_outputs`) tienen exactamente un Concept identificable y esos índices difieren, se entrega `ZERO` a la actualización sináptica. Si faltan fuentes inequívocas, **no** suprimir. Se almacena después el Concept efectivamente usado por la nueva elección.
- La traza nueva es memoria **artificial de laboratorio**, *no* gen C1 ni neurona sensorial autónoma demostrada; presupuesto lógico máximo **dos valores de 8 bits** más marcador de inicialización. El costo real de objetos Python será mayor y no se debe confundir con bytes de memoria física de la implementación.

## Diseño congelado y oráculos

- Contraste con tres referencias existentes, sin cambiar `C1ContextBrain` ni químicos:
  - **C:** `train_brain` original de g.5.
  - **G:** `train_variant(..., mode="G")` de g.8, oráculo externo con frontera de bloque.
  - **IG:** candidato interno sin acceso a fronteras ni posicionamiento en el bloque.
- Dos fases de 32 bloques de 8 ticks, mappings A/B inversos, holdouts de 16 bloques×8 ticks sin plasticidad. Semillas **100..119 inclusive**, no utilizadas en diseño ni en el preregistro de g.9. Los códigos de G/C y su entrenamiento se conservan íntegros.
- Métrica primaria de **factibilidad**: en cada semilla, **igualdad exacta** IG vs G de dendritas (STW/LTW/sus/strength), estados/output de neuronas y Concepts, tick, químico pendiente y número de omisiones después de cada fase. Debe cumplirse **20/20**. Las métricas de holdout (`steady`, `early`, `overall`) deben coincidir al bit de float o `abs(delta)<=1e-12`.
- Control C: no se altera el aprendizaje ni el estado original. Se reportará si C/G/IG cumplen >=0.90 steady A+B, pero **este es un estudio de equivalencia**, no mejora independiente ni nueva aprobación de G05. Si el control C se altera, invalidar protocolo.
- Pruebas unitarias: estado inicial sin fuente, mismatch correcto con pares `(126,0)` y `(0,126)`, sin supresión cuando ambas parejas son idénticas, pulso cero y fuente ausente/ambigua. Replay determinista de misma semilla. La compuerta no puede codificar explícitamente `position==1` ni mirar la secuencia futura.
- El supuesto de equivalencia solo tiene sentido para estímulo binario one-hot con un único cambio de Concept por bloque y el reloj actual. No extrapolar a distractores, múltiples acciones/Concepts o asincronía.

## Interpretación de resultados

**Si IG == G 20/20**, la información local actual **basta en esta tarea sintética** para imitar el filtro externo con pequeño estado; no demuestra que el circuito C1 lo aprendió ni que mejore respecto a tabla 2×2. **Si no**, informar exactamente qué semilla/tick se separa y revisar si el reloj/codificación hace imposible la igualdad, sin ajuste libre post hoc.

**Siguiente pregunta, independientemente del resultado:** ¿puede la traza interna *atribuir* correctamente refuerzo con distractores y señales asíncronas, no solo filtrar cambios evidentes? Ese sería un protocolo diferente; G05 sigue abierta. No integrar en Nilo ni aumentar tamaño por defecto.
