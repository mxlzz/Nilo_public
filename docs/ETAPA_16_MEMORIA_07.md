# Nilo 0.7 — Etapa 16: memoria, investigación y evidencias

Fecha: 5 de noviembre de 2026. Rama: refactor/0.7. Referencia: 0.6.4 conservada en main.

Plan: [reestructuración integral](PLAN_REESTRUCTURACION_NILO_07.md). Seguimiento: [tablero de etapas](ESTADO_REESTRUCTURACION_07.md), [issue #74](https://github.com/mxlzz/Nilo_public/issues/74), [PR #77](https://github.com/mxlzz/Nilo_public/pull/77).

## 1. Reauditoría de responsabilidades y fallos concretos

Archivos examinados: episodic_memory.py, cognition.py, research_cycle.py, experiment_log.py, laboratory.py, world.py, inventions.py, habits.py, cognitive_projection.py, brain.py, nilo_runtime/application/decisions.py, nilo_runtime/application/clockwork.py, los presupuestos y gateway de la etapa 15, escenarios y pruebas históricas.

Hallazgos:

1. La recuperación episódica analizaba nombres del catálogo interno de sitios próximos sin exigir revelado previo. Un sitio que el personaje todavía no había descubierto podía modificar la selección de recuerdos. Se eliminó ese camino: la cercanía semántica a un sitio solo se utiliza cuando la celda fue observada. El recuerdo de una transición real puede recuperar una ruta conocida, pero no conceder un acceso nuevo.
2. La eliminación de duplicados en life_history comparaba operación, éxito y texto: ensayos distintos pero redactados de igual manera quedaban confundidos. Ahora las acciones con ID independiente preservan la identidad; el mecanismo de deduplicación por texto subsiste para entradas legadas sin IDs.
3. Las experiencias recuperadas no explicaban la coincidencia temática ni la proximidad, dificultando distinguir relevancia de verificación. Se añadieron criterios de recuperación y resoluciones explícitas de action_id y measurement_id; referencias fuera de la memoria de trabajo quedan como tales, no como pruebas disponibles.
4. Al retomar una investigación, register_research sustituía su hipótesis anterior sin historial de cambios. Las reformulaciones nuevas conservan su secuencia como creencias, sin conceder estados de comprobación.
5. La consolidación temática copiaba evidencia narrativa de otras investigaciones sin registrar siempre su procedencia de origen. Los registros integrados se copian con source_research_id y evidencia legacy sin verificar; los originales no se reescriben como ensayos físicos.
6. Las conclusiones y comparaciones verificaban IDs con rutas distintas; ahora comparten la resolución de mediciones existentes y rechazan ID duplicado, inexistente o registro administrativo, conservando la admisión de identificadores de partidas históricas sin prefijo.
7. Los cierres descriptivos derivados de ensayos sin física evaluable se distinguían insuficientemente de resultados comprobados. Se separa observacion_no_evaluable de observacion_comprobada, con el alcance de verificación explícito.
8. El presupuesto de la etapa 15 omitía investigaciones_activas: el motor podía conservar preguntas, pero el proveedor no recibirlas. Ahora se prioriza el interrogante y su hipótesis; la reducción conserva entradas completas e historial reciente de formulaciones, sin alterar el documento persistido.
9. El campo heredado experimentos_comprobados incorporaba también textos de pruebas fallidas guardados en knowledge. La proyección cognitiva ya no envía ese alias ambiguo y ofrece conocimiento_con_procedencia, con estado de la acción y su ID exacto si existe.
10. Un mensaje en condiciones_de_ensayo_descanso todavía indicaba que esperar podía recuperar energía. Se corrigió para distinguir wait de rest según las reglas físicas vigentes.

## 2. Arquitectura resultante

- nilo_runtime/cognition/memory.py: recuperación episódica determinista, filtrado por sitios conocidos, puntuación temática/espacial y descripción de criterios y fuentes. La entrada original sigue en life_history.
- nilo_runtime/cognition/research.py: términos, similitud temática, consolidación conservadora, apertura/reapertura y reformulación de hipótesis. El parecido entre preguntas no produce mediciones ni hechos nuevos.
- nilo_runtime/cognition/predictions.py: predicciones del personaje y contraste de métricas físicas reales. La coincidencia de una magnitud no equivale a confirmar la causa propuesta.
- nilo_runtime/cognition/topics.py: normalización y temas de investigación compartidos con los registros físicos; sin dependencia inversa de experiment_log.
- nilo_runtime/cognition/evidence.py: índice temporal y resolución de referencias tipadas, validación de mediciones y proyección de conclusiones, conocimiento e investigaciones con estados de trazabilidad.
- episodic_memory.py, cognition.py y research_cycle.py permanecen como fachadas de importación; no contienen segundas implementaciones. experiment_log.py y laboratory.py reutilizan el resolver de ensayos.
- brain.context_for entrega memoria pertinente, investigaciones abiertas y conocimiento tipado, y aplica proyección cognitiva antes de que Gemini, Groq o un proveedor compatible lean la solicitud. El historial humano y el motor no son reescritos por estas vistas.

## 3. Contratos y cambios compatibles

Las fuentes de evidencia son registros efectivamente existentes: mediciones, resultados de acciones, predicciones y conclusiones, identificados por su propio tipo de colección. Un ID textual por sí solo nunca constituye un hecho. Los registros administrativos —diseño, informe, comparación o conclusión— no pueden usarse como ensayos físicos primarios.

El estado de trazabilidad distingue registro disponible, referencia histórica fuera de la ventana de trabajo, ID inválido e incompatibilidad de tipo. Una conclusión histórica puede conservar su texto original sin que se finja tener la medición actualmente cargada. Las notas narrativas integradas siguen siendo notas: no se promueven por similitud a resultados mensurables.

Las hipótesis pueden cambiar de formulación por decisión de Nilo; la secuencia de creencias se conserva sin transformarse en evidencia. Las investigaciones de temas relacionados pueden vincularse para evitar repetición innecesaria, pero no reciben una orden automática de continuar, abandonar o concluir.

Se preservan el esquema SQLite vigente, las reglas del mundo, la física del descanso, los límites de recursos y la referencia estable 0.6.4. No se migran ni reescriben historiales personales. La recuperación de evidencia archivada fuera de la ventana de memoria activa queda señalada, sin inventar un resultado ausente.

## 4. Puertas de salida y comprobaciones

- Auditor estático tools/auditar_memoria_16.py: propietarios únicos y fachadas sin duplicación, contratos tipados, inclusión de investigaciones abiertas en el prompt, laboratorio de conclusiones por IDs y filtrado de sitios no revelados.
- tests/test_memoria_16.py: casos focalizados de memoria oculta/descubierta, acciones con textos iguales pero IDs distintos, referencias no resueltas, recuperación pura, actualización de hipótesis, integración con procedencia, límites entre observaciones y comprobación, historial de mediciones, conocimiento fallido y payloads LLM.
- Se mantienen las pruebas preexistentes sobre memoria episódica, cierres de proyectos, planes, investigación, laboratorio y replay. Dos fixtures históricos fueron adaptados a la regla de información observada y a mensajes de diagnóstico más precisos.
- El seguimiento de CI integral y compatibilidad histórica se registra en el tablero cuando finaliza cada ejecución. Una prueba sintética aprobada no demuestra ausencia de bucles con proveedores reales: esa evaluación queda en la etapa 23.

## 5. Límites y trabajo posterior

La recuperación de recuerdos continúa siendo determinista y usa el historial biográfico completo. El costo de índices y el rendimiento en partidas de gran duración quedan para la evaluación de performance de etapa 22. Resolver una medición archivada en SQLite pero fuera de la ventana activa requerirá revisar el acceso persistente en etapa 18/21, sin modificar retrospectivamente su veracidad.

Próxima etapa: 17, proyectos y hábitos. Las pruebas de comportamiento autónomo Gemini/Groq corresponden a la etapa 23. Este trabajo no autoriza fusionar el PR ni publicar 0.7.0 antes de completar las 25 etapas.