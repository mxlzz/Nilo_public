# NeuroLab E09.02i–I3c.7c — preregistro de auditoría retrospectiva de extinción

**21/11/2026 · NL-AUDIT-I3c7c-v1 · DESPUÉS DE CONOCER I3c.7b Y SU ARCHIVO, ANTES DE IMPLEMENTAR AUDITOR/REPLAY.** Esta auditoría **NO ES CIEGA NI CONFIRMATORIA**, sino una inspección forense reproducible del mismo ensayo de desarrollo.

## Origen y hechos que motivaron el análisis (no predicciones)

[I3c.7b](E09_02I_I3C7B_RESULTADO_CONTRASTE_SENAL.md): 20 semillas1500..1519, 80 decisiones A/B y 4 ramas por episodio. Artefacto ZIP14733055528, run [44968344691](https://github.com/mxlzz/Nilo_public/actions/runs/44968344691), JSON `i3c7b.json` de **12.128.800 bytes, SHA256 `2660ba63b866abfff469d754ff88cab8941b215b1078a652ddc52dfca0cce8a6`**. En primera lectura exploratoria del ZIP se observó: brazo C 60/80 contactos con STW≥5 y fuerza positiva en tick7, cambios de score en36/80 y de acción congelada en22/80 al leer tras ticks7/9; después t10 todas las ocho conexiones perdieron fuerza, t11 perdió señal, y no hubo mejora t16/128. **Ya se observaron estos datos; no volver a llamarlos descubrimiento independiente.**

## Auditoría bloqueada antes de código

- **NO generar nuevas semillas ni modificar C1.** Reejecutar `e09_i3c7b_paired_signal.run_all()` con los mismos20 seeds/contrato y exigir **igualdad SHA256 del archivo completo** con el artefacto original, antes de interpretar. Esta reproducción es una nueva ejecución de **datos conocidos**, no un holdout.
- Desarrollar un auditor read-only que acepte exclusivamente el JSON de I3c.7b con esquema íntegro, IDs de20 semillas, 80 episodios, 320 brazos, 124 frames por brazo, ticks5..128. Comprobar que no hay etiquetas del evaluador dentro de los frames neurales ni cohortes1400..1419.
- Por brazo N/M/C/F, por ticks **7,8,9,10,11,16,128**, contar dendritas con fuerza positiva por episodio, episodios con alguna STW>0 en fuerza positiva, alguna STW≥5 en fuerza positiva, presencia de entrada real Decision `type0/type1>0` y eventos de cambio de score contra N, y estado LTW>0 post tick. Recordar que `class_type_inputs` **se calculan sobre estado previo al tick**, mientras `post_live_stw` y fuerza son **posteriores**; no confundir un `type>0` en tick10 con supervivencia después de la pérdida de ese mismo tick.
- Desagregar por semilla/mapping/target, sin elegir subgrupos favorables. En lecturas sin plasticidad t7/t9/t16/t128, contar `0→1` mejores, `1→0` peores, `0→0` y `1→1` sin cambio frente N, por brazo; verificar que la diferencia de medias derivada coincide con el resumen I3c.7b.
- Verificar sumas de efectos por fuente de objetivo/distractor contra [reporte primario](E09_02I_I3C7B_RESULTADO_CONTRASTE_SENAL.md), igualdad de química M/F y N/C ya testeadas en el runner, 80 signos originales 40/40 y cero decisiones None.
- **Criterio G-I3c7c-DATA**: SHA completo idéntico y auditable, todos los contadores y denominadores enteros exactos; tests de datos corruptos/estado fuera de rango rechazan. **G-I3c7c-MECHANISM**: reporte que delimite desaparición de STW/strength y cronología de propagación, sin afirmar identificación de causa única del C1 original ni retención G05.

## Decisión si el resultado conocido se reproduce

Separar tres fenómenos: (1) **sensibilidad** a recompensa directa unitaria255, (2) **crédito causal** imperfecto, con incremento en fuentes distractoras, (3) **persistencia**: pérdida sincronizada tick10 antes de la siguiente ventana `LTW_rate128`. No proponer nuevos parámetros por alcanzar accuracy. Un nuevo experimento multiepisodio, si conviene, debe comparar **los controladores E09g.5 existentes** y analizar previamente si eventos de refuerzo pueden coincidir con `gain_rate3` y con atrofia `lose_rate5`, sin seleccionar tick ganador por validación de cohortes.

**G05/G09/G00-H ABIERTAS**, PR#103 draft, no merge, no Nilo0.7. Resultado al [estado canónico](ESTADO_Y_CONTINUIDAD.md), con fuente original, código y CI explícitos.
