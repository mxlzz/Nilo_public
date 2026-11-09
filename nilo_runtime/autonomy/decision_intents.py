"""Acciones inmediatas y atribución documental, independientes del proyecto.

Una transición del ciclo de vida NO invalida un plan físico. Cada operación
sigue pasando por improve_plan + validate_plan y por el motor de mundo.
La agenda diferida sí tiene dueño: nunca ejecutar tareas del proyecto retirado.
"""
from __future__ import annotations

from agenda import set_agenda
from habits import set_wait_preferences


def admit_immediate_actions(sim, decision, source, transition):
    """Un único sitio para admitir operaciones de TODAS las deliberaciones.

    Las actividades explícitas pueden suceder aun cuando un proyecto se pause,
    abandone o complete. No restauran automáticamente un proyecto archivado.
    El cierre y los efectos físicos se registran por canales separados.
    """
    person = sim.s["person"]
    person["plan"] = sim.validate_plan(sim.improve_plan(decision.get("plan") or []))
    review_minutes = decision.get("revisar_en_minutos", 90)
    person["review_at_minutes"] = (person.get("clock_minutes", 0) + review_minutes
                                   if person["plan"] or transition.kind == "active"
                                   else person.get("clock_minutes", 0))
    person["local_followups"] = 0
    sim.s["last_reason"] = decision.get("motivo", "")
    if transition.kind == "active" and not person["plan"]:
        sim.event(["El plan del modelo quedó sin pasos verificables; necesito reconsiderar."],
                  "evaluación")
    if source != "llm":
        return

    if transition.kind == "retired":
        # Una pausa puede registrar recordatorios de reanudación pero NO
        # tareas delegadas del proyecto ya archivado.
        set_wait_preferences(person, [], sim.stamp())
        if transition.retired_status == "pausado":
            reminders = [entry for entry in decision.get("agenda", [])
                         if isinstance(entry, dict)
                         and entry.get("modo") == "recordatorio"]
            added = set_agenda(person, reminders, person["clock_minutes"],
                               transition.project_id)
            if added:
                sim.event([f"Dejé {len(added)} recordatorio(s) para reconsiderar "
                           "este proyecto al cumplirse sus condiciones."], "agenda")
        return

    # Los proyectos nuevos/activos son dueños de sus tareas; las actividades
    # sin proyecto usan ID nulo. Una solicitud de cierre sin proyecto no crea
    # tareas fantasma ni atribuye acciones a una investigación inexistente.
    if transition.kind == "missing":
        set_wait_preferences(person, [], sim.stamp())
        return
    set_wait_preferences(person, decision.get("actividades_en_espera"),
                         sim.stamp())
    added = set_agenda(person, decision.get("agenda", []),
                       person["clock_minutes"],
                       transition.project_id if transition.kind == "active" else None)
    if added:
        sim.event([f"Preparé {len(added)} tarea(s) para ejecutar más adelante, "
                   "si se cumplen las condiciones."], "decisión")


def record_decision_note(sim, decision, source, project_id=None,
                         research_id=None, trace_link=None, tokens=None):
    """Un solo cuaderno para continuar, pausar, completar o actuar sin proyecto.

    La nota se vincula con el ID histórico aun después de retirarlo. Solo las
    acciones del plan de esta deliberación adquieren _journal_id.
    """
    linked = {"project_id": project_id, "research_id": research_id}
    note = sim.journal(decision["cuaderno"], decision.get("pregunta", ""),
                       decision.get("hipotesis", ""), source, linked=linked)
    if trace_link is not None:
        trace_link(note)
    for action in sim.s["person"].get("plan") or []:
        if action.get("_origin") not in ("agenda", "espera", "rutina", "motor"):
            action["_journal_id"] = note["id"]
    if tokens:
        sim.s["last_tokens"] = tokens
    return note
