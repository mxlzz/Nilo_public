# NeuroLab E09.02i–I3c.5e — preregistro de auditoría de microrefuerzo no transmitido

**21-11-2026 · NL-EXP-I3c5e-v1 · DESPUÉS de observar I3c.5d, ANTES de nuevo código de auditoría. ESTUDIO POST HOC, NO CONFIRMATORIO.**

## Pregunta delimitada

[I3c.5d](E09_02I_I3C5D_RESULTADO_VENTANA_PRECOZ.md) recibió química mientras había 8 dendritas con fortaleza positiva en ambos brazos; sin embargo, 0/80 decisiones de lectura cambiaron frente N y STW en todos los snapshots preregistrados resultó0. Las trazas del artefacto original [CI 44965370419](https://github.com/mxlzz/Nilo_public/actions/runs/44965370419) muestran efectos de **máximo 1 por sinapsis/tick**, sólo en tick7 D0 (16 episodios) y tick10 D3 (48 episodios).

**Hipótesis auditables, no equivalentes**:
- **H-Q (cuantización):** la entrada Concept reducida que produce `C1ContextBrain` bajo un solo contexto activo es 126 (de sensor255, peso128, atenuación255); el Decision necesita una STW mayor que 1 para que el doble desplazamiento `>>8` y la atenuación128 generen un `type0/type1` no cero. Buscar **mínimo entero** de STW por barrido exhaustivo0..255; no fijarlo a priori.
- **H-R (relax):** el pulso efectivo unitario de D0 cae en tick7, donde la relax STW del gen Decision (`rate80`) puede descartar una unidad completa en un paso; comprobar mediante `transition` y `relax` existentes con STW0/LTW0 y química que produzca efecto exacto1.
- **H-L (loss):** el efecto D3 cae en tick10, cuyo `lose_rate=5` desde strength inicial2 provoca fuerza0; comprobar con `update_strength` si limpia STW/LTW inmediatamente cuando strength1 desciende a0.
- **H-W (cambio real de la decisión):** confrontar una microred fixture con estado Decision fijo y fuentes Concept idénticas, modificando sólo una STW de0→1→umbral calculado, con `learn=False` y sin reward. La pregunta es si la señal llega a *scores*, NO si una acción supervisada es aprendida.

## Anclaje de evidencia / contrato

- No tocar `C1ContextBrain`, `c1_runtime_math`, `c1_decay_math`, `c1_strength`, `c1_synapse_integrated`, `dad1.gen`, dosis, tasa, migración o semillas.
- Estudio **numérico de mecanismos** + lectura del **mismo artefacto original I3c.5d**. Reutilizar su [fixture de 20 hashes y sumario](resultados/e09i3c5d_resumen_y_hashes.json); no reentrenar ni reemplazar outcome por una simulación nueva. Los 20 hashes proceden de JSON completo de artefacto14730837789 con SHA256 `b6a97ae5ae765d55330b122050c60b29ffcb9eb95080efa5af5ed5df37658192`.
- Para el test de relajación elegir estados artificiales tipados que produzcan un `reinforcement_effect` exactamente1 en tick7, y confirmar `stw_after_reinforcement` y `stw_after_relaxation` separadamente; documentar que es fixture matemático ilustrativo, no identidad de todo el estado orgánico original.
- Para pérdida usar condición artificial `strength1, tick10, loss_rule_output>0`, `gain_rule_output=0`, tasas gene Decision3/5; comprobar `lost_connection`, fuerza y pesos posteriores.
- Para cuantización usar funciones de señal existentes y una microred sin aprendizaje, no fórmulas reinterpretadas. Reportar mínimo STW con valor de señal positivo y scores sin atribuir conciencia/causalidad.
- Gates: **G-I3c5e-NUMERIC** si tests con testigos independientes y referencias originales pasan. **G-I3c5e-DIAG** si se distinguen cuantización, relajación y pérdida como mecanismos compatibles con datos, no como causalidad global única. **G05/G09/G00-H ABIERTAS**.

## Decisión precomprometida

Si el incremento de STW1 no alcanza el umbral y queda borrado en tick7/tick10, concluir que I3c.5d NO podía generar diferencia conductual con esos pulsos específicos bajo este modelo y no seguir probando semillas equivalentes. **No ajustar dosis ni gain para forzar el umbral.** El próximo paso válido sería volver a fuentes auténticas: qué constituye el régimen basal de excitación/refuerzo y reposición de sinapsis en C1 completo, y contrastarlo contra el cerebro reducido antes de diseñar confirmación. Esta etapa sigue **aislada de Nilo0.7 y main**; PR#103 draft.
