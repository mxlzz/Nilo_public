# Laboratorio Nilo 0.7.1 · Etapa 04 — Inspector contextual de reglas

**Fecha:** 2026-11-07  
**Implementación:** [PR #88 (borrador)](https://github.com/mxlzz/Nilo_public/pull/88), sobre [#87](https://github.com/mxlzz/Nilo_public/pull/87).  
**Estado:** implementado en rama; CI pendiente de comprobación. No fusionado a `main`.

## Necesidad que resuelve

Desde una acción observada o una prueba física, permitir entender **qué regla aplica, qué entró al motor, qué condiciones y consecuencias se documentan, qué fue efectivamente observado y qué no podemos saber con los registros actuales**.

No crear un «manual técnico» como pantalla principal. El inspector es una **lente desplegable junto a una acción**, que conserva a un clic los originales. Nunca confundir un ejemplo de código, texto del contrato o una función presente en el registro con la ejecución de una condición concreta.

## Tres superficies integradas

| Lugar | Cómo acceder | Evidencia realmente accesible |
|---|---|---|
| **Pruebas → Mundo interactivo** | Elegir una acción → «Ver reglas y condiciones de esta operación»; después de ejecutar → «Reglas del motor · contrato y condiciones observadas» | Contrato/documentación, evaluación de forma recalculada, diagnóstico tipado generado durante **esa acción de sandbox**, condiciones expuestas por `ActionResult.physical.conditions`, mediciones y funciones instrumentadas. Cuando no hay diagnóstico, no usar el marcador `sin_medicion` como física real. |
| **Historial → Recorrido → episodio → acción** | «Ver reglas de esta acción» desde el checkpoint individual o pasos de la ficha | Contrato y parámetros del checkpoint **previo** de la partida histórica. Diagnósticos dentro de ventana temporal se muestran **solo como candidatos próximos**, no como hechos atribuidos a esa operación. |
| **Pruebas → Escenarios** | Abrir una etapa física → «Ver reglas de [operación]» | Contrato vigente con condiciones documentadas; resultados originales y trazas ya disponibles en el bloque cronológico de esa etapa. No inventar unión por el nombre de operación. |

## Fuentes técnicas, sin duplicación del motor

- `nilo_runtime/core/operations.py::registered_operations` y `get_spec`: catálogo de **26 operaciones** y sus descripciones, duración prevista, requisitos de forma y ejecutor.
- `action_contracts.py::spec_for`: expectativas y postcondiciones documentadas; **referencia**, no hechos.
- `nilo_runtime/core/operations.py::validate_operation`: validación **recalculada** con reglas actuales. La compatibilidad puede aceptar formas incompletas; los campos faltantes se informan por separado.
- `action_contracts.py::classify`: clasificación del verificador **registrada** cuando aparece en un diagnóstico de la operación actual.
- `ActionResult.to_record` y `physical.conditions`: condiciones que el motor **expuso efectivamente** al finalizar una acción. La ausencia del campo no significa que el motor no comprobara condiciones.
- `laboratorio_motor.py::ExecutionTrace`: nombres, líneas y conteos de funciones **instrumentadas realmente recorridas** en el sandbox. **No registra el valor de cada bifurcación condicional**, ni prueba la ejecución de funciones fuera de su lista blanca.
- `historical_lab.select_event`: acciones históricas sin reejecutar; las referencias y las métricas posteriores se muestran en secciones distintas.

El adaptador `nilo_runtime/labs/rules_inspector.py` es puro: **lee y estructura información existente**. No registra propiedades físicas nuevas, no altera contratos ni prompt ni incluye nuevos comandos disponibles para Nilo. En la simulación solo se agrega un objeto `rule_inspection` a la **respuesta de laboratorio** de `MotorLab.act`.

## Contrato de presentación de evidencias

| Etiqueta | Significado | Qué NO prueba |
|---|---|---|
| `documented_rule_not_executed` | Regla publicada en el catálogo instalado | Que la condición se evaluó en el run |
| `rechecked_now_not_original_validation` | Validación de formato calculada ahora, con motor actual | Que el motor histórico ejecutó ese validador |
| `actual_simulation_output` | Resultado físico y verificador recogidos en una ejecución de sandbox real | Que todas las condiciones posibles se evaluaron |
| Funciones instrumentadas | Funciones de la lista de traza efectivamente recorridas | Qué valor booleano tuvo cada predicado |
| Registros cercanos al checkpoint | Diagnóstico archivado dentro de la ventana temporal | Que corresponde inequívocamente a esa acción |
| Ausencia de evidencia | Dato no guardado o no disponible | Que nunca ocurrió |

Cuando una operación carece de contrato verificable específico, se dice así; no se sustituye silenciosamente por un contrato inventado. Cuando el sandbox solo genera el marcador `sin_medicion`, **no** se muestra como resultado físico real.

## Interfaces y seguridad

- `GET /api/lab/rule?op=OPERACIÓN`: catálogo estático desde el registro de operaciones, sin argumentos de ruta.
- `GET /api/history/rule?event=cp:ID`: ficha documental desde el checkpoint seleccionado por `HistorySource`, validando ID y exigiendo operación física; no acepta direcciones de archivos del navegador.
- El resultado histórico nunca confunde análisis con reproducción aislada ni sustituye datos originales por interpretación.
- Texto de registros y descripciones se escapan en el navegador para impedir que el contenido de una respuesta o partida actúe como HTML.
- Todas las APIs viven en el servidor local del laboratorio. El motor principal, las reglas de supervivencia, la memoria y el contexto LLM no reciben información adicional.
- El módulo nuevo se incluye en `MANIFIESTO_SHA256.json` para instalación portátil.

## Comprobaciones para dar por cerrada la etapa

1. Las 26 operaciones del registro tienen referencia y las desconocidas se rechazan.
2. Una consulta puramente documental no dice que la regla se ejecutó.
3. La validación posterior identifica campos requeridos ausentes sin inventar un fallo físico.
4. Una acción real en `MotorLab` conserva resultado original y expone aparte contrato/verificador, condiciones presentes y traza.
5. Los diagnósticos de otra operación no se atribuyen, aunque estén próximos.
6. Los checkpoints históricos no afirman resultados físicos específicos, ni añaden datos no guardados.
7. Los endpoints no aceptan rutas ni IDs arbitrarios, y la partida se consulta sin mutarla.
8. Los tres visores mantienen navegación/funciones anteriores, y el JavaScript compila.
9. Empaquetado Windows y suite de regresión completa aprueban.

**Siguiente etapa:** 05 — inspector literal de contexto LLM, integrando el visor HTTP ya existente y su procedencia con estas fichas, sin alterar el contenido enviado al modelo.
