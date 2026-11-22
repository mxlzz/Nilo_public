# NR01.03-DP — piloto de desarrollo acotado, preregistro anterior a ejecución

**22/11/2026; ANTES de crear el runner, y antes de observar resultados.** Continuación del [plan NR01](NR01_PLAN_INVESTIGACION_REPRESENTACIONES.md), [desafío fijado NR01.02](NR01_02_PREREGISTRO_DESAFIO_20261122.md) y [contrato del decoder](NR01_03C_CONTRATO_DECODER_COSTOS_20261122.md). Los [tests técnicos NR01.03-C/D](https://github.com/mxlzz/Nilo_public/actions/runs/45049269589) terminaron SUCCESS con datos ficticios. Eso no valida una hipótesis sobre aprendizaje.

## Propósito del piloto

**Objetivo exclusivo:** comprobar sobre un mundo de desarrollo que todos los brazos completan la misma tarea, conservan evidencia de igualdad de entrada, respetan el techo de categorías, producen métricas de precisión y costo y no alteran estado en holdout. No inferir promedios, intervalos, superioridad ni seleccionar hiperparámetros con este piloto aislado.

**Mundo de desarrollo:** semilla **23000**, familias A y B por separado. Las semillas 23001..23019 quedan disponibles para la cohorte completa. **Prohibido** abrir confirmación 24000..24019 e históricos1400..1419. Los tests ficticios 0/1/42 ya fueron empleados en software y no entran en inferencia.

**Ocho brazos fijos por familia:** baseline raw lineal, baseline FIFO 1-NN16, MiniBatchKMeans K=4,8,16 y ARTlib FuzzyART rho=.60,.80,.90. Sin agregar River/SOM, cambios en decoder, nuevas neuronas ni privilegios de factores latentes. Las mismas 1.200 observaciones sin etiquetas, las mismas 64 señales de refuerzo por fase y holdouts, y el mismo decoder congelado D-v1 según contrato.

**Ejecución:** un script que invoca el harness versionado `run_world` (sin duplicar ecuaciones ni generar mundos adicionales) para las 2×8 condiciones, guarda JSON completo y resumen de estado. Cada resultado incluye digest SHA256 de observaciones de adquisición y test, checkpoints 8/16/32/64, control negativo, presupuesto de categorías y tamaño de estado. Los tiempos de CPU por fase se registran exploratoriamente en el mismo runner. El código del piloto **no** puede aceptar semillas fuera del rango de desarrollo; nunca acepta `allow_confirmation=True`.

**Parada por fallo:** si un brazo falla por excepción no prevista, conservar error y hacer fallar el job después de guardar artefacto. Si ART excede16 categorías, registrar `over_budget` (no error de código), no truncar ni promoverlo a ganador. El exceso de presupuesto no invalida resultados de otros brazos, pero sí impide considerar elegible esa condición. Verificar que los ocho brazos de cada familia tengan el mismo digest de cada cinta compartida.

**No ajustar por el resultado:** la métrica piloto no permite modificar rho, K, pesos del decoder, tarea ni generador. Si surge un defecto real de software/protocolo, registrar diagnóstico, corregirlo con nueva prueba y explicar el impacto en la semilla expuesta. No usar 23000 como una segunda confirmación encubierta.

**Criterio de cierre:** job y archivo completo recuperables; 16 condiciones o causas explícitas de incumplimiento, igualdad de cintas, ninguna semilla prohibida. Tras esto, decidir si la cohorte de desarrollo 23001..23019 puede correrse con el mismo contrato; no tocar NR01.05.

**Estado al registrar:** PROTOCOLO, piloto todavía NO ejecutado. PR#103 sigue draft, Nilo0.7 y main intactos.
