# NeuroLab — G05-INFO.01 resultado de identificabilidad y fuga estructural

**Fecha:** 22/11/2026. **Estado:** UNIDAD DOCUMENTAL COMPLETADA, RESULTADO **C (atajo temporal determinista)**. No se entrenó ningún modelo ni se ejecutó una cohorte científica; no es confirmación G05 ni altera el ensayo original. Referencia: [selección y contrato G05-INFO](DECISION_PRIORIZACION_Y_GATE_G05_INFO_20261122.md). Rama de investigación aislada; PR#103 draft.

## 1. Material inspeccionado y condición de validez

- [Preregistro g.10b](E09_02G_10B_DEMORA_DISTRACTORES_PRE_REGISTRO.md) fija 4 ticks en contexto objetivo `S`, solo puntúa la cuarta decisión `a*`, luego `d∈{1,2,3}` ticks del contexto contrario `1-S`, y en un tick adicional de **ese mismo contexto contrario** llega Reward/Punishment por `a*`.
- [Runner exacto](../../experiments/neurolab/e09_delayed_distractors_protocol.py), `neural_phase()`, envía `_step(... target, ZERO)` cuatro veces, `_step(... distractor, ZERO)` `delay` veces y `_step(... distractor, pulse)` una vez. `pulse=ZERO` si `action is None`; caso contrario es Reward/Punishment según la decisión puntuada.
- [C1ContextBrain.step](../../experiments/neurolab/c1_context_brain.py) recibe un `context∈{0,1}`, químicos y su estado previo y produce una `action` por tick; no recibe bandera de evaluación ni ID causal. El runner Q, en cambio, conserva `stored=(target,action_index)` desde un punto de evaluación que solo el evaluador conoce, y no actúa en distractores.
- [g.10b resultado](E09_02G_10B_RESULTADO_DEMORA_DISTRACTORES.md) y [g.10c susceptibilidad](E09_02G_10C_RESULTADO_ELEGIBILIDAD.md): C 16/40 semillas en ambas fases≥90%, IG 6/40, Q 40/40 **con información privilegiada**; la susceptibilidad C1 retiene componente del objetivo pero reparte crédito al distractor.

## 2. Resultado matemático

En **todo ensayo con pulso no nulo** del generador g.10b:

- Sean `S` el contexto objetivo en los cuatro primeros ticks y `D=1-S` el distractor.
- La cuarta acción `a*` es **exactamente la acción inmediatamente anterior a la transición observada `S→D`**.
- Desde esa transición hasta que llega el pulso, **no existe otra transición de contexto**, porque todos los `d+1` ticks siguientes ven `D`.
- En consecuencia, al recibir el pulso en el contexto `D`, un controlador que solo haya observado `(context_t, action_t, pulse_t)` puede recuperar `S=1-D` y `a* =` última acción antes del **último cambio de contexto**.
- Una memoria de longitud constante basta: `prev_context`, `action_before_last_switch` y `valid`. No hace falta un token oculto de `target`, ni `delay`, ni contador de ensayos. Se trata de capacidad informacional **posible**, NO de capacidad implementada en C1.
- Esto sigue siendo cierto cuando el contexto final de un ensayo coincide con el contexto inicial del siguiente: el cambio `S→D` dentro del ensayo más reciente ocurre de todos modos antes del pulso.
- **Excepción importante:** si el modelo elige `action=None` en el tick puntuado, el runner entrega pulso `ZERO`. No se puede reconstruir la procedencia de un evento de recompensa **que no existe**; esa ausencia debe reportarse y no sustituirse por la respuesta del evaluador.

**Conclusión:** el origen de cada pulso no nulo es **reconstruible sin señal privilegiada**, siempre que el controlador preserve su historial de decisiones y use el patrón de cambio sensorial. Eso **no** significa que conozca el significado de ese patrón o aprenda la regla causal; una solución programada «último cambio de contexto» es un **atajo estructural del banco**.

## 3. Dos testigos analíticos

1. `S=0`, ticks objetivo `(0,D0),(0,D1),(0,D0),(0,D1)`; luego `d=1`, `(1,D0)`, `(1,D0,Reward)`. Último cambio `0→1`; decisión anterior `D1`; origen recuperado `(0,D1)`.
2. `S=1`, ticks objetivo `(1,D1),(1,D1),(1,D1),(1,D0)`; luego `d=3`, tres `(0,...)` sin premio y `(0,...,Punishment)`. Último cambio `1→0`; acción anterior `D0`; origen `(1,D0)`.

