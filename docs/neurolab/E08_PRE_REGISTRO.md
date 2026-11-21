# E08 — pre-registro: actividad neuronal sin estimulación continua

**Fecha:** 2026-11-20. Experimento propio NeuroLab, independiente de la investigación histórica C1 (no constituye evidencia de conciencia o pensamiento). Se define antes de ejecutar.

## Hipótesis y controles

Un circuito neuronal recurrente mínimo puede conservar actividad y fase después de retirar las entradas externas. La misma arquitectura sin conexiones recurrentes pierde la actividad. Un circuito similar con sinapsis atenuadas termina extinguiéndola.

No introducir una fuente aleatoria oculta ni un generador artificial de «pensamientos». Todas las señales deben salir de las ecuaciones y del estado inicial especificado.

## Diseño matemático predefinido

Usar `experiments/neurolab/kernel.py` E01, con dos neuronas `A,B` de tipo compute, `threshold=0`, `rest=0`, `decay=255` (estado interno regresa al reposo cada tick). **La salida** de cada neurona se calcula antes de su relajación, según la convención NeuroLab documentada.

Condición 1 **Control sin recurrencia:** sin sinapsis, estado inicial `A.output=120`, `B.output=0`. Esperado: ambas salidas cero desde tick1.

Condición 2 **Recurrencia excitatoria:** `A→B` y `B→A` con peso255. Estado inicial `A.output=120`, `B.output=0`. Esperado: alternancia exacta cada tick `(A,B)=(0,120),(120,0),(0,120)...`, ciclo de período 2.

Condición 3 **Recurrencia atenuada:** mismos enlaces peso200. Valor máximo de activación no crece; la señal se pierde progresivamente. Esperado: en ≤64 ticks ambas salidas cero.

Condición 4 **Perturbación inicial:** con sinapsis255 iniciar `A.output=120,B.output=50`. Esperado: alternancia entre `(50,120)` y `(120,50)`, diferente de la condición 2 sin necesidad de nuevas entradas.

Condición 5 **Robustez y control numérico:** 20 estados iniciales generados por `random.Random(seed)` con `seed=0..19` y entradas ausentes por 100 ticks; amplitudes permanecen [0,255], determinismo y checkpoint/restauración exactos.

## Instrumentación y métricas

Registrar salida de A/B por tick, clasificación de dinámica (inactiva, ciclo2, transitoria amortiguada), periodo, amplitud, efecto perturbación, comparación sin conexiones y duración en ticks.

**G08:** resultados numéricos comparados con oráculos manuales y condición de control. Es validación de dinámica matemática, no de autonomía psicológica ni de motivaciones espontáneas. Un circuito alimentado por conexiones propias puede oscilar por diseño sin sentir ni elegir nada.

No modificar la regla de neurona E01: pruebas G01–G07 deben seguir pasando. No adicionar LLM, mundo, cuerpo ni objetivos.
