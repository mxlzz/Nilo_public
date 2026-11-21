# E09.02i-I3a — preregistro de diagnóstico mecanístico POST HOC (solo observación)

**Fecha:** 2026-11-21. **Tipo:** exploratorio sobre el I3 negativo ya publicado. No constituye un nuevo ensayo confirmatorio ni modifica la puerta fallida. La cohorte 200..219 y parámetros de I3 están contaminados para seleccionar hiperparámetros futuros.

## Observación que motiva el diagnóstico

[I3 negativo](E09_02I_I3_RESULTADO_NEGATIVO.md): M y F dan rendimiento prácticamente idéntico (+0.00069444); Reward49/Punishment50 no superaron concentración25 al final de los ensayos observados, y existen 146 decisiones objetivo faltantes en el entrenamiento M. **Esto no identifica la causa.**

Hipótesis falsable de inspección: al llegar los valores CHEM a la SVRule de refuerzo, la transformación entera **(susceptibilidad×CHEM)>>8** produce pocas actualizaciones positivas de STW, aunque haya sustancias en el pool. Otra posibilidad: hay actualizaciones pero quedan atribuidas al contexto distractor. Ambas se mantienen abiertas.

## Método fijado antes de observar nuevos conteos

- Reejecutar **exactamente** el brazo M de las 20 semillas I3, mismo orden de ensayos, tasas40, dosis80, reacciones57/71/111/112, 6 neuronas, 8 sinapsis.
- **No editar** C1ContextBrain, C1Synapse, generador de entradas, recompensa, decay ni el runner I3; instrumentar una réplica *read-only* de los argumentos que recibe cada sinapsis durante brain.step.
- En cada tick de entrenamiento: capturar CHEM Decision previa (CHEM0/1), susceptibilidad de entrada, resultado numeric.reinforcement_effect de update_c1_synapse para cada una de las ocho sinapsis, cambio STW y LTW, salida del lóbulo Concept previa y output de Decision previa. Reutilizar **la función sináptica existente** sin recomputar fórmulas propias.
- **Control de equivalencia estricto:** todos los estados dendríticos pronosticados por el cálculo observacional deben coincidir con los del brain.step real; después de cada fase, el estado completo obtenido por el observador debe ser idéntico al de metabolic_phase I3 convencional. Si no, **fallar el diagnóstico**, no corregir cambiando el modelo.
- Reportar conteos de ventanas CHEM>0, susceptibilidad>0, reinforcement_effect>0, cambios de STW/LTW, tasas por sinapsis y por fase, máximos CHEM y pool y eventos de ausencia de elección. Añadir algunos ejemplos auditables sin simular que prueban causa.
- Interpretación predefinida: si hay CHEM positivo pero reinforcement_effect casi siempre cero, reportar cuello de botella aritmético plausible; si es frecuentemente positivo pero acierto no mejora, evaluar interferencia/atribución, **sin culpar al mecanismo todavía**. Esta es una auditoría post hoc sin prueba independiente del diagnóstico.

## Límites y puerta

- El diagnóstico **no altera el resultado de I3** ni cierra G05/G09. No se introducen parámetros nuevos ni adaptaciones. Cualquier corrección/ensayo confirmatorio futuro requerirá nuevo preregistro y **nuevas semillas**.
- Gate D3a es **validez de la observación** (equivalencia de estados y trazas, CI completa, JSON persistente), no éxito de aprendizaje.
- Para fidelidad H siguen abiertas G00-H, G-I1b-RATES y G-H6-CLOCK efectiva. Nilo/main intactos, PR #103 draft.
