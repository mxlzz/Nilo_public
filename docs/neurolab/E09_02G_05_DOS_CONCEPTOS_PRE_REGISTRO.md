# E09.02g.5 — preregistro: dos conceptos y discriminación contextual sin mundo

**Fecha:** 2026-11-21. Se fija **antes del código y antes de ejecutar las pruebas**.

## Pregunta falsable

La microred C1 de cinco neuronas solo reconoce un contexto C fijo y aprende una preferencia. ¿Puede la **menor ampliación pertinente, seis neuronas**, representar dos situaciones abstractas alternadas y asociarlas a acciones diferentes, para luego invertir ambas asociaciones sin olvidar una al aprender la otra?

No agregar cuerpo, mapa, mundo, necesidades físicas, lenguaje ni LLM. Las señales `S0` y `S1` son entradas binarias de un banco de pruebas, no objetos simulados.

## Topología congelada

- **6 neuronas:** dos señales perceptuales `P0,P1`, dos detectores `C0,C1`, dos decisiones `D0,D1`.
- `C0` reconoce solo P0; `C1` reconoce solo P1. Cada detector usa **una dendrita**, permitido por `dad1.gen` Concept min1 max3, con peso STW128, attenuation255. Señal del Concept activo = `(255×128 >>8)×255>>8 = 126`. El otro concepto emite cero. Ambos detectores son **predefinidos**: esta prueba NO demuestra formación autónoma de conceptos.
- **8 dendritas plásticas de decisión:** por D0/D1, una excitatoria y una inhibitoria **desde cada uno de C0 y C1**. C1 original tiene 128 por clase; usar 2 por clase en lugar de128 es una **reducción de laboratorio**.
- Cada dendrita inicia sus=STW=LTW=0, strength=2; tasas y SVRules auténticas del genoma Decision, con `Reward49`→CHEM0 excitatorio, `Punishment50`→CHEM1 inhibitorio, CHEM2/3 cero.
- El score de Decision combina señales TYPE0/TYPE1 de **ambos Concept** con cálculo `>>8`, attenuation128, estado neuronal persistente, SVRule `STATE+TYPE0-TYPE1` y relajación hacia80 (rate24).
- **Reloj del ejecutable:** Decision lee outputs de Concept del tick previo, las reglas sinápticas reciben OUTPUT Decision previo post-WTA, Concept se actualiza después de Decision; WTA de mayor OUTPUT.
- Política de empate `random_tie` con semilla reproducible de laboratorio, sin epsilon continuo.
- Flujo químico: pulso Reward/Punishment suministrado por el evaluador **un tick después** de la acción anterior, sin etiqueta de contexto ni respuesta correcta dentro de la red.
- No migrar dendritas en esta fase, ya que CHEM2/3=0; red topológicamente fija para comparar discriminación.

## Datos congelados antes de probar

- **20 semillas 0..19**.
- Entrada de cada tick: exactamente **un** contexto S0 o S1. Se forman bloques de 8 ticks. Cada fase de entrenamiento tiene **32 bloques**, 16 S0 y16 S1 en **orden aleatorio balanceado**, con PRNG `random.Random(seed+10000)` para fase A y `random.Random(seed+20000)` para fase B. Esto evita que un reloj periódico indique trivialmente el contexto.
- **Fase A:** 256 ticks, en S0 premiar D0 y en S1 premiar D1. **Fase B (inversión simultánea):** 256 ticks, S0→D1, S1→D0. Conservar sinapsis, estados neuronales y pulso pendiente entre fases.
- Después de cada fase hay holdout sin plasticidad de **16 bloques** balanceados, ocho S0 y ocho S1, reordenados con `random.Random(seed+30000)` para A y `random.Random(seed+40000)` para B. Ejecutar sobre copia inmutable del estado: ni el evaluador ni el entrenamiento deben reiniciarse tras el holdout.
- Evaluación total sobre los **128 ticks** de holdout; evaluación `steady` sobre **las seis últimas decisiones de cada bloque de ocho** (96 ticks), excluyendo los dos primeros para medir reconocimiento una vez propagada la señal a Concept y Decision. **Ambas métricas se informan siempre**, incluida exactitud inmediatamente después de transiciones.
- No aumentar episodios, número de neuronas, peso inicial ni explorar hiperparámetros tras conocer resultado.

## Controles y competencia de complejidad

1. **Frozen:** idéntica red de seis neuronas, mismas secuencias y química, pero sin cambios sinápticos. Controla aprendizaje real contra decisiones casuales.
2. **Ablación sin contexto:** idénticas ocho dendritas y reloj, pero internamente siempre ve S0, aunque el evaluador mantiene S0/S1 y sus objetivos. Verifica si una preferencia sin información contextual basta.
3. **Baseline tabular simple:** tabla 2×2 de valores asociativos `Q[context][action]` con epsilon0.10 durante entrenamiento y política greedy en holdout; actualización `Q ← Q + 0.2*(r−Q)`. Utiliza una cola de un evento `(contexto, acción, recompensa)` para actualizar la asociación que realmente causó el pulso. Es una alternativa deliberadamente **más informada respecto de crédito causal** que la sinapsis local; se reporta esa ventaja, no se finge presupuesto cognitivo equivalente.

## Puertas preregistradas

Por red neuronal aprendida:
- **Puerta contextual:** al menos **18 de 20 semillas** logran precisión steady ≥0.90 **en A y B** sobre las mismas semillas; ventaja media steady inicial ≥0.25 sobre frozen; y ventaja media steady inicial ≥0.20 sobre ablación ciega.
- Las tasas total/steady por contexto y los errores en primeros dos ticks de cada bloque se publican igualmente.
- Para baseline tabular se informa tasa y tiempo de actualización, sin exigir que la red lo supere: si la tabla iguala o supera la red, **no hay justificación empírica para preferir la arquitectura compleja en este problema**.

## Oráculos y pruebas antes de evaluar

1. Con S0 activa y S1 inactiva, C0 output126, C1 output0 **después del primer tick**; Decision del primer tick lee (0,0).
2. Al cambiar de S0 a S1, el siguiente tick Decision todavía lee el Concept de S0; tras actualizar Concept, la salida refleja S1; no adelantar información del futuro.
3. El refuerzo tarda un tick; no se introduce la identidad `correct_action` en el cerebro.
4. Ocho dendritas no crecen ni cambian de origen; si el código indica una pérdida estructural, medirla y no migrar silenciosamente.
5. Baseline frozen no modifica ninguna sinapsis; tabla actualiza únicamente Q del contexto/acción almacenado en su cola.
6. Secuencias de bloques balanceadas y deterministas; 20 seeds, checkpoints de 8 dendritas/estados/outputs de C0/C1; no fuga del target en el modelo.
7. Si el gate falla, conservar resultado negativo, no modificar umbrales, y evaluar si el origen es temporización/cambio de contexto, plasticidad excesivamente lenta, saturación o ausencia de un mecanismo de memoria causal.

**Interpretación:** éxito = discriminación asociativa elemental entre dos señales abstractas y dos respuestas en un circuito de seis unidades. No = autonomía de Nilo, creación de conceptos, pensamiento semántico ni emulación del Norn de 952 neuronas.

**Siguiente criterio de continuidad:** no aumentar tamaño más allá de seis neuronas si todavía no discrimina dos señales. Si discrimina, comparar ruido y crédito diferido con contextos alternos antes de pasar a motivación intrínseca.
