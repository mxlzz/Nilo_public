# NeuroLab I3c.7f — retención funcional de STW/LTW: dos mecanismos distintos de olvido

**21-11-2026 · AUDITORÍA POST HOC de I3c.7e, NO nuevo experimento ni confirmación G05.** [Preregistro retrospectivo, anterior al auditor](E09_02I_I3C7F_PERSISTENCIA_PESOS_PRE_REGISTRO.md) · [auditor inmutable](../../experiments/neurolab/e09_i3c7f_weight_persistence_audit.py) · [CI de reproducción y análisis #44969817536](https://github.com/mxlzz/Nilo_public/actions/runs/44969817536), cuya conclusión debe consultarse antes de declararla aprobada. Fuente original: [I3c.7e CI44969153930](https://github.com/mxlzz/Nilo_public/actions/runs/44969153930), artefacto14733290218, JSON39.359.911 bytes, SHA256 `193ef109e214d33b9779611f1757d3bf23781755d38a0212778ed4269748752c`. La matriz completa de las20 semillas `per_seed` tiene SHA256 canónica `311b387817b4f0d645cf191df99ae701641c11e9329758fe64f1f71701af8f8e`, fijada en el auditor/CI. Reproducción no es un holdout nuevo.

## Unidades y método

El diseño ya ejecutado I3c.7e tiene 20 seeds1600..1619, dos fases A/B invertidas, seis brazos D0/D16/M0/M16/FD/FM, dos evaluaciones clonadas (`frozen` y `active_no_new_reward`), 128 ticks cada una; **30.720 observaciones de evaluación**. Auditoría read-only sobre los propios `frames` de origen, sin cambiar C1 ni química.

Cada cuarto del holdout comprende **32 ticks consecutivos**: 1–32/33–64/65–96/97–128. Se registra precisión global, y precisión por contexto con denominadores originales para evitar inferencia por ventanas no balanceadas, número de sinapsis con fuerza positiva, con `strength>0 & STW>=5`, con `strength>0 & LTW>0`, y los pesos de cada enlace vivo. **STW≥5 es condición matemática para una contribución positiva en la entrada Decision del laboratorio con Concept-output126 (I3c.5e), no condición suficiente de que la entrada real active cuando el concepto no está presente o cuando hay inhibición**. Las métricas de peso son **POST-tick**; la decisión del propio tick usa pesos del estado previo.

## Segunda fase invertida, lectura ACTIVE sin nuevos refuerzos externos (media 20 seeds)

**M0: químico80 + atrofia artificialmente desactivada**
- 8/8 sinapsis siguen con fuerza positiva durante **los 128 ticks en las20 semillas**. LTW sigue positiva en **8/8** slots vivos, pero su magnitud media era alrededor de **2,49** al inicio de evaluación y apenas **2,56** en el último tick (ambas menores que el umbral de contribución STW5; sus valores no sustituyen automáticamente el STW de cada paso).
- Promedio de conexiones vivas con **STW≥5** por tick en cada cuarto: **3,54 → 2,41 → 1,57 → 0,61** (sobre ocho).
- Precisión global por cuarto: **0,836 → 0,828 → 0,747 → 0,572**. En el último cuarto, aproximación por contexto: S0 **0,568** y S1 **0,574**, ambos cercanos al azar. Las mismas ocho dendritas continúan conectadas; **no basta tener LTW positiva para mantener señal funcional**.

**M16: químico80 + señal de pérdida nominal16 sin emisor endógeno**
- Conexiones vivas medias por tick en cuatro cuartos: **4,12 → 2,32 → 0,79 → 0,17**; STW≥5 en vivo: **3,18 → 2,13 → 0,79 → 0,17**. **19/20 semillas terminan con cero enlaces; una con uno**.
- Precisión global: **0,642 → 0,713 → 0,638 → 0,494**. En cuarto final S0 **0,451** y S1 **0,524**, próximos al azar. La precisión no cae estrictamente de manera monótona, por lo que evitar explicar todo por un solo peso.
- También se pierde **la estructura misma de conexiones**, además de la disminución de su aporte.

**D0 y D16, para contraste descriptivo**
- Directo sin atrofia D0 conserva **8/8** enlaces y el promedio con STW≥5 permanece cerca de **8/8**, lo que concuerda con mayor estabilidad conductual durante el mismo periodo. D16 conserva **6–8** por semilla al final (media7,55), y conserva peso transmisible en los enlaces vivos restantes.
- Estas diferencias **no prueban superioridad propia del directo**: la dosis neural directa255, la cantidad y el calendario de feedback difieren de M y están informacionalmente acoplados a decisiones propias; no son dosis químicas equiparadas.

## Qué información adicional aporta

Los datos distinguen **dos límites**:
1. **Pérdida de conectividad (M16)**: la regla nominal de atrofia elimina dendritas antes de terminar el holdout activo.
2. **Relajación de peso funcional, aun con conectividad intacta (M0)**: la STW cae gradualmente por debajo del nivel en que se transmitiría una señal desde Concept126; los cambios de LTW que alcanzan una unidad por ventana de128 ticks son pequeños en esta cohorte, y no sustituyen la señal transitoria.

En los cuadros hay variaciones del equilibrio por contexto: el cuarto1 reúne **312 S0 y 328 S1** entre20 seeds; el cuarto4 **264 S0 y376 S1**. Por eso todas las precisiones de cuarto son **descriptivas y no causalmente comparables sin condicionar el contexto**; en el cuarto final M0/M16 ambas precisiones contextuales están próximas al azar, lo que respalda la descripción sin hacer de ello una prueba confirmatoria.

**El arrastre químico inicial es real:** en la segunda fase invertida ACTIVE, `M0` tiene media CHEM0 de **~5,32** durante el primer cuarto y luego0 en los tres restantes; `M16` **~4,44** durante el primer cuarto y luego0. `ACTIVE-NOREWARD` significa **sin NUEVAS entregas del evaluador**, no supresión del pool químico que dejó el entrenamiento. Esta distinción importa para atribuir el decaimiento posterior.

**Límites epistémicos:** los dos controles están *on-policy*, el código usa dosis80/tasa40 sintéticas, se han observado los resultados antes de diseñar esta auditoría, el valor STW≥5 se infiere de un Concept-output específico, y ninguna correlación peso/accuracy prueba causalidad individual. No se midió cerebro C1 completo ni motivación/mente autónoma.

## Cota estructural del calendario de consolidación

Esta consecuencia es **deductiva**, no un parámetro ajustado ni un resultado adicional dependiente de las20 semillas: el estado `C1ContextBrain.initial()` crea todas las dendritas con `LTW=0`; el gen Decision original tiene `ltw_rate=128` y `ltw_toward()` permite como máximo **una unidad de cambio** en ticks divisibles por128. Antes de iniciar el holdout invertido, hay exactamente cuatro oportunidades (`tick128,256,384,512`), por lo que **LTW<=4 en cada dendrita** incluso bajo estímulo/recompensa perfectos. El holdout invertido comprende ticks513..640; hasta tick639 no hay consolidación adicional. En tick640 puede pasar a5 **después de calcular la decisión de ese tick**, demasiado tarde para afectar cualquier elección de ese holdout mediante LTW sola.

Bajo `Concept output=126` y atenuación Decision128, el mínimo `STW=5` para una contribución positiva ya fue verificado en [I3c.5e](E09_02I_I3C5E_RESULTADO_PUERTA_SENAL.md). **En este protocolo fijo la LTW sola NO puede sostener una contribución positiva durante ninguna de las 128 elecciones del holdout invertido**, aunque la STW aún pueda ser mayor y decaiga progresivamente. Por eso el resultado FROZEN alto (STW bloqueada) no demuestra memoria estable en el tiempo de prueba, y aumentar conexiones sin revisar el horizonte no soluciona la restricción.

Esta cota no se aplica de manera automática a una arquitectura con migración y LTW inicial resembrada ni a un Norn completo; sólo al cerebro `C1ContextBrain` fijo y la ventana `I3c.7e`. La respuesta correcta de método no es cambiar la tasa128 a posteriori, sino diseñar **antes de correr nuevos casos** si el protocolo debe incluir suficientes oportunidades naturales de consolidación para poder evaluar la propiedad buscada.

## Decisión científica y siguiente paso

La comparación ACTIVE vs FROZEN de I3c.7e sigue mostrando que los resultados de evaluación congelada **sobreestiman la persistencia que se observa cuando la dinámica continua**. **La intervención loss0 por sí sola no alcanza robustez suficiente (sólo1/20 semillas M0 con precisión steady≥0.90 en ambas fases ACTIVE).** No tiene sentido desarrollar de inmediato un emisor histórico de atrofia ni doblar sinapsis para buscar mejores aciertos.

**Próximo paso de bajo costo:** antes de un experimento factorial nuevo, hacer un **análisis de adecuación del gate LTW** desde el algoritmo genético/exe ya auditado: cuánto LTW produce realmente cada dosis y número de consolidaciones; si el sistema existente no puede ofrecer aprendizaje con retención bajo el presupuesto/estímulos declarados, definir una hipótesis técnica falsable y control de recursos. No elegir dosis o tasa por los resultados de esta cohorte. En paralelo, distinguir explícitamente qué requisito es fidelidad histórica C1 y cuál es una propiedad deseada para un cerebro N mínimo.

**G-I3c7f-INTEGRIDAD / DIAGNOSTICO** se acepta sólo si el CI que reejecuta los20 casos y revisa 30.720 frames concluye SUCCESS; **G05/G09/G00-H ABIERTAS**, tanto antes como después. PR#103 draft, sin merge, main/Nilo0.7 intactos.
