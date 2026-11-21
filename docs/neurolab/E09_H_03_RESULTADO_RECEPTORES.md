# E09h.3 — resultado de transferencia aislada de receptor C1 a locus

**Fecha:** 2026-11-21. [Preregistro original](E09_H_03_RECEPTORES_QUIMICOS_PRE_REGISTRO.md) antes del código, con **errata explícita** en receptor126 explicada abajo. Fuente primaria: mismos EXE y GEN del CD verificados por SHA256 y examinados localmente; no se redistribuyen.

## Evidencia ejecutada

- [Implementación pura](../../experiments/neurolab/e09_historical_receptor.py) de la etapa local de receptor, [tests sin binarios propietarios](../../experiments/neurolab/tests/test_e09_historical_receptor.py) y [resultados derivados de los receptores originales](resultados/e09h3_receptores_genoma_original.json).
- [CI #44945435224](https://github.com/mxlzz/Nilo_public/actions/runs/44945435224), commit verificado `5b04374e5f80a27e5a01c0bd190c9a9f12832e2c`: **success, 332 tests, 2 expectedFailure históricos**. Un run previo [#44945392755](https://github.com/mxlzz/Nilo_public/actions/runs/44945392755) falló por un fixture erróneo: no ocultarlo.
- El parser aislado recupera **43 genes receptores** del GEN original; seis apuntan al cerebro. Los datos relevantes permanecen idénticos a [E00](E00_MAPA_NEUROQUIMICO_C1.md).

## Aritmética aislada

Para cada receptor con química no nula, `available=max(0, pool[chem]-threshold)`; `effect=gain` si `flags&2` y hay química disponible; en caso contrario `effect=(available*gain)>>8`. `flags&1` resta el efecto de `nominal` con piso0; sin ese flag, suma con techo255. **El resultado es el byte que se escribiría en un locus**; todavía no representa concentración química ni actividad neuronal medida en el juego.

- **Reward49 receptor88** y **Punishment50 receptor89**: ambos enlazados genéticamente al lóbulo Decision 6, loci13/14, nominal0 gain255. Con concentración12 en cada químico, el valor calculado es **11**, no 12, por división entera de 8 bits.
- **ConASH52 receptor126**, lóbulo Concept 8 locus14, nominal4 gain255 flags1: concentración5 produce **0**.
- **DecASH1=53 receptor127**, lóbulo Decision 6 locus15, nominal16 gain255 flags1: concentración12 produce **5**.
- **DecASH2=70 receptor128**, lóbulo Decision 6 locus16, nominal16 gain255 flags1: concentración0 devuelve **16**.
- **Reinforcement51 receptor129**, lóbulo Concept 8 locus13, nominal0 gain255 flags0: concentración0 devuelve **0**.

## Errata del oráculo preregistrado (sin cambiar preregistro)

El documento de preregistro decía para receptor126, concentración5, nominal4 y gain255, resultado esperado **1**. Eso es **incorrecto**: `(5*255)>>8 = 4`, `max(0,4-4)=0`. Al ejecutar el test inicial, CI detectó `0 != 1`. Se corrigió **solo el valor esperado del test**, no la regla C1 ni el genoma; [run exitoso](https://github.com/mxlzz/Nilo_public/actions/runs/44945435224). Se preserva el error original para trazabilidad y para no aparentar un preregistro perfecto.

## Qué significa para NeuroLab

La secuencia reconstruida hasta ahora es: **reacciones generan y consumen químicos → receptores muestrean concentraciones disponibles en otra etapa/ciclo → transferencias de 8 bits condicionan loci cerebrales → reglas neuronales/sinápticas C1 usan estos valores**. En la ruta normal verificada de criatura, el cerebro se procesa antes que química, y en una llamada química los receptores se procesan antes que las reacciones. La cronología impide tratar una etiqueta externa de "respuesta correcta" como reproducción fiel de la química C1.

**Límites:** no se ha probado toda la vinculación de punteros de loci a `CHEM0..3` del cerebro, el orden preciso de todos los modos del scheduler, ni la dinámica global de reacciones/emisores/recepción en tiempo real. El test es una transferencia aislada y estática, no emulación completa del Norn. G00-H/G05/G09 global permanecen abiertas, sin integración en Nilo.

**Siguiente paso útil y limitado:** E09h.4, verificar el enlace **receptor del genoma → puntero/locus del lóbulo → variable CHEM de SVRule**, usando la ruta de construcción del cerebro en el ejecutable, sin diseñar otras neuronas. No alterar g.10 ni la bioquímica aislada antes de contar con esa evidencia.
