# E09.02i-I3b.1 — preregistro ejecutable de bifurcaciones químicas pareadas

**Fecha:** 2026-11-21. **ANOTADO ANTES DE IMPLEMENTACIÓN Y RESULTADOS**. Depende del [diseño I3b](E09_02I_I3B_DISENO_COMPARACION.md) y del [I3 negativo](E09_02I_I3_RESULTADO_NEGATIVO.md). **Subexperimento diagnóstico N**, no prueba confirmatoria de G05/G09 ni réplica histórica C1.

## Hipótesis y control de procedencia

I3 comparó brazos on-policy, cuyas recompensas diferían según las propias decisiones. Para separar intensidad de CHEM (H-A) frente a retraso y distractores (H-T) se necesita intervenir sobre **el mismo estado/acción causal**. Se fija la elección en un tronco sin feedback, se clona el estado y cada rama recibe el MISMO signo/dosis derivado solo de la decisión común. La red no accede al mapping ni a la etiqueta de la respuesta correcta.

## Cohorte y topología predefinidas

- Nuevas semillas **300..319** (20), objetivo0/1, demora **d=1,2,3**, mappings A=(D0,D1), B=(D1,D0): **240 episodios pareados** (20×2×3×2), no independientes dentro de semilla.
- Cada episodio REINICIA la red de seis unidades/ocho dendritas; es un diagnóstico de un solo pulso y **NO** aprendizaje prolongado. Tronco sin feedback: 32 ticks habituación (8×S0,8×S1,8×S0,8×S1) y luego 4 ticks del contexto objetivo; se fija la **cuarta decisión**. Mappings afectan solo el signo exterior, no la trayectoria ni la acción.
- Copias del estado antes del precursor: **N** sin precursor, **E1** dosis temprana antes del primer distractor CHEM×1, **L1** tardía antes del tick de llegada CHEM×1, **E4** temprana CHEM×4, **L4** tardía CHEM×4.
- Posterior al objetivo: d+1 ticks contexto opuesto y 8 ticks adicionales del distractor sin nuevos precursores. Todos los brazos reciben el mismo número de ticks. Una única inyección de dosis **80** para cada brazo distinto de N, o cero si la decisión no fue emitida.
- Con acierto según mapping, añadir una vez 80 a químicos33 y1; con error, 80 a químico17. Sin acción: registrar nulo y no inyectar. Se procesa por las reacciones originales genes **57,71,111,112**, receptores genes **88,89,126..129** y decay explícito de pool256 tasa **40 para todas las sustancias**. Estos son parámetros de laboratorio FIJOS de I3, no de genoma C1 original.
- Exploración final: 4 ticks de objetivo sin plasticidad ni precursores, registrar cuarta respuesta. No declarar aprendizaje a partir de un solo episodio.
- Intervención amplitud: escalar exclusivamente las entradas cerebrales CHEM0 y CHEM1 (saturadas a 255) antes de invocar C1ContextBrain.step, con ganancia 1 o 4. CHEM2/3 intactas. **La ganancia 4 es un contrafactual de laboratorio, no mecanismo C1 certificado**. La ganancia1 debe ser bit-a-bit igual a e09_i3_metabolic_protocol.metabolic_step. No cambiar pesos, reglas ni cerebro existentes.
- La química es unidireccional (sin emisores conectados a outputs): para ramas E1/E4 y L1/L4, los pools/canales deben ser idénticos tick a tick; solo difiere la ganancia aplicada al input neural. N, E y L mantienen el mismo estado troncal antes del primer feedback.

## Mediciones y criterios preregistrados

- Reportar por episodio/condición, semilla, mapping, objetivo, d, cuarto ganador, signo y tick de inyección, pool, CHEM leída, susceptibilidad, refuerzo, cambios STW y LTW, y decisión final.
- Testigo sináptico: ejecutar la función EXISTENTE update_c1_synapse sobre estado anterior, contrastar cada una de las ocho dendritas resultantes con el verdadero brain.step, y sumar numeric.reinforcement_effect (no rehacer la fórmula).
- Partición: **candidato causal** = dendrita con origen Concept del contexto objetivo Y propietaria Decision que eligió el cuarto ganador. **Distractor** = origen Concept del contexto contrario en cualquier propietaria. Es solo una clasificación operacional, NO prueba causal del origen del comportamiento.
- **H-A amplitud:** contrastar E4−E1 y L4−L1 (mismo calendario) para efecto de refuerzo acumulado en candidato causal y magnitud absoluta de cambio STW final vs rama N. No inferir mejora conductual por construcción.
- **H-T temporal:** contrastar E1−L1 y E4−L4 en la proporción del efecto total atribuido a dendritas de contexto objetivo frente a distractoras. Cuando el efecto total es cero, el cociente es NO EVALUABLE, jamás cero imputado. Dirección exploratoria definida: intervención temprana debería aumentar proporción objetivo.
- Secundarias: fracción sin efecto, dosis efectiva, pico CHEM, cambios LTW, elecciones finales, ausencia de elección, por d/signo/mapping. La intervención temporal puede modificar concentraciones por decaimiento: **equivale dosis entregada y total de ticks, NO exposición cerebral resultante**; es parte del mecanismo probado.
- Comparaciones por episodios apareados con incertidumbre agregada **por semilla** (no por 240 muestras independientes). Bootstrap de clusters de 20 semillas, **2000** réplicas, semilla PRNG **60513**, intervalos percentiles95 %. Publicar todas las salidas y los resultados nulos.
- **G-I3b1-WIRING**: estados iniciales iguales, único evento por rama, dosis idéntica, chem igual para ganancia1/4 en igual calendario, witness sináptico exacto, reproducibilidad y CI. **G-I3b1-OBSERVATION**: resultados completos publicados, sean positivos/negativos/nulos. **G05/G09 no se cierran** con esta prueba.

## Limitaciones y continuidad

Red habituada pero no entrenada, un único evento, sin metabolismo corporal, mundo, emisiones neuronales automáticas ni tasas genómicas verificadas. Después de resultados de esta cohorte 300..319 no ajustar ganancia/dosis/rates para fabricar éxito; toda validación de un mecanismo elegido requerirá otra cohorte y preregistro. PR #103 continúa draft, Nilo 0.7/main intactos.
