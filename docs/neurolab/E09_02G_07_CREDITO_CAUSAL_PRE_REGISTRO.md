# E09.02g.7 — preregistro de auditoría causal del refuerzo, solo observacional

**Registrado:** 2026-11-21, antes de la instrumentación g.7, después de resultados de g.6. **No es modificación del cerebro ni prueba de fidelidad plena de Creatures 1.**

## Hipótesis específica

En `C1ContextBrain.step`, el valor `concept_outputs` almacenado en el estado anterior participa en la plasticidad del tick actual, mientras la acción anterior fue calculada usando el Concept disponible **un tick antes**. Tras el cambio S0/S1, esta diferencia de fase puede hacer que un pulso de feedback sea aplicado con una fuente Concept que **no intervino** en la decisión premiada/castigada. El fenómeno es distinto de la persistencia de Decision estudiada en g.6.

**Predicción falsable:** los eventos con pulso no nulo y Concept discernible de acción anterior tendrán más discordancias entre `source_at_previous_choice` y `source_at_plasticity` en los ticks de transición/primeros ticks posteriores a cambios que en bloques repetidos; habrá ejemplos con modificación de STW bajo esa discordancia. Una diferencia temporal por sí sola **no** demuestra que sea la causa única del fallo g.5 ni que las reglas de C1 original sean erróneas.

## Datos/congelación

- Red E09g.5 intacta; semillas 0..19; dos fases de 32 bloques aleatorios balanceados×8 ticks, mismas mapping A/B, recompensas químicas, WTA, estado continuo, entrenamiento y pulse `pending` entre fases.
- Se comparará el estado de dendritas y neuronas final de cada fase más el pulso pendiente contra `train_brain` **sin instrumentación** con igualdad estructural exacta.
- Por tick registrar: fase, semilla, bloque, posición, contexto sensorial actual, acción previa y contexto sensorial de su evaluación, Concept que la acción anterior realmente leyó, Concept alimentado al actual update sináptico, presencia/tipo del pulso (Reward/Punishment/Zero), y deltas STW/LTW por las 8 dendritas.
- `source_at_previous_choice` se obtiene del `old_concepts` que **entró al cálculo de la decisión previa**, no del estímulo visual actual. `source_at_plasticity` sale del `concept_outputs` del estado de entrada al tick. Un vector sin Concept activo se clasifica `unknown`, nunca se inventa una fuente.
- Definición de discordancia **evaluada solo cuando ambas fuentes son identificables y hay pulso no nulo**. Medir también eventos con alguna fuente desconocida, separados del denominador.
- Reportar conteos (no solo proporciones) por fase y para posiciones 0,1,2,3+ de cada bloque, con cortes de borde `switch`/ `repeated`; se conservan todas las semillas y los eventos negativos.
- Reportar si en los eventos discordantes se alteran STW/LTW en alguna dendrita, distinguiendo cambios de plástico y cambios de relajación. No atribuir causalidad de un cambio sináptico exclusivamente al feedback sin ablación química.
- Criterio de integridad: paridad exacta de estados finales, pulsos y determinismo con runner E09g.5 para las 20 semillas. Si falla, **invalidar** la auditoría sin interpretar indicadores.

## Fuera de alcance

No cambiar el delay del refuerzo, no desactivar química en fronteras, no introducir una memoria causal externa como mecanismo neuronal, no corregir créditos retrospectivamente, no subir a 7+ neuronas. La auditoría mide **coincidencia temporal**, no suficiente para aprobar G05.

## Decisión posterior

Si hay discordancias observables, diseñar por separado una intervención temporal controlada con nuevas puertas y controles emparejados para distinguir error de crédito y error de persistencia. Si no hay, descartar esta hipótesis para esta microred e investigar otros mecanismos. Ningún resultado da derecho a fusionar con main ni a integrar con el motor Nilo.
