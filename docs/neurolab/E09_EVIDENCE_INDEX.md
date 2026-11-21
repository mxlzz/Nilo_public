# NeuroLab — evidencia reproducible de la ejecución conjunta E01–E08

**Fuente de verdad de estos datos:** [GitHub Actions run #44852299967](https://github.com/mxlzz/Nilo_public/actions/runs/44852299967), job `136686250858`, SHA del código ensayado `56cb2e7456103eee7a65cdadc275da01a1869720`. Conclusión CI: **success**, 85 métodos de prueba además de los protocolos E03/E06/E07/E08 y benchmark E01. Ambiente CI: Python 3.11.18 sobre runner Ubuntu. La captura de logs se realizó después de finalizar la ejecución.

**Las salidas JSON completas con resultados por semilla se recuperaron del log del job y guardaron en el repositorio**, en esta misma rama, para que no dependan de la caducidad (90 días) de los artefactos Actions.

## Archivos de resultados

| Archivo | Qué contiene |
|---|---|
| [e01_benchmark.json](resultados/run-44852299967/e01_benchmark.json) | Rendimiento kernel de tres neuronas, 100.000 ticks, ambiente |
| [e03.json](resultados/run-44852299967/e03.json) | 20 semillas: entrenamiento, controles congelados, reversión y pesos |
| [e06.json](resultados/run-44852299967/e06.json) | 20 semillas: conceptos conjuntivos vs baselines y pesos |
| [e07.json](resultados/run-44852299967/e07.json) | 20 semillas: migración/fijo/LRU, pérdidas de memoria, posiciones |
| [e08.json](resultados/run-44852299967/e08.json) | Trazas por tick de controles, recurrencia y perturbación |

Los archivos se reconstruyeron semánticamente a partir del JSON que imprimieron los runners; la procedencia es el log del job indicado. No constituyen datos recogidos en Creatures 1.

## Resultados exactos

| Ensayo | Métrica | Valor |
|---|---|---:|
| E03 | Precisión media de aprendizaje | **1.0000** |
| E03 | Precisión media control pesos congelados | 0.4250 |
| E03 | Diferencia media | **0.5750** |
| E03 | Precisión media después de inversión | **1.0000** |
| E03 | Semillas con ≥90 %, antes/después de inversión | **20/20 y 20/20** |
| E06 | Precisión media conceptos por pares | **1.0000** |
| E06 | Precisión media señales individuales | 0.5375 |
| E06 | Precisión media memorizador exacto | 0.5000 |
| E06 | Precisión media conceptos congelados | 0.4500 |
| E06 | Ventaja sobre señales individuales | **0.4625** |
| E06 | Semillas ≥90 % | **20/20** |
| E07 | Precisión patrones nuevos con migración | **1.0000** |
| E07 | Precisión patrones nuevos con LRU | **1.0000** |
| E07 | Precisión patrones nuevos con conexiones fijas | 0.5000 |
| E07 | Pérdida media de precisión en patrones antiguos (migración) | **0.5000** |
| E07 | Semillas ≥90 % en patrones nuevos (migración) | **20/20** |
| E01 | 100.000 ticks (red pequeña: 3 neuronas, 2 sinapsis) | **0.70426 s** |
| E01 | Rendimiento en runner CI (este caso de prueba solamente) | 141.993 ticks/s |

**Interpretación crítica de E07:** migración y LRU lograron resultados equivalentes en este banco de prueba. Reutilizar conexiones ayuda frente a un conjunto fijo de detectores, pero **no demuestra ventaja sobre gestión simple de memoria**. No escoger migración como diseño definitivo de Nilo sin nuevas pruebas que aíslen su aporte.

**Interpretación crítica de E03/E06:** son tareas abstractas de asociaciones con refuerzo suministrado por evaluador. No demuestran autonomía, planificación, creatividad, conceptualización espontánea ni comprensión semántica. E06 no aprende los detectores, solo sus enlaces a acciones.

**E05:** [prueba de atribución espuria](../../experiments/neurolab/tests/test_eligibility.py) confirma que una conexión B más reciente puede recibir aumento de peso 23 y A causal solo 13 en un ejemplo preregistrado. **G05 no superada** aun con CI verde.

**E08:** oscilación recurrente, control apagado y atenuación se comprueban matemáticamente, no equivalen a pensamiento.

## Estado de calidad

- G00-H: abierta, sin genoma C1 original inspeccionado y divergencias documentales.
- G01–G04: validadas para sus modelos experimentales, con **E04 aislada**.
- G05: no superada por atribución espuria.
- G06: validada para invariancia al contexto irrelevante, no formación de conceptos.
- G07: capacidad estructural demostrada, beneficio no superior a LRU.
- G08: dinámica matemática demostrada, no «vida mental».
- **G09: abierta**, ya que aún no se integraron mecanismos bajo un mismo cerebro/tick ni se compararon ablaciones integradas.

## Reproducción posterior

1. Fijar commit `56cb2e7456103eee7a65cdadc275da01a1869720` (versión efectivamente medida).
2. `python -m unittest discover -s experiments/neurolab/tests -v`.
3. `python -m experiments.neurolab.e03_protocol`, `e06_protocol`, `e07_protocol`, `recurrent`, `bench` (todos vía módulo `experiments.neurolab`).
4. Comparar contra archivos JSON guardados. No asumir que distintos runners/versions tienen idénticos tiempos de benchmark.
5. Ante corrección o nueva regla neuronal, crear nueva corrida y nuevo directorio de resultados; **no sobrescribir** estos JSON.

### Siguiente dependencia

Antes de afirmar fidelidad con Creatures 1 se requiere inspeccionar un genoma real C1 con procedencia verificable, por ejemplo `dad1.gen` de una instalación legítima y un editor como [Gene Loom](https://lisdude.com/Creatures/Community/GeneLoom/). La reconstrucción matemática documentada puede continuar sin ello, pero sus supuestos deben seguir rotulados como hipótesis. La etapa de integración G09 es investigación posterior, no éxito tácito.
