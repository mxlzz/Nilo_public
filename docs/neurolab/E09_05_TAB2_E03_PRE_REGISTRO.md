# NeuroLab — E09.05-TAB2: preregistro de equivalencia E03 y tabla binaria

**22/11/2026 · ANTES del comparador/test.** Fuente: [E03 preregistro](E03_PRE_REGISTRO.md), [plasticity.py](../../experiments/neurolab/plasticity.py), [circuit.py](../../experiments/neurolab/circuit.py), [kernel.py](../../experiments/neurolab/kernel.py), [e03_protocol.py](../../experiments/neurolab/e03_protocol.py). Continúa [TAB1 E06](E09_05_TAB1_RESULTADO_EQUIVALENCIA.md) bajo la misma pregunta original E09.05: ¿la red aporta función no explicada por un baseline simple con igual representación? No se seleccionan parámetros ni metas nuevas.

## Hipótesis y límites

**H-identidad:** bajo el protocolo exacto E03, con episodios de **tres ticks reiniciados**, input exclusivamente `A=(255,0)` y `B=(0,255)`, las seis neuronas de `PlasticLearner` son matemáticamente equivalentes a una **tabla de 2 estímulos ×2 pesos de acción**, con igual inicialización, premio/castigo y tasa16. Se comparan scores y acciones, no sólo precisión. **H0 de test:** cualquier discrepancia en un estado alcanzado bajo estas condiciones.

Esto no propone que una red continua con entradas parciales, combinadas o arrastre de estado sea tabular; esas condiciones están excluidas.

## Derivación a verificar

[`make_six_neuron`](../../experiments/neurolab/circuit.py) fija excitación E0→C0 y E1→C1 de peso255, un valor inicial por C0/C1→D0/D1 y `threshold=0,rest=0,decay=255` para todas las neuronas. [`run_episode`](../../experiments/neurolab/circuit.py) crea un estado inicial nuevo y aplica exactamente E→C→D en tres ticks. Con entrada255 en solo una E, su Concept alcanza salida255 en tick2; la Decision correspondiente recibe `floor(255*w/255)=w` en tick3; la otra Concept queda en0. La variable residual `state` no persiste porque `floor(pre*(256-255)/256)=0` para todo `pre≤255`. Los scores D0/D1 coinciden con el par de pesos almacenados para ese estímulo. En caso score máximo0, `choose_action` retorna None; si hay empate **positivo**, elige D0. Al feedback, `PlasticLearner.update` cambia solo el peso `(concepto activo, acción elegida)` en ±16 saturado. Una tabla que reciba el mismo estímulo y recompensa aplica el mismo cambio; por inducción mantiene igualdad.

## Diseño del control independiente

- Implementar tabla propia independiente, sin llamar a `PlasticLearner.respond/update`. La fila se elige por el input exactamente (255,0) o (0,255), se computan scores desde 2 enteros, abstención si ambos0, empate D0 si positivo; 4 pesos variables, mismos `random.Random(seed).randint(40,220)`.
- **20 semillas originales 0..19**: mismas secuencias `e03_protocol.sequence` de train100 (sal1000), holdout80 (sal2000), inversión160 (sal3000), holdout80 (sal4000). Comparar scores, acciones, estados y contador **después de cada update**, así como acciones en ambos holdouts sin reentrenar. Reportar unidades y discrepancias; no usar confirmación 1400..1419.
- Pruebas adicionales para empates positivos, dos pesos0 (abstención), saturación superior/inferior, campos de entrada fuera del dominio explícitamente rechazados por el comparador. Estos edge cases NO prueban igualdad para estímulos no-E03, sólo el contrato exacto.
- Métrica primaria: **cero discrepancias exactas** en acciones, scores, estado y trials; 1+ falsifica comparación implementada y se investiga. Las muestras comprueban código; la afirmación universal bajo este dominio descansa en la derivación algebraica, no en estadística.

## Decisión preregistrada

**Si se confirma:** los resultados E03 de 100 % train/reversal son evidencias genuinas de aprendizaje del modelo, **pero no ventaja específica de computación neuronal frente a un mapeo tabular con idéntica representación y cuatro pesos**. No justifica integrar E03+E06 en un cerebro nuevo para reproducir estas tareas aisladas; la siguiente pregunta tiene que exigir memoria continua, crédito temporal selectivo, aprendizaje de representación u otra capacidad no reducible.

**Si se rechaza:** publicar testigo y diferencia, sin ajustar datos ni cambiar umbrales del experimento E03 original.

No modificar núcleo E03, historia C1, `main`, Nilo0.7 ni PR#103 draft; semillas confirmatorias intactas.
