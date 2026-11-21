# E09.02i-I3 — preregistro de primer benchmark conductual con química temporal

**Fecha:** 2026-11-21. **Estado:** preregistrado ANTES del runner y de mirar resultados. Dependencias: [I1/I2](E09_02I_I1_I2_RESULTADOS.md), [I1b](E09_02I_I1B_RESULTADO_POOL_DECAY.md). **Se usa únicamente línea N**, con parámetros sintéticos declarados: NO predice el comportamiento exacto de C1.

## Pregunta

¿La microred de seis unidades sigue aprendiendo y revirtiendo asociaciones con recompensa diferida cuando el evaluador entrega precursores externos que atraviesan **reacciones → receptor → cerebro** y un decaimiento de pool, en lugar de una CHEM de ±255 inyectada directamente?

**Hipótesis nula:** no supera a la misma microred con sinapsis congeladas (F). Es legítimo obtener resultado negativo. **No calibrar ni cambiar genoma, tasa ni dosis mirando el holdout**.

## Cohorte y tarea congeladas

- **20 semillas nuevas: 200..219**, nunca utilizadas en g.10a/b/c. A y B con inversión de S0→D0/S1→D1 a S0→D1/S1→D0.
- Reusar generador existente de g.10b: 60 ensayos de entrenamiento y 36 holdout por fase, balanceando (contexto 0/1)×(d=1,2,3) con salts 50000/60000 y 70000/80000, respectivamente.
- Cada ensayo 4 ticks objetivo (solo decisión cuarta cuenta), d ticks del contexto opuesto y 1 tick adicional de llegada de refuerzo durante distractor. Holdout sin **nuevas** recompensas y con sinapsis congeladas. No reiniciar estados entre fases, ni modificar seis unidades/ocho sinapsis.
- No equivale a 90 ms por tick ni incluye estados de pausa/otras rutas scheduler.

## Condición bioquímica N congelada

- Todos los 256 químicos usan **tasa de decaimiento de laboratorio 40**. Es una **convención explícita**, no genética C1: G-I1b-RATES sigue abierta.
- Entrada metabólica exógena al pool **una sola vez por ensayo** después de conocer la elección objetivo: para resultado correcto agregar con saturación **80** a químico33 y **80** a químico1; para incorrecto agregar **80** a químico17; si no hay acción, no entregar nada.
- El evaluador conoce contingencias y calcula el resultado desde la elección, pero solamente agrega **precursores químicos**; no pasa contexto de origen, acción correcta ni clase objetivo al cerebro.
- Reacciones genómicas del CD **57,71,111,112**, en ese orden de índice, reconstruidas de fixture original H2; receptores cerebrales **88,89,126–129** de fixture H3.
- Tick del brazo metabólico: cerebro consume el CHEM Decision existente del tick anterior → químicos reciben precursores y procesan las cuatro reacciones → receptor muestreó antes de reacciones → decaimiento del pool final. La inyección se hace **antes de la llamada acoplada pero después de que el evaluador observó la elección causante**. Como cerebro solo lee CHEM guardados, no ve el precursor en forma directa.
- No usar emisores cerebrales si sus puertos de origen no están conectados fielmente a la actividad de C1ContextBrain. Es una omisión explícita, no un emulador.

## Brazos y comparabilidad

1. **M:** microred N con química y plasticidad.
2. **F:** misma arquitectura y química, sin plasticidad; se conserva proceso químico y reloj.
3. **C:** microred C1ContextBrain existente g.10b con pulsos REWARD/PUNISHMENT externos directos, sirve de **referencia, no control perfectamente apareado**: amplitud y cronología difieren.
4. **Q:** tabla2×2 del protocolo g.10b con token de procedencia objetivo+acción. **Control privilegiado**, no prueba de paridad de información.

La comparación más útil es M-F, pero las experiencias químicas endógenas difieren entre brazos porque el evaluador recompensa sus propias decisiones (on-policy). Informar el límite.

## Métricas y puerta preregistrada

- Exactitud y no-acción de la **cuarta decisión objetivo** en holdout A/B y por demora1/2/3; conteos de pulsos y saturaciones del pool49/50/51 (para detectar contaminación/estado químico acumulado); por semilla y agregados; distribución de ganancias M-F.
- Gate neural exploratoria, exigente a propósito: al menos **18/20** semillas M deben obtener exactitud ≥0.90 en ambas fases, media A y B≥0.85, cada demora por fase≥0.70 y M supera a F en exactitud media total por≥0.15. Este criterio no altera g10b retrospectivamente y **NO** cierra G05 automáticamente, que exige atribución causal selectiva.
- Todo resultado negativo se guarda como JSON y se informa. El workflow CI sale correctamente si el runner/contratos se ejecutan, aun cuando la hipótesis neuronal falla; propiedad de software ≠ resultado científico.

## Límites y próxima decisión

No se aprende concepto nuevo, no se verifican tasas genómicas originales, cuerpo/mundo, necesidades ni causalidad autónoma. Si falla, no ajustar dosis/tasa para fabricar acierto: inspeccionar trazas de fase, acumulación, desfase y atribución antes de proponer otro mecanismo. PR #103 draft, sin merge ni tocar Nilo 0.7.
