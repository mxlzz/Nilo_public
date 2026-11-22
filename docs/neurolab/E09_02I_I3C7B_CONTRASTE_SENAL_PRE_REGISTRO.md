# NeuroLab E09.02i–I3c.7b — preregistro: prueba de sensibilidad del circuito al refuerzo directo versus químico

**21-11-2026 · NL-EXP-I3c7b-v1 · PREREGISTRO ANTERIOR A CÓDIGO Y DATOS.** Dependencias: [I3c.7a](E09_02I_I3C7A_REUSO_CONTROLES_Y_CONTRASTE.md), [I3c.5d](E09_02I_I3C5D_RESULTADO_VENTANA_PRECOZ.md), [I3c.5e](E09_02I_I3C5E_RESULTADO_PUERTA_SENAL.md). **No es una prueba confirmatoria G05; no se alteran genes, neuronas ni magnitudes ya usadas en ensayos previos.**

## Pregunta falsable y controles existentes

¿Una sola oportunidad de feedback **directo** C1 (pulso neural255; referencia ya usada en E09g.5/E09g.10b) produce una señal/decisión diferente del control sin feedback en **el mismo estado y tick de lectura** en que el precursor químico (dosis80, tasa sintética40) dio respuesta STW insuficiente? Alternativas:
- H-S: el brazo directo produce algún cambio en la entrada real de Decision y/o acción de readout frente a N, y el precursor M no; la cadena química limita esta comparación de un pulso, **sin probar aprendizaje**.
- H-0: ninguno produce cambio funcional, aunque haya efecto numérico; el circuito limitado por intensidad/ventana/fortaleza no permite atribuir la falla sólo al puente químico.
- H-X: ambos cambian señal o elección; distinguir mecanismos sin optimización posterior.

Se **reutilizan** `C1ContextBrain`, `witness_step`, `inspect_synapses`, `selected_genes`, `add_environment_precursors`, `chemical_bridge_tick`, `decay_pool`, `update_c1_synapse`; NO implementar plasticidad nueva, regla de fuerza, migración ni emisor ficticio.

## Cohorte/cadena precomprometidas

- **20 semillas nuevas de desarrollo 1500..1519**. No usar semillas previas ni la cohorte **1400..1419**, reservada para una futura confirmación **separada**; una vez vistas estas 20, también son de desarrollo.
- Por semilla, `target=0,1`, dos mappings invertidos A/B para balancear acierto/error del **mismo** acto de tick4. **40 troncos físicos únicos**, 80 coordenadas evaluativas, **4 brazos N/M/C/F** para 320 ramas, todas clonadas del mismo `CoupledState` tras cuatro ticks del target sin feedback ni migration. `TRUNK_TICK=4`, `END_TICK=128`; el post-tronco siempre tiene distractor `1-target` durante124 ticks. No excluir episodios según salida inicial (si `None`, M/C/F no reciben refuerzo; reportar).
- **N:** sin precursor ni pulso directo, plasticidad normal del gen original y química nominal/decay.
- **M:** exactamente el precursor exógeno de I3 (`correct → pool33+1`, `incorrect → pool17`, dosis80) **antes del tick5**, con `CHEM` cerebral leída de fase anterior, receptor y reacciones después de cada tick y decay40. Plasticidad activa todos los ticks.
- **C:** sin precursor, pero aplicar `REWARD=(255,0,0,0)` o `PUNISHMENT=(0,255,0,0)` **sólo al paso neural del tick7**; la fase química conserva sus químicos originales sin pulso y avanza normalmente. Timing escogido **antes de datos** para coincidir con la **primera lectura de CHEM0/1 positiva observada en M en I3c.5d**, no calibrado por resultados de la cohorte nueva. Plasticidad activa todos los ticks. El nombre C significa *control positivo directo histórico del laboratorio*, NO autenticidad del metabolismo.
- **F:** recibe el MISMO precursor en tick5 y la MISMA trayectoria química, byte a byte, que M, pero tiene `learn=False` en todos los ticks; su dendrita y fuerza deben permanecer idénticas a tick4. Permite comprobar que cualquier cambio neural de M requiere plasticidad, sin confundir una acción diferente con el origen de la recompensa.
- Para las cuatro ramas, **signo** del reward se calcula UNA sola vez por el evaluador externo desde la decisión del tronco y mapping; jamás se pasa `target`, `mapping` ni `correct` al módulo neuronal, excepto una tupla de químicos externa con signo autorizado. `M/F` deben tener estado químico **exactamente idéntico en cada tick** (misma cantidad, orden y fuente de precursor), y `N/C` química idéntica en cada tick; si no, ABORTAR. No afirmar igualdad de intensidad de C y M.

