# ADR-0018 — Etapa5: intervención LOCAL de erodibilidad con proveedor existente

**2026-11-22. Estado:** selección reversible de H32, NO cierre E5. [H31](../ETAPA_5_H31_RESULTADOS_SUELO_CONTACTO.md) ya aprobó transferencia causal unilateral de erosión global a contacto rígido sobre un owner xarray con dos runtimes. El criterio explícito de Etapa5 exige **perturbación local y efectos aguas abajo**; cambiar K_sed globalmente H31 no cumple ese apartado.

## Alternativas evaluadas antes de programar

- **SpaceLargeScaleEroder Landlab2.11 nativo, K_sed espacial:** código upstream [SPACE](https://github.com/landlab/landlab/blob/v2.11.0/src/landlab/components/space/space_large_scale_eroder.py) declara `K_sed` aceptando float, array o nombre de campo, con flujo sobre nodos. Podemos anular K_sed **solo en3×3 nodos core** y mantener0,10 en los demás. El sistema transporta sedimento con su propia física, las salidas se registran y la diferencia puede propagarse por red de flujo. **Menor cambio** con H31 y sin modificar ley ni masa manualmente. Seleccionado.
- **Mover masa de suelo arbitrariamente de un nodo a otro:** es una intervención de obra externa pero necesita modelar transferencia inicial con evento/material explícito, y puede contaminar la atribución causal del flujo nativo. No elegida.
- **Rebajar geometría bedrock local manualmente:** sin modelar extracción o volumen del lecho generaría una fuente/sumidero geológico injustificado. Rechazada.
- **Dos motores erosivos o DEM nuevo:** innecesarios, E5 busca acople y propagación, no otro proveedor.

## Experimento seleccionado

**H32**: para las mismas dos seeds WorldEngine, escoger un patch3×3 de K_local=0 mediante un criterio de drenaje calculado **solo desde relieve inicial** (no en función del resultado de intervención). Comparar contra K=.10 en todos los nodos con mismo suelo/cuerpo. Observar cambios en nodos **fuera del patch y aguas abajo en la red D8 inicial**, y reconstruir desde el mismo owner un patch downstream cuyo contacto de Bullet se modifique. Mantener exactamente los mismos solvers/física/mallas/temporalidad y reservorio de H31. La distribución K pasa a ser **propiedad explícita del owner**, no masa/inventario duplicado.

[H32 protocolo](../ETAPA_5_H32_PROTOCOLO_PERTURBACION_LOCAL.md) fija selección, umbrales, controles, seguimiento, replay, SHA y salida CI antes de código.

**No afirmar:** efecto aguas abajo de un río real, bidireccionalidad, estabilidad de cavidades, relojes sincronizados, parámetros de erosión calibrados ni evolución infinita. Si el supuesto de propagación falla, **H32 NO aprobada** y conservar H31 aprobado como enlace unilateral global; no ajustar tamaño/posición local post hoc.
