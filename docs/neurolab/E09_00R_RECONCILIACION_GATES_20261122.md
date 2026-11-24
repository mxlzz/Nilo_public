# NeuroLab — E09.00R: reconciliación del contrato de puertas (22/11/2026)

**Clase:** errata metodológica y trazabilidad; NO experimento, NO reformulación retroactiva de criterios. **Línea base:** commit `ad4745dac437f309068ad830312d779ff286e9a3`, PR #103 draft. **Autorización:** continuar auditoría E09 sin integrar Nilo 0.7 ni fusionar `main`.

## Fuente normativa y jerarquía

1. **Objetivo:** [issue #102](https://github.com/mxlzz/Nilo_public/issues/102) y [README maestro](README.md): estudiar una mente neuronal pequeña inspirada en C1 que adquiera, conserve, modifique, transfiera y reorganice asociaciones. La vía **H** busca fidelidad histórica limitada a evidencia; la **N** prueba mecanismos propios; el resultado de N NO se presenta como organismo autónomo ni C1 fiel.
2. **Etapas/puertas originales:** [ETAPAS_00_09.md](ETAPAS_00_09.md), escrito antes de los experimentos. Sus IDs G00–G09 y significados NO cambian; este documento solo corrige uso posterior.
3. **Criterio por experimento:** preregistros individuales fijan ensayos específicos, poblaciones, métricas y umbrales. Un criterio de una familia I3c no sustituye una puerta G##.
4. **Evidencia:** resultados, hashes, archivos y CI; éxito de una suite técnica no prueba automáticamente una hipótesis científica.
5. **Estado:** [ESTADO_Y_CONTINUIDAD.md](ESTADO_Y_CONTINUIDAD.md) registra progreso; si un texto histórico entra en conflicto con este contrato, se conserva y se anota su errata, sin alterar los resultados originales.

## Correspondencia vinculante de puertas

- **G00:** especificación matemática suficiente para el primer motor *con divergencias documentadas*. **G00-H** = alias operativo para las lagunas de fidelidad histórica C1, NO puerta alternativa creada por el plan; H permanece incompleta pese a GEN y EXE posteriormente aportados e inspeccionados.
- **G01:** invariantes numéricos, determinismo y restauración.
- **G02:** selección de acción trazable de la microtopología.
- **G03:** aprendizaje asociativo y reversión frente a control en el modelo y ensayo definidos.
- **G04:** comportamiento funcional de dos escalas STW/LTW, incluidos perturbación y pausa. El éxito en *una sinapsis aislada* NO acredita memoria conductual larga en un cerebro activo integrado.
- **G05:** **crédito temporal del refuerzo retrasado**, preferencia por conexiones implicadas y ausencia de refuerzo sistemático de distractores. No equivale a retención ACTIVE sin nuevo premio. E05 original y [g.10b](E09_02G_10B_RESULTADO_DEMORA_DISTRACTORES.md)/[g.10c](E09_02G_10C_RESULTADO_ELEGIBILIDAD.md) NO cierran G05.
- **G06:** generalización a holdouts frente a memorizador; E06 demuestra *detector conjuntivo predefinido* que resiste contexto irrelevante, NO concepto formado autónomamente.
- **G07:** beneficio específico de recableado frente a controles de complejidad comparable; E07 iguala a LRU en tarea ensayada, no acredita superioridad.
- **G08:** dinámica interna recurrente cuantificada, con controles; NO intención ni pensamiento.
- **G09:** **síntesis reproducible** por capacidad, ablaciones, baselines, coste, arquitectura mínima y decisión `crecer / revisar / detener`. La integración de mecanismos en un solo cerebro es una *pregunta experimental de E09*, **no** integración de cerebro+cuerpo+mundo/LLM ni autonomía general; esta última está expresamente fuera de alcance de la etapa.

## Erratas de terminología detectadas

1. En [I3c.7l](E09_02I_I3C7L_CIERRE_ESTRATEGICO_LINEAS_H_N.md), [I3c.7h](E09_02I_I3C7H_RESULTADO_CONTINGENCIA.md), [I3c.7k](E09_02I_I3C7K_RESULTADO_TRANSFERENCIA.md) y múltiples entradas del [estado canónico](ESTADO_Y_CONTINUIDAD.md), expresiones «**G05 retención ACTIVE**», «**G05 ≥18/20 semillas con ≥.90 ambas fases**» se interpretan desde hoy como **R-ACT-I3c**: *criterio específico preregistrado de robustez de retención activa sin nuevo feedback*. **R-ACT-I3c NO superado**; **G05 original tampoco superado**, pero por razones de crédito temporal documentadas independientemente. Conservamos la denominación textual de los informes antiguos como evidencia histórica.
2. En [I3c.7l](E09_02I_I3C7L_CIERRE_ESTRATEGICO_LINEAS_H_N.md) y en entradas del estado, «**G09 integración conductual como agente autónomo con entorno**» es incorrecto. Debe leerse **G09 síntesis/arquitectura mínima del cerebro aislado**. G09 abierta; mundo y cuerpo excluidos.
3. [E09_AUDITORIA_INTERMEDIA.md](E09_AUDITORIA_INTERMEDIA.md) y [E09_EVIDENCE_INDEX.md](E09_EVIDENCE_INDEX.md) datan de antes de incorporar `dad1.gen`/EXE originales. Su frase «no se dispone de originales» ha quedado **obsoleta**, NO es evidencia de que hoy falten esos archivos de origen. Ver [comparación del genoma](E00_GENOMA_ORIGINAL_COMPARACION.md) y [auditoría de EXE](E09_02F_INFORME_EJECUTABLE.md). Los archivos propietarios se inspeccionaron sin publicarse; la reconstrucción completa sigue incompleta.
4. [README.md](README.md) y [PROTOCOLO_EVALUACION.md](PROTOCOLO_EVALUACION.md) preservan apartados de **estado inicial** («primer paso pendiente», «todavía no hay datos»). Se interpretan como *fotografía histórica del preregistro*, no estado actual. La portada deberá enlazar esta adenda y el estado canónico.

## Regla de decisión para E09

- No repetir ajuste incremental de `C1ContextBrain` de ocho conexiones ni cambiar la definición de G05/G09 para mostrar un éxito.
- Conservar E01–E08 y experimentos g/h/i como evidencia de **mecanismos específicos**, etiquetada por ámbito y condiciones. No sumar tasas de tareas distintas como si fuesen desempeño integrado.
- Antes de implementar un cerebro combinado, elaborar **inventario y matriz de compatibilidad**, determinar si una comparación documental o un baseline tabular ya resuelve la pregunta.
- Si es necesaria prueba nueva: pregunta que cambie decisión, preregistro, control pareado con igual información, coste, holdout intacto y condición de detención. Semillas 1400..1419 reservadas para confirmación, no exploración.
- Una decisión E09 de **revisar o detener** también es válida y **no exige** emular C1 completo o construir un mundo.
