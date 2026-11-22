# NeuroLab E09.02i–I3c.5d — refuerzo temprano en conexiones activas: NO produce aprendizaje

**21/11/2026 · análisis post-ejecución del ensayo preregistrado.** [Preregistro anterior a código](E09_02I_I3C5D_REFUERZO_PRECOZ_PRE_REGISTRO.md) · [runner](../../experiments/neurolab/e09_i3c5d_early_window.py) · [tests](../../experiments/neurolab/tests/test_e09_i3c5d_early_window.py) · [CI 44965370419](https://github.com/mxlzz/Nilo_public/actions/runs/44965370419) **SUCCESS, 6/6 tests, 20 semillas1300..1319, 80 combinaciones y 240 ramas**, artefacto íntegro `neurolab-i3c5d-early-feedback`, ID **14730837789**. [Resumen y hashes originales](resultados/e09i3c5d_resumen_y_hashes.json), huella SHA256 del JSON completo **b6a97ae5ae765d55330b122050c60b29ffcb9eb95080efa5af5ed5df37658192**, sin seleccionar casos favorables.

## Contrato efectivo

El cerebro de ocho dendritas fijas decide tras cuatro ticks del contexto objetivo, sin preparación prolongada. En el momento de la bifurcación, **las ocho dendritas tienen strength>0**. Sigue el distractor constante durante124 ticks. Tres ramas: N sin pulso, D0 precursor en tick5 (inmediato al distractor), D3 mismo precursor en tick8 (tres ticks después), manteniendo genoma, tasa40 y dosis80 sintéticas, gain1, sin migración. Los **80/80** troncos tienen una acción y reciben **80 pulsos en D0, 80 en D3, cero en N**; 40/80 elecciones iniciales correctas, 40/80 errores. Las dos etiquetas A/B comparten el estado neuronal previo a recompensa.

El primer tick de lectura neuronal CHEM0/1 positiva es **tick7** en D0 y **tick10** en D3, no el mismo tick de inyección. En ambos brazos, la conexión original todavía dispone de fuerza positiva cuando llega química (**80/80 eventos cada uno**); el problema de fuerza0 ANTES del feedback observado en I3c.5a está eliminado aquí.

## Resultados medidos, con denominadores

- D0: efecto de refuerzo **en 16 de80 ramas**; **16 unidades** totales, concentradas en conexiones de fuente objetivo y dueño de la acción previa. **64/80** ramas con efecto exactamente0.
- D3: efecto en **48 de80 ramas**; **60 unidades** totales, **16** sobre conexiones de fuente objetivo y **44** sobre distractor. **32/80** ramas con efecto exactamente0.
- Todos los eventos de efecto positivo se concentran en **tick7 (D0)** o **tick10 (D3)**; el máximo por sinapsis/tick es **1**. Ningún efecto positivo se observó en el control N.
- La fracción media de efecto objetivo en D0 fue **1,0 entre las 16/80 ramas con denominador** y en D3 **0,2083 entre 48/80**. **No extrapolar estas fracciones a las 80 ramas** ni utilizar el intervalo D0−D3 como evidencia robusta: sólo **4/20 semillas** tuvieron al menos una pareja con ambas fracciones definidas, con IC condicionado a esos casos.
- Exposición integrada media CHEM0 y CHEM1 por rama fue **20,5 y20,5 en D0 y D3**, pero los calendarios de exposición son diferentes. No asumir igual coincidencia temporal con actividad.

**Conducta y memoria:** las tres ramas N/D0/D3 obtuvieron **0,50 de exactitud en readout congelado** tras ticks9,16 y128; diferencia pareada de exactitud **0** (IC bootstrap agrupado por semilla `[0,0]` en las tres comparaciones). De hecho **0/80 elecciones finales cambiaron frente a N** para D0 y D3 en cualquiera de las tres lecturas. STW máxima en TODOS los snapshots preregistrados (4/5/6/8/9/10/16/128): **0**. Al tick10, el control y ambos modos tienen fuerza0 en8/8 contactos (en este calendario); al tick128 **LTW positiva con fuerza>0 =0**.

## Interpretación y nueva duda forense

La disponibilidad en el primer tick químico **no basta**. Los microefectos que se detectan son demasiado pequeños y/o demasiado breves para transformarse en la entrada de Decision antes del borrado por pérdida de fortaleza. Sin ampliar red ni cambiar reglas, la siguiente unidad debe adjudicar en qué fase desaparece la señal:

1. **Cuantización de aporte:** la regla Decision usa `(concept_output*STW)>>8` y otra atenuación; ¿qué STW mínima hace no-cero la clase para el concepto original?
2. **Relajación STW:** en D0 el efecto positivo aparece exactamente en tick7, que coincide con el patrón del helper de tasa80; comprobar si el peso transitorio se convierte a0 DENTRO de ese tick.
3. **Borrado por fuerza:** en D3 el efecto aparece exactamente tick10, cuando la fuerza inicial2 llega a0; comprobar si `lost_connection` anula la STW en ese mismo tick.
4. **Trayectoria real de señal:** cuando el efecto numérico es1, ¿alguna señal llega a `type0/type1`/score de Decision? Un resultado analítico sin efecto de salida no habilita ensayos de aprendizaje complejos.

Esta investigación es **post hoc sobre I3c.5d**, no una nueva cohorte confirmatoria. Debe quedar registrada antes de cualquier instrumentación I3c.5e y reutilizar funciones/oráculos existentes.

**Puertas:** G-I3c5d-SOFTWARE VALIDADA, G-I3c5d-AVAILABILITY VALIDADA; **G05/G09/G00-H ABIERTAS**. El ensayo prueba que no bastó adelantar el pulso, NO que la biología de Creatures sea incapaz de aprender. No tunear dosis/ganancia ni modificar fuerza para aumentar un resultado; no integrar a Nilo0.7. El PR #103 permanece draft y `main` sin cambios.
