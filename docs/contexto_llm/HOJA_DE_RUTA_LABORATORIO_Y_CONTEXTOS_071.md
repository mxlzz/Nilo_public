# Nilo 0.7.1 — Hoja de ruta consolidada · Laboratorio y revisión del motor

**Fecha:** 2026-11-07  
**Estado:** planificación acordada para desarrollo iterativo; **no** equivale a etapas ejecutadas.  
**Seguimiento:** [#70 · Laboratorio](https://github.com/mxlzz/Nilo_public/issues/70) · [#31 · Contexto LLM](https://github.com/mxlzz/Nilo_public/issues/31) · [#63 · Proyección cognitiva](https://github.com/mxlzz/Nilo_public/issues/63) · [#3 · Evaluación](https://github.com/mxlzz/Nilo_public/issues/3).  
**Auditorías de referencia:** [contraste con Claude sobre prompt](AUDITORIA_PROMPT_CLAUDE_2026-11-07.md); dos propuestas externas de UX revisadas en el issue #70, **no directrices obligatorias**.

## Propósito y límites

Laboratorio como instrumento de investigación: permite reconstruir episodios de Nilo, entender reglas del motor, inspeccionar **literalmente** el contexto que llegó al LLM y el estado físico que el LLM no conoció, proponer exclusiones mediante checks, adjuntar exportaciones para revisión y después realizar experimentos aislados. Los resultados posteriores guían cambios del motor, no al revés.

La decisión del LLM organiza los episodios de deliberación, pero también existen operaciones de agenda/rutina/motor sin consulta y pruebas sandbox. No se inventan vínculos ausentes ni se atribuye causalidad a justificaciones narradas por el modelo.

**Reutilizar antes de crear:** visor HTTP literal y procedencia, histórico con checkpoints, escenarios y sandbox, ajustes con perfiles/checks parciales. No sustituir la exactitud del transporte por una reconstrucción estética. La UI final de Pruebas/columna derecha se debate después de contar con la estructura de información.

## Fase A · Laboratorio (8 etapas)

| Etapa | Alcance acotado | Entregable y prueba de aceptación |
|---|---|---|
| **01 · Auditoría de infraestructura** | Inventariar qué registra cada módulo, sus límites de retención, joins y carencias; congelar muestras de solicitudes, escenarios, planes y resultados. | Matriz **disponible / parcial / inexistente** y fixtures reproducibles, hashes/versiones; no afirmar que se capturó una respuesta bruta cuando solo hay decisión normalizada. |
| **02 · Trazabilidad de episodios** | Enlazar intento HTTP, respuesta cruda (instrumentar captura segura en adelante), normalización/errores, plan, ejecución, memoria y eventos automáticos. | Un episodio se puede reconstruir del origen al resultado; datos ausentes explícitos, sin mutar simulación ni simular históricos inexistentes. |
| **03 · Recorrido + ficha de episodio** | Vista temporal y ficha progresiva: situación → contexto recibido → respuesta/plan → acciones → resultado → información disponible posterior. | Recorrido reproducible de un turno real y un evento sin LLM; acceso al original para cada eslabón; distinción secuencia/causalidad. |
| **04 · Inspector de reglas del motor** | Desde cada operación: argumentos, validaciones efectivamente evaluadas, razón observada de rechazo/fallo/efecto parcial, diferencias antes/después, trazas y referencias de código opcionales. | Probar una operación con éxito y otra sin él, sin inferir como ejecutadas condiciones no instrumentadas; información interna y perceptible claramente distinta. |
| **05 · Inspector literal de contexto LLM** | Reutilizar el visor y su procedencia: bloques desplegables por rol/origen y texto literal original; datos omitidos vs ausentes, perfil/presupuesto, HTTP real vs solicitud local calculada. | Copiar original coincide con captura, sin reescritura; subtítulos y referencias fuera del cuerpo; acciones automáticas diferenciadas de solicitudes. |
| **06 · Marcas, notas y exportación** | Checks por ruta/sección como **propuesta de exclusión**, notas vinculadas a contenido/episodio/versión, exportación JSON autocontenida arriba de la ficha. | Archivo suficiente para revisión externa (texto literal, hashes, rutas, contexto, propuesta y notas), no modifica prompt activo, motor ni SQLite; campos obligatorios solo revisables. **Hito usable**. |
| **07 · Experimentación aislada y A/B** | Tres modalidades: prueba física del motor, respuesta del LLM con contexto alternativo y evolución multivuelta; comparación baseline/variante y límites explícitos de reproducibilidad. | Mismo estado de partida de referencia cuando aplica; pruebas locales sin API por defecto, consultas reales solo bajo acción explícita; no contaminar partida original. |
| **08 · Análisis transversal y QA de UX** | Seguimiento de experiencia→memoria→recuperación, patrones operativos, matriz campo×turno, revisión final de navegación/columna derecha y ayudas. | Tres pruebas reales de usuario: decisión inesperada, repetición, contexto excesivo; diferencias entre dato original, inferencia y anotación visibles; regressions/compatibilidad verificadas. |

**Hito:** al completar **06** ya es posible inspeccionar, marcar y exportar hallazgos para analizar con otra IA. 07–08 amplían capacidad experimental y evaluación de UX.

## Fase B · Mejoras del motor con el laboratorio (3 etapas)

| Etapa | Alcance acotado | Entregable y prueba de aceptación |
|---|---|---|
| **09 · Correcciones verificadas** | Contratos de operaciones y respuestas, pérdidas de `design.prediction`, valores `null`, semántica de `descend`, planes válidos de un paso y otras inconsistencias comprobadas. | Tests por defecto/regresión, compatibilidad de saves; corregir bugs bloqueantes de la fase A antes si impiden su prueba. |
| **10 · Contexto e instrucciones modulares** | Núcleo conciso, índice completo de capacidades, detalle condicional de contratos, selección multi-foco de memorias, deduplicación con procedencia, presupuesto y schema opcional. | Variantes comparables contra baseline, sin quitar capacidades ni imponer metas; cambios aislados y revertibles. |
| **11 · Runs comparativos e integración** | Evaluar validez, repetición, memoria, proyectos, exploración, autonomía y costo en partidas comparables; conservar evidencia cualitativa. | Seleccionar mejoras por resultados medidos, documentar aceptaciones/rechazos, mantener referencia anterior y cerrar pruebas. |

## Método de cada etapa

1. Auditar el tramo de código existente y sus dependencias; actualizar límites y riesgos observados.
2. Especificar el comportamiento deseado y los datos necesarios; incluir casos positivos, negativos, antiguos e incompletos.
3. Implementar en rama/PR pequeño, ejecutar tests y comprobar no mutación cuando corresponda.
4. Documentar diferencias, cobertura, estado y pendientes en #70/#31 y esta hoja de ruta. No afirmar que una etapa está terminada sin evidencia.

Las etapas son **unidades de trabajo**, no once versiones/paquetes descargables. Mantener PRs/UI de etapas históricas del laboratorio sin rehacerlos indiscriminadamente; crear paquetes ejecutables en hitos de prueba, no uno por etapa. Nunca aplicar una exclusión de checkbox como regla activa sin decisión explícita.

## Estado

| Etapa | Estado |
|---|---|
| 01 | **Implementada y validada**: auditoría contra rama UI 04, 6 casos de referencia, manifest sin textos privados y pruebas; CI de [PR #85](https://github.com/mxlzz/Nilo_public/pull/85) aprobada. [Informe](https://github.com/mxlzz/Nilo_public/blob/work/0.7.1-lab-stage01-inventario/docs/laboratorio/AUDITORIA_ETAPA_01_2026-11-07.md). Pendiente integración de PR apilado. |
| 02 | **Implementada y validada en PR #86 (borrador)**: respuesta textual original con SHA y fases de validación, `trace_call_id` de checkpoint, vínculo de acciones por `journal_id`, evidencia por IDs exactos, lectura local compatible con registros antiguos. **CI aprobada: 1.116 tests (1 omitido), Windows exitoso.** [Informe](https://github.com/mxlzz/Nilo_public/blob/work/0.7.1-lab-stage02-trazabilidad/docs/laboratorio/TRAZABILIDAD_ETAPA_02_2026-11-07.md). Pendiente integración y prueba real de una partida con nueva instrumentación. |
| 03 | **Implementada y validada en PR #87 (borrador)**: Recorrido histórico y ficha literal de 4 pasos, decisiones archivadas sin checkpoint, acciones automáticas separadas, reintentos y evidencias por IDs exactos; replay previo conservado. [CI #42413107213](https://github.com/mxlzz/Nilo_public/actions/runs/42413107213) aprobada: **1.130 tests, 1 omitido, Windows correcto**. [Informe](https://github.com/mxlzz/Nilo_public/blob/work/0.7.1-lab-stage03-recorrido/docs/laboratorio/RECORRIDO_ETAPA_03_2026-11-07.md). Pendiente integrar PRs apilados y prueba visual con partida real. |
| 04 | **Implementada y validada en PR #88 (borrador)**: inspector contextual desde acciones históricas, mundo interactivo y escenarios; contratos documentados vs condiciones físicas efectivamente registradas, validación de formato retrospectiva, trazas y límites de evidencia. [CI #42414264938](https://github.com/mxlzz/Nilo_public/actions/runs/42414264938) aprobada: **1.144 tests, 1 omitido, Windows correcto**. [Informe](https://github.com/mxlzz/Nilo_public/blob/work/0.7.1-lab-stage04-reglas/docs/laboratorio/INSPECTOR_REGLAS_ETAPA_04_2026-11-07.md). Pendiente integrar PRs apilados y validar UX con una partida real; no hay instrumentación universal de todos los booleanos físicos. |
| 05 | Pendiente (visor literal existente, falta integración del recorrido) |
| 06 | Pendiente (checks parciales existentes en Ajustes, falta notas/exportador integrado) |
| 07 | Pendiente (sandbox y comparación parcial ya existentes) |
| 08 | Pendiente |
| 09 | Pendiente |
| 10 | Pendiente |
| 11 | Pendiente |

**Reemplaza como planificación activa** la primera división tentativa A1–A5 / B1–B5 del 07/11/2026. Se preservan los issues y PRs originales como historial; las claves antiguas no implican una etapa ya completada de esta nueva hoja de ruta.