## Métricas y pruebas

**Observación por tick de los 8 slots sinápticos:**
- estado químico leído por cerebro `CHEM0/1`, AUC y primer tick de química positiva;
- fuerza pre/post, número de slots strength0, efecto `numeric.reinforcement_effect` por slot y por fuente `target/distractor`, amplitud STW/LTW, número de slots *strength>0 con STW≥5*, primer tick con `type0/type1` o score distinto de N;
- entrada real de Decision antes del step con `dendrite_signal(previous_concept_outputs,STW,attenuation128)` por cada owner/clase, registrada por tick, comparada con `brain.step().scores` para verificar aritmética;
- decisiones de readout `learn=False`, cuatro ticks de target desde copia inmutable del estado, tras ticks **7, 9, 16, 128**, con evaluación de acierto A/B. El readout no debe modificar ninguna sinapsis. Contrastar **acción distinta** vs N por cada mapeo, y **puntos porcentuales de acierto** vs N, separados de distancias de peso.

**Controles de software**: mismos checkpoints SHA en cuatro ramas, misma acción original y signo del evaluador, 0 reward en N, 1 entrega por M/C/F salvo `None`, F inmutable, los pares de química idénticos en C/N y M/F, `inspect_synapses` coincide exactamente con 8 transiciones del brain en N/M/F; en C usar `update_c1_synapse` directamente para testigo del único override, sin modificar helpers de producción. Lecturas congeladas y timing exacto.

**Tratamiento:** medias/contrastes por semilla agrupando cuatro coordenadas `(2 targets×A/B)`, bootstrap pareado 2000 réplicas, seed **60517**, IC95; conservar casos sin efectos y denominador cero en forma null. Resultado de acción diferente y diferencia de exactitud se reportan ambos (pueden ser 0 aunque weights cambien). No seleccionar tiempos favorables posteriormente ni usar éxito numérico como G05.

**Variables no equiparables:** C entra directamente con255 durante un tick y no produce la misma química temporal ni dosis efectiva que M con precursor80 y reacciones; **por diseño esto es un control de sensibilidad, NO comparación de superioridad bajo la misma intervención**. La química M puede continuar en otros ticks; el directo C no. F cambia también la atrofia al congelar, por lo que sirve de testigo instrumental de aprendizaje, no contrafactual conductual perfecto. El pulso directo no es un input privilegiado de identidad de origen; Q tabular NO se usa.

## Decisiones de salida congeladas

- Si **C cambia señal/decisión y M no**, queda diagnosticada sensibilidad del circuito al control directo bajo este calendario; no autoriza cambiar ganancia a4 ni concluir aprendizaje.
- Si **C y M no cambian entrada/decisión**, un pulso es insuficiente, seguir con análisis de exposición **repetida** usando el `train_brain` de E09g.5 antes de diseñar nueva confirmación, sin ampliar estructura.
- Si **ambos cambian** señales, el siguiente estudio deberá distinguir permanencia y crédito, no escoger el modo que rinda más.

**G-I3c7b-CONTRATO** tests y JSON íntegro reproducible; **G-I3c7b-SENSIBILIDAD** sólo diagnóstico de señal; **G05/G09/G00-H permanecen ABIERTAS** aun con CI verde. Preservar datos por semilla, el SHA de configuración/código y resultados negativos, no tocar `main`, Nilo0.7 o genoma original, no merge PR103.
