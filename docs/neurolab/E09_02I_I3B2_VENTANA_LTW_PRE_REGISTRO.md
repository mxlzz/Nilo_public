# E09.02i-I3b.2 — preregistro ANTES de código: cruce de ventana LTW tick128

**Fecha:** 2026-11-21. **Estado:** preregistrado antes de implementar y ejecutar. Se desprende de [I3b.1](E09_02I_I3B1_RESULTADO_RAMAS.md). Es un diagnóstico mecanístico nuevo de **línea N**, sin pretensión de fiel temporalidad real de Creatures y sin resolver G05/G09.

## Hallazgo que motiva el ensayo, sin atribución indebida

I3b.1 terminó entre ticks50 y52; la regla **ltw_rate=128** de las sinapsis Decision (genome original ya registrado en C1Synapse) condiciona update_LTWat tick%128==0. Por tanto, la LTW nula de I3b.1 es una limitación estructural de su ventana. No atribuirla a «química débil» o «C1 incapaz de consolidar».

## Hipótesis contrastables

H-GATE: un precursor químico idéntico y administrado antes del límite puede producir refuerzo STW antes de tick128 y un cambio LTW en tick128; administrarlo más tarde traslada la primera oportunidad de consolidar hasta tick256 (si la STW persiste), bajo la regla de discretización observada. No se garantiza que ocurra: depende de susceptibilidad y estado.
H-AMP: ganancia artificial4 puede aumentar probabilidad/magnitud de cambio LTW frente a ganancia1, sin convertir la ganancia en un mecanismo histórico.
H-NULL: ningún brazo altera LTW en tick128; registrar resultado nulo, incluyendo señales previas y por qué.

## Condiciones CONGELADAS

- **20 semillas nuevas400..419**, dos objetivos0/1, dos mappings A/B, **d=3 fijo** para separar la llegada temprana y tardía tres ticks. **80 episodios pareados** (20×2×2) con cinco ramas N, E1, L1, E4, L4, mismos nombres y semántica que I3b.1.
- Tronco sin feedback ni metas: **120 ticks** de contextos 0/1 alternados en bloques de8 (15 bloques), luego **4 ticks del objetivo** y se fija la cuarta acción. El estado común termina exactamente en **tick124**; ninguna recompensa antes de clonarlo, y todas las ramas incluyen idéntico estado del cerebro y química.
- Las ramas E reciben una única dosis precursora80 antes del primer distractor **tick125**; las ramas L reciben la misma dosis antes del cuarto tick de contexto distractor **tick128**; N no recibe nada. Se mantienen tasas sintéticas40 para todas las 256 sustancias, gen reacciones57/71/111/112, receptores88/89/126..129, sin emisores automáticos. La recompensa se calcula por evaluación de **la acción común** con mapping A/B: correcto→ químicos33 y1, incorrecto→químico17, sin acción→no se inyecta.
- Procesar cuatro ticks de distractor más ocho ticks de distractor sin nuevo precursor (total12, estados hasta tick136); medir **estado LTW en tick127, tick128 y tick136** y efectos STW/chem previos. Cuatro ticks finales de lectura del contexto objetivo sin plasticidad hasta tick140; no extrapolar a retención duradera.
- Ganancia CHEM0/1 exclusivamente:1 normal o4 contrafactual sintético, CHEM2/3 no cambia. Las ramas E1/E4 y L1/L4 deben tener **misma trayectoria de pool y receptores**, y misma dosis bajo diferente gain.
- **No se cambian** reglas C1, pesos, tasas, redes, dosis, I3 ni I3b1. Se reutiliza witness_step y el par de estados iniciales exactos, con tests y CI, registrando eventos nulos y negativos.

## Mediciones y puerta

- Indicador primario: cambio ABSOLUTO LTW en 8 dendritas respecto al control N **exactamente en tick128**, por rama, especialmente contraste pareado E4−L4, separado por signo correcto/incorrecto y contexto objetivo/distractor. Informar suma y número de sinapsis que cambian. No asignar signo a mecanismo de causa de acción.
- Acompañar CHEM0/1 antes de cada paso, STW y susceptibilidad pre-tick, efecto de refuerzo por conexión en ticks125–130, de manera que un resultado nulo pueda discriminar ausencia de señal vs indisponibilidad del gate.
- Variables secundarias: diferencia LTW al tick136, distancia STW al tick128 y136, lectura de acción al tick140, cambios por rama E1/L1 y E4/L4. Analizar con medias apareadas por **20 clusters semilla** e IC bootstrap95% 2000 réplicas PRNG60513. Informar todas las ochenta observaciones y todos los nulls, no ignorar valores cero.
- **G-I3b2-WIRING:** garantía de estado troncal idéntico, misma química bajo ganancia diferente, dosis única, regla LTW sin alterar, test de equivalencia de witness y cálculo de ticks124→125/128. **G-I3b2-OBSERVACIÓN**: JSON completo y evidencia CI; la puerta de aprendizaje G05/G09 sigue ABIERTA **independientemente** del resultado.
- Si H-GATE no se manifiesta, no subir dosis/tasa/gain ni retocar seeds para hacerlo aparecer; investigar por qué la susceptibilidad o STW no sobrevive a tick128 y proponer un nuevo protocolo solo después del diagnóstico.

## Interpretación permitida

Este ensayo estudia la dependencia de una regla de consolidación a la fase del tick **lógico**, NO periodicidad real de un Norn ni aprendizaje duradero. No requiere recuperar GEN para probar la regla experimental ya registrada; reclamar C1 histórico completo exige retomar la investigación H. Sin cambios en main, Nilo0.7 ni merge del PR#103.
