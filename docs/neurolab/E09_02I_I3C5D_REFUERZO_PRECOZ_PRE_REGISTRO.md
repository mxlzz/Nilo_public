# NeuroLab E09.02i–I3c.5d — preregistro de ventana de refuerzo con fuerza positiva

**Fecha 21-11-2026 · NL-EXP-I3c5d-v1 · ESTADO PREVIO A CÓDIGO, SIN RESULTADOS.** Continúa [I3c.5c](E09_02I_I3C5C_RESULTADO_DISPONIBILIDAD.md) y la puerta G05; separa viabilidad mecánica de aprendizaje conductual. No reemplaza G05 con un criterio más fácil.

## Pregunta y límites

I3c.5c: 40/40 troncos de I3c.5a agotaron las ocho dendritas en tick10, mientras el feedback comenzaba en tick124. En lugar de alterar tasas genéticas, número de contactos, dosis o ganancia, **mover el único ensayo hasta una decisión al tick4**, conservando exactamente la red y las reglas C1/N. Comparar recompensa entregada justo después de la decisión (D0), recompensa con **tres ticks de retraso y distractor** (D3), y ningún precursor (N). Se pregunta si la ruta química produce refuerzo sináptico cuando todavía existe fortaleza positiva, qué fuente/dueño recibe el efecto, si llega antes de agotarse, y si queda alguna ventaja conductual/retención. **D0/D3 difieren sólo en momento del precursor**, no en intensidad; N es control sin refuerzo.

Es diagnóstico de **una sola elección y un solo pulso**: aun un resultado positivo no demostraría aprendizaje reiterado, reversión o memoria a largo plazo. No extrapolar a un Norn completo ni a su esquema de emisores ambientales. **No modificar `C1ContextBrain`, `update_c1_synapse`, fuerza, genoma, química ni migración**; reutilizar `witness_step`, `inspect_synapses`, `add_environment_precursors`, `selected_genes`.

## Cohorte y calendario congelados antes de ejecutar

- **Desarrollo independiente:** 20 semillas **1300..1319**. Nunca se usaron en I3c.4–I3c.5c. Se consumen después como desarrollo; reservar **1400..1419** fuera de todo este experimento para confirmación futura si un mecanismo justifica continuar. No elegir semillas según éxito.
- Por semilla, estímulo objetivo `target=0,1` y contingencia `A/B`: 80 troncos de cuatro ticks objetivo sin premio, **los dos mappings comparten estado prefeedback**. Cada tronco se bifurca en **N, D0 y D3** = 240 ramas. Reutilizar el mismo objeto estado inicial inmutable, mismas cuatro entradas y decisión previa. Si la decisión es None, las tres ramas NO reciben precursores; registrar frecuencia sin descartar.
- `TRUNK_TICK=4` y `END_TICK=128`. Tras el tronco, 124 ticks del **contexto distractor 1-target**, con aprendizaje activado. D0 recibe una sola dosis exógena sintética80 inmediatamente antes del primer tick distractor (índice0, tick5); D3 recibe la misma dosis en índice3 (tick8); N ninguna. **Cerebro lee CHEM anterior, luego avanzan reacciones/receptores y `decay_pool(rate40)`**, idéntico I3. Refuerzo/castigo viene de elección anterior medida contra mapping en el evaluador externo; ningún target/correct ni mapping entra al cerebro o al testigo sináptico.
- Registrar estados completos y huellas SHA por semilla, tick de primera CHEM0/1 positiva, primera modificación sináptica, fuerza positiva exactamente ANTES de cada tick de refuerzo, y exposición química AUC. No asumir que entregar en tick5 significa efecto neuronal en tick5. **NO** seleccionar post hoc la ventana más favorable.
- Snapshots **tick4,5,6,8,9,10,16,128**, y lectura congelada de cuatro ticks objetivo inmediatamente tras **9,16,128** sobre clones separados (`learn=False`; no alterar el camino principal). Separar acierto de selección previa, lectura corto plazo y retención; registrar STW/LTW por fuente/owner, número fuerza0 y peso positivo en fuerza0.
- Observador read-only en cada tick post-tronco llama `inspect_synapses(old)` sobre las ocho dendritas y exige igualdad exacta con `brain.step` tras cada tick; si falla, **abortar sin interpretar conducta**.
- Una rama `N` tiene que conservar química0 en las cuatro posiciones si no recibe precursores; D0 y D3 llevan dosis nominal idéntica (pero el calendario de CHEM por tick cambia). Comparar también AUC total y máximos, sin confundir AUC con exposición instantánea equiparada.

## Métricas y puertas

**Primaria de diagnóstico (no confirmatoria G05):**
1. Proporción de ramas con **≥1 dendrita strength>0 en el primer tick que lee CHEM0/1 positiva**, junto con el número de dendritas positivas y el número de contactos de **fuente objetivo+owner de la elección** con `strength>0` en ese instante.
2. Fracción de efecto sináptico incremental sobre fuente objetivo frente distractor y fracción del par objetivo+owner, **separando efecto en contactos strength>0 y strength=0 pre-tick**. Reportar denominadores0 como null, no descartar episodios.
3. En ticks9/16/128: distancia STW/LTW contra N, LTW en contactos funcionales (strength>0), conteo fuerza0 y exactitud de readout con `learn=False`. Comparación por semilla D0−N, D3−N, D0−D3 de exactitud; el test original de decisión antes del pulso debe dar mismo score entre brazos.

**Análisis:** medias por semilla y bootstrap pareado agrupado por las 20 semillas, 2.000 réplicas y RNG bootstrap **60516**; intervalos 95% incluso si el resultado es negativo. Informar todas las ramas/signes, rangos, observaciones faltantes y desglose por acierto/error inicial. No declarar aprendizaje si se observan únicamente cambios numéricos sin ventaja en decisión y retención. No interpretar ventajas de lectura si la fuente está agotada y no hay retención.

**G-I3c5d-SOFTWARE:** 20 semillas, 80 troncos, 240 ramas, mismos hashes/estados prefeedback por mapping y brazo; 0/1 entrega según modo/acción, mismo horizonte, testigo coincidente en todos los ticks, lectura sin cambio de pesos, reproducción SHA por seed y artefacto integral de CI. **G-I3c5d-AVAILABILITY:** número positivo al tick4 documentado; reporte de coincidencia química con fuerza sin exigir que sea positiva. **G05/G09/G00-H ABIERTAS aunque los tests den éxito**.

**Si el refuerzo sigue llegando demasiado tarde o no mejora readout:** no aumentar dosis ni cambiar genes para ganar. Documentar límite, volver a controladores históricos y diseñar hipótesis de arquitectura o migración bajo otro preregistro. Si aporta mejora, planificar después experimento confirmatorio *multi-episodio* y reversión en semillas nuevas 1400..1419 y baselines equiparados, no declarar la mente aprendida.

## Artefactos proyectados (no existentes al momento de preregistro)

- `experiments/neurolab/e09_i3c5d_early_window.py`, tests de contrato y workflow con JSON completo por semilla más sumario.
- `docs/neurolab/E09_02I_I3C5D_RESULTADO_VENTANA_PRECOZ.md` **sólo después de ejecutar y auditar CI**. Registrar SHA, run, negativos, métrica y siguiente nodo en `ESTADO_Y_CONTINUIDAD.md`, PR #103 draft, sin cambios a `main` ni Nilo0.7.
