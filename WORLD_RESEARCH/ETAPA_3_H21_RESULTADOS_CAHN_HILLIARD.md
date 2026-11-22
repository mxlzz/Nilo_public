# Etapa 3 — H21. Cahn–Hilliard 2D conservó masa, pero NO segregó bajo condiciones fijadas

**2026-11-22. Dictamen:** **H21 NO APROBADA como prueba de segregación y organización espacial no trivial**; el modelo se ejecutó completamente. [Protocolo previo](ETAPA_3_H21_PROTOCOLO_CAHN_HILLIARD.md), [ADR-0012](DECISIONES/ADR-0012_CAHN_HILLIARD_E3.md), [código](experiments/probe_e3_h21_spinodal_fipy.py), [CI H21 45061348648 — FAIL por gates](https://github.com/mxlzz/Nilo_public/actions/runs/45061348648). FiPy4.0.3, NumPy2.4.6, SciPy1.17.1, xarray2026.9.0, Python3.11.18.

## Resultado medido sin ajustar hipótesis

Se ejecutó la estructura exacta del PDE Cahn–Hilliard del ejemplo FiPy 4.0.3 en grilla20×20 con dx=dy0,25, `D=a=epsilon=1`, 400 pasos con dt adaptativa predefinida y tiempo físico/adimensional acumulado ~35,93. El owner tenía masa total400kg (1kg/celda) y dos especies A/B, con `phi` derivada de sus cantidades; ruido inicial uniforme ±0,07 sobre media0,5.

- **Composición A:** media ~0,50191353 antes y después, cambio de masa A máximo observado por paso **1,24×10⁻¹⁰kg**: *conservación material muy superior al umbral1e-4kg*, y B se conserva por complementariedad. Replay bit a bit, siete estados corruptos rechazados, snapshot NetCDF exacto.
- **Sin movilidad D=0:** valores y patrón quedaron exactamente idénticos al inicio.
- **Composición fuera del régimen espinodal, media0,1:** tendió a homogeneizarse; cuantil95 final~0,101925, varianza final6,04×10⁻¹¹, inferior a varianza inicial0,0015992.
- **Escenario activo media0,5:** **también se homogeneizó**, contra la hipótesis registrada. Varianza **0,0015992→0,0000553952**; q05 final0,49108, q95 final0,51275, muy lejos de los umbrales `q05<0.3` y `q95>0.7`. Había regiones `phi>0.5` pero de amplitud minúscula, **no dominios de composición segregados**.
- **Correlación espacial binaria:** proporción de vecinos con mismo rótulo `phi>0.5` fue0,97105 frente a percentil95 de nulo condicionado por filas **0,95132**; diferencia0,01974, menor que el umbral preregistrado0,08. Las 222 celdas «altas» forman una componente, pero el gran tamaño también se explica mayormente por el gradiente/estructura por filas: no prueba organización diferencial. Jaccard entre pasos300 y400 fue0,83146, que sí supera umbral0,60.
- **Fallo instrumental diferenciado:** `global_mass_A_B_conserved` del arnés exige en *otro subcheck* que `mass_final_kg==400.0` bit a bit. En el caso estable B la suma NumPy produjo400,00000000000006kg por redondeo (~5,7e-14kg), lo que marcó ese subcheck como FAIL a pesar de pasar el criterio físico preregistrado de1e-4kg. **El check exacto es un defecto de validación adicional, no creación de materia.** No se cambiaron tolerancias ni se repitió H21 para ocultarlo.
- **Otros fallos preregistrados:** `segregation_quantiles`, `variance_growth`, `spatial_organization_over_row_null`. Por eso, corregir el falso negativo de flotantes **no convertiría H21 en éxito**.

## Diagnóstico físico plausible, NO verificado

La relación dispersiva lineal del modelo Cahn–Hilliard alrededor de `phi=0,5` con energía libre de doble pozo y `a=1` es `lambda(k)=D*k²*(0.5-epsilon²*k²)`: la energía de gradiente `epsilon=1` penaliza las fluctuaciones de pequeña longitud de onda. Con dominio de ancho físico5 unidades (`20×0,25`), solo ondas largas pueden ser inestables y crecer lentamente; en las primeras ~36 unidades simuladas la difusión de modos cortos predominó. **Esto es hipótesis explicativa**, no prueba del error del solver ni justificación para modificar H21 retroactivamente. La fórmula y su régimen deben respaldar un futuro protocolo comparativo de escala/epsilon.

## Dictamen y decisión siguiente

- **E3 ABIERTA; H21 rechazada bajo sus condiciones.** No confundir un patrón dicotómico obtenido por umbral `phi>0,5` con segregación material real si el contraste de composición se redujo.
- **No adoptar** Cahn–Hilliard como mecanismo estructural ya validado; sí se conserva como proveedor existente capaz de evolucionar y conservar inventario en 2D.
- Si se intenta H22, debe ser un **nuevo experimento preregistrado** de dependencia de escala `epsilon` vs dominio, con un factor causal aislado, controles negativos y todos los umbrales fijados antes; no «tuning» oportunista para aprobar. No cerrar E3 ni pasar a E4 por este experimento.

Fuente upstream: [NIST FiPy Cahn–Hilliard](https://github.com/usnistgov/fipy/blob/4.0.3/examples/cahnHilliard/mesh2D.py).
