# NeuroLab E09.02e — comparación completa y resultados conservados

**Fecha:** 21/11/2026 · **Estado:** E09.02e VALIDADA dentro del modelo experimental NeuroLab; G09 de mente unificada y G00-H de fidelidad histórica NO resueltas.

**Protocolo previo:** [E09_02E_STW_LTW_PRE_REGISTRO.md](E09_02E_STW_LTW_PRE_REGISTRO.md).
**Evidencia ejecutada:** [GitHub Actions #44920963462](https://github.com/mxlzz/Nilo_public/actions/runs/44920963462), job `136896676971`, commit ensayado `7066bef28ff6788cb89b4dc85063238e40f0331b`, resultado `success`. Los tres programas (E09c negativo, E09d negativo, E09e) corrieron en el mismo job bajo Python 3.11. La consola emitió JSON completos por cada una de las 20 semillas.

## Resultados exactos recuperados de logs

| Métrica | E09.02c pesos acumulativos, sin exploración | E09.02d pesos acumulativos + ε 0.10 | E09.02e STW/LTW, sin ε |
|---|---:|---:|---:|
| Precisión media inicial | 1.0000 | 0.9450 | **1.0000** |
| Precisión media control pesos congelados | 0.4925 | 0.4375 | 0.4925 |
| Precisión media después de invertir recompensa | **0.3000** | **0.8000** | **1.0000** |
| Semillas iniciales con precisión ≥0.90 | 20/20 | 19/20 | **20/20** |
| Semillas invertidas con precisión ≥0.90 | **6/20** | **16/20** | **20/20** |
| Ventaja media sobre control inicial | 0.5075 | 0.5075 | 0.5075 |
| Puerta preregistrada | **NO** | **NO** | **SÍ** |

### Artefactos versionados con los pesos por semilla

- [E09c — registro negativo íntegro](resultados/run-44920963462/e09c_negative.json)
- [E09d — registro negativo íntegro](resultados/run-44920963462/e09d_negative.json)
- [E09e — STW/LTW validada](resultados/run-44920963462/e09e_stw_ltw.json)

La versión original E09c y la variante E09d **no fueron modificadas** para crear la ventaja de E09e. Los controles negativos se conservan para reejecuciones.

## Qué demuestra y qué NO

- **Demuestra:** en un ensayo de contingencia de dos acciones, un circuito de **cinco unidades** que mantiene la misma representación (Concept AND; Decision excitación - inhibición) y la misma política de selección recupera reversibilidad al usar sinapsis con **dos velocidades**. Gana sin añadir unidades ni ε-greedy.
- **No demuestra:** que el algoritmo exacto del Norn original esté reconstruido, que cinco neuronas sean capaces de sobrevivir, inventar conceptos o aprender objetivos propios, ni que una ecuación STW/LTW particular sea necesaria para cualquier tipo de aprendizaje. La tarea es extremadamente simple, con refuerzo inmediato del evaluador; se requieren generalización, ruido, varias tareas y pruebas de larga duración para extrapolar.
- **Control metodológico crucial:** los coeficientes STW/LTW provienen de **nuestro prototipo E04** (±32 refuerzo rápido, LTW se mueve 1, STW vuelve 6), NO del ejecutable C1. La estructura de las reglas neuronales (`ANDTYPE0` y `STATE+TYPE0-TYPE1`) sí se extrajo de `dad1.gen`.

## Implicación para la investigación

Antes de diseñar otra arquitectura o sumar neuronas, la prioridad es **comparar estos coeficientes experimentales con la actualización sináptica real de C1**. Ya conocemos del genoma original las tasas para Decision (susceptibility decay48, STW decay80, LTW rate128; dos clases con 128 dendritas por neurona), sus SVRules y los químicos:
- 49 Reward, 50 Punishment, 51 Reinforcement;
- 52 ConASH, 53 DecASH1, 70 DecASH2.

La guía técnica de C1 documenta el orden de cálculo aproximado (susceptibilidad → refuerzo STW → relajación → LTW → fortaleza → migración) y los comportamientos especiales de lóbulos. Pero **no hay aún una comparación contra el motor de ejecución original**. [C1 Brain Guide](https://zenzoa.com/creatures/c1-brains.html).

**Siguiente subtarea:** E09.02f — especificar y medir un único tick sináptico de Decision basado en la guía, con todas las divergencias marcadas y oráculos numéricos. Si queremos afirmar fidelidad bit a bit, pedir el ejecutable original extraído del instalador, sin necesidad de instalar ni ejecutarlo. Mientras tanto, mantener separadas la línea histórica y la experimental.
