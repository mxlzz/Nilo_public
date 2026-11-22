# NeuroLab I3c.6b — preregistro de umbral endógeno y límite estructural de la microred

**21/11/2026 · estudio determinista de mecanismos, ANTES del nuevo código.** Continúa [I3c.6a](E09_02I_I3C6A_REALIMENTACION_ATROFIA_PRE_REGISTRO.md). No incluye un ensayo de aprendizaje ni autoriza modificar neuronas, químicos o migración.

## Pregunta e hipótesis falsable

La ruta estática C1 x86 local muestra que para **Decision Type1** cada locus emisor (lobe+0xC1 / +0xC2) almacena el **mínimo** de dendritas `strength=0` de los registros neuronales/clase procesados, inicializando la variable en255. El GEN original verifica emisor124→químico53 / emisor125→químico70, `gain=255`, `sample_rate=1`, `flags=1`; receptor127/128 lee respectivamente 53/70 para CHEM2/3, `nominal=16`, `gain=255`, `flags=1`.

**Hipótesis H-T:** bajo pool químico inicial cero y *únicamente esta pareja emisor→receptor*, es necesaria una entrada de locus **mínima 3** para reducir siquiera 1 punto CHEM2/3 desde nominal16. Los dos truncamientos `(x*255)>>8` (emisión) y `(y*255)>>8` (recepción) anulan todo x≤2. Si el lóbulo original asigna su mínimo sobre clases con capacidades menores o iguales2, **ningún estado de esas clases puede activar esta retroalimentación por sí sola**. Aun x≥3 puede no persistir con el calendario real/saturación/decaimiento.

## Diseño inmutable

- **Sin nuevos datos ni semillas:** recorrer exhaustivamente `locus=0..16`, ambos emisores Decision 124/125, receptores127/128, `pool` cero, sample tick0 y `source` explícita. Reusar exactamente `Emitter`, `emitter_tick`, `Receptor`, `receptor_value` y fixture GEN original `docs/neurolab/resultados/e09h3_receptores_genoma_original.json`. No escribir otra versión de las dos funciones.
- Fuente genómica: auditar que los campos de ambos emisores transcritos en [E09h.5](E09_H_05_RESULTADO_EMISORES.md) son `(organ0,lobe6,locus1/2,chemical53/70,threshold0,sample_rate1,gain255,flags1)`. Receptores127/128 verificados con `nominal16, flags1`; el EXE y GEN ya tienen SHA fijos, sin incluir bytes en el repo.
- H-T calculada **mediante las dos funciones originales existentes**, sin reemplazar reglas por cálculos de Python a mano. Reportar `emitter_amount`, `pool[chem]`, `locus_after`, `receptor_output` y primera entrada que modifica CHEM. Mantener test oráculo que compare con fórmula de enteros para x0..16.
- Contar capacidad real **por neurona y clase** desde `C1ContextBrain.initial()` (cada owner D0/D1, clase exc/inh con dos fuentes; máximo agotadas2 por clase) y desde `DynamicContextBrain.initial()` (cada owner/clase un único slot; máximo1). Las fuentes apuntan a Concept0/1, no inventar nuevas. La comparación con 128 conexiones por clase/Decision del GEN es **capacidad**, no cantidad observada en ejecución.
- No afirmar que químico53/70 del Norn siempre sea cero: hay otros posibles orígenes y reacciones del pool; sólo se aísla la ruta emisor Decision→receptor sin fuentes adicionales. El modelo N originalmente desactiva los emisores y no actualiza estos puertos.

## Criterio de validación y resultado esperado (no garantizado)

- G-I3c6b-FUNCTION: `emitter_tick` y `receptor_value` de las clases históricas usan 17 valores0..16 y ambas parejas, con control de `flags1` y source reset; reporte y tests independientes.
- G-I3c6b-TOPOLOGY: demostrar aritméticamente que `capacity C1ContextBrain=2` y `DynamicContextBrain=1` por clase/neurona, ambas menores que el umbral requerido; no alterar clases.
- Si H-T se confirma, **no conectar emisores en la microred y declarar solucionada la regulación**: integrarlos de forma histórica sería un camino químico funcionalmente mudo en la topología reducida. Documentar esto como **limitación de escala** y formular comparaciones futuras separadas (mayor capacidad justificada vs transformación explícita N de locus, incluyendo control sin realimentación), sin elegir por precisión.
- G05, G09, G00-H ABIERTAS; esta etapa es mecanística, no demuestra que el Norn original aprenda ni que la versión de Nilo deba crecer.

Artefactos: módulo read-only, tests y CI independiente, JSON íntegro de x0..16, informe y continuidad. No modificar `main` ni integrar al Nilo0.7.
