# Nilo 0.7 · Contrato del ciclo de decisiones

**Fecha:** 2026-11-08 · **Estado:** rama experimental, antes de fusión.

## Motivo

En la primera ejecución A/B real con Gemini, la condición B decidió
`accion_proyecto=pausar` y `plan=[{op:rest,minutes:120}]`. El motor archivó
el proyecto y luego ignoró el descanso. La causa era que
`DecisionUseCases.plan_ready` mezclaba transición, validación física, agenda,
cuaderno y atribución de avances.

La corrección inicial preservaba el plan solo en la rama `pausar`, pero
mantenía la dependencia estructural. El contrato de 0.7 es independiente de
los tipos concretos de acción y de la formulación del proyecto.

## Responsabilidades y flujo

1. `nilo_runtime.agent.responses.normalize_decision` verifica el **formato**
   y parámetros sintácticos. No afirma posibilidad física.
2. `nilo_runtime.autonomy.project_decisions.apply_project_transition`
   resuelve **solo el proyecto**: seleccionar/reanudar, crear, pausar,
   abandonar o completar con evidencia. Devuelve `ProjectTransition`.
   Nunca lee ni escribe la cola `person.plan`.
3. `nilo_runtime.autonomy.decision_intents.admit_immediate_actions` recibe
   la misma deliberación y **siempre valida su plan físico**, con
   `improve_plan` y `validate_plan`; admite tareas y hábitos con reglas
   explícitas de propiedad. No declara éxito de una acción.
4. `record_decision_note` almacena la nota una sola vez, con el ID
   histórico del proyecto cuando corresponda, y asigna cada acción
   deliberada a su propia nota y a un **dueño explícito**:
   `_decision_project_id`, que puede valer `null`.
5. `ClockUseCases` verifica las precondiciones y ejecuta operaciones en
   el mundo. `nilo_runtime.core.action_ownership.active_project_for_action` registra sus efectos en el
   proyecto **solo si el dueño explícito coincide con el proyecto
   actualmente activo**. Las acciones históricas sin esa marca conservan
   compatibilidad con las partidas antiguas.

## Matriz de transiciones

| Acción de Nilo | Estado del proyecto | Plan explícito del turno | Agenda / hábitos |
| --- | --- | --- | --- |
| `nuevo` | Crear; pausar formalmente el activo previo | Validar y ejecutar bajo el nuevo ID | Tareas nuevas al nuevo ID; las antiguas pasan a pospuestas |
| `continuar` | Reanudar por ID o continuar el activo | Validar y ejecutar bajo el ID activo | Retomar tareas pospuestas de ese proyecto |
| `sin_proyecto` | No alterar el proyecto que exista | Validar y ejecutar **sin dueño** | Tareas independientes, ID nulo |
| `pausar` | Archivar como pausado, conservar evidencia | Validar y ejecutar **sin dueño** | Solo recordatorios de reanudación; hábitos anteriores desactivados |
| `abandonar` | Archivar sin declarar éxito | Validar y ejecutar **sin dueño** | Cancelar tareas dependientes; no agendar tareas de ese proyecto |
| `completar` | Archivar solo con prueba verificable | Validar y ejecutar **sin dueño** | Cancelar tareas dependientes |
| Cierre rechazado | No archivar ni declarar éxito | Validar y ejecutar según proyecto vigente | Sin nuevas tareas para un proyecto inexistente |

Las operaciones de una deliberación son decisiones voluntarias de Nilo.
La transición de un proyecto **no las invalida implícitamente**. Si
una operación no es físicamente posible, la rechaza el entorno y deja
su diagnóstico. Un cierre sin prueba nunca se transforma en un éxito
por la presencia de otras operaciones.

## Propiedad y conservación

- Los datos reales (mediciones, hechos, necesidades del motor) pertenecen
  al mundo y al observador; la atribución a un proyecto se hace por ID
  efectivo, nunca por mera cercanía temporal o por estar abierto otro
  proyecto.
- El cuaderno de una pausa o cierre se conserva, vinculado al proyecto
  histórico; las acciones posteriores no reactivan el archivo.
- La agenda tiene dueño individual: la pausa pospone tareas; el abandono y
  la finalización las cancelan. Los recordatorios de proyectos pausados
  permanecen como avisos, no ejecutan acciones.
- Las investigaciones abiertas con `project_ids` del proyecto retirado
  se archivan; las vinculadas a otros proyectos continúan abiertas.
- Los replays antiguos sin `_decision_project_id` conservan la atribución
  anterior y se prueban por separado; no se reescriben partidas.
- El laboratorio A/B registra `project_transition` (estado real) además
  de resultados físicos; no usa el SHA físico como prueba de pausa.

## Cobertura verificable

`tests/test_project_decision_boundaries.py` cubre todos los tipos de
transición, ejecución de `rest`/`wait` tras retiro, rechazo de cierre,
propiedad independiente con proyecto activo, pausa formal de tareas al
crear uno nuevo, reanudación y compatibilidad de pasos históricos.

`tests/test_lab_stage11_evaluation.py` cubre el caso A/B real
`pausar + rest(120)`, el archivo del proyecto y el cuaderno.

`tools/auditar_autonomia_17.py` comprueba la conservación de una
investigación no vinculada al proyecto retirado por **comportamiento**,
en lugar de buscar texto de una rama antigua.

## Límites de evidencia

La suite automatizada prueba contratos del motor con SQLite temporal;
no prueba que Gemini elija planes más originales, y no se deben interpretar
dos deliberaciones por rama como una mejora causal. Para evaluar autonomía
real hacen falta varios mundos, réplicas y trazas longitudinales.
