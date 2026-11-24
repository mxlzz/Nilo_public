# E04 — pre-registro de memoria sináptica a dos velocidades

**Fecha:** 2026-11-20 · **Estado:** registrado antes de implementar E04.

## Fuente y límite histórico

Grand, Cliff y Malhotra (1996–1997) distinguen un peso de corto plazo **STW** que modula la propagación y se modifica con el refuerzo, y uno de largo plazo **LTW** que actúa como reposo del primero y se desplaza más lentamente. El documento de Steve Grand *I Am Ron's Brain* (1995) explica el motivo de usar ambas escalas. Ninguno de esos textos fija por sí solo los mismos parámetros universales de todas las sinapsis de un genoma C1: éstos son genéticos. Las funciones propuestas abajo **son una aproximación NeuroLab propia**, no ecuaciones verificadas de Creatures 1.

Fuentes: [paper original](https://eem.foo/ccarchive/Sites/fp.cyberlifersrch.plus.com/articles/agents_%2797_paper.htm) y [notas de Grand 1995](https://web.archive.org/web/20071208173623/fp.cyberlifersrch.plus.com/creaturesarchive/braindesc.htm).

## Hipótesis falsables

- H1: una sinapsis con STW/LTW reacciona a un refuerzo adverso inmediato modificando principalmente STW y no borra rápidamente el estado LTW consolidado.
- H2: durante una serie larga de refuerzos opuestos, LTW cambia de tendencia, posibilitando reaprendizaje sostenido.
- H3: después de un refuerzo contrario breve, el peso funcional STW se aproxima nuevamente a LTW durante un intervalo sin recompensa; un solo peso del baseline sin relajación no muestra esa recuperación por sí solo.
- H0: no hay separación funcional entre ambos tiempos o el modelo falla ante un control de un solo peso.

## Regla discreta experimental previa al código

Estado `(stw, ltw)`, enteros entre 0 y 255; inicial ambos `128`.

Para un tick con `reward` en `{-1,0,+1}`:
1. `stw0 = clamp(stw + 32*reward, 0, 255)`.
2. `ltw1 = ltw + move_toward(ltw, stw0, max_delta=1)`. Aquí `move_toward` devuelve el desplazamiento firmado de magnitud máxima 1, con objetivo `stw0`.
3. `stw1 = stw0 + move_toward(stw0, ltw1, max_delta=6)`.
4. La señal efectiva de la sinapsis utiliza STW; no hay inhibición plástica ni elegibilidad todavía.

**Nota:** la diferencia `stw0-ltw` debe interpretarse de forma firmada, nunca transformar castigo en premio por saturación.

Baseline de un solo peso: `weight_new = clamp(weight+32*reward,0,255)`, sin recuperación al cesar refuerzo.

## Tests fijados antes de la ejecución

- T01: calcular a mano `(128,128), reward=+1`: `stw0=160`, `ltw1=129`, `stw1=154`; chequeo por test.
- T02: calcular a mano `(128,128), reward=-1`: `stw0=96`, `ltw1=127`, `stw1=102`.
- T03: entrenar 100 ticks `reward=+1` desde (128,128); comprobar que LTW sube claramente y STW no cae por debajo de LTW.
- T04: después de T03, aplicar 2 ticks de `reward=-1`, luego 20 ticks de `reward=0`; medir recuperación del STW respecto del STW inmediatamente después del castigo. La recuperación debe ser >0 y el cambio de LTW durante el castigo debe ser ≤2.
- T05: tras T03, aplicar 100 castigos seguidos; LTW debe disminuir al menos 40 unidades respecto de su pico, y la señal efectiva descender; verificar que no se queda congelado.
- T06: comparar con baseline simple después de la misma secuencia T03→2 castigos→20 sin recompensa: el baseline no modifica peso durante los 20 ticks en silencio; la sinapsis doble sí modifica STW.
- T07: 20 estados iniciales entre rangos válidos y ciclos prolongados: todos los valores deben permanecer en [0,255].
- T08: checkpoint de STW/LTW reproduce la continuación, no solo el último peso funcional.
- T09: verificar que no hay acceso al mapa de respuestas correctas A/B en `TwinSynapse`.

## Control experimental

Esta fase estudia primero **la dinámica sináptica aislada**, no pretende comparar el rendimiento de dos cerebros completos con diferencias de hiperparámetros. Se requiere evidencia de memoria de dos escalas según las pruebas anteriores. Integrar el modelo con el selector de E03 será un paso posterior si aporta alguna ventaja o utilidad clara.

**Criterio G04:** tests de oráculos manuales, diferencias temporales, reversión sostenida y control de un peso superados. Si no hay separación, registrar resultado negativo, no retocar umbrales tras conocer los resultados.
