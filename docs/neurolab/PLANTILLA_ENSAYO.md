# NeuroLab — plantilla de ensayo experimental (NO es un ensayo ejecutado)

Copiar este archivo a un acta individual cuando exista una corrida real, por ejemplo `experiments/NL-E03-T05-R001.md`. Nunca rellenar con datos simulados que parezcan una ejecución real. Conservar todas las versiones de resultados, incluidos los fallos.

## A. Identificación

| Campo | Valor |
|---|---|
| ID único | NL-E##-T##-R### |
| Estado | propuesto / aprobado / ejecutado / analizado / inválido |
| Etapa y subtarea | E##.## |
| Fecha de pre-registro | YYYY-MM-DD |
| Fecha de ejecución | pendiente |
| Hipótesis | |
| Hipótesis nula | |
| Familia de mecanismo | histórica C1 / adaptación NeuroLab |
| Evidencia histórica vinculada | `claim_id`, fuente y rango |
| Autor / ejecutor | |
| Auditor / observador | |

## B. Diseño congelado antes de correr

- Variable independiente (qué se cambia):
- Variables dependientes (qué se mide):
- Condiciones A/B y control negativo/positivo:
- Correspondencia entre señales y respuestas: **solo en el evaluador**, nunca en cerebro.
- Topología (identificadores neuronales/sinápticos):
- Regla(s) de actualización y versiones:
- Estado inicial, parámetros, límites y pesos:
- Tipo de secuencia y longitud:
- Semillas de entrenamiento y holdout:
- Contingencia de refuerzo, signo, escala, reloj:
- Presupuesto máximo de pasos/ciclos/recursos:
- Criterio de aceptación/fallo antes de ver resultados:
- Riesgos de fuga, sesgo y no comparabilidad:
- Plan de pausa/rollback:

## C. Identidad del artefacto

- Repositorio / rama / commit SHA:
- Versión de Python/paquetes:
- SO, arquitectura y detalles deterministas:
- SHA de configuración:
- SHA o ubicación de entradas:
- PRNG y estado inicial:
- Ruta y checksum del checkpoint:
- Ruta y checksum de traza cruda:
- Ruta y checksum de resultados derivados:

## D. Ejecución real

```text
[No rellenar hasta ejecutar]
comando:
inicio:
fin:
código de salida:
```

- ¿Cuántas semillas se ejecutaron?:
- ¿Hubo fallos / timeout / retries?:
- ¿La ejecución incluyó alteraciones del diseño?:
- ¿Existió contaminación train/test?:
- ¿Se pueden reconstruir decisiones, refuerzos y cambios por tick?:

## E. Resultados

| Métrica | Baseline | Variante | Diferencia | Variación / intervalo | Observaciones |
|---|---:|---:|---:|---|---|
| Exactitud de test | — | — | — | — | |
| Aprendizaje/reaprendizaje | — | — | — | — | |
| Retención | — | — | — | — | |
| Generalización | — | — | — | — | |
| Fallos sin decisión | — | — | — | — | |
| Coste de ciclos | — | — | — | — | |

- Distribución por semillas:
- Cambios de neuronas/sinapsis observados:
- Resultados inesperados:
- Efectos alternativos que podrían explicarlos:
- ¿El control se comportó como se esperaba?:
- Limitaciones del experimento:

## F. Veredicto y siguiente paso

- Puerta aplicable: G##
- Resultado: validado / fallido / nulo / bloqueado / inválido
- Evidencia concreta que sustenta el veredicto:
- Qué NO podemos concluir:
- ¿Qué exige cambiar?:
- ¿Repetir, ampliar, descartar o continuar?:
- PR/commit/issue de actualización:
- Siguiente subtarea exacta:

**Regla:** no modificar las mediciones crudas después del análisis. Si una evaluación se reconsidera, agregar revisión fechada con razones y comparación.
