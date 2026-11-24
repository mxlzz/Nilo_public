# E09.02i — integración mínima y ensayo de crédito, sin cambiar la microred

**Fecha:** 2026-11-21. **Estado:** preregistro previo a código experimental. **Antecedentes:** [E09 audit](E09_AUDITORIA_INTERMEDIA.md), [resultado H6](E09_H_06B_RESULTADO_CADENCIA.md), [comparación g.11](E09_02G_11_ALTERNATIVAS_Y_PRIORIDAD.md).

## Decisión metodológica NL-DEC-0020

**Se adopta exclusivamente para la línea N un reloj lógico por invocación, SIN equivalencia en segundos.** La evidencia H6 comprueba que C1 solicita un WM_TIMER de 90 ms, pero no demuestra frecuencia efectiva por criatura. No convertir el número 90 en un parámetro de plasticidad ni en duración de episodio. La línea H permanece abierta donde corresponde.

**Motivo:** se puede verificar la interacción de piezas ya existentes sin alterar el reloj histórico ni inventar nuevas neuronas. Aplazar la investigación experimental hasta medir un Norn ejecutado no mejora el contraste del primer acoplamiento. La decisión es reversible y no implica integrar con Nilo 0.7.

## Pregunta de E09.02i

¿Se conserva el orden de señales **cerebro → emisor → receptor → reacción** bajo un estado continuo reproducible, y cómo afecta a la plasticidad de la misma microred de seis unidades de E09g? **No presupone que la integración mejore el rendimiento**.

## I1. Puente químico, condición de cierre técnica

- Reutilizar sin modificar: [emitter](../../experiments/neurolab/e09_historical_emitter.py), [receptor](../../experiments/neurolab/e09_historical_receptor.py), [loci](../../experiments/neurolab/e09_historical_locus.py) y [reacción](../../experiments/neurolab/e09_historical_reaction_math.py).
- Estado explícito e inmutable con pool de 256 bytes, loci CHEM0..3 de **Decision6 y Concept8**, puertos fuente emisores (lobe,locus,value), tick lógico. No usar IDs de acción correctos ni contexto dentro del puente.
- Una invocación química procesa **emisores en orden → muestreo de receptores en los loci → reacciones en orden**. No implementar aquí **decaimiento global de 256 químicos**, porque no quedó integrado con un oráculo completo; informar omisión en la traza y no afirmar equivalencia bit a bit.
- Datos originales de E09h.2/h.3 como fixtures; si se usa un subconjunto de genes, declarar cuáles y qué falta.
- Oráculos fijados: con pool Reward49=20, Reinforcement51=0 y solo reacción gen111, primer muestreo: Decision CHEM0=19 y Concept CHEM0=0; reacción produce Reinforcement51=12 después del muestreo. En el siguiente tick, Concept CHEM0=11. Esto distingue el orden histórico de la versión incorrecta reacción→receptor.
- Emisor gen124 con fuente de lóbulo6/locus1=80, pool DecASH1(53)=0 produce 79 y pone fuente a cero; receptor gen127 escribe Decision CHEM2=0. El pool y estado previos permanecen inmutables.
- Controles: sin emisores, sin receptores, sin reacciones; aislación de lóbulo, saturaciones; errores de entradas; no mezclar fuente de gen123 (Concept8) con Decision6. Duplicados se rechazan explícitamente (convención segura N, **no** el loader histórico).
- **Gate I1:** unit tests y CI verdes + traza de cada fase. El éxito de I1 **no es aprendizaje**.

## I2. Acoplamiento cerebral sin rediseñar neuronas

- Reutilizar C1ContextBrain de E09g.5, exactamente las mismas ocho sinapsis/6 unidades, decisión antes que concepto y salidas WTA.
- Tick lógico: cerebro lee **CHEM de Decision almacenado ANTES de la química del tick**; luego fase química prepara CHEM para el siguiente tick. Las fuentes del emisor se proporcionarán por puertos explícitos etiquetados, **sin inventar que son automáticamente outputs de Decision**: C1 no expone aún un adapter completamente validado para los loci fuente.
- Estado checkpoint completo, comparación continuar vs restaurar; congelar las sinapsis con learn=False sin congelar la química, para distinguir dinámica de plasticidad.
- **Gate I2:** determinismo, traza de desfase, checkpoint, independencia de la recompensa del evaluador. I2 demuestra **acoplamiento temporal parcial**, no circuito neuroendocrino autosuficiente ni G09.

## I3. Solo después de I1/I2: ensayo conductual

- No introducir mutaciones adicionales ni afinar tasas para evitar sobreajuste. Comparar al menos: A química inmediata externa g.10 (control conocido), B puente químico con precursor metabólico generado por evaluador **fuera** del cerebro, C red con pesos congelados, D baseline tabular con la misma información causal permitida.
- Tareas/semillas predefinidas para un nuevo holdout, separar train/test, inversión, distractores y recompensa demorada, registrar conteos de no-acción y errores de crédito. **No atribuir a C1 una etiqueta de recompensa externa**.
- Si el protocolo actual de g.10 no puede portarse sin introducir un mapeo no verificado, registrar **bloqueo científico** y restringirse a I2. No sumar neuronas ni una compuerta artificial IG para forzar éxito.
- **Gate I3 y G05:** no se cierran por pruebas unitarias, requieren diferencias de rendimiento reales y control de crédito sin transferencia de ground truth al modelo.

## Restricciones y reversibilidad

Este es un subexperimento de **E09.02**, no una fase nueva que reemplace el plan E00–E09. Mantener línea N distinta de H, PR #103 draft, sin merge, mundo, cuerpo, LLM o integración con Nilo 0.7. Registrar errores y resultados fallidos antes de cambiar código. No declarar nuevo estado canónico validado antes de una ejecución CI enlazada.
