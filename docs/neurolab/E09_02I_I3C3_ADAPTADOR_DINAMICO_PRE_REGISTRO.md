# E09.02i-I3c.3 — preregistro del adaptador dinámico de cuatro contactos

**2026-11-21 — PRE-IMPLEMENTACIÓN.** Fuentes: [contrato I3c.1](E09_02I_I3C1_CONTRATO_MIGRACION_DINAMICA.md), [llamadas originales I3c.2](E09_02I_I3C2_RESULTADO_INVOCADOR_MIGRACION.md), [límite estructural I3b.3](E09_02I_I3B3_RESULTADO_MIGRACION.md). G05/G09/G00-H ABIERTAS aun con todos los tests verdes.

## Hipótesis y contrato fijo

- **C1, identidad de fuente:** estado tipado de cuatro contactos Decision (D0 exc, D0 inh, D1 exc, D1 inh), cada uno con source_pointer persistente e independiente del slot. Concept0=0x1000, Concept1=0x2000 son punteros sintéticos de identidad, **NO direcciones del EXE**. Cambiar puntero con pesos iguales debe cambiar señal si outputs Concept difieren. El wiring inicial debe aportarse explícitamente: no elegirlo para favorecer mapping A/B del evaluador.
- **C2, migración:** REUSAR sin modificar la función existente **c1_migration.decision_migrate**. Slot agotado con strength0, receptor output>0, origen alternativo libre → migración posible; seleccionar origen duplicado → rechazo; output0 → sin migración ni consumo de azar. Fijar inicialización SINTÉTICA N de nueva dendrita: LTW=0, STW=0, strength=2, susceptibility=0; NO es parámetro GEN histórico comprobado.
- **C3, orden y convenio:** preservar lógica reducida Decision lee Concept previo → cuatro llamadas a C1 synapse update → cálculo WTA → Concept nuevo → intentar migración después de WTA solo en destinatario con output no cero, por clase. El uso del **output post-WTA** y ofrecer ambos conceptos registrados (independiente de actividad instantánea) son **CONVENCIONES N**, porque invocador histórico completo y filtros de fuentes activas no se reconstruyeron. La evidencia H sólo fija que la llamada Type1 es posterior a WTA y exige salida no cero. Si no hay migración, la conexión sigue strength0. Con learn=False se congelan pesos y migraciones.
- **C4, azar:** RandStream precargado con draws crudos (0..32767), sin random global para migración: candidato ocupa 1 draw, si es válido inicialización consume 2 adicionales, si duplicado solo 1, receptor inactivo0. Cursor y draws en estado y checkpoint. Agotamiento debe disparar RuntimeError, sin fabricar PRNG. Empate WTA utiliza únicamente el desempate determinista actual de C1ContextBrain, NO afirmar CRT histórica.
- **C5, persistencia:** checkpoint schema versionado y ESTRICTO: seed/blind/config/migration_enabled, cuatro source pointers y sinapsis, Decision/Concept outputs, tick, RandStream/cursor. Restaurar rechaza versión errónea, extras, fuente desconocida, identidad/slot alterados y semilla distinta. checkpoint tras restore idéntico; continuar multi-ticks desde restore produce transiciones y eventos idénticos.
- **C6, aislamiento:** no editar C1ContextBrain, genes originales, c1_migration.py, I3/I3b ni Nilo0.7/main. Esta es B, arquitectura experimental nueva de **6 unidades/4 dendritas**, NO simulador histórico, NO integración con la red A de ocho contactos.

## Oráculos / pruebas preregistrados

1. Cuatro contactos exactos, dos fuentes registradas, owner/kind predeterminado, puntero conocido; wiring obligatorio. Validación estricta de tipos y tamaños.
2. Mismos pesos y outputs Concept=(255,0), alternar pointer C0↔C1: la señal de clase debe cambiar; el actualizador toma source_output de pointer, nunca del índice físico del slot.
3. Grupo desconectado con source C0 y receptor output255: stream (1,0,0) → migración a C1, LTW/STW0, strength2, cursor3; stream (0) → duplicate_source con estado idéntico, cursor1; output0 con stream vacío → inactive_recipient, cursor0.
4. Fortaleza positiva: no migración/consumo RNG. Sin aprendizaje: pesos, fuente y stream quedan constantes, aunque avance tick.
5. Mismo estado, seed, stream y señales → misma secuencia; checkpoint/restore a mitad + reanudación idénticos, incluso cursor; corrupción y schema extra rechazados.
6. No mostrar acierto de tarea como éxito de migración. La firma pública de step recibe solo state, context, chemicals, learn (sin mapping/correct/reward/expected_action).

## Puertas y continuidad

- **G-I3c3-SCHEMA** estados/checkpoints estrictos, reproducibilidad.
- **G-I3c3-MIGRATION** tests reales sobre Type1 existente, rechazo y aceptación contra oráculos.
- **G-I3c3-STEP** uso del actualizador neuronal y químico existente, gating post WTA, congelamiento holdout.
- **G-I3c3-REPO** suite NeuroLab completa sin regresiones y datos sintéticos de prueba guardados.
- G05/G09 y G00-H siguen ABIERTAS. I3c.4 solo si I3c.3 pasa: diseñar comparación **B sin migración vs B con migración** de igual capacidad (4 contactos) con cohorte nueva y controles A/D separados, antes de ejecutar un ensayo conductual.

**No cambiar parámetros tras mirar resultados; conservar también los fallos.** PR#103 borrador, main y Nilo0.7 intactos.
