# E09.02i-I3c.4b — preregistro de testigo del gate LTW en la corrida I3c.4

**Fecha: 2026-11-21.** Auditoría **exploratoria POST HOC** sobre el experimento I3c.4 de semillas 900..919 ya observadas; no es ensayo confirmatorio ni nueva cohorte. Se preregistra ANTES del nuevo observador, sin editar C1ContextBrain, DynamicContextBrain, genes ni química.

## Pregunta falsable

I3c.4a encontró migraciones abundantes, LTW0 antes de migrar y LTW0 al terminar; cada slot migra en mediana cada20 ticks. Falta discriminar si LTW no aparece porque (H-G) en ticks múltiplos de128 los contactos no tienen STW suficiente, (H-D) el helper numérico sí crea LTW pero el paso de fortaleza/migración la borra EN el MISMO tick, o (H-P) existe LTW transitoria que se pierde más tarde. No asumir la respuesta antes de registrar el testigo.

## Contrato congelado

- Reproducir exactos 20 seeds900..919, fases primera e invertida y modos B/Y/P/F. Verificar SHA256 de salida por semilla contra [fixture congelado](resultados/e09i3c4_golden_seed_hashes.json) de [I3c.4 corregido](E09_02I_I3C4_RESULTADO_QUIMICA_APAREADA.md), no recalcular un hash nuevo de referencia.
- Instrumentación read-only: subclase observadora de DynamicContextBrain, intercepta **cada tick de entrenamiento** con tick%128==0 (no cuenta tick128 durante holdout congelado). Capturar, para cada una de las 4 dendritas, estado anterior (source, STW/LTW, susceptibilidad, strength), lectura CHEM0/1 previa, refuerzo sináptico recalculado por update_c1_synapse existente sobre el estado anterior, dendrita **después de la fase numérica/fortaleza**, y estado tras Type1. Comparar cada valor contra transición original; nunca modificar su respuesta.
- Contar por modo/fase: número de ventanas LTW elegibles, total de contactos examinados, contactos con STW post-refuerzo positiva, contactos con LTW numérico aumentado, pérdidas LTW por strength en mismo tick, LTW sobreviviente al final del tick, eventos Type1 en tick128, susceptibilidad/efecto refuerzo positivos, y contactos con strength0 antes del gate. Capturar todas las ventanas por semilla para diagnosticar un cero.
- La secuencia de químicos y recompensas es EXACTAMENTE la original, sin incremento de dosis ni source de aprendizaje. F congelado no se contará como ventana de consolidación; reportar por separado sólo si se desea verificar ausencia de cambios.
- Contraste interno de falsación: si la transición numérica predicha no coincide con salida cerebral previa a migración o una LTW desaparece sin lost_connection, **fallar**. Si hash por semilla difiere, **abortar** y corregir el observador, no el modelo.
- Reportar por separado H-G, H-D y H-P de acuerdo a los conteos, sin inferir utilidad causal de sinapsis específicas. Todas son hipótesis explicativas de N experimental, NO de C1 histórico.

## Puertas

G-I3c4b-EQUIVALENCE: cada seed coincide exactamente con I3c.4 corregida. G-I3c4b-GATE-ACCOUNT: recuentos por tick/slot coherentes, incluyendo ceros; los outcomes numéricos se basan en las rutinas existentes. G05/G09/G00-H **no evaluadas y ABIERTAS**. No se modifica ni refuerza el sistema. Cualquier intervención causal posterior exige otra cohorte, preregistro y comparación estructural con fuentes iguales.