**Comprobación determinista independiente en esta revisión:** se construyeron secuencias ficticias de **3 ensayos consecutivos** para cada combinación de `2³` objetivos y `3³` demoras (=216 secuencias), con una elección de acción determinista por tick distinta según posición/ensayo/demora. Para **648 pulsos** de esas secuencias, el algoritmo «último cambio» reconstruyó exactamente el par `(target, action)` puntuado. **648/648 fixtures PASS**. Estas son pruebas sintéticas del **calendario y la inferencia**, NO corridas de microC1, NO semillas 120..159, NO predicción de exactitud conductual ni benchmark estadístico. La identidad algebraica anterior no depende de ese muestreo de acciones.

Procedimiento independiente para replicar los fixtures (pseudocódigo):
```text
por cada targets en {0,1}^3 y delays en {1,2,3}^3:
  construir tres ensayos consecutivos [target×4, (1-target)×(delay+1)]
  generar arbitrariamente una acción por tick; guardar la acción del 4º tick
  al marcar cada último tick del distractor como pulso:
    buscar hacia atrás el último cambio de contexto observado
    assert (contexto_anterior, acción_anterior) == (target, acción_del_4º_tick)
```

## 4. Matriz de acceso, costo y controles

**Inputs del cerebro C:** contexto binario, químicos en tiempo real, decisión previa generada internamente, estado neuronal/sináptico y reloj de ticks; no recibe `target`, `mapping`, `delay`, banderas de inicio/final ni etiqueta de acción puntuada. **Q histórico:** sí recibe `target` y la acción evaluada del evaluador, actúa una sola vez por ensayo; es techo oracular, **no control fair**.

**Mínimo analítico de memoria para recuperar una procedencia de pulso:** último contexto (1 bit), acción antes de último cambio (D0/D1/None, 2 bits), flag de validez (1 bit) y posiblemente un registro de signo de recompensa; estado constante **O(1)** adicional. Es una cota de información, **no medida de bytes Python**. Para un controlador que aprenda asociación se requiere también su tabla/pesos y política de exploración, medidos por separado.

**Controles que harían falta en un banco útil:** un decisor que elija en cada tick y aprenda con última acción, otro con trazas de elegibilidad y otro con buffer propio, todos con exactamente el mismo flujo; Q solo como oráculo. **Pero ni siquiera esa comparación basta en g.10b para afirmar crédito general**, porque el último cambio aporta una clave temporal perfecta al origen del premio. Si se implementara un «buffer de transición» aquí, demostraría explotar el atajo, no resolver ambigüedad causal arbitraria.

## 5. Verificación de atajos y dictamen A/B/C

- **Identificabilidad:** sí para pulsos no nulos de **este** generador, por construcción; por tanto **no** se demostró imposibilidad informacional.
- **Atajo:** sí; siempre se observa `D=1-S` y el evento puntuado queda en el último cambio de contexto antes del pulso. No requiere inferir una dependencia causal a partir de experiencia; puede reconstruirse mecánicamente.
- **Comparación histórica:** asimetría de acceso de Q probada por inspección de código; éxito Q no implica que C tenga la misma señal causal; su desigualdad **no invalida** el resultado negativo g.10b para la arquitectura C bajo ese protocolo.
- **Resultado C:** **el banco g.10b no es una prueba suficientemente discriminante de crédito causal general**. No ejecutar nuevas variantes ni consumir más semillas de G05 con ese generador; su valor como evidencia histórica limitada y diagnóstico de interferencia se conserva sin modificación.

## 6. Próxima decisión — G05-INFO.02 (solo diseño previo a código)

Evaluar una tarea de consecuencias diferidas que **no permita recuperar la acción causal por una transición sensorial fija** y que a la vez preserve una señal estadística identificable para aprender sin IDs de origen. Requisitos mínimos:

1. Distintos distractores independientes del contexto objetivo, y transiciones que no identifiquen unívocamente el tick puntuado.
2. Demoras variables y superposición posible de candidatos, con protocolo que no se pueda descifrar mediante el pulso como marcador fijo de final.
3. Evaluar primero si dos historias observacionalmente iguales admiten atribuciones incompatibles: en tal caso, no exigir recuperación perfecta de eventos individuales; medir **valor esperado de conducta y selectividad de actualización** bajo la distribución especificada.
4. Controles simplísimos de igual información e idénticas oportunidades de acción; un oráculo con procedencia solo como techo descriptivo.
5. Una auditoría analítica de filtraciones/calendario y viabilidad antes de codificar: si un baseline con regla temporal fija logra inferencia perfecta, **rediseñar**, no promover el resultado como aprendizaje causal.
6. Comparación con soluciones existentes (TD/SARSA(λ), trazas de tres factores; no nuevas bibliotecas pesadas sin coste justificado), preregistro nuevo y semillas distintas. No cambiar retrospectivamente g.10b ni reabrir las reservas `1400..1419` o `24000..24019`.

**Estado final:** G05-INFO.01 documental **COMPLETADA — C**; G05 original y G09 **NO SUPERADAS**; H histórica pendiente; NR01 STOP confirmado; PR#103 draft. Ningún experimento nuevo aprobado.
