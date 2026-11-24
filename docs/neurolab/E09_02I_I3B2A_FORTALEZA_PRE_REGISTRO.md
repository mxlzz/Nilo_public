# E09.02i-I3b.2a — preregistro de auditoría post hoc de borrado LTW por fortaleza

**21/11/2026.** Se registra después del [resultado I3b.2](E09_02I_I3B2_RESULTADO_VENTANA_LTW.md) y **antes de instrumentar** el nuevo auditor. Es **diagnóstico retrospectivo exploratorio**, NO cohorte confirmatoria nueva y NO cambia G05/G09.

## Pregunta

¿Por qué la media de LTW creada en tick128 bajo E1 cae desde 1,475 a 0,050 para tick136, si la regla LTW solo actualiza en múltiplos de128? ¿Cuántos de esos cambios se deben a pérdida de fortaleza (lost_connection) que borra la dendrita, frente a otros mecanismos?

## Procedimiento congelado

- **Repetir las mismas 80 trayectorias** de I3b.2, semillas400..419, target0/1, mappings A/B, estados clonados en tick124, químicas/dosis/rates, ventanas tick125–136, ganancias1/4. No cambiar un solo parámetro ni introducir feedback nuevo.
- Observador sináptico puro por tick y por cada una de ocho dendritas: llamar a la función existente update_c1_synapse con el estado previo real y CHEM aplicada, inspeccionar sus estructuras internas: numeric.after.ltw, strength.after.dendrite.ltw, strength.did_gain, strength.did_lose, strength.lost_connection y strength.before/after.strength.
- **Invariante de no interferencia:** todas las dendritas predichas y estado completo post-tick idénticos a brain.step real. Contrastar el estado final/tick128/tick136 con el reporte I3b.2 por cada episodio; la corrida de auditoría debe reconstituir el resultado anterior exactamente.
- En cada tick por brazo: contar borrados de conexión, de cuáles la LTW previa era >0, suma de LTW borrada por atrofia (numeric.after.ltw > final.ltw), otros decrementos LTW, fortalezas de entrada/salida y distribución por clase exc/inh, target/source distractora, señal química, y momento 130 o135. Registrar cero y casos sin cambios.
- Regla de falsación: si LTW cambia en tick129–136 sin lost_connection (y sin updateLTW programado), **no atribuirlo a atrofia**; marcar discrepancia y localizar otra vía, no cambiar motor. Si todo decremento extra-gate coincide con lost_connection, explicitar que el modelo experimental omite la reconexión/migración completa del cerebro original.
- CI con tests adversariales para detectar que se cuente atrofia aunque final.LTW no se borre, y test de equivalencia con I3b.2. Conservar resultado completo JSON por episodio; semilla reproducible.
- **No usar este diagnóstico para seleccionar hiperparámetros ni afirmar retención duradera.** G-I3b2a-WITNESS es técnica (igualdad y contabilidad); no evalúa G05/G09.

## Decisión posterior potencial (NO tomada)

Si fortaleza y borrado explican la pérdida, estudiar primero si la **migración histórica posterior a la atrofia**, aún no integrada en la microred, es esencial para aprender a lo largo de muchos ticks. Contrastar documentación y código x86 original antes de implementar migración, en lugar de sumar neuronas o parches a STW/LTW. PR#103 continúa draft, Nilo/main intactos.
