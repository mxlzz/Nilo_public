# Nilo 0.7 — Etapa 17: proyectos, agenda, hábitos y reconsideración

Fecha: 5 de noviembre de 2026. Rama de trabajo: refactor/0.7. Baseline estable: main 0.6.4.

[Plan de 25 etapas](PLAN_REESTRUCTURACION_NILO_07.md) · [Seguimiento](ESTADO_REESTRUCTURACION_07.md) · [PR #77](https://github.com/mxlzz/Nilo_public/pull/77) · [Issue #74](https://github.com/mxlzz/Nilo_public/issues/74).

## 1. Auditoría del estado anterior

Se revisaron las transiciones de proyecto y validación de objetivos; las agendas y recordatorios; las actividades delegadas y su aprendizaje; las alertas de repetición; y la coordinación de los casos de uso de decisions y clockwork. También se examinaron escenarios de versiones históricas.

Hallazgos verificados:

- La continuación local sin LLM podía disparar una prueba de herramienta nueva no escogida en el último plan. En reglas actuales la herramienta solo se prueba si Nilo eligió el ensayo; la ruta anterior persiste únicamente para reproducir partidas antiguas.
- Retirar un proyecto como terminado modificaba su estado antes de rechazar una llamada sin evidencia. Ahora esa precondición se comprueba antes de cualquier escritura sobre el proyecto.
- La coordinación de un retiro borraba incondicionalmente active_research, aunque una investigación de otro proyecto continuara abierta. El motor actual respeta las relaciones explícitas de IDs y deja activa la investigación independiente. La limpieza histórica se conserva solo en replay.
- Una tarea diferida de un proyecto abandonado o inexistente podía ejecutarse al cumplirse su condición. El selector ahora verifica que el proyecto propietario siga activo; las pausadas quedan pospuestas, las retiradas o sin dueño activo se cancelan. Un recordatorio puede avisar durante la pausa, sin reanudar por sí mismo el proyecto.
- Las políticas actuales de bebida, recolección y forraje podían consultar agua o vegetación no revelada o calcular alguna ruta sin known_only. Se exige información espacial descubierta para las delegaciones nuevas; el comportamiento anterior se conserva solo por la ruta legacy de hábitos.
- El validador de condiciones de agenda podía admitir NaN, infinito y booleanos por conversión; coordenadas infinitas podían generar excepciones. Esas propuestas se rechazan antes de ejecutar.
- Los hábitos materiales delegados podían repetir un procedimiento fallido sin límite claro. Tras tres resultados fallidos consecutivos de la misma operación y objetivo, el selector actual suspende la delegación hasta que Nilo vuelva a autorizarla en una deliberación. Esto no elimina su aprendizaje ni añade objetivos automáticos.
- La repetición de experiment, use o explore se agrupaba solo por nombre de operación, confundiendo objetivos y lugares diferentes. Los intentos actuales incorporan método, material u objeto, dirección y destino. El diagnóstico de reiteración es informativo: no cancela la acción vigente.
- La evidencia de cierre admitía un fragmento de la descripción verificada o un prefijo de ID como cita. La comprobación exige ahora el ID completo delimitado o el texto íntegro del resultado registrado, además de requisitos físicos instrumentados. La semejanza narrativa no confirma objetivos.

## 2. Arquitectura resultante

La capa nueva nilo_runtime/autonomy contiene seis módulos propietarios:

1. projects.py: retiro, pausa, abandono, cierre con evidencia, preservación de investigaciones relacionadas y guardas de transición.
2. goal_evidence.py: verificación física del objetivo, resolución de mediciones pertinentes y validación estricta de citas.
3. progress.py: evidencia de avance material o de descubrimiento, separada de porcentajes subjetivos.
4. strategy.py: firmas operativas y alertas por método, objeto, material o destino, sin vetos automáticos.
5. agenda.py: condiciones normalizadas, estado de proyecto, comprobación anterior a cada paso y diferencia entre ejecutar una tarea y cumplir el objetivo declarado.
6. habits.py: capacidades aprendidas, delegaciones del LLM, recursos y rutas conocidos, intentos y límites de reiteración.

Los archivos anteriores project_lifecycle.py, goal_evidence.py, project_progress.py, strategy_review.py, agenda.py y habits.py permanecen como fachadas de importación, sin segundas implementaciones. tools/auditar_arquitectura.py reconoce la nueva capa y supervisa sus dependencias.

El orquestador conserva la coordinación, la física y el replay, y deja el ciclo de vida bajo esos propietarios. No hay otra agenda ni otro router de proveedores.

## 3. Contrato de autonomía

Proyecto activo: Nilo elige continuar, pausar, abandonar o solicitar cierre. Completar exige una prueba pertinente y citada del motor. Pausar no equivale a completar ni a fracaso físico; abandonar tampoco. Los proyectos no asignan misiones a Nilo por el solo hecho de existir.

Agenda: únicamente pasos que Nilo delegó; cada operación vuelve a verificar condiciones reales. Un recordatorio puede pasar a listo sin ejecutar trabajo. La conclusión de pasos no demuestra el propósito escrito en el título.

Hábitos: ninguna rutina consume agua o alimentos solo porque el personaje cruza un umbral. El descanso voluntario conserva duración elegida. Las actividades materiales solo utilizan competencias comprobadas y no obtienen acceso a casillas ocultas. Tres fallos de una delegación requieren una nueva decisión para volver a intentarla. Reautorizar no fuerza ejecución: las precondiciones físicas siguen siendo obligatorias.

Reconsideración: la repetición se describe por la misma operación y los mismos parámetros de ensayo, con datos físicos verificables. El diagnóstico no cambia automáticamente de proyecto ni elimina pasos; permite que Nilo decida.

Compatibilidad: se preserva SQLite v5, la física vigente, el historial de mundos anteriores y el baseline 0.6.4. No se reescribieron partidas personales.

## 4. Puertas de salida y evidencia

- Auditor específico tools/auditar_autonomia_17.py: propietarios únicos, facades sin duplicación, guardas de proyecto, límites espaciales, selección por IDs y exclusión de continuaciones inventadas.
- tests/test_autonomia_17.py: 28 casos nuevos (cierre atómico; continuidad de investigaciones; pausas y recordatorios; delegaciones finitas; entradas inválidas; terreno descubierto; estrategias diferenciadas; prueba exacta de cierre; compatibilidad de importaciones).
- [CI integral #42059108778](https://github.com/mxlzz/Nilo_public/actions/runs/42059108778): **success**; 912 tests ejecutados, uno omitido; auditoría y 28 pruebas de la etapa 17 aprobadas. También pasaron los escenarios físicos deterministas, reproducción sin LLM, ZIP portable y replay entre procesos con fingerprint idéntico 9c4d43a5815fb042e06e32789b7dc6606023c3eb0634fe08dd7ad90616dc5c24.
- [Compatibilidad histórica #42059108934](https://github.com/mxlzz/Nilo_public/actions/runs/42059108934): **success**; seis partidas históricas SQLite sintéticas importadas sobre copias, sin alterar el original.
- Los fixtures históricos adaptados reflejan explícitamente un proyecto activo antes de ejecutar su agenda y sitúan el mock en el nuevo propietario real. El baseline no perdió sus pruebas funcionales.
- Las ejecuciones sintéticas no demuestran mejor iniciativa ni ausencia de bucles en Gemini/Groq reales: evaluación reservada a la etapa 23.

## 5. Pendientes

Etapa 18: persistencia, migraciones y transacciones; revisar continuidad de tareas y reintentos a través de escrituras y reanudaciones. Etapa 22: pruebas largas y rendimiento. Etapa 23: comparar autonomía real con proveedores. Etapa 24: cierre, rollback, entrega y publicación de 0.7.0.

La etapa 17 queda cerrada tras CI y compatibilidad histórica aprobadas; no autoriza fusionar PR #77 ni publicar la versión intermedia.
