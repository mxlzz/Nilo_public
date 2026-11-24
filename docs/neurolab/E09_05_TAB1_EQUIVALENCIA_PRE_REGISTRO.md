# NeuroLab — E09.05-TAB1: preregistro de equivalencia entre detector E06 y tabla de pares

**22/11/2026 · PRE-IMPLEMENTACIÓN.** Esta ficha se registra ANTES de escribir el comparador o ejecutar sus tests. Base fuente: [E06_PRE_REGISTRO.md](E06_PRE_REGISTRO.md), [concepts.py](../../experiments/neurolab/concepts.py), [e06_protocol.py](../../experiments/neurolab/e06_protocol.py), [E09.02–.05](E09_02_EVALUACION_INTEGRACION_MINIMA_20261122.md). **No** es un nuevo algoritmo neuronal, ni evaluación C1, ni sustitución del G06 original.

## Pregunta y afirmación falsable

**H-identidad:** en el **dominio legal de E06** (exactamente una señal A entre A0/A1 y una B entre B0/B1, con bit C=0/1 irrelevante), `ConceptLearner(mode="pair",rate=16)` es operacionalmente idéntico a una **tabla de cuatro claves (par A×B) con dos pesos por clave**, inicializada de igual modo y actualizada por premio/castigo en la acción elegida. No hay operación neuronal temporal adicional en esta implementación E06.

**H0 para comprobación computacional:** existe al menos una entrada legal, estado alcanzable, semilla o secuencia de premios que produce acciones, pesos o contadores distintos.

## Demostración matemática esperada (no depender del test)

Dado `bits` legal, solo un índice `i∈{0,1,2,3}` de `PAIR_FEATURES` cumple `all(bits[j]==1)`. El bit4 (C) no pertenece a esos pares. Por código fuente, el selector neuronal calcula `score(Dj) = sum(edges[k][j] for k in active) = edges[i][j]`; elige D0 en empate, D1 en otro caso. Una tabla que almacene `W[i,0],W[i,1]` con iguales valores usa el mismo `argmax`. Ante `reward∈{-1,+1}`, ambos modifican únicamente `W[i,selected]←clamp(W[i,selected]+16*reward,0,255)`. Si el estado inicial es igual, la igualdad se conserva por inducción en el número de entrenamientos; `C` no cambia la clave. Se comparan **8 pesos adaptables y mismo contador**, no «tabla exacta de cinco bits» usada en el control antiguo. La función de extracción de la pareja también es representación fijada externamente en ambos brazos.

## Contrato de prueba independiente

1. Nuevo `experiments/neurolab/e09_pair_tabular_equivalence.py` con implementación tabular autónoma: claves `PAIR_FEATURES` pueden compartirse como *definición estática del experimento* (preferentemente replicación explícita de los cuatro pares), pero no reutilizar `ConceptLearner.respond/update` dentro del control. Inicializar por `random.Random(seed).randint(40,220)` en el mismo orden, `rate=16`.
2. Para cada seed **0..19** (ya usada en E06; **desarrollo/diagnóstico**, NO validación externa): comprobar igualdad inicial exacta y las 4 parejas×2 valores C, incluyendo acción y puntuación.
3. Reproducir los **120 ejemplos** de entrenamiento original E06 (4 pares×30, contexto C=0) usando `e06_protocol.sequence(seed, context=0, repetitions=30,salt=6000)`. Tras **cada** premio E06, comprobar acción, dos puntajes, 8 pesos y contador iguales.
4. Reproducir **80 observaciones** holdout E06 (4×20, C=1, salt=7000) sin aprendizaje: 1.600 comparaciones de acción en total, sin mutar el estado ni conocer etiqueta correcta dentro de los modelos.
5. Añadir **120 entrenamientos** por seed de contingencia invertida (sobre el mismo estado, sin reset) y C alternante, con recompensa del evaluador invertido; comprobar identidad tick por tick. La secuencia debe ser determinista y publicada.
6. Ensayar test unitario de empate artificial y saturación ±255 en ambos brazos, y evento legal C=1 que no cambie elección. Para entradas fuera del dominio (ningún par o varios pares), registrar **exclusión explícita**, no extender la conclusión ni forzar igualdad.
7. Guardar resumen JSON de conteos, condiciones, equivalencia exacta y SHAs de archivo fuente; CI corre tests específicos; **no publicar sólo un porcentaje de aciertos** para una igualdad estructural.

## Métrica, umbral, decisión

Métrica primaria: **cero discrepancias** en acción, scores, pesos y trial para cada estado/entrada legal del recorrido. Una sola discrepancia => falsación de equivalencia implementada, analizar caso mínimo antes de concluir. Prueba general: argumento por inducción más tests que detectan errores de implementación, **no** confundir 20 semillas con prueba estadística de universalidad.

**Si igualdad:** el E06 **no aporta una ventaja funcional respecto a una tabla con exactamente la misma representación fija y presupuesto de 8 pesos**. El resultado E06 de 1,0 vs memorizador exacto completo 0,5 sigue siendo correcto, pero muestra beneficio de ignorar un bit irrelevante mediante una representación previa, no superioridad exclusiva de neuronas. Para G09, desaconseja implementar un adaptador E03+E06 que solo reproduzca esta tabla.

**Si discrepancia:** publicar entrada/estado contrafáctico, corregir test o revisar la derivación; no ajustar modelos hasta conseguir acuerdo. Nunca retroalterar G06 ni sus métricas preregistradas.

Sin nuevas semillas confirmatorias 1400..1419, nueva química, ni modificación de Nilo 0.7.
