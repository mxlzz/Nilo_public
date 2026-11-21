# E05 — pre-registro de susceptibilidad temporal y atribución imperfecta

**2026-11-20 · Antes del código E05.**

## Fuente y distinción histórica

Grand, Cliff y Malhotra (1996–1997) describen dendritas de Decision con susceptibilidad que aumenta cuando se activa la combinación de concepto y acción, luego decae. El refuerzo químico posterior modifica pesos sensibles. Steve Grand (1995) reconoce que la recompensa puede atribuirse equivocadamente a acciones cercanas en el tiempo y que la ventana corta limita el aprendizaje de consecuencias distantes.

Fuentes: [paper original §3.1.2](https://eem.foo/ccarchive/Sites/fp.cyberlifersrch.plus.com/articles/agents_%2797_paper.htm) y [I Am Ron's Brain §2.a](https://web.archive.org/web/20071208173623/fp.cyberlifersrch.plus.com/creaturesarchive/braindesc.htm). Fórmulas discretas debajo: **modelo propio**, no copia de tasas exactas C1.

## Regla congelada antes de implementar

Estado local `(weight, eligibility)`, enteros 0..255, `weight=128`, `eligibility=0`.

- Evento de uso real de la conexión: `eligibility=255`.
- Tick sin nuevo uso: `eligibility = floor(eligibility*3/4)`.
- Feedback `reward ∈ {-1,0,+1}` aplicado cuando llega: `weight = clamp(weight + reward*floor(32*eligibility/255),0,255)`. El feedback no activa ni reinicia la elegibilidad.
- Peso constante si elegibilidad 0; no se permite actualizar conexiones nunca utilizadas.
- Sin STW/LTW en esta prueba aislada: se mide crédito temporal independientemente de consolidación E04.

## Condiciones de laboratorio fijadas

1. Refuerzo positivo después de retrasos k=`0,1,3,5,10` ticks. Magnitud positiva monotónica no creciente con k; verificar contra cálculos manuales.
2. Control sin elegibilidad siempre 0: no cambia peso ante premio retrasado. Control refuerzo inmediato k=0 debe tener respuesta mayor que k=5.
3. Feedback no relacionado con ninguna acción (sin uso): no modifica peso.
4. Distractor no correlacionado: una segunda conexión B se activa en episodios emparejados con refuerzos +1 y -1; su cambio neto debe ser 0 si no hay saturación, evitando confundir simple activación con evidencia de causalidad.
5. Distractor correlacionado espuriamente: A se activa antes y provoca recompensa, B se activa más recientemente antes de la recompensa. Predicción: el método local asignará **más** crédito a B, aunque la causa verdadera sea A. No eliminar ni suavizar este resultado negativo.
6. Tests de saturación, invalidaciones, valores extremos, series largas y checkpoint.
7. Repetir cada caso con y sin la nueva capacidad de elegibilidad. No ajustar la constante 3/4, la magnitud 32 ni los retrasos después de ver los resultados.

## Interpretación y puerta de fase

**Éxito local:** demostrar crédito diferido vs sin elegibilidad, caída temporal y ausencia de actualización de conexiones inactivas; documentar el caso de atribución errónea. **G05 del plan maestro es más exigente**: “sin reforzar sistemáticamente decisiones ajenas”. Si el caso correlacionado muestra refuerzo falso (esperado), **declarar G05 parcial/no superada en ese componente**, no alterar criterios a posteriori. Antes de avanzar a E06 analizar si hay una alternativa causal con evidencia adicional, o si la intención histórica de mantener un mecanismo imperfecto justifica su uso bajo límites definidos.

Opciones a comparar después sin decidir aquí: (a) heurísticas de elegibilidad histórica, (b) trazas condicionadas por identidad de evento/acción cuando el evaluador conoce realmente la causa, (c) métodos temporales de aprendizaje por refuerzo más potentes. No dar como real una causalidad que la mente no puede observar.

## Entrega

`experiments/neurolab/eligibility.py` y `tests/test_eligibility.py`, CI y un informe que separe las pruebas satisfechas del problema de crédito indebido. No genera personaje, entorno ni LLM.
