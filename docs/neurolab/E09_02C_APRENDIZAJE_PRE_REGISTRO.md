# E09.02c — preregistro de aprendizaje en microcircuito C1 de cinco unidades

**21/11/2026.** Se define *antes del código*. Continuación de [E09.02b](E09_02B_MICROCIRCUITO_PRE_REGISTRO.md), ahora probando plasticidad sin añadir cuerpo, mundo, LLM ni semántica de objetos. La primera mente mínima debe aprender, no solo responder.

## Pregunta

¿Puede un microcircuito de 2 entradas, 1 detector de concepto AND y 2 neuronas de decisión, que usa las **reglas neuronales extraídas de dad1.gen**, adquirir y revertir una preferencia mediante consecuencias posteriores a sus propias decisiones?

No se afirma que reproduzca el aprendizaje bioquímico de C1: la simulación original tiene susceptibilidad, STW/LTW, fortalezas, químicos y condiciones de migración. Este ensayo introduce una **aproximación de refuerzo con dos canales**, inspirada en clase TYPE0 excitatoria y TYPE1 inhibitoria, no su ecuación histórica.

## Variables y estado

- Entradas constantes de laboratorio en entrenamiento y evaluación: `P0=255,P1=255` → `Concept=255` por `ANDTYPE0`, con pesos conceptuales `128/128`. Sin estímulos semánticos.
- Dos neuronas de decisión con regla genética `STATE + TYPE0 - TYPE1`, estado basal80, umbral0; el resultado se satura [0,255] por la convención E09.02a.
- Cuatro pesos experimentales 0..255: `D0Exc,D0Inh,D1Exc,D1Inh`, **inicialmente todos cero**; no copiar los valores demostrativos fijos de E09.02b (su objetivo era solo mostrar propagación).
- Sin actividad del concepto, no puede haber modificación de pesos (ensayo auxiliar).
- La elección es D0/D1 por mayor score; ante empate, **exploración** con generador reproducible `random.Random(seed*1000000+trial)`. Esta es una política experimental no descrita por el genoma.
- El agente **no conoce** la acción correcta. Solo conoce: acción elegida, concepto que realmente se activó y un refuerzo escalar posterior `reward=+1/-1`.
- Actualización de pesos solo del **canal de la acción elegida**: recompensa +1 incrementa en 16 su peso excitatorio TYPE0; castigo -1 incrementa en 16 su peso inhibitorio TYPE1. Ningún otro peso cambia. No existe STW/LTW, elegibilidad temporal ni migración todavía.
- Checkpoint guarda los 4 pesos, número de ensayos y semilla; la elección por empate depende solo de semilla y número de ensayo (sin estado PRNG oculto).

## Diseño congelado

- Semillas `0..19` para aprendizaje y control.
- Primera contingencia oculta **solo en evaluador**: `D0` se premia, `D1` se castiga. Entrenar 60 ensayos por semilla.
- Holdout 80 elecciones sin refuerzo y sin actualización de pesos.
- Control de misma red, mismas semillas e inputs, pero pesos congelados y exploración de empates igual.
- Reversión: ahora `D1` premiado, `D0` castigado. Entrenar 120 ensayos. Segundo holdout80.
- Criterio preregistrado de prueba: ≥18 de 20 semillas con precisión ≥0.90 antes y después de inversión; ventaja media ≥0.30 ante congelado.
- Tests manuales: primer premio a D0 desde pesos0 produce `D0Exc=16`; primer castigo a D0 produce `D0Inh=16`; no se modifican otras conexiones ni por feedback obsoleto.
- Comparar aprendizaje invertido y observar saturación. No cambiar los parámetros después de mirar el holdout.

## Interpretación permitida

Un resultado positivo demostraría **aprendizaje asociativo y reversión usando estructura de reglas C1 bajo una regla química simplificada** en un circuito de cinco unidades. No prueba la configuración real de los 952 nodos ni capacidad de aprender conceptos (el detector está fijado). Si no aprende, documentar resultado negativo y explicar si falla por exploración, saturación, refuerzo o topología antes de sumar componentes.

**G09:** sigue abierta; E09.02c no integra E04/STW-LTW, E05/elegibilidad, E07/migración ni E08/recurrencia en la misma red.
