# E09.02i–I3c.5c — resultado: agotamiento uniforme ANTES del feedback

**21-11-2026 · Observación descriptiva preregistrada, cohorte I3c.5a reutilizada.** [Preregistro](E09_02I_I3C5C_DISPONIBILIDAD_TRONCO_PRE_REGISTRO.md) · [código](../../experiments/neurolab/e09_i3c5c_trunk_availability.py) · [oráculo de 40 SHA](resultados/e09i3c5c_original_trunk_hashes.json) · [CI #44964605558](https://github.com/mxlzz/Nilo_public/actions/runs/44964605558) **SUCCESS** (4/4 tests), trazas completas en artefacto `neurolab-i3c5c-pre-feedback-connectivity`.

## Qué se evaluó

Se reejecutó sin recompensa exactamente el período preparatorio preregistrado en I3c.5a, **20 semillas×2 contextos=40 troncos únicos, ticks0..124 (125 observaciones/tronco)**. Los 40 hashes SHA256 del checkpoint final coinciden **exactamente** con los del artefacto original I3c.5a (separados de las etiquetas A/B). No se tocó `C1ContextBrain`, genética, químicos, migración, tasas, ganancia ni dosis. Este estudio reutiliza la cohorte y por eso es **descriptivo, no validación independiente**.

## Hallazgo central

- **En los 40/40 troncos, las ocho conexiones pasan a `strength=0` juntas exactamente en el tick10.**
- **0/40** recupera espontáneamente alguna fuerza desde el primer agotamiento hasta tick124, puesto que no hay feedback ni migración en esta variante.
- En **40/40 troncos, 0/8 conexiones tienen fortaleza positiva en el momento de la bifurcación de recompensa** (tick124).
- Este resultado explica la observación retrospectiva del artefacto I3c.5a: el pulso llega a una red cuyos ocho slots ya agotaron fuerza, después de **114 ticks** desde el agotamiento, aunque la ruta numérica de plasticidad pueda responder temporalmente a químicos más tarde.

Las dos clases Decision del `dad1.gen` aquí implementadas tienen **`lose_rate=5`**; el baseline del cerebro reducido inicia cada slot con fuerza2 y sin revalorización en el período sin recompensa. La atrofia sincronizada a ticks5 y10 es consistente con ese contrato genético-sintético. No implica que el Norn original, con cerebros/lóbulos, aportes químicos ambientales y migración histórica completa, pierda toda su conectividad a los diez ticks.

## Consecuencia experimental / decisión

El experimento I3c.5a **sigue siendo válido como medición numérica de coincidencia temporal entre pulso químico y susceptibilidad**, pero **NO debe emplearse como base para afirmar o descartar adquisición de conducta con sinapsis funcionales durante la recompensa**: su fase de feedback comienza después de un agotamiento previsible y sin migración. Algunas ramas recuperaron fortaleza temporalmente al recibir un pulso; ninguna consolidó LTW al final.

No corregir `strength=0` para silenciar señal: la auditoría [I3c.5b-H](E09_02I_I3C5B_H_RESULTADO_X86.md) verificó estáticamente que el EXE histórico no introduce esa guardia en el bloque observado y que la pérdida limpia STW/LTW.

**G-I3c5c-REPLAY VALIDADA, G-I3c5c-DIAG VALIDADA. G05, G09, G00-H ABIERTAS.**

**Próxima decisión científica a diseñar antes de ejecutar:** asegurar una contingencia de refuerzo durante una ventana con fortaleza positiva **sin alterar a posteriori tasas/ganancia**, o introducir solo los mecanismos históricos de migración faltantes bajo controles apareados. La alternativa debe preregistrarse con cohorte independiente, control sin recompensa, evaluación de retención y baseline explícito; no seleccionar ahora la versión que parezca aprender mejor.
