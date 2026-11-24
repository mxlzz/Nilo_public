# E09.02g.10c — preregistro exploratorio: susceptibilidad C1 y crédito diferido

**Fecha:** 2026-11-21. Esta auditoría de mecanismo se decide después de la prueba g.10b negativa; es **post hoc respecto del resultado g.10b**, pero los indicadores que siguen quedan fijados **antes de escribir/ejecutar g.10c**. No confirma una hipótesis independiente de g.10b.

## Antecedente de la propia implementación

En las dendritas Decision originales, la SVRule de susceptibilidad del genoma se representa como **OUTPUT TRUE INPUT** (10,22,16). La traza `susceptibility` de cada sinapsis aumenta en pasos de 4 bajo coincidencia OUTPUT del propietario y INPUT de origen; si no, decae según tasa genética (48 en Decision). Cuando llega Reward/Punishment, la magnitud del refuerzo STW depende de **(susceptibility × chem) >> 8**. Estos mecanismos **ya son un tipo de traza de elegibilidad temporal local**, aunque no equivalen automáticamente a TD(λ) ni implementan necesariamente crédito correcto por acción explícita. Fuentes primarias locales: `c1_synapse_integrated.py`, `c1_svrule_runtime.py` y `c1_dendrite_tick.py`, derivadas del ejecutable C1 aportado.

Por tanto, es incorrecto inferir que C1 carece por completo de memoria del evento previo solo porque `Concept` haya cambiado al llegar la recompensa. g.7 observó discordancias de fuente, **no** demostró que el pulso se asignase exclusivamente a la fuente nueva. La falla de IG en g.10b puede estar eliminando un refuerzo todavía útil para sinapsis elegibles.

## Pregunta e instrumentación congeladas

¿Persiste susceptibilidad en las sinapsis asociadas a la acción objetivo cuando llegan pulsos diferidos entre distractores, y qué efecto **causal del pulso en un único tick** se observa sobre STW de esas mismas sinapsis?

Se reproducirá exactamente el **brazo C** del calendario g.10b, mismas 40 semillas 120..159 y las dos fases A/B (sin holdout durante la secuencia de entrenamiento). Es un **diagnóstico del conjunto ya conocido**, no replicación OOS. Por cada ensayo:

1. Ejecutar cuatro ticks de contexto objetivo y conservar únicamente la cuarta elección; después d=1,2,3 ticks del contexto opuesto con química ZERO, como g.10b.
2. Antes del tick de entrega química capturar estado inmutable completo, `susceptibility`, STW y Concept.
3. Ejecutar **dos trayectorias locales desde ese mismo estado**: `brain.step(..., pulse)` y `brain.step(..., ZERO)`, ambas con `learn=True` y el mismo estímulo distractor. **Descartar** la rama ZERO; continuar el entrenamiento con la rama verdadera `pulse`.
4. Identificar la dendrita Decision del **propietario seleccionado en el target** y el **concepto target**, de clase excitatoria si Reward o inhibitoria si Punishment. Comparar su STW posterior entre ambos estados: esto mide la contribución inmediata del pulso manteniendo idénticos estado/tiempo/estímulo. Repetir para la dendrita del mismo propietario conectada al **distractor** y para las dendritas de ambos conceptos del **propietario no seleccionado** (clase química activa). No atribuir diferencias globales futuras a esta comparación de un tick.
5. Guardar por evento: fase, semilla, objetivo, d, acción causal, tipo de química, susceptibilidad previa target/distractor, `delta_STW_pulse_vs_ZERO` de target/distractor/otro propietario, y presencia de pulses ZERO por ausencia de acción. Publicar todos los eventos o al menos JSON íntegro si el volumen lo permite.
6. Al terminar cada fase, **reproducir exactamente** estado final y métricas de entrenamiento del runner `neural_phase` de g.10b usando una trayectoria original no instrumentada. Si no hay paridad exacta por semilla/fase, invalidar el diagnóstico.

## Resultados sin calibración posterior

- Totales y promedios por fase/delay de SUS objetivo y distractor antes del refuerzo; fracción SUS objetivo >0 y SUS distractor >0.
- Efecto causal medio y fracción de eventos con STW objetivo modificado por la química en cada delay. Comparar con distractor y otras dendritas, **sin** asignar destino exclusivo al feedback.
- Contar en d=1 cuántos pulsos afectan positivamente a STW objetivo en el brazo C: esta es una pérdida potencial del filtro IG de g.10b, que eliminó 800/2400 pulsos por fase. Las trayectorias C e IG no son idénticas, por lo que el dato no predice cuánto recuperaría IG al dejar pasar esos pulsos.
- **Sin puerta de éxito cognitivo**: es análisis mecanístico. Un valor SUS objetivo >0 prueba persistencia local de estado, NO prueba que el algoritmo siempre asigne crédito correcto; un aumento STW target no prueba aprendizaje útil de tareas futuras.

## Decisión posterior

Si C1 ya mantiene trazas útiles, priorizar **comprender su fidelidad temporal y química histórica** antes de agregar memoria causal nueva. Evaluar la necesidad de una cola explícita o trazas tipo RL solo frente a fallos que el mecanismo verificado no resuelve, con costo/beneficio frente al Q tabular. No modificar código de C1, genoma, mundo, LLM, motor Nilo ni `main`.
