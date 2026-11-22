# Etapa 1 — H6: migración reversible de frontera espacial

**Fecha:** 2026-11-22. **Estado:** H6 APROBADA como contrato de conversión de datos, NO como adaptación autónoma del mundo. Etapa 1 ABIERTA.
**Plan preregistrado:** `ETAPA_1_H6_PROTOCOLO_ROI_DINAMICA.md`
**Código:** `experiments/probe_e1_dynamic_roi_boundary.py`
**CI:** https://github.com/mxlzz/Nilo_public/actions/runs/45035363232 (**SUCCESS**).
**Entorno observado:** Python 3.13.18, xarray 2026.9.0 y Landlab 2.11.0.

## Resultados
- Estado original H5 con cavidad de 16m³ ya extraída como intervención externa y salida registrada **32kg A**. Balance de arranque del H6: **A=730kg, B=3kg**.
- ROI original x=[2,10), y=[1,7): 8×6 = **48 columnas volumétricas**. `xarray.Dataset.reindex` extendió a x=[2,11), y=[1,7) = **54 columnas**.
- Se promovieron exactamente seis columnas antes representadas solo como altura compacta, cada una con **4kg A** distribuidos en voxeles z0,z1 (2kg c/u), desplazando **24kg A** desde propietario exterior hacia propietario volumétrico, sin crear ni destruir material.
- La altura de las 96 columnas permaneció **exactamente igual**, tanto antes como después de promoción y después de revertir.
- La cavidad original y todos los voxeles preexistentes quedaron intactos.
- Al ampliar ROI y añadir 24kg sin retirar inventario exterior, el **validador rechazó propiedad duplicada**. Al retirar masa exterior sin depositarla en voxel, rechazó el faltante en balance global.
- El criterio geométrico identificó como **no degradable** a una columna que contenía un vacío interior bajo techo; prohibió reducirla a altura sola.
- La franja compacta agregada sí era degradable: se devolvió al campo de masa exterior y la ROI volvió a 48 columnas. El hash de inventario+mascara original coincidió **exactamente** tras el ciclo de promoción/reversión.
- Un NetCDF del estado expandido (9,212 bytes) conservó información y altura derivada tras recarga.

## Juicio crítico
H6 acredita **una migración reversible puntual** para una franja con geometría simple y datos de misma escala. No demuestra reconfiguración dinámica de una región volumétrica arbitraria, mallas no rectangulares, chunks óptimos, conversión con materiales heterogéneos, leyes de fase, topología continua, ni el costo temporal de promover miles de regiones.

Tampoco prueba que un mundo detecte por sí solo cuándo necesita 3D: la migración fue ordenada y ejecutada como **intervención de representación**, sin una ley de excavación, erosión ni formación de cavidades. El caso de cavidad interna se creó exógenamente. **No confundir viabilidad de formato con autoorganización emergente.**

## Gate
Con H4–H6 existe evidencia suficiente para un **ADR experimental de representación híbrida condicionada**. Evitar nuevas pruebas de gestión de arrays por inercia. Antes de extender o construir un motor, volver a la hoja de ruta de la etapa 1: propiedades mínimas físicamente justificadas, masa/volumen/composición/energía, y qué leyes existentes podrían actuar sobre el estado sin duplicar cantidades. El motor material para etapas 2–3 no está seleccionado.
