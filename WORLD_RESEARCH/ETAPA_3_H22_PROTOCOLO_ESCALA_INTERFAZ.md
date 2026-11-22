# Etapa3 — H22. Prerregistro de contraste causal de escala interfacial de Cahn–Hilliard

**2026-11-22. ANTES DE CODIGO Y CI.** Esta prueba parte del resultado adverso [H21](ETAPA_3_H21_RESULTADOS_CAHN_HILLIARD.md), que no logró segregación a tiempo ~35,93 y epsilon1 a pesar de conservar masa. El experimento original permanece **NO APROBADO**. H22 **no modifica** su criterio retroactivamente.

## Pregunta causal y fundamento teórico

La [ecuación Cahn–Hilliard FiPy](https://github.com/usnistgov/fipy/blob/4.0.3/examples/cahnHilliard/mesh2D.py) de movilidad `D`, doble pozo `a=1` y gradiente `epsilon` linealizada alrededor de la mezcla homogénea `phi=.5` tiene tasa de crecimiento por modo de onda `lambda(k)=D*k²*(0.5-epsilon²*k²)`. Si `epsilon=1`, los modos con `k>=sqrt(.5)=0.7071` son estables; en el dominio H21 de lado5, las longitudes de onda permitidas son relativamente grandes. Al reducir **solo epsilon a0,5**, el corte se desplaza a1,4142 y se habilitan más modos inestables a la misma malla y el mismo tiempo.

**Hipótesis falsable H22:** bajo el mismo ruido, masa y tiempo de H21, **epsilon0,5** aumenta segregación espacial de A/B respecto a **epsilon1**, sin perder masa, mientras el control D0 no cambia. Eso puede fallar por tiempo, aproximación numérica, estado o por tamaño de dominio. No resolver el resultado fallido H21 mediante «tuning» sin registrar el nuevo contraste.

## Diseño fijo y medidas

- FiPy4.0.3 original con `TransientTerm==DiffusionTerm(coeff=D*(1-6PHI*(1-PHI)))-DiffusionTerm(coeff=(D,epsilon²))`; misma `Grid2D(20×20,dx=dy0,25)`, mismo seed20261122 y ruido uniforme±0,07, igual owner xarray A/B1kg/celda, igual `DefaultSolver`, 400 pasos con `dt=min(100,exp(-5+0.01*i))`, mismos instantes300 y400.
- A=epsilon0,5, D1, mean0,5; control B=epsilon1, D1, mean0,5, reproduciendo H21; control C=epsilon0,5, D0, mean0,5; control D=epsilon0,5, D1, mean0,1; replay A'. **Único factor que cambia entre A y B: epsilon**. No variar tamaño de malla ni amplitud de ruido.
- FiPy deriva `phi` del único owner de masa A/B; cada paso publica solo candidato validado. Toda masa total400kg dentro de tolerancia por redondeo1e-9kg y masa individual A/B desviación <1e-4kg respecto a inicio; negativos y fuentes inexistentes prohibidos, sin clipping/rebalanceo.
- **Gates preregistrados:**
  1. A produce separación fuerte: `q95(phi)>0.7`, `q05(phi)<0.3`, `Var_final>2*Var_initial`; ambos grupos `phi>0.5` y `<=0.5` tienen ≥8 celdas. Si el solver sale de rango físico0..1, **NO APROBADA**.
  2. Var_final A al menos **5 veces** Var_final B, con masa igual.
  3. Organización: `same-neighbor frac` del binarizado A en paso400 supera por **>0,08** el P95 de 512 nulos que preservan los conteos `phi>0.5` por fila, RNG20261123. No aceptar nulo global.
  4. Persistencia de máscara A entre paso300 y400 **Jaccard≥0,60**, replay A/A' bit a bit idéntico, y escena D0 cambia menos de1e-8 en campo.
  5. Control mean0,1 permanece en `q95<0,3` y var final<1,5var inicial, no desarrolla segregar la mezcla estable.
  6. Integridad: en los cinco escenarios, masa global por especie <1e-4kg de deriva, celda1kg exactamente dentro1e-12kg, siete corrupciones owner rechazadas; NetCDF exacto y reconstrucción del estado `phi`.
- Informar también efecto de `epsilon` en morfología, varianzas, tamaño de componentes, tiempo total, energía libre solo como diagnóstico si se mide, y controles; nunca afirmar formación de objetos mecánicos.

## Interpretación y salida

H22 solo podrá **aprobar contraste de escala y dominios binarios conservativos**; **no** cerrará automáticamente etapa3, porque aún no demuestra autoorganización funcional 3D ni estabilidad mecánica independiente. `WORLD_EVAL_JSON` precede a cualquier exit1. Si los gates fallan, documentarlos; no ajustar epsilon, tiempo, grid ni umbrales después de observar el resultado. **No tocar H21 ni el código físico upstream, main, NeuroLab.**
