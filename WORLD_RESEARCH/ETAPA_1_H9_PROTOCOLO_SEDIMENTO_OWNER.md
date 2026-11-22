# Etapa 1 — H9: transporte nativo de sedimento con publicación material auditable

**Fecha:** 2026-11-22. **Estado:** PROTOCOLO PRERREGISTRADO; no contar como prueba realizada. **Rama aislada:** `research/world-foundations-2026-11`.

## Alineación y decisión del gate (ocho puntos)

1. **Propósito aprobado:** etapa 1 (materia compartida) y prueba exploratoria vinculada al futuro transporte local de etapa 2. Un mundo que cambia requiere que la física modifique su inventario real, no una imagen ni un campo duplicado.
2. **Hipótesis refutable:** `SpaceLargeScaleEroder` de Landlab 2.11, ya probado en E0.4-H7b, puede mover/depositar suelo móvil a lo largo de pasos sucesivos y publicar cada estado en **un solo owner xarray** con exportación declarada, sin violar el balance de materia. Un control sin erosividad debe conservar exactamente la distribución inicial. Posibles fallos: drift de inventario, incompatibilidad entre nodos y masa, una diferencia entre cálculos consecutivos o una falsa acreción.
3. **Reutilización:** usar la API pública de `PriorityFloodFlowRouter` + `SpaceLargeScaleEroder` (MIT); ningún solver nuevo. El ensayo precedente E0.4-H7b comprobó exportación y acreción en una cuenca, pero **no commit al owner**. H1–H6 comprobaron contratos de estados, no transporte nativo. Sandspiel/TPT siguen 2D de material local y PyBullet rígido no simula suelo fluvial; GeoTaichi/Project Chrono son candidatos para *otra pregunta* (granular/deformable), no requisitos para validar sedimentos fluviales de 2.5D.
4. **Técnica:** un `xarray.Dataset` con `soil_mass_kg(y,x)` **único inventario autoritativo** para suelo transportable, `bedrock_elevation_m` como geometría inmóvil y `exported_soil_kg` como sumidero acumulado. La profundidad en Landlab es un estado de trabajo transitorio del solver; se reconstruye desde xarray antes de cada paso y se convierte en candidato validado antes de publicar. La topografía es derivada. No usar xarray y Landlab como dos inventarios sumables.
5. **Alcance mínimo:** la misma cuenca 16×16 de E0.4-H7b, suelo A homogéneo de densidad experimental constante `1200 kg/m³`, `100m²` por nodo interior, roca inerte, una salida, `phi=K_br=F_f=0`, 12 pasos de `dt=0.2`, `K_sed=0.10`. El `soil_mass_kg` en nodos de borde permanece 0 (solo se contabilizan `core_nodes`). Los parámetros son **de banco** y no implican validez geológica o calibración temporal.
6. **Pruebas previas a la implementación:**
   - Transporte activo: espesor y masa cambian realmente en nodos interiores, hay exportación, erosión, deposición y al menos un receptor desnudo acumula suelo neto.
   - Balance por paso: `masa_actual + exportación_acumulada == masa_inicial` con tolerancia absoluta `max(1e-4 kg,1e-8*masa_inicial)`; residuo y tolerancia siempre impresos. No reparar automáticamente residuos fuera de rango.
   - Ablación `K_sed=0`: propietario sin cambios **exactos** y sin exportación/deposición/erosión.
   - Repetición completa con idénticas condiciones: arrays finales y sumideros exactamente iguales.
   - Rechazar candidato con fuente no declarada (añadir 1 kg en un nodo), masa negativa, unidad de masa cambiada, masa en borde y salida disminuida; owner original intacto tras cada rechazo.
   - Checkpoint NetCDF: relectura exacta del inventario, unidades, geométrico derivado, ledger, hash de datos y control de que no se guardó una segunda copia de material como `soil__depth` o `topographic__elevation`.
   - Regresión: importar código del experimento previo sin mutarlo; no modificar H1–H8 ni los módulos Nilo/NeuroLab.
7. **Evidencia:** código bajo `WORLD_RESEARCH/experiments/probe_e1_h9_sediment_owner.py`, workflow dedicado, salida `WORLD_EVAL_JSON` con versiones y métricas; registrar CI success/fail, corrigiendo solamente errores demostrados. No completar un resultado sin la ejecución remota.
8. **Salida:** **ACEPTAR H9** únicamente si todos los controles anteriores se cumplen, incluido balance físico y fuente/sumidero correctos. **CORREGIR** si el arnés confunde salida/borde o API; **DESCARTAR** si Landlab no puede suministrar cambios consistentes. Independientemente del resultado, **etapa 1 continúa abierta**: esto no cubre ROI volumétrica, granos 3D, energía/térmica, transformación de fase ni emergencia, y no autoriza etapa 2.

## Registro de condiciones no negociables

La densidad fija `1200 kg/m³` es solo conversión dimensional para este material abstracto A; el modelo empleado transporta **volumen de sólidos**, no energía. La exportación usa la salida física de `run_one_step`; no deducir artificialmente el sumidero como diferencia de inventarios porque eso escondería errores. Si la API emite volumen de finos, debe agregarse también como salida, aun cuando el escenario lo configure nulo. Nunca inferir realismo a partir del balance numérico.

**Antecedentes:** `ETAPA_0_4_PROTOCOLO_SEDIMENTO_FEEDBACK.md`, `ETAPA_0_4_RESULTADOS_SEDIMENTO_Y_ECOLOGIA.md`, `ETAPA_1_H5_RESULTADOS_ACOPLAMIENTO_ESTADO.md`, `DECISIONES/ADR-0006_PROVEEDOR_CONTACTO_BULLET.md`.