# E0.6 — Resultado H10b: retorno geométrico durante 90 días

**Fecha:** 2026-11-21. **Estado:** H10b APROBADO como ensayo de sensibilidad y continuidad con intervención externa. **No** aprobado como mundo ecológico calibrado ni como arquitectura final.
**Protocolo escrito antes de implementar:** `ETAPA_0_6_PROTOCOLO_RETORNO_RADIACION.md`.
**Código:** `experiments/probe_landlab_90day_radiative_return.py`.
**CI reproducible:** https://github.com/mxlzz/Nilo_public/actions/runs/44952698259 (**SUCCESS**; ambos ensayos H10a + H10b).
**CI anterior con error instrumental de tiempo:** https://github.com/mxlzz/Nilo_public/actions/runs/44952595861 (**FAIL**, registrado y corregido sin alterar hipótesis).

## Pregunta
¿Puede una modificación de la topografía alterar radiación→PET→humedad/vegetación y modificar la redistribución posterior de suelo a través de los componentes ya existentes de Landlab, sin crear nueva física?

## Componentes y contrato
Se usaron solo `RasterModelGrid`, `Radiation`, `PotentialEvapotranspiration`, `SoilMoisture`, `Vegetation` y `DepthDependentDiffuser` de **Landlab 2.11.0**. Cada día se reconstruyó `Radiation` sobre el relieve actual por la limitación de pendientes cacheadas detectada en H10a. `PET` usó método `Cosine`, base sintética 10 mm/día y ratio solar local. `PET30` se obtuvo mediante promedio de los últimos 30 días disponibles para el cambio de estación; la agregación no añade un modelo climático nuevo.

- 8×8 nodos, separación 10 m, borde cerrado, capa inicial de suelo 0.6 m (2.160 m³ en los 36 nodos interiores).
- 90 eventos diarios; tormenta de 1h e intertormenta 23h; lluvia sintética 12 mm cada quinto día; tres pasos de geomorfología, uno cada 30 días con `dt=1/3` de estación.
- Movilidad de suelo por ley publicada `K_d=2.5e-4 exp(-0.3V)` m² por estación; espesor de decaimiento 1 m supuesto experimental de Landlab.
- El día 46 se introdujo una **intervención externa de +12 m** en un nodo; aumentaron cota y roca madre simultáneamente para mantener fija la capa de suelo móvil. **No** es elevación emergente ni conservación de roca madre; fuente geológica exógena declarada.
- Cuatro escenarios factoriales: con/sin intervención, vínculo topografía→radiación activo o ablacionado usando perfil original inmutable a igual fecha. Repetición del caso activo con intervención.

## Resultados medidos
- Antes del día 46, ambos mundos con vínculo activo tuvieron PET idéntica: diferencia máxima **0**.
- Después de intervención con vínculo activo: diferencia máxima PET **2.704602032913111 mm/día**; en primer día posintervención **1.5209994913422413 mm/día**.
- Diferencia máxima de fracción de humedad/saturación **0.0354725988709583**.
- Diferencia máxima de biomasa **4.166370693608229** (unidades del estado Landlab; no extrapolar a biomasa real sin revisar calibración).
- Diferencia máxima de cobertura vegetal **0.011507454713055032**.
- En control con vínculo topografía→radiación anulado: diferencia PET **0**, humedad **0** y biomasa **0**, pese a la perturbación geométrica en el otro modelo.
- Efecto endógeno **sin intervención externa**: comparación de radiación geométricamente actualizada frente a radiación congelada tras el día 30 dio diferencia PET máxima **4.424286288440271e-7 mm/día**. Es distinto de cero, pero **extremadamente pequeño** en la escala/horizonte estudiados.
- Inventario sólido inicial **2160 m³**; a los días 30/60/90 continuó en 2160 m³, residual máximo del orden de **2.8e-11 m³**. Capa no negativa y finita, no se crea ni destruye materia móvil. La roca madre de la perturbación **sí** cambió +12m como forzante externo.
- Tiempo aproximado por corrida 90 días, solo cálculo en runner de referencia: **2.14–2.21 s** con geometría activa y **3.43–3.53 s** bajo ablación (esta última genera también una escena radiativa de referencia diaria); **no** es benchmark escalable a tamaños mayores.
- Repetición exacta del escenario con intervención dio mismo PET y relieve final.

## Interpretación
**H10b PASÓ sus criterios predefinidos:** existe un lazo causal de APIs Landlab que puede continuar 90 días y responder a una alteración geométrica, con transporte de suelo conservativo en dominio cerrado y con control negativo que invalida explicaciones triviales.

**No prueba:** formación espontánea de un relieve significativo; realismo físico de una montaña que sube 12m; cuantificación completa del presupuesto hídrico; transporte/sedimentación fluvial en este mismo mundo; calibración climática; estabilidad durante décadas; evolución abierta de formas biológicas o materiales.

Un problema de representación permanece: la respuesta de PET al **relieve endógeno** en 90 días fue minúscula. No es correcto describir eso como un ecosistema realimentado con efecto macroscópico. La perturbación exógena solo prueba la conectividad funcional.

## Auditoría de errores
El ensayo original falló antes del primer día por asignar a `pet.current_time` una fecha igual a la fecha de inicialización (Landlab exige tiempo estrictamente creciente). Se corrigió actualizando el setter solo desde día 2; se conservaron aserciones y condiciones experimentales. La segunda corrida concluyó en éxito.

## Próximo gate
- Evaluar respuesta **hidrológica real** del relieve (caudal, almacenamiento, infiltración, sedimentos), más allá de la ruta solar/PET. Priorizar módulos nativos y comparar compatibilidad de `OverlandFlow`, `SoilMoisture` y `SpaceLargeScaleEroder` antes de conectarlos.
- Formalizar unidades, ownership del agua y del sedimento, malla nodo/celda, fronteras y subpasos. No usar el mismo estado de suelo simultáneamente con dos motores de erosión sin un presupuesto conjunto.
- Evaluar persistencia completa de estados de los componentes, escalado de rendimiento (8×8 no basta) y luego emergencia/organización.
- **Etapa 0 sigue ABIERTA; decisión Landlab-first sigue provisional/reversible.**
