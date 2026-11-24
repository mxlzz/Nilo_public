# NeuroLab E09.02i–I3c.7k — resultado: transferir el contenido STW a LTW es útil, pero INSUFICIENTE para justificar una regla nueva

**22/11/2026. EXPERIMENTO POST HOC, intervención oráculo artificial sobre cohorte ya vista.** [Preregistro previo a la intervención](E09_02I_I3C7K_TRANSFERENCIA_CONTENIDO_PRE_REGISTRO.md) · [runner](../../experiments/neurolab/e09_i3c7k_transfer_stw_to_ltw.py) · [CI final #44987744410](https://github.com/mxlzz/Nilo_public/actions/runs/44987744410) **SUCCESS 5/5 tests, 20 semillas originales**, artefacto `neurolab-i3c7k-stw-content-instant-ltw-capacity` ID **14740013286**. JSON completo `i3c7k.json` **82.959 bytes**, SHA256 **`d67d77d09844ab6699d3e2d56434f21b91d56fb79fb05c882cdd5ea9f4b4fccf`**, arreglo `per_seed` SHA256 canónica **`b87545a66e2811c20707f57c40417e092e19156058b26297aefd34846fa3fe5c`**. Se descargó y verificó el artefacto y sus resúmenes después de CI, sin excluir casos.

## Qué se comparó

- Los20 estados M0 LONG de la **misma cohorte de desarrollo1700..1719** de [I3c.7g](E09_02I_I3C7G_RESULTADO_HORIZONTE.md), B invertida terminando tick896. [Huellas fuente por semilla](resultados/e09i3c7g_fuente_huellas.json) verificadas reejecutando `run_seed` original; adicionalmente comprobados **todos los 640 frames de B y vector `strength,STW,LTW` exactos** del checkpoint reconstruido. No hay nuevos datos independientes de entrenamiento, modificaciones genéticas ni redes nuevas.
- **S** original/sham sin alteración. **C**, única operación sobre clone: `LTW_i := STW_i` para sus8 conexiones, desde el estado propio. **X**, control de igual magnitud y mismo multiconjunto completo: `LTW_i := STW_{(i+4) mod8}`, intercambia propietarios Decision de la información. Mismo STW original, química, fuerza, susceptibilidad, neurona y eventos en los tres estados iniciales. **F** control frozen del original.
- Lectura `ACTIVE-NOREWARD` de128 ticks con el motor original, mismo holdout B por seed. El estado químico residual legítimo sigue procesándose, no se inyectan nuevos premios. Se comprobaron **128 elecciones FROZEN idénticas** bajo S/C/X para cada seed y exactitud media FROZEN idéntica **0,9271**. Por eso LTW no cambió directamente los inputs de decisión: la variación sólo se manifiesta cuando las reglas sinápticas continúan y STW se relaja hacia LTW.
- Todos los resultados tienen seed como cluster bootstrap pareado 2000 réplicas RNG60522; no se trataron ticks como independientes.

## Resultado primario (fase invertida, ACTIVE, 20 semillas)

- **S:** steady accuracy **0,8370**. **C:** **0,88594**. **X:** **0,63125**.
- **C−S = +0,04896** (IC95 por seed **[+0,00833,+0,08906]**). Señal positiva y pequeña, **menor que el umbral preregistrado de +0,10**. El IC superior tampoco llega a+0,10. **Puerta de suficiencia del mecanismo NO SUPERADA**, aunque el IC no incluya0.
- **C−X = +0,25469** (IC95 **[+0,13438,+0,36771]**). La misma cantidad total de pesos LTW reubicada al otro owner empeora notablemente la discriminación. **S−X = +0,20573** (IC95 [+0,09844,+0,30573]).
- Para C comparado con S: semillas con `steady≥0,90` **10/20 frente8/20** (conteo sólo en fase invertida; **NO criterio de G05 en ambas fases**). X3/20. FROZEN S/C/X idéntica0,9271.
- **Precisión ACTIVE por cuartos de32 ticks, post hoc descriptiva**: S **0,8234→0,8406→0,6844→0,7281**; C **0,8000→0,8328→0,7766→0,8344**; X **0,6844→0,7484→0,5281→0,4641**. El patrón C mejora sobre S hacia el final, pero no debe sustituir la métrica primaria ni seleccionar sólo la ventana conveniente.
- Promedio final de conexiones vivas con STW≥5: S **3,80**, C **4,55**, X **5,55**. **El brazo con MÁS STW funcional según simple umbral (X) rinde mucho peor**. Esto refuerza la distinción entre cantidad de señal y su **distribución direccional útil**.

## Interpretación estricta

El test muestra que preservar el patrón STW en LTW es **relevante para la memoria activa** y que una distribución incorrecta de pesos puede ser peor que una cantidad menor de pesos. **Pero el oráculo que copia instantáneamente ocho STW a LTW no alcanza el efecto mínimo preregistrado**. Tampoco implementa una regla que el agente pueda ejecutar, por lo que incluso un gran acierto de C no equivaldría a aprendizaje autónomo ni restauración C1 histórica.

Este es el tercer hallazgo coherente de la familia:
- I3c7g: aumentar oportunidades de `LTW_rate128` y producir LTW≥5 no mejoró retención.
- I3c7j: análisis de márgenes LTW-only reveló que M0 LONG no favorece ambos contextos en ninguna semilla, y D0 LONG aun con todos los pesos≥5 tiene márgenes iguales a0 por poca diferenciación. Este análisis era post hoc.
- I3c7k: **forzar transferencia del patrón funcional** mejora un poco, pero no basta; intercambiarlo de owner anula buena parte de la capacidad. No hay justificación para incrementar simplemente magnitud/número de sinapsis o introducir una copia STW→LTW como solución.

**Limitaciones:** el control X reubica peso entre propietarios y altera sus trayectorias después del inicio, así que no es un contrafactual «todo igual excepto asociación» a lo largo de todo el holdout; sí comparte magnitud, checkpoint y química iniciales. El oráculo C **no es un mecanismo histórico ni físicamente local** demostrado. Un éxito promedio de un mini-modelo no prueba memoria vital del Norn original. G05 tiene gate de≥18/20 semillas robustas en ambas fases ACTIVE, sin intervención de memoria externa; sigue **ABIERTA**.

## Decisión estratégica tras ensayo

**G-I3c7k-SOFTWARE VALIDADA; G-I3c7k-SUFICIENCIA NO ALCANZADA; G05/G09/G00-H ABIERTAS.** Con las pruebas e/f/g/h/i/j/k, **el retorno científico de seguir probando ajustes de STW/LTW, duración, tasas, fuerza o cantidad de contactos a ciegas es bajo**. Se propone **CONGELAR la microred fija de8 contactos como benchmark negativo y testigo**; no eliminarla ni fusionar PR experimental. No implementar un algoritmo de consolidación sólo porque pueda dar una mejora local. Si el proyecto prosigue:
1. Mantener la línea **H histórica** como auditoría separada, sin generalizar la fisiología original desde esta topología reducida.
2. Para la línea **N**, exigir antes de desarrollos una definición **funcional de memoria durable y crédito** independiente de C1: fuente de recompensa, señal de elegibilidad y qué contenido deberá proteger frente a reversión sin «congelar» sinapsis. Comparar candidatos existentes en vez de inventar tasas ad hoc.
3. Desarrollar sólo una alternativa si supera **un ensayo de suficiencia y un control de complejidad** con preregistro nuevo y **cohorte genuinamente independiente**. La reserva1400..1419 sigue sin consumirse y no debe usarse para diseño/ajuste.

No se alteraron `main`, Nilo0.7, C1ContextBrain original ni PR103 draft. El experimento concluye con criterio negativo, no con otra lista automática de parámetros.
