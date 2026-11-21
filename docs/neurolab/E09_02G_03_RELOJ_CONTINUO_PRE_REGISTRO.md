# E09.02g.3 — preregistro de microred C1 con reloj continuo y salida del tick anterior

**21/11/2026, antes de código.** Hipótesis: respetar el orden temporal del propio ejecutable cambia los resultados de aprendizaje respecto de [E09g.2](E09_02G_02_MICRORED_PRE_REGISTRO.md), que reiniciaba Decision a estado80 por episodio y usaba la actividad del ganador del mismo ensayo.

## Evidencia estática C1 del ejecutable

Binario `Creatures.exe` del usuario, SHA-256 `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7`.

- **VA 0x403C92–0x403CBB:** el bucle recorre lóbulos de salida con índices **6,7,8...** y llama a VA 0x403E00; en el `dad1.gen` significa Decision(6), Attention(7), Concept(8).
- **VA 0x403ED1–0x403EF0:** al entrar en una neurona, copia `[neuron+2]` (OUTPUT) y `[neuron+3]` (STATE) al SVTable **antes** de calcular la nueva activación. El OUTPUT guardado ya fue sometido a WTA en el ciclo anterior.
- **VA 0x403F2F–0x4040B6:** Decision lee señales dendríticas anteriores a la actualización de Concept del mismo tick; computa estado y output usando SVRule genética.
- **VA 0x404114–0x404162:** el nuevo STATE se relaja hacia el reposo según rate genético después de emitir OUTPUT. Decision tiene rest80 y neural decay24.
- **VA 0x40418C–0x4047E2:** las SVRules de las dendritas reciben la tabla de valores de la neurona capturada y una instantánea de la dendrita antes de modificarla.
- **VA 0x4048CC–0x404911:** se aplica WTA de lóbulo **después** del cálculo de las neuronas; winner de mayor output, desempate por primer índice. Las salidas no ganadoras quedan en cero.

**Conclusión estática delimitada:** la red lee la salida de Concept **del ciclo previo** al procesar Decision y usa OUTPUT de la neurona **del ciclo previo** al evaluar su susceptibilidad. Esta relación es mucho más fiel que el modo `post_wta_gated` de g.2, que utilizaba un ganador calculado ese mismo ensayo.

## Modelo mínimo congelado

Cinco neuronas nominales P0,P1,C,D0,D1; **ningún cuerpo, mundo ni LLM**.
- Entradas P0=P1=255 en cada tick (señales abstractas).
- Concept=C, ANDTYPE0 y dos dendritas de Perception con STW128; produce salida253 después del tick de Concept. Su salida inicial en tick0 es **0**. Se calcula **después** de Decision.
- Decision D0/D1, cada una con UNA dendrita excitatoria y UNA inhibitoria desde C, no 128+128 originales. STW/LTW, susceptibilidad y strength por gen C1 de la fase g.1.
- Estados iniciales Decision=(80,80); outputs iniciales=(0,0). Tick empieza en1.
- Durante tick: computar los puntajes de ambas D con **concept_output antiguo** y `STATE antiguo` (no restablecerlo a80); tomar nuevas salidas antes de relajación; procesar sinapsis con **OUTPUT antiguo tras WTA anterior** y químicos recibidos; relajar estado neuronal usando rate24/rest80; hacer WTA sobre nuevas salidas; recién entonces calcular nueva salida de Concept253 y guardar.
- Si una dendrita agota strength y el motor indica borrar su neurona propietaria, borrar STATE/OUTPUT de esa neurona en el mismo ciclo. Sin químicos de atrofia CHEM2/3 en este ensayo, así que no debería haber migración.
- **Química de prueba:** señal Reward49/CHEM0=255 si la última acción obtuvo buen resultado, Punishment50/CHEM1=255 en caso contrario; se entrega **en el tick siguiente** a la acción causante. Es un puente temporal artificial entre evaluador y cerebro, **no** cinética bioquímica original de C1; no se permite conocer el objetivo dentro del módulo.
- Desempates: variante principal `first_index` (C1), control `random_tie` con semilla de laboratorio, sin epsilon. Se usan las mismas 20 semillas que g.2.
- No introducir atención, lenguaje, nuevos conceptos, drive interno ni migración para favorecer el score.
- Baseline frozen con idéntico reloj y señales, pero sin plasticidad.

## Ensayo y puertas

- Fase A: 60 ticks, objetivo D0; holdout 80 ticks con sinapsis congeladas y sin químicos.
- Fase B: invertir contingencia a D1 durante120 ticks, partiendo de estado A **sin alterar por holdout**; segundo holdout80.
- Métricas por 20 semillas: exactitud, control congelado, ventajas, porcentajes ≥0.90, trayectoria STW/LTW, estado y OUTPUT persistentes, variaciones de señal Concept previa, número de cambios de ganador.
- Puerta por desempate: ≥18/20 semillas con precisión ≥0.90 en ambas fases y ventaja media inicial ≥0.30 contra congelado. Una condición `first_index` puede tener control inicial perfecto por sesgo D0, así que se reportará por separado la reversión de 0 a1 y la imposibilidad de distinguir aprendizaje inicial de preferencia innata.
- En caso de resultado negativo, conservarlo y no modificar las duraciones/reglas. No prometer éxito ni comparar porcentajes de paradigmas temporales distintos como si fueran idénticos.

## Oráculos previos al código

1. Tick1 con Concept previo0: ambas decisiones puntúan80, desempate first_index→D0, nuevo Concept253.
2. Tick1: OUTPUT previo=(0,0), sin químico; ninguna susceptibilidad cambia.
3. Tick2, con pulso Reward global de la acción D0 anterior: Concept previo253; OUTPUT previo=(80,0); solo dendrita excitatoria D0 aumenta susceptibilidad a4 y STW a3; D1 no aumenta.
4. Tick3 usa STW D0 adquirida en tick2, no antes. La salida de concepto actual no puede influir en Decision de tick2 retroactivamente.
5. Actualización neuronal persistente: cuando un puntaje supera el reposo, STATE relajado debe conservar una fracción, no volver instantáneamente a80.
6. Control frozen no modifica pesos aunque sí avanza el reloj neuronal.
7. Checkpoint recupera outputs, estados neuronales, concepto, tick y cuatro sinapsis y produce la misma continuación.
8. Determinismo de 20 semillas y un resultado reportado para **ambas** políticas, sin ocultar resultados negativos.

**Gate:** validar el reloj y registrar efectos reales del aprendizaje, no declarar que un circuito de cinco neuronas emula todas las funciones del Norn. Si queda un desacuerdo sobre química o actualización de Concept, consignarlo como tal.

**Próximo:** cuantificar en qué medida el reloj y la elegibilidad anterior explican el rendimiento y después evaluar si el entrenamiento necesita una fuente interna de refuerzo/drive en vez de un evaluador de respuestas; eso será un experimento distinto, siempre sin mundo/cuerpo.
