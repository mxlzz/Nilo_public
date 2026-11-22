# Etapa 3 — H22. Escala interfacial activa segregación, pero fallan persistencia y nulo exigente

**Fecha:** 2026-11-22. **DICTAMEN H22 NO APROBADA como gate integral**, aunque el contraste causal de escala **SÍ confirma segregación material medible y conservativa** en la geometría/tiempo fijados. No se modifica ni se reinterpreta el resultado negativo de H21. [Protocolo previo](ETAPA_3_H22_PROTOCOLO_ESCALA_INTERFAZ.md), [código](experiments/probe_e3_h22_spinodal_epsilon.py), [CI FAIL por dos gates físicos](https://github.com/mxlzz/Nilo_public/actions/runs/45084072284), commit `8f778002de355404429a886bf0fc36755ab7c176`.

## Intervención y observaciones

Se reutilizó sin editar `probe_e3_h21_spinodal_fipy.py`, con misma malla 20×20 (`dx=dy=.25`), misma materia A/B400kg, mismo ruido seed20261122, misma ecuación FiPy4.0.3 y los mismos 400 pasos / t≈35,934. **Único parámetro cambiado entre escenarios A/B: epsilon interfacial1→0,5**; se utilizó el coeficiente en el término original `DiffusionTerm(coeff=(D,epsilon²))`.

- **Epsilon0,5:** varianza `phi` pasó **0,001599206291→0,070532376089** (×44,1); q05 **0,0851801**, q95 **0,8612854**. 213 celdas `phi>0,5` y 187 del otro lado. Masa A por paso desviación máx **2,6887×10⁻¹¹kg**, total400kg.
- **Epsilon1, réplica H21:** varianza final **0,000055395229984**, q05 **0,4910783**, q95 **0,5127464**: se homogeneiza con mismo inicial, solver y reloj. Contraste varianza eps0,5/eps1 **1.273,257×** (gate ≥5 superado). Confirmación de sensibilidad a epsilon, NO afirmación de material natural real.
- **Control D0:** sin movimiento (cambio de fracción0). Control composición0,1: homogénea, q95~0,101932 y varianza~1,61e−10; sin separación. Replay idéntico bit a bit. Siete corruptelas del owner rechazadas y NetCDF 7.220bytes reconstituido con hash exacto.
- **Criterio espacial fallido:** `same-edge-score` observado **0,9644736842**; nulo de 512 permutaciones que conservan conteos por fila p95 **0,8921052632**. Diferencia **0,07236842105**, menor al **+0,08 preregistrado** por aproximadamente0,00763. El control condicionado impide declarar éxito a partir de una imagen.
- **Criterio temporal fallido:** Jaccard entre máscaras `phi>0,5` en pasos300 y400 **0,57835820896**, menor al umbral0,60 en0,02164. Esto puede deberse a coarsening activo, no está comprobado que la estructura se estabilice en una etapa posterior.

**CI exit1 por gates `spatial_coherence_exceeds_row_conditioned_null` y `pattern_persists`; todos los demás pasaron.** No existe error de conservación como en el check aritmético de H21; H22 usó tolerancia física para masa total.

## Lectura de rigor

**Demostrado:** en este modelo publicado de mezcla idealizada, reducir la penalización de gradientes de composición y dejar los demás inputs invariantes **provocó separación de materiales por la dinámica**, desde ruido casi homogéneo, conservando A/B. Es evidencia local de causalidad, no «emergencia funcional».

**No demostrado:** estabilidad temporal según umbral, separación frente al nulo por filas según margen fijado, geometría mecánicamente soportada, estructuras volumétricas, acoplamiento de composición con fenómenos de gravedad/sedimento/energía térmica, independencia de semilla y dominio, patrón que conserve función. H22 **NO APROBADA** y **E3 ABIERTA**.

## Decisión siguiente

El cuello de botella ahora NO es encontrar otra PDE o activar la segregación: ya se observó. La incógnita crítica del propio plan E3 es **persistencia y variación bajo distintas condiciones iniciales**, con nulos condicionados. Una nueva prueba H23 podría evaluar **coarsening longitudinal de epsilon0,5** y **varias semillas** con ventanas tardías preregistradas, sin modificar H22 ni forzar sus resultados. Si los dominios siguen cambiando sin persistencia comparable, documentar como limitación real y reconsiderar si E3 exige estructuras mecánicas, no solo mezcla.
