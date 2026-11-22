# NeuroLab — priorización científica y contrato G05-INFO (22/11/2026)

**Estado:** evaluación documental completada; **G05-INFO.01 ESPECIFICADA, NO EJECUTADA**. No constituye preregistro de una nueva cohorte, aprobación de un nuevo mecanismo ni superación de G05. Se deriva de la [auditoría de alineación](AUDITORIA_ALINEACION_PREVIA_SIGUIENTE_ETAPA_20261122.md) y respeta el [objetivo #102](https://github.com/mxlzz/Nilo_public/issues/102), las [puertas originales](ETAPAS_00_09.md) y su [errata](E09_00R_RECONCILIACION_GATES_20261122.md). **Nilo 0.7, `main`, PR draft y semillas de confirmación intactos.**

## 1. Regla de selección y decisión

**Objetivo rector:** identificar, no presumir, la capacidad neuronal mínima para adquirir, conservar, modificar, transferir y reorganizar asociaciones mediante experiencia en un **cerebro aislado**. La reproducción fiel del C1 histórico es la línea H separada; aquí N es un modelo experimental, no un organismo.

Evaluación de alternativas a partir de evidencia y costo de oportunidad:

1. **G05 — crédito temporal bajo distractores: PRIORIDAD 1 para diagnóstico de identificabilidad.** Ataca una puerta original concreta sin superar, tiene [resultado reproducible g.10b](E09_02G_10B_RESULTADO_DEMORA_DISTRACTORES.md), [diagnóstico contrafactual g.10c](E09_02G_10C_RESULTADO_ELEGIBILIDAD.md), una posible asimetría material de información y varios controles existentes reutilizables. El próximo paso NO es inventar una traza: primero determinar si los datos disponibles bastan para asignar recompensa de manera atribuible.
2. **Memoria durable ACTIVE tras inversión: PRIORIDAD 2, CONGELADA.** Es central para el objetivo, pero tras [I3c7g/j/k](E09_02I_I3C7K_RESULTADO_TRANSFERENCIA.md) el oráculo de copiar STW→LTW mejoró ~4,90pp, por debajo del criterio de suficiencia 10pp. No hay todavía una razón diferenciada para desplegar consolidación multiescala, EWC, replay ni variar tasas. Reabrir solo ante hipótesis distinta y un diagnóstico que prediga un cambio decisivo.
3. **Formación de representaciones: PRIORIDAD 3, CONFIGURACIÓN NR01 DETENIDA.** [NR01.06](NR01_04_06_RESULTADO_Y_CIERRE_20261122.md): KMeans4 +3,53pp respecto al mejor control simple, menor que 5pp fijados, más memoria, peor reversión; ART excede capacidad en 104/120 condiciones. Nada de tuning ni uso de semillas 24000..24019.
4. **H histórica:** no compite por métricas N; consultar de manera **acotada** el scheduler y la procedencia de la química real C1 solo si cambia una inferencia del diagnóstico G05. No afirmar que los mecanismos de microC1 reproducen todo C1.

**Decisión:** elegir una sola unidad de **factibilidad informacional, G05-INFO.01**, antes de gastar recursos en experimentos. Si la tarea no es identificable bajo el flujo sensorial permitido o se resuelve trivialmente por una clave temporal diseñada, **rediseñar el desafío antes de comparar modelos**. Si no surge pregunta discriminante, proponer **PAUSA**, no nuevo mecanismo.

## 2. Evidencia decisiva que motiva el diagnóstico

- **g.10b:** la microred C logra A=0,8896, B=0,8472 y solo **16/40 semillas** con ambas fases≥0,90; la compuerta IG es peor (6/40). Congelada ~azar. La tabla Q consigue 40/40, PERO el runner [`e09_delayed_distractors_protocol.py`](../../experiments/neurolab/e09_delayed_distractors_protocol.py) confirma que el evaluador le entrega `stored=(target,action_index)`, con `target` y posición de acción puntuable ya conocidos. Además **Q solo elige una vez, en el cuarto tick**, mientras C/IG eligen en **cada tick** y no ven marcas de ensayo. **Q es oráculo privilegiado, no baseline equivalente**. No usar su 100% para deducir superioridad de un algoritmo tabular con mismas observaciones.
- **g.10c:** 4800/4800 eventos mantienen susceptibilidad positiva de la conexión objetivo cuando llega el pulso; no falta toda la memoria local. Con 3 distractores, el cambio químico en STW deja de ser selectivo (objetivo y distractor reciben efectos de incidencia semejante), por lo que **añadir otra variable de elegibilidad indiscriminadamente podría ser redundante**. Es un diagnóstico sobre estados contrafactuales, no demostración de la causa única del fallo conductual.
- **Límite más profundo del banco:** el programador conoce `TARGET_TICKS=4`, secuencias objetivo→1..3 distractores→pulso y mapeo oculto. La mente observa contexto, su propia acción y químicos, pero no un indicador de «esta es la decisión puntuada» ni `target` de origen. **No está demostrado** si un aprendiz sin señales privilegiadas puede inferir ese evento mediante regularidades temporales; tampoco está demostrado que sea imposible. Al mismo tiempo, una regla codificada «recompensar siempre la cuarta acción» podría explotar el diseño artificial sin resolver crédito temporal general.

## 3. Alternativas existentes: pertinencia y límites verificados

**No implementar nueva familia todavía.** Las siguientes soluciones ya existen y deben servir como referencias, no como promesas de rendimiento en esta tarea:

- **Elegibilidad temporal tabular / SARSA(λ), TD(λ):** método clásico de asignación a estados o acciones anteriores; el libro de [Sutton y Barto, 2ª edición, cap. 12](https://web.stanford.edu/class/psych209/Readings/SuttonBartoIPRLBook2ndEd.pdf) y [Sutton 1984](https://gwern.net/doc/reinforcement-learning/model-free/1984-sutton.pdf) distinguen demora conocida de incertidumbre causal por demora desconocida. Existe implementación reutilizable de **SARSALambda** y **TrueOnlineSARSALambda** en [MushroomRL](https://mushroomrl.readthedocs.io/en/latest/source/mushroom_rl.algorithms.value.html) ([repositorio](https://github.com/MushroomRL/mushroom-rl)), pero **no se comprobó compatibilidad con el protocolo por tick** ni costo de dependencias. No asumir que una implementación TD ordinaria resuelve una asignación causal no identificable.
- **Tres factores con marcas sinápticas:** [revisión 2025 sobre eligibility traces](https://pubmed.ncbi.nlm.nih.gov/39965463/) y [revisión 2018 sobre reglas de tres factores](https://pmc.ncbi.nlm.nih.gov/articles/PMC6079224/) fundamentan el mecanismo de pre/postactividad y refuerzo demorado; el circuito microC1 **ya tiene susceptibilidad local** y debe compararse antes de copiar una regla genérica.
- **e-prop:** [Bellec et al. 2020](https://www.nature.com/articles/s41467-020-17236-y) usa elegibilidad y señales de aprendizaje en redes recurrentes de picos; pertinente a crédito de larga duración, pero **no plug-and-play** para un circuito de seis unidades/GEN-C1, con distinto alcance y mayor costo conceptual.
- **Brian2:** incluye un [ejemplo público de aprendizaje con dopamina](https://brian2.readthedocs.io/en/latest/examples/frompapers.Izhikevich_2007.html). Relevante como referencia sináptica, no prueba un sustituto C1 listo ni justifica migrar el motor.
- **Memoria explícita de eventos causal:** control elemental de bajo costo en un entorno donde la procedencia sea legítimamente observada o reconstruida por el controlador. Si recibe IDs de ensayo desde el evaluador, **es solo un techo oracular** y no un comparador justo.

**Resultado de alternativas:** ya hay métodos para ensayar crédito demorado. La cuestión no es desarrollar uno nuevo, sino comprobar si tenemos un desafío cuya solución exija una capacidad discriminante en condiciones informacionalmente justas.

## 4. Contrato verificable — G05-INFO.01 (siguiente unidad, SIN ensayo científico)

### 4.1 Pregunta

> Con exactamente el flujo que recibe la microred (percepción de contexto en cada tick, acción propia y pulso químico con su instante), ¿qué procedencia de recompensa puede reconstruirse y qué información permanece latente? ¿Es el banco g.10b útil para distinguir crédito temporal o evalúa principalmente un patrón temporal codificado por el diseñador?

### 4.2 Matriz de acceso a información a cerrar

Separar campos:
- **Públicos al controlador C/IG:** `context_t`∈{0,1}, su decisión `action_t`, pulso `chemicals_t` y momento relativo inferible de su propia secuencia de ticks; estado neuronal interno y eventos de plasticidad locales.
- **Privados del evaluador:** `mapping`, `target` puntuable, `delay` sorteado, `TARGET_TICKS` como norma explícita de puntuación, marcas de inicio/fin de ensayo y `stored=(target,action)` causal. **Matiz:** una constante pública en el código no es necesariamente una señal entregada al modelo; se debe declarar qué conocimiento del protocolo puede presuponerse sin favoritismos.
- **Q histórico:** recibe `target` de origen, `action` y evento puntuable directamente del evaluador; ejecuta solo la acción puntuada y aprende su premio a posteriori. No cumple igualdad de información ni reloj.

### 4.3 Verificación de identificabilidad (solo análisis y oráculos, no modelos nuevos)

1. Auditar la traza `(context_t, action_t, pulse_t)` por tick, cuál agente decide y qué datos llegan realmente a cada interfaz. **No acceder al mapeo durante una decisión** ni usar el flag `ok` como input del aprendizaje. Tomar la señal de premio únicamente después de la elección.
2. Construir dos ejemplos manuales/fixtures analíticos de segmentos **observacionalmente distinguibles** y, si existen, dos historias con el **mismo pasado observable completo hasta el pulso** y distinta atribución causal latente. Si tal par existe y ambas atribuciones importan, no afirmar identificabilidad perfecta; especificar el límite por clase de historias.
3. Evaluar si transiciones de contexto, historial de acciones, tiempo desde último pulso o patrón fijo de cuatro ticks revelan el objetivo de modo trivial. Diseñar control de **etiquetas temporales permutadas** conservando el contenido sensorial y recompensa agregados; si el predictor solo aprendió el calendario del banco, no lo llamar «crédito causal general».
4. Establecer **tres clases de baseline con igualdad de información** para una posible futura comparación, **sin implementarlas aún**: (i) atribución al último par estado/acción observable; (ii) elegibilidad temporal online de pares estado/acción con decaimiento, sin ID de origen; (iii) buffer de los últimos K eventos **generados por el controlador**, sin campos del evaluador. Mantener a Q privilegiado exclusivamente como **oráculo**, nunca como baseline justo. C/IG deben seguir el mismo reloj y políticas de feedback; contabilizar todos los ticks y bytes.
5. Verificar si el esquema de pulso nulo ante `action is None` oculta límites de ensayo de manera desigual y si las decisiones de distractores de C/IG (frente a inactividad de Q) cambian fundamentalmente la pregunta. Los controles futuros deben actuar **todos los ticks**, con recompensa calculada solo tras la acción puntuable oculta, igual que la microred.
6. Elaborar al final una **decisión explícita**: (A) atribución suficientemente identificable con el flujo actual y prueba discriminante viable; (B) atribución subdeterminada, requiere nueva observación legítima o pregunta distinta; (C) inferencia trivial por calendario artificial, requiere un protocolo que no entregue la respuesta vía timing. Registrar ejemplos, límites de la prueba y evidencia por ruta. **No basta una afirmación intuitiva de identificabilidad.**

### 4.4 Puerta de salida de G05-INFO.01

**G05-INFO.01 documental solo se declara COMPLETA** cuando existen: matriz de acceso revisada contra runner/cerebro, casos analíticos verificables, evaluación de riesgo de atajos, selección de control más simple sin privilegios, costo estimado de memoria y decisión A/B/C fundada. **No se transfiere automáticamente a G05 ni se autoriza corrida por una descripción.**

Si (A): proponer un **nuevo preregistro separado**, con nuevos datos de desarrollo, una confirmación verdaderamente cerrada, métricas de atribución y de conducta, conteo de errores con distractores, reversión, memoria/CPU y stop rule. Evitar reutilizar 120..159 como confirmación; 1400..1419 históricas y 24000..24019 NR01 se mantienen sin usar.
Si (B)/(C): **rediseñar primero el contrato del banco**, justificar la información sensorial adicional o romper el atajo temporal antes de elegir algoritmo. Si el nuevo diseño ya puede ser resuelto por un baseline trivial, detener línea N o redefinir hipótesis, sin tuning retrospectivo.
En todos los casos: antes de cada unidad, contrastar pregunta original, etapa y evidencia; registrar también que una pausa es decisión válida.

## 5. Decisión de alcance y conservación

- **Etapa actual:** priorización documental terminada; comienza como siguiente unidad `G05-INFO.01` solo análisis/validación de interfaz.
- **No autorizado por este texto:** cambiar `C1ContextBrain`, implementar nuevo algoritmo, correr cohorte científica, tocar Nilo 0.7/`main`, publicar binarios propietarios, fusionar PR draft ni consumir holdouts.
- **Condición para reabrir arquitectura N:** primero factibilidad informacional; luego hipótesis discriminante, baselines pares, preregistro, costo y evidencia causal. Sin esa secuencia se conserva el STOP NR01 y el cierre parcial E09.
