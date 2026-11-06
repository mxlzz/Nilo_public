# Etapa 23 — Acta de cierre arquitectónico (Nilo 0.7)

**Fecha:** 2026-11-06 · **Rama:** `refactor/0.7` · **Resultado:** **cerrada bajo alcance arquitectónico revisado**; etapa 24 habilitada. Este documento reemplaza la condición antigua de cuatro corridas comparativas como puerta de salida del refactor, sin borrar el protocolo experimental.

## Criterio de aceptación y cambio de alcance

El objetivo contractual de 0.7 es refactorizar íntegramente el código para separar responsabilidades, hacerlo trazable, verificable y más fácil de modificar, **conservar funcionalidad y no introducir regresiones**. La mejora conductual de Nilo se aborda en versiones posteriores. Por decisión expresa del proyecto, se acepta evaluar Groq y comparativas de múltiples semillas en trabajos futuros, **sin afirmar que funcionan, que hubo pruebas ni que se demostró mejora de autonomía**.

La evidencia de esta etapa debe comprobar que el sistema funciona de extremo a extremo y que las anomalías son localizables. Las observaciones de comportamiento históricamente defectuoso no constituyen por sí mismas un defecto de la reestructuración.

## Evidencia comprobada

**Prueba de uso real:** dos snapshots de **la misma sesión** SQLite aportados voluntariamente por el usuario, revisados localmente y **no incorporados al repositorio**.

- Sesión del 5 al 6 de noviembre de 2026, 5 h 53 min reales y 6.391,24 min simulados (4,4 días); el usuario confirmó ausencia de intervención en las decisiones y solo ajuste de velocidad (aprox. ×60).
- `PRAGMA integrity_check = ok`; **6.182** filas del historial con secuencia continua `1..6182` e IDs de fila no duplicados.
- **566** decisiones `llm_decision`, cada una con proveedor, modelo y hash SHA-256 del contexto; los **566 hashes son distintos**. Los contadores de `session_model_usage` coinciden: 489 deliberaciones Gemini 3.1 Flash-Lite, 76 Gemini 3.5 Flash-Lite y 1 Gemini 3.8 Flash; una llamada adicional de chat Gemini 3.5 fuera de las deliberaciones autónomas.
- **350 mediciones** físicas con ID único y **350 diagnósticos** con ID único: 257 éxitos físicos registrados, 93 fallos explícitos. Las categorías incluyen exploración, navegación, recolección, inspección, descanso, fabricación y uso.
- Hubo progreso observable fuera del estancamiento: descubrimiento de agua, fabricación y prueba de recipiente, y posteriormente exploración y recolección autónomas. La corrida **no** garantiza calidad de las conclusiones del agente.
- **CI de refactor**: [run #42159680935](https://github.com/mxlzz/Nilo_public/actions/runs/42159680935), resultado `success`. Incluye auditores de módulos, integridad de contratos, pruebas focalizadas de etapa 23, suite sin credenciales, escenarios físicos, replay determinista y prueba del bundle portátil desde ZIP. El job de proveedor real se omitió porque solo se ejecuta manualmente. Etapa 22 incorporó ensayos sintéticos de carga y compatibilidad previa; no se confunden con conducta autónoma.

**Limitaciones que permanecen abiertas:** `engine_sessions.code_commit=NULL` y `engine_version=0.6.4` en el snapshot, lo que impide verificar con esa base, por sí sola, el commit concreto utilizado. Se conoce la procedencia declarada por el usuario, pero no se certifica criptográficamente. **Groq: no hubo una respuesta de deliberación exitosa registrada ni ejecución autónoma real con ese proveedor en estos snapshots.** No afirmar cobertura de ambas redes.

## Anomalías funcionales preexistentes / seguimiento posterior

- Rechazos reiterados de cierre de proyectos, recreación de un mismo proyecto luego de terminarlo y criterios de evidencia de objetivos compuestos; [partida inicial](ETAPA_23_CORRIDA_REAL_01_07.md), [continuación](ETAPA_23_CORRIDA_REAL_02_07.md).
- Elección de direcciones sin frontera explorable, pese a existir sectores aún explorables.
- Se localizaron los controles de cierre en `nilo_runtime/autonomy/goal_evidence.py`, `nilo_runtime/autonomy/projects.py` y `nilo_runtime/application/decisions.py`. Esto acredita **capacidad de localizar reglas y observar eventos**, pero **no** demuestra por sí solo menor tiempo de mantenimiento ni mejora conductual.
- Ninguna de estas anomalías ha sido demostrada como introducida por la refactorización. Se traslada su mejora al backlog funcional después de 0.7, salvo hallazgo nuevo que bloquee integración. Se conserva la evidencia y se evita afirmar que están resueltas.

## Dictamen

**Etapa 23 cerrada en el alcance acordado: validación de integración y auditabilidad con una sesión real y CI de regresión.** No se ejecutaron cambios al motor por conjeturas de comportamiento. Las pruebas no evidencian una regresión nueva atribuible al refactor, pero la falta de baseline real emparejado impide demostrar equivalencia conductual universal.

**Se habilita etapa 24**, que sigue exigiendo limpieza del árbol, examen de adaptadores heredados, coherencia de números/manifest, seguridad, distribución, instalación nueva, importación de partida y rollback. **No fusionar PR #77 ni publicar 0.7.0 por el solo cierre de etapa 23.**
