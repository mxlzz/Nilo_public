# NeuroLab E09.02b — pre-registro de microcircuito C1 de cinco unidades

**21/11/2026 · antes de programar.** Objetivo: conectar las tres SVRules genéticas verificadas en una unidad mínima funcional, sin cuerpo, mundo, LLM ni aprendizaje todavía. **No emular un Norn completo.**

## Diseño

- Neuronas `P0,P1`: dos señales abstractas del banco de pruebas, ocupan dos posiciones funcionalmente semejantes a Perception, **no** ejecutan la lógica hardcoded de Perception de C1.
- `C`: un detector de concepto con **dos** dendritas de clase 0 desde P0 y P1, respetando el rango genético original 1–3; LTW inicial 128 para cada una. Valor `ANDTYPE0` según la convención numérica de [E09.02a](E09_02A_PRE_REGISTRO_SVRULE_C1.md).
- `D0,D1`: dos neuronas de decisión, SVRule exacta `STATE PLUS TYPE0 MINUS TYPE1` y estados iniciales de reposo 80 según genoma. `D0` recibe el concepto con peso255 por TYPE0 (excitador); `D1` recibe el mismo concepto con peso255 por TYPE1 (inhibidor); los otros pesos son cero. **Estas conexiones son elegidas por el laboratorio para construir un ejemplo explicable**, no están preconectadas así en el genoma.
- Cálculo de una presentación: P0/P1→C por AND→D0/D1 por SVRule→ganador por máximo, empate explícito como abstención. **Reloj de laboratorio sincrónico por fases**; no afirmar mismo orden que en ejecutable C1.
- El peso fijo 255 en decisiones es **experimental**, aunque C1 codifica LTW inicial cero para conexiones de decisión: se hace aquí para observar respuesta del microcircuito antes de añadir aprendizaje químico. Se registra como divergencia intencional.
- No hay aprendizaje, recompensa, estado fisiológico ni variación de topología. La misma entrada produce el mismo resultado.

## Oráculos previos

| Entrada (P0,P1) | Concept | Estado D0 | Estado D1 | Salida |
|---|---:|---:|---:|---|
| (0,0) | 0 | 80 | 80 | abstención por empate |
| (255,0) | 0 | 80 | 80 | abstención |
| (0,255) | 0 | 80 | 80 | abstención |
| (100,80) | 90 (50+40) | 170 | 0 | D0 |
| (255,255) | 255 (saturado de 256) | 255 | 0 | D0 |

El valor numérico 170 y la saturación son nuestras convenciones, no resultados de Creatures C1. Reglas de estado `Decision` y `Concept` provienen de los genes; la política de empate es de laboratorio.

## G09.02b

Tests independientes de cinco neuronas, cálculo conceptual y acción, 20 semillas irrelevantes para este circuito fijo, trazabilidad `P→C→D` y ausencia de reglas de recompensa. Se considera **conectividad funcional mínima demostrada**, no inteligencia, autonomía, memoria ni cerebro consolidado.

**Siguiente etapa posible E09.02c:** incorporar dos familias de plasticidad en decisiones (TYPE0 recompensa, TYPE1 castigo) bajo estímulos químicos abstractos e investigar un mecanismo de exploración inicial; preregistrar separadamente y compararlo con el E03 simple. No mezclar aún E04/E05/E07 como una mente unificada sin pruebas de interacción.
