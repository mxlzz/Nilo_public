# NeuroLab I3c.7b — resultado: el refuerzo directo genera conducta breve, el químico no

**21-11-2026. ESTUDIO MECANÍSTICO PREREGISTRADO, NO CONFIRMATORIO G05.** [Preregistro anterior al código](E09_02I_I3C7B_CONTRASTE_SENAL_PRE_REGISTRO.md) · [runner](../../experiments/neurolab/e09_i3c7b_paired_signal.py) · [CI #44968344691](https://github.com/mxlzz/Nilo_public/actions/runs/44968344691) **SUCCESS 6/6 tests**, artefacto ZIP **`neurolab-i3c7b-chemical-direct-four-arms` ID14733055528**, con **12.128.800 bytes del JSON íntegro**, SHA256 del JSON **`2660ba63b866abfff469d754ff88cab8941b215b1078a652ddc52dfca0cce8a6`**. Verificado por descarga, lectura y conteos del ZIP íntegro, no sólo logs abreviados. No se modificó ninguna regla C1, genética, dosis, ganancia ni tamaño de red.

## Contrato y población

- **20 semillas nuevas1500..1519** (desarrollo), 40 troncos únicos tick4, 80 coordenadas `seed×target×mapping A/B`, 320 ramas `N` neutra, `M` química con precursor80 en tick5, `C` directo255 sólo tick7, `F` misma química que M pero sin plasticidad.
- Misma decisión inicial antes de bifurcación, signos 40 correctos/40 incorrectos, cero acciones `None`. **M/F** química completa idéntica por tick y **N/C** también idéntica; testigo sináptico y scores de `C1ContextBrain` exactos. Cuatro lecturas `learn=False` tras ticks7,9,16,128, testigos de fuerza/STW/score cada tick.
- **No es igualación de intensidad:** C entrega CHEM255 directamente en el paso neuronal una sola vez, M entrega precursor80 en el pool y su lectura neural comienza dos ticks después de la inyección con amplitudes mucho menores. Los brazos sólo son comparables en *decisión original, tiempo de primer pulso efectivo, contexto de distractor y estado inicial*. F retiene conexiones por estar congelado y no es un contrafactual de conducta equiparado con M.

## Resultado primario de sensibilidad

- **C refuerzo directo:** 80/80 ramas con efecto sináptico numérico; **60/80** alcanzaron al menos una dendrita con `strength>0` y STW≥5; **36/80** mostraron alguna entrada `type0/type1` y algún score de Decision distinto de N. En lecturas de ticks **7 y 9**, **22/80 elecciones cambiaron** respecto de N: **20** mejoraron y **2** empeoraron. Exactitud **0,725**, contra N **0,500**, diferencia pareada **+0,225** (IC95 bootstrap por 20 semillas **[+0,100, +0,350]**). Eso es efecto inmediato de una intervención de magnitud255, no retención ni aprendizaje general.
- **M precursor químico:** 80 pulsos, **20/80** ramas con efecto numérico unitario, total20; **0/80** con STW≥5 en fuerza positiva, **0/80** con diferencias de entrada, score o acción respecto a N; exactitud **0,500** en todas las lecturas.
- **N:** cero efecto y cero pulso, exactitud0,500. **F:** plasticidad/desgaste completamente congelados, 8/8 dendritas conservan fuerza positiva hasta tick128, pero sin STW/entrada funcional y exactitud0,500. Los scores internos en F pueden diferir de N por la distinta **trayectoria neuronal ocasionada por conservar conexiones**; no confundirlo con efecto positivo de aprendizaje.

**No atribución causal individual garantizada:** el efecto sináptico directo total fue **1196 unidades** distribuidas **724 sobre fuentes del objetivo** y **472 sobre fuentes del distractor**. Por eso un resultado conductual inmediato del directo **no demuestra** que haya acreditado correctamente cada conexión causante de la decisión. En M el total fue20 y todas las unidades correspondieron a fuente objetivo (etiqueta de fuente, no mecanismo causal individual).

## Desaparición de la señal: auditoría exploratoria del ZIP completo

La siguiente inspección es **post hoc, no prueba independiente**. Para cada brazo C, a tick7 **80/80** tienen alguna STW positiva y **60/80** cumplen STW≥5 en alguna dendrita con fuerza positiva. En ticks8–9 la señal persiste en esas60; **36/80** episodios generan entrada/score no nulos frente a N. **A tick10**, para los **80/80** episodios C, M y N las ocho dendritas quedan **strength0**, su STW funcional desaparece y ninguna retiene LTW positiva. La entrada `type` calculada **al inicio** de tick10 puede seguir siendo positiva en 36/80 (lee el estado anterior), pero después de la actualización de fuerza y borrado no queda señal; a tick11 entradas positivas0/80.

En lectura congelada tras **tick16 y tick128**: **0/80 elecciones diferentes** respecto de N para C y M; exactitud0,500, ventaja0 (bootstrap [0,0]). Los circuitos no conservaron la mejora inmediata. El testigo demuestra un cuello de botella de **persistencia de conexión/ventana LTW**, no que el original C1 sea incapaz de aprender: el genoma y motor originales tienen migración, fuentes químicas endógenas y otra escala de conectividad.

**Observación de control crucial:** F conserva8/8 dendritas por no ejecutar ni la regla de pérdida, pero sigue en 0,5 sin STW porque no tiene plasticidad; el control sirve para atribución instrumental, **no demuestra que mantener fuerza por sí sola produzca memoria**.

## Decisión

**G-I3c7b-CONTRATO VALIDADA, G-I3c7b-SENSIBILIDAD observada en C pero de alcance transitorio. G05/G09/G00-H ABIERTAS.** El modelo responde a un premio directo suficientemente intenso sin añadir neuronas; el químico sintético80 no cruza el umbral de propagación. Un solo pulso no consolida la mejora cuando las ocho conexiones se agotan en tick10. **No aumentar ganancia ni dopar el metabolismo**.

Siguiente unidad **I3c.7c**, preregistrada expresamente como auditoría **post hoc** del mismo ZIP: fijar huella de origen, reejecutar el estudio sin modificar parámetros, comprobar todas las transiciones en ticks7..11, preservar diagnóstico y no consumir el holdout1400..1419. Luego decidir un ensayo *multiepisodio* basado en `train_brain` histórico de E09g.5, con alternativas de pérdida/migración analizadas sin implementación automática.
