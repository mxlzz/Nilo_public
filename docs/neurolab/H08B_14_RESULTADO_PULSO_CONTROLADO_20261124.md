# H-08b.14 — entrega controlada de premio y castigo, gate técnico

Fecha 2026-11-24. [Preregistro](H08B_14_PREREGISTRO_PULSO_CONTROLADO_20261124.md), commit f674a8ed51a5a6199e6891f729d017f1f7c77b1c. [CI #45488311903](https://github.com/mxlzz/Nilo_public/actions/runs/45488311903), commit workflow 5987e615bcc75ae4daf97b64b238d30a0388ab2f. [Evidencia íntegra derivada](resultados/h08b_14_pulse_pilot_20261124.json), commit af708bb64d6fad63dc95788fa0444977f36402af. Tres sesiones independientes, original y CD verificados, un Norn con dad1 por sesión, 85s de espera, sin depurador durante sondeos, una macro de intervención por sesión. No reinyección.

**PASS de factibilidad de entrega:**
- Sham, job 138779534051: chemical49 0→0 (delta0).
- Reward, job 138779534310: chemical49 0→32 (delta32).
- Punishment, job 138779534585: chemical50 5→37 (delta32).
- Identidad verificada, 5/5 ventanas válidas por brazo, 90/90 consultas de los seis campos válidas. Lecturas pre/post independientes y consecutivas, no atómicas. En reward se observaron 32→14→2 en 49, y 2→14→12 en 51; sham y punishment tienen dinámica endógena diferente. No ajustar dosis ni declarar causalidad sobre cada concentración derivada.
- Decision6/cell0/type0: count128 constante, suma susceptibilidad=0, STW=0 y LTW=0 en **todas las 15 ventanas**; strength agregado estable por individuo (42/133/140). Ningún cambio de peso en el punto muestreado. No es una prueba negativa de plasticidad en toda la red: se eligió una célula sin susceptibilidad observable y un solo tipo. Punishment actúa directamente sobre clase1, no sobre clase0 observada. Los tres sujetos difieren antes de la intervención; no utilizar comparación entre ellos como efecto causal sin réplicas y actividad controlada.

**Decisión:** gate de administración superado, aprendizaje no evaluado. Evitar repetir pulsos en célula inactiva. H08b.15 debe evaluar disponibilidad real de susceptibilidad por las 16 células Decision y sus dos tipos, en ventanas predefinidas y sesiones independientes, sin pulso. Si existe disponibilidad, justificar observación por dendrita antes de inferir plasticidad y preregistrar ensayo con actividad previa/identidad/control sham. Si no existe, la ruta de estímulo sin contexto no es un ensayo discriminante; no optimizar dosis arbitrariamente. N STOP, G05/G09 abiertas; main intacto, PR103 draft.
