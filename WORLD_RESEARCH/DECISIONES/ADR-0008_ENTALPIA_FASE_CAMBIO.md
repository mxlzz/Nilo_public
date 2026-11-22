# ADR-0008 — Primera transformación material térmica acoplada: fracción de fase por entalpía

**Fecha:** 2026-11-22. **Estado:** decisión reversible de **ensayo H15**, no adopción del modelo constitutivo definitivo.

## Pregunta y alineación

La [auditoría post-H14](../AUDITORIA_GATE_ETAPA_1_POST_H14_2026-11-22.md) halló que cada ensayo material/energético funciona aislado, pero no probamos un cambio de estado material condicionado por energía y balanceado en el mismo inventario. La etapa1 del [plan rector](../BASES_Y_HOJA_DE_RUTA.md) exige masa, energía y transformaciones trazables; no exige escoger ya geometría o render.

**Elegimos un experimento de cambio de fracción sólido/líquido por conducción térmica en un material abstracto de cambio de fase**. No pretendemos magma, roca, metal concreto, clima ni nucleación: la transición será **reversible, local y en equilibrio** dentro de un intervalo de temperaturas predefinido, sin movimiento de masa.

## Alternativas comprobadas

1. **FiPy4.0.3, NIST**: volumen finito, PDE transitoria y conducción con fuentes. [Ejemplo acoplado de solidificación/difusión](https://pages.nist.gov/fipy/en/latest/generated/examples.phase.polyxtalCoupled.html) modela acoplamiento de temperatura y fase con liberación de calor latente, pero tiene ecuaciones adicionales de campo de fases, anisotropía, orientación y cinética que **no requiere el gate de conservación mínima**. Su [licencia original](https://github.com/usnistgov/fipy/blob/4.0.3/LICENSE.rst) es términos de uso NIST con permiso de uso/modificación/distribución bajo aviso, no llamarla erróneamente MIT o BSD.
2. **Método de capacidad calorífica aparente / entalpía**, consolidado en [COMSOL 6.4 — teoría](https://doc.comsol.com/6.4/doc/com.comsol.help.heat/heat_ug_theory.07.024.html), [revisión de técnicas](https://ccc.illinois.edu/PDF%20Files/Publications/90_Fixed%20Grid%20Techniques%20for%20Phase%20Change%20Problems-%20A%20Review.pdf) y [comparación aplicada](https://www.mdpi.com/2076-3417/9/20/4334). Concentra calor latente en capacidad térmica efectiva a lo largo de una banda de temperatura finita («mushy zone»). Es la aproximación **más simple que aún conserva energía** en un ensayo con banda lineal constante, sin imponer microestructura o forma final. **FiPy resuelve** la PDE; nuestro arnés solo describe un constitutivo publicado e invierte estado/temperatura. No reimplementa el solver FV.
3. **OpenFOAM `solidificationMeltingSource`**: [documentación](https://api.openfoam.com/2606/classFoam_1_1fv_1_1solidificationMeltingSource.html), ofrece entalpía/porosidad y momentum acoplados, pero toolchain compilado, GPL y fluidodinámica no necesaria para esta prueba.
4. **FVTool** [BSD-2-Clause](https://github.com/FiniteVolumeTransportPhenomena/FVTool): incluye ejemplo de entalpía/PCM, pero Matlab/Octave, requeriría una segunda runtime/puente y menos reutilización de H14.
5. **Solución algebraica sin PDE**: conserva energía por construcción, pero **no demuestra que la fracción de fase cambie causalmente por intercambio térmico físico**. Rechazada como gate H15 aislado.
6. **Nuevas ecuaciones propias**: innecesarias; se evita inventar motor o transporte.

## Delimitación física crítica

Material A: masa por celda fija, `cp` igual para fases, densidad fija y calor latente fijo; volumen constante. Fracción líquida `f(T)=clip((T-T_s)/(T_l-T_s),0,1)`. Energía material `E=m*[cp*T + L*f(T)]` con referencia energética arbitraria cero a0K. La fase **no** es un segundo stock: masa líquida `m_l=m*f` y sólida `m_s=m*(1-f)` son **derivadas** de la masa total y la energía canónica. La temperatura también es derivada y se invierte analíticamente de entalpía. En la banda `T_s<T<T_l`, `cp_eff=cp+L/(T_l-T_s)` constante; FiPy resuelve `rho*cp_eff*dT/dt=div(k grad T)` con no-flux.

Se elige una prueba en que **todas las temperaturas permanecen dentro de la banda**. Esta limitación no se disimula: **no** se validarán frentes de fusión abruptos ni transferencia fuera de la banda. La inversión constitutiva es un adaptador algebraico de modelo existente, no una ley física nueva del mundo.

**Hipótesis H15:** con diferencia térmica, conductividad y latente>0, la fracción líquida cambia entre celdas sin transportar ni crear masa, y la energía total permanece constante; sin k o sin gradiente no cambia, y sin L la propagación sensible es mayor, siempre con la misma forma y parámetros salvo L. Prerregistro en [H15](../ETAPA_1_H15_PROTOCOLO_FASE_ENTALPIA.md).

**No decidir en esta ADR:** material real, transición de volumen o densidad, fuerzas/fricción, acoplamiento MPM, masas de especies, fases fuera del rango, repetibilidad multiplataforma, arquitectura de almacenamiento final. H15 NO cierra etapa1 automáticamente.
