# E09.02g.4 — preregistro de robustez y orden invertido

**Fecha:** 2026-11-21. Documento congelado **antes** de implementar esta fase.

**Punto de partida:** [E09g.3](E09_G_MICRORED_RESULTADOS.md) alcanzó 20/20 semillas con precisión perfecta para entrenamiento D0→D1 y desempate `random_tie`, pero utiliza un solo concepto fijo y un evaluador que inyecta químicos. **El resultado puede ser frágil al sesgo por la primera acción, al ruido del refuerzo y al retraso causal.**

## Pregunta y controles

Con la misma microred histórica de cinco unidades, las mismas tasas genéticas y el mismo reloj de salida previa, ¿se conserva la capacidad de aprender y revertir cuando:
- la primera acción recompensada es D1, no D0;
- el 10% de los pulsos de feedback invierte su signo;
- el pulso llega **tres ticks** después de la acción, en lugar de uno?

No modificar `c1_continuous_brain.py`, la regla STW/LTW, su árbol de conexiones, ni reglas de empate. **Explorar estas condiciones es un test de validez, no una búsqueda de hiperparámetros.**

## Diseño preregistrado

- **Política única primaria:** `random_tie`, pues `first_index` presenta sesgo D0 y el ensayo previo con D0 primero no superó la ventaja sobre el control congelado. Conservar first_index como evidencia histórica, pero no usarlo para decidir mejora en esta fase.
- **Seis condiciones (2 órdenes ×3 perturbaciones)**:
  - `D0→D1`, `D1→D0`;
  - base **limpia, delay1**;
  - **noise=0.10, delay1**;
  - **limpia, delay3**.
- **20 semillas** 0..19 por condición, 60 ticks fase A, 120 fase B, 80 ticks de evaluación sin aprendizaje después de cada fase. En ambas evaluaciones, el estado neuronal avanza con entrada química cero y sin cambiar el estado entrenado.
- El control `frozen` recibe la **misma secuencia de semillas, reloj, señales y química**, pero sus sinapsis no se modifican. Evaluar precisión y ventaja inicial por semilla.
- El estímulo P0=P1=255 y el único concepto C no cambian; no se incluyen objetos, cuerpo, mundo, metas internas, ni LLM.
- `delay=1`: la recompensa/castigo de una acción en tick t se administra al comienzo de tick t+1 (semántica del E09g.3).
- `delay=3`: el pulso de una acción en tick t se administra en t+3. Una **cola explícita de 3 pulsos** recibe/retiene eventos, y la cola se lleva sin vaciar entre A y B, para que se vean las consecuencias todavía pendientes del antiguo objetivo. Tampoco se vacía antes del holdout, pero el holdout se ejecuta **sobre una copia** sin afectar el entrenamiento ni la cola.
- `noise=0.10`: cada acción observada puede recibir el **químico opuesto** de forma aleatoria, incluyendo acciones correctas e incorrectas; el sorteo del evaluador es determinista por combinación `seed`, número de tick y salteo constante explícito. **No se pasa el target al cerebro**, solo los cuatro niveles químicos. Ausencia de acción emite pulso cero. Informar número de pulsos invertidos, no afirmar exactamente10% por muestra.
- Definir cola/tick y producción de pulso en el **evaluador**, no en `C1ContinuousBrain`.
- Para asegurar independencia entre semillas y estabilidad reproducible, generar ruido por `random.Random(seed*2_000_000+tick+93017).random()<0.10`, sin estado RNG oculto; la misma seed/tick implica el mismo resultado para controles.
- **Sin ajuste post hoc** de epsilon, pesos, duración, nivel de ruido o delay.

## Métricas y puertas congeladas

Para cada condición medir precisión por semilla en ambas fases, `mean_train`, `mean_reversal`, `mean_frozen`, cantidad de semillas con precisión≥0.90 tras A y B, ventaja media inicial vs frozen, cantidad de pulsos invertidos, sinapsis final y estado neuronal persistente.

**Puerta primaria por condición**: ≥18/20 semillas logran ≥90% de precisión tras A Y B, y ventaja media sobre frozen ≥0.30. Informar todas las puertas aunque fallen.

**Comparación secundaria:** reportar caída de precisión respecto a `clean/delay1` con mismo orden, pero no exigir tolerancia arbitraria: el test de estrés busca identificar exactamente si el retraso o el ruido rompen el aprendizaje.

**Aceptación de implementación:** pruebas de cola1/3, signo químico, inversión de pulsos, reproducibilidad, holdout sin mutación, control frozen, mismo estado/evaluador que E09g.3 en D0→D1 sin perturbación, y suite histórica completa. Que falle una puerta científica es resultado, no bug; el runner debe registrar `passed:false` sin ocultarlo.

## Advertencia fundamental

Las respuestas correctas son conocidas por el evaluador de laboratorio y nunca por la red. Sigue sin ser una mente libre ni sin estímulos externos. Si la señal llega tarde mientras varias decisiones ocurren, puede atribuirse a la neurona equivocada: esto se conectaría con el problema E05. **No compensar dándole al cerebro una etiqueta causal invisible.**

**Siguiente fase prevista:** después de reportar resultados, diseñar segundo concepto/contexto con igual capacidad y control tabular. No sumar nuevos mecanismos sin demostrar que el modelo mínimo aprende situaciones diferenciadas.
