# Nilo 0.7.1 · Etapa 09 — correcciones verificadas de contratos

**Fecha:** 2026-11-08  
**Rama:** `work/0.7.1-lab-stage09-contracts`  
**Base:** `work/0.7.1-lab-stage08-transversal` (PR #92).  
**Estado:** implementación de contratos y pruebas; validación de CI e integración pendientes.

## Evidencia y criterio

Se contrastaron los contratos de `nilo_runtime/agent/responses.py`,
`nilo_runtime/core/operations.py`, `nilo_runtime/agent/prompts.py`,
`nilo_runtime/cognition/predictions.py` y `inventions.register_design`.
Los desajustes siguientes son reproducibles leyendo el código; se modifican
únicamente los casos de contradicción, no se reinterpreta una partida histórica.

| Hallazgo previo | Cambio aplicado | Límite |
| --- | --- | --- |
| `validate_operation` acepta `design.prediction` como texto, pero `normalize_decision` lo eliminaba por aplicar un normalizador de ensayos físicos. | Conservar el texto de diseño, acotado a 450 caracteres (límite que ya usa `register_design`); para otras operaciones conservar el normalizador numérico existente. | Una predicción de diseño no se convierte en resultado físico ni crea `prediction_log`. |
| Campos textuales opcionales con JSON `null` se convertían en la cadena `"None"`. | Normalización común: `None` → `""` en campos textuales; `accion_proyecto=null` → valor por defecto `nuevo`. | No migrar ni reescribir textos históricos que ya incluyan literalmente `"None"`; la palabra escrita por el LLM se conserva. |
| Contrato de `cuaderno` decía 350 caracteres, mientras el normalizador permitía 500. | El límite efectivo pasa a 350 caracteres. | Puede recortar texto largo del modelo: cambio intencionado y visible; medir si conviene cambiar ambos límites en experimentos posteriores. |
| `SYSTEM` y `GROQ_SYSTEM` pedían planes de 2–12 pasos; `normalize_decision` admite uno. | Instrucciones alineadas a 1–12 operaciones; cierre, pausa y abandono pueden tener lista vacía. | No se obliga a Nilo a ejecutar más acciones ni se altera el máximo de 12. |
| La guía de `descend` duplicaba la explicación de `ascend`. | Describir la entrada accesible desde superficie y la operación real `{"op":"descend"}`. | No modificar el recorrido físico ni prometer descender desde lejos. |
| La guía de `drink` revelaba un incremento exacto de reserva corporal (interno) `+27 hidratación`. | Se retira ese incremento de la guía enviada al LLM; se conserva el volumen físico de bebida (0,18). | La agenda sigue aceptando condiciones numéricas: su traducción a sensaciones requiere adaptador validado, no un cambio aislado de texto. |

## Pruebas de aceptación

- `tests/test_operaciones_07.py`: expectativa histórica de la pérdida de predicción corregida; verifica conservación literal.
- `tests/test_lab_stage09_contracts.py`: texto de diseño atraviesa normalización → `register_design` → ficha persistida en memoria; se preserva carácter hipotético.
- Valores opcionales `null` no producen `"None"`; `cuaderno=null` sigue siendo inválido; entrada original no muta.
- Límite de 350 caracteres, plan de 1 paso, máximo 12 y plan vacío para pausa.
- Guía de descend distinta de ascend y alineada con requisitos de entrada; manual sin incremento oculto de hidratación.
- Toda la suite existente y paquete Windows deben aprobar CI antes de cerrar la etapa.

## Compatibilidad y riesgos

La normalización se aplica **solo a respuestas nuevas** del LLM. Los saves y
replays no se migran ni alteran; `legacy_rest` mantiene su parámetro y ruta.
Ninguna modificación toca persistencia, configuración de APIs, ritmo de
deliberación ni física. La captura literal del laboratorio conserva la respuesta
HTTP original: solo la decisión posterior normalizada cambia.

La reducción del cuaderno puede eliminar la parte final de una nota más larga:
es coherente con el contrato que ya recibía el modelo, pero debe registrarse
como cambio de conducta observable. Eliminar un incremento numérico interno
del manual evita revelar ese valor; no demuestra que el contexto global esté
limpio de otras variables internas.

## Fuera de esta etapa

La agenda cualitativa, la segmentación contextual, la política semántica de
campos opcionales y el esquema JSON del proveedor no se implementan sin
comparar payloads y contratos (etapa 10). Tampoco se reordena la columna
derecha de Pruebas sin revisión de la vista con una partida real.

**Integración:** PR apilado sobre #92; no fusionar directamente a `main`
mientras falte validar la pila de etapas 01–08 con datos reales.
