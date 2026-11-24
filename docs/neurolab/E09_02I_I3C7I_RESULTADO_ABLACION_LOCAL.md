# NeuroLab E09.02i–I3c.7i — resultado: sinapsis alineadas sostienen acciones correctas localmente

**22/11/2026 · AUDITORÍA MECANÍSTICA POST HOC de I3c7h; NO nueva cohorte ni confirmación G05.** [Preregistro antes de microlesiones](E09_02I_I3C7I_ABLACION_LOCAL_PRE_REGISTRO.md) · [fuente y runner](../../experiments/neurolab/e09_i3c7i_synapse_necessity.py) · [CI FINAL #44987034290](https://github.com/mxlzz/Nilo_public/actions/runs/44987034290) **SUCCESS 7/7 tests, 20/20 semillas**, artefacto completo `neurolab-i3c7i-c1-local-synaptic-necessity` **ID14739729195**, JSON `i3c7i.json` **1.041.852 bytes SHA256 `e6a30b3c2271a87b7404e4c0a9544f41c5ba0d265f946c8ece188fcc93952b5d`**. La lista íntegra de resultados individuales `per_seed` mantiene SHA256 canónica **`bed54546d4dbfba0f9fb55e5db6bbbc9b537708ae48f37f52bbb3ba8a76502e5`**, EXACTA a la primera corrida que llegó a generar datos. Esta identidad fue exigida en CI después del agregado estadístico.

**Fuentes comprobadas**: [manifest I3c7h original](resultados/e09i3c7h_resumen_y_hashes.json) con SHA por semilla, full JSON39.394.817bytes y artefacto14739997041; el auditor reejecutó cada una de las semillas **1800..1819** y exigió identidad de las SHA **por semilla y de los checkpoints neuronales completos B/P en ticks256/512** antes de cualquier ablación. **No se generaron datos de entrenamiento independientes ni nuevas semillas**.

## Ensayo y controles

- Mismo `C1ContextBrain` de ocho slots; modalidades B (feedback químico ligado a acción) y P (valencia original permutada por contexto). Fases A original y B invertida, dos contextos. Sobre cada checkpoint original se prueba **SHAM**, ocho ablaciones separadas `STW(slot_j)=0`, y `ALL_ZERO` con las8 STW0.
- **1.600 microbloques de8 ticks**, 1.280 ablaciones de una conexión,160 SHAM y160 ALL_ZERO, es decir **12.800 microticks**. La discrepancia con el conteo anterior800/640/6400 se explica y conserva en la **fe de erratas** del preregistro: fue aritmética de CI, no intervención genética ni cambio de diseño.
- Todos los experimentos locales usan `learn=False` y CHEM=(0,0,0,0). Se mide sólo la misma decisión a través de **ticks3–8** de un contexto constante, a partir del MISMO estado inicial; fuerza, LTW, susceptibilidad, estados ajenos y química no se cambian. La comparación química cero vs255 en `learn=False` es idéntica. La lesión de una STW ya0 es inerte; SHAM reproduce exactamente scores/acciones. Es un test de **necesidad local de señal STW**, NO de la regla de aprendizaje que la generó.
- **Puerta de sensibilidad superada:** ALL_ZERO cambió alguna elección en **20/20 semillas B de la fase invertida** (mínimo preregistrado12/20). El SHAM B tuvo **0,9667** de exactitud steady invertida (mínimo.65), P0.5000. Son micropruebas congeladas de8 ticks, **no** el benchmark ACTIVE de128 ticks del ensayo original.

## Resultado: tercera dimensión, utilidad y dirección del enlace

**Fase invertida (principal para localizar función), promedios de20 semillas:**

- **B:** anular un slot aleatorio alteró **10,73 %** de las acciones steady de las micropruebas, pero perdió neto **9,48 %** de las decisiones correctas por intervención×tick. **P:** las ablaciones alteraron **14,11 %** de las acciones (MÁS que B), pero el cambio neto de decisiones correctas fue **−0,57 %** —en promedio, eliminar enlaces en P resulta casi neutro o levemente beneficioso.
- **Contraste neto B−P = +10,05 puntos porcentuales** en pérdida de decisiones correctas por intervención×tick; IC95 bootstrap pareado seed-cluster2000 RNG60521 **[+6,61,+13,23 pp]**. **La tasa bruta de cambio de acción B−P es negativa** (−3,39pp, IC95 [−5,31,−1,46pp]). Por lo tanto **el número de conexiones que alteran decisiones NO equivale a utilidad causal alineada**.
- **Conexiones `aligned` según mapping/contexto**, definidas ANTES de lesiones como excitatoria hacia decisión correcta o inhibitoria hacia la incorrecta, ambas desde concepto del contexto: **B:** ablación perjudica acciones correctas en **40,00 %** de los ticks steady afectados por esta categoría. **P:** **26,88 %**. B−P en este grupo **+13,13 pp**, IC95 **[+6,04,+20,21 pp]**. Hay4 combinaciones aligned por seed/fase frente12 unaligned.
- **Conexiones `unaligned`:** B genera diferencia neta **−0,69 %**, casi ninguna alteración perjudicial; P **−9,72 %** neto (ablarlas mejora decisiones, señal de conexiones funcionalmente conflictivas en este checkpoint). Contraste B−P **+9,03 pp**, IC95 **[+6,32,+11,53 pp]**.
- En la **primera fase** también hay el patrón: B aligned41,88% vs P30,21%, y B unaligned−0,97% vs P−6,53% de pérdida neta; contraste general B−P en utilidad +7,08 pp IC95[+3,70,+10,78]. No seleccionar exclusivamente la fase o slots favorables.
- **Todas las8 dendritas conservaban fuerza positiva** en los checkpoints de estas ablations (atrofia CHEM2/3=0 del protocolo I3c7h); no interpretarlas como reconstrucción de realimentación C1. Una señal STW0 puede hacer inerte un slot incluso si su fuerza sigue2, y el núcleo puede propagar STW si fuerza0 en otros experimentos: no imponer filtro nuevo.

Los **intervalos por grupo aligned/unaligned** se implementaron en un **agregado analítico posterior a inspeccionar los datos**, utilizando los grupos ya definidos en el preregistro. No constituyen una segunda prueba ciega ni una hipótesis confirmatoria. Se exigió por CI que la SHA `per_seed` fuera idéntica a la primera simulación. Se cuentan **20 semillas como clusters**, no las miles de microdecisiones como independientes.

## Qué se demuestra y qué NO

**Comprobado bajo intervención:** hay conexiones cuya señal STW sostiene la elección correcta en un estado neuronal concreto, y la estructura funcional del circuito B es más coherente con el mapping aprendido que la de P. El alineamiento de signos temporalmente contingentes del ensayo I3c7h resulta en una microred con sinapsis que tienen consecuencias causales locales relevantes, no sólo pesos altos sin efecto.

**NO comprobado:** el mecanismo que decide *qué sinapsis reforzar* asigna de manera causalmente correcta un evento previo a su origen; una ablación local aislada no excluye redundancias, estado/saturación/WTA ni determina fidelidad del aprendizaje a la fisiología de un Norn. Tampoco demuestra memoria activa persistente: [I3c7h](E09_02I_I3C7H_RESULTADO_CONTINGENCIA.md) apenas obtuvo **2/20 semillas con steady≥.90 en ambas fases ACTIVE**, frente al gate G05≥18/20. Esta auditoría `learn=False` no reemplaza ese criterio.

## Correcciones y trazabilidad

- [CI #44986729926](https://github.com/mxlzz/Nilo_public/actions/runs/44986729926) falló por un test que esperaba40 en vez de80 microbloques por una semilla, luego corregido.
- [CI #44986812101](https://github.com/mxlzz/Nilo_public/actions/runs/44986812101) pasó7 tests y produjo el dataset completo, pero falló sólo el `assert` de volumen que esperaba800/640/6400 en vez de1600/1280/12800.
- [CI #44986928497](https://github.com/mxlzz/Nilo_public/actions/runs/44986928497) validó el dataset original por7 tests y el volumen corregido.
- [CI FINAL #44987034290](https://github.com/mxlzz/Nilo_public/actions/runs/44987034290) SUCCESS7 después de agregar ambos contrastes estructurales y pinnear **SHA idéntica de las20 microintervenciones**. Los fallos de infraestructura se conservan, no son resultados científicos negativos. La corrección estadística fue posterior al conocimiento del resultado; no se ocultó ni cambió la cohorte.

## Decisión de continuidad

**G-I3c7i-CHECKPOINT / SHAM / MICROINTERVENCIONES VALIDADA. Puertas informativas ALL_ZERO y baseline B superadas; efecto funcional local observado. G05/G09/G00-H ABIERTAS.**

La secuencia I3c7h→i ahora demuestra (a) la recompensa temporalmente alineada es operativamente necesaria para la discriminación del contexto frente a un signo permutado, y (b) determinadas señales sinápticas influyen localmente en las acciones coherentes con la tarea. **El cuello de botella principal restante es la persistencia ACTIVE sin refuerzo**, no simplemente si existe alguna respuesta aprendida.

**Siguiente decisión de método, NO experimentar automáticamente:** evaluar si el criterio G05 (128 ticks activos sin recompensa y≥18/20 semillas robustas tras reversión) corresponde a una propiedad necesaria de un agente autónomo cuya vida real recibe feedback intermitente, o si exige una clase de memoria que la microred C1 fija de8 dendritas carece de forma estructural. Antes de diseñar más, comparar **mecanismos ya disponibles en NeuroLab/C1** y posibles adaptaciones N explícitas, con costo, fidelidad y controles; no elegir gain, tasa, tamaño, más bloques o atrofia por éxito retroactivo.

Conservar semillas1400..1419 sin usar, `main` y Nilo0.7 intactos, PR#103 draft. **No afirmar G05 aprobada**.
