"""Ciclo de vida de proyectos, independiente de la cola de operaciones.

El resultado expresa solo el destino del proyecto y la atribución histórica.
Nunca valida/borra planes físicos, registra un cuaderno ni ejecuta una agenda.
El motor conserva la propiedad de las transiciones mediante este puerto.
"""
from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

from cognition import same_research
from nilo_runtime.autonomy.projects import (
    completion_evidence, closure_diagnostic, project_needs_review, retire_project,
)
from nilo_runtime.core.identity import new_uuid
from agenda import acknowledge_reminders


@dataclass(frozen=True)
class ProjectTransition:
    """Resultado de dominio; la ejecución de acciones es una decisión separada."""
    kind: str                  # unassigned | active | retired | missing
    requested_action: str
    effective_action: str
    project_id: str | None = None
    project: dict | None = None
    retired_status: str | None = None


_STATUS = {"completar": "terminado", "abandonar": "abandonado",
           "pausar": "pausado"}


def _select_project(person, action, selected_id, objective):
    """Consultar antes de mutar. Nunca quitar de proyectos un ID inválido."""
    current = person.get("project")
    saved = person.setdefault("projects", [])
    if action == "nuevo":
        return None
    if selected_id:
        if current and current.get("id") == selected_id:
            return current
        match = next((record for record in saved
                      if record.get("id") == selected_id
                      and record.get("status") != "terminado"), None)
        if match is not None:
            return match
    if current and (action == "continuar" or
                    (action != "nuevo" and
                     SequenceMatcher(None, current.get("title", "").lower(),
                                     objective.lower()).ratio() > .82)):
        return current
    return None


def _record_rejected_closure(sim, target, proof):
    from goal_evidence import check_goal
    person = sim.s["person"]
    valid, ids, reason = (check_goal(target, person, proof) if target else
                          (False, [], "No hay proyecto activo."))
    if valid:
        reason = ("El objetivo tiene mediciones pertinentes, pero la prueba de cierre "
                  "no cita una de ellas. ID verificable: " + ", ".join(ids[:5]) + ".")
    fields = {}
    if not getattr(sim, "historical_replay", False):
        diagnosis = closure_diagnostic(target, person, proof)
        fields = {
            "estado_verificacion": diagnosis["estado"],
            "ids_evidencia_pertinente": diagnosis["ids_evidencia"][:6],
            "limitacion_fisica": (diagnosis["motivo"]
                if diagnosis["estado"] == "criterio_no_instrumentado" else None),
        }
    person["last_closure_rejection"] = {
        **fields, "project_id": (target or {}).get("id"),
        "objective": (target or {}).get("title"), "reason": reason,
        "when": sim.stamp(), "not_a_completed_goal": True,
        "next_options": (
            ["reformular el objetivo hacia una propiedad medible",
             "pausar", "abandonar"]
            if fields.get("estado_verificacion") == "criterio_no_instrumentado"
            else ["continuar con una evidencia pertinente", "pausar", "abandonar"]),
    }
    sim.event(["No puedo declarar el objetivo cumplido: " + reason +
               " Puedo continuar, pausarlo o abandonarlo sin simular un éxito."],
              "evaluación")


def apply_project_transition(sim, decision, source):
    """Mutar solamente el ciclo de vida del proyecto; no tocar person.plan.

    Reglas:
      - sin_proyecto deja intacto un proyecto eventualmente activo;
      - completar requiere prueba verificable; el rechazo no archiva nada;
      - pausar/abandonar son decisiones, no pruebas de éxito;
      - un proyecto nuevo retira formalmente el anterior, incluidas sus tareas;
      - continuar un proyecto pausado lo retoma tras comprobar su ID;
      - los pasos físicos del mismo turno no se examinan aquí.
    """
    person = sim.s["person"]
    saved = person.setdefault("projects", [])
    current = person.get("project")
    action = decision.get("accion_proyecto", "nuevo")
    if action == "sin_proyecto":
        return ProjectTransition("unassigned", action, action)

    objective = decision.get("objetivo") or "Investigar el entorno"
    selected = _select_project(person, action, decision.get("proyecto_id") or "",
                               objective)
    if action in _STATUS:
        target = selected or current
        if target is None:
            sim.event(["No hay un proyecto identificado para cerrar o pausar."],
                      "evaluación")
            return ProjectTransition("missing", action, action)
        if action == "completar":
            proof = (decision.get("prueba_cierre") or "").strip()
            evidence = completion_evidence(target, proof, person)
            if not evidence:
                _record_rejected_closure(sim, target, proof)
                # El rechazo deja activo el proyecto actual. Si solo existe
                # un proyecto pausado, no lo reanuda ni genera uno ficticio.
                if current is None:
                    return ProjectTransition("missing", action, "cierre_rechazado",
                                             target.get("id"))
                selected = current
            else:
                retire_project(person, target, "terminado", sim.stamp(),
                               reason=decision.get("estado_actual") or
                                      decision.get("motivo"),
                               evidence=evidence)
                sim.event(["Di por terminado el proyecto con la evidencia registrada: " +
                           target.get("title", "Proyecto")], "decision", True)
                return ProjectTransition("retired", action, action,
                                         target.get("id"), retired_status="terminado")
        else:
            status = _STATUS[action]
            retire_project(person, target, status, sim.stamp(),
                           reason=decision.get("estado_actual") or
                                  decision.get("motivo"))
            prefix = ("Decidí abandonar esta investigación sin declarar el objetivo cumplido: "
                      if status == "abandonado" else
                      "Decidí pausar la investigación y conservar sus resultados: ")
            sim.event([prefix + target.get("title", "Proyecto")], "decision", True)
            return ProjectTransition("retired", action, action,
                                     target.get("id"), retired_status=status)

    chosen = selected
    if chosen is None:
        precedent = next((old for old in reversed(saved)
                          if old.get("status") in ("pausado", "abandonado")
                          and same_research(old.get("title", ""), objective)), None)
        if current and current.get("status") != "terminado":
            # Pasar por la misma transición que una pausa explícita: cancelar
            # o suspender agenda y clasificar investigaciones vinculadas.
            retire_project(person, current, "pausado", sim.stamp(),
                           reason=current.get("state") or "Cambio de proyecto")
        chosen = {
            "id": str(new_uuid())[:8], "title": objective,
            "reason": decision.get("motivo", ""),
            "started": sim.stamp(), "source": source,
            "status": "activo", "progress": 0, "steps_done": 0,
            "failed_actions": 0, "no_progress_steps": 0,
            "verified_results": [], "subgoals": [],
            "deliberations": 0, "deliberations_since_progress": 0,
            "state": decision.get("estado_actual") or "Definiendo los siguientes pasos",
        }
        if precedent:
            chosen["antecedente_pausado"] = {
                "id": precedent.get("id"), "titulo": precedent.get("title"),
                "estado": precedent.get("status"),
                "motivo": precedent.get("closure_reason"),
                "acciones_sin_avance": precedent.get("no_progress_steps", 0),
            }
            sim.remember_strategy(
                "Este tema se parece a una investigación antes suspendida: " +
                str(precedent.get("title", ""))[:95] +
                ". Revisar sus evidencias y motivo antes de considerar nueva una prueba repetida.")
        sim.event(["Me propuse: " + chosen["title"]], "decision", True)
    else:
        if chosen.get("status") == "pausado":
            for task in person.get("agenda", []):
                if (task.get("proyecto_id") == chosen.get("id")
                        and task.get("ultimo_motivo") == "Proyecto pausado"
                        and task.get("estado") == "pospuesta"):
                    task["reanudar_minuto"] = person.get("clock_minutes", 0)
                    task["ultimo_motivo"] = "Proyecto retomado"
        acknowledge_reminders(person, chosen.get("id"), sim.stamp())
        chosen["status"] = "activo"
        chosen["reason"] = decision.get("motivo") or chosen.get("reason", "")
        chosen["state"] = (decision.get("estado_actual") or
                           chosen.get("state", "Continuando la investigación"))
        sim.event(["Retomé el proyecto: " + chosen["title"]], "decision")

    if chosen in saved:
        saved.remove(chosen)
    chosen["progress"] = min(95, max(0, int(decision.get("avance_estimado", 0))))
    chosen["deliberations"] = chosen.get("deliberations", 0) + 1
    chosen["deliberations_since_progress"] = (
        chosen.get("deliberations_since_progress", 0) + 1)
    if project_needs_review(chosen):
        chosen["reconsideration_required"] = True
        chosen["state"] = ("Objetivo prolongado sin nuevos resultados: revisar "
                           "si conviene continuar, pausar o cambiar de proyecto.")
        sim.remember_strategy(
            "Este proyecto lleva varias deliberaciones sin avances materiales. "
            "Elegí explícitamente continuar, iniciar otro o completar SOLO con evidencias.")
    if decision.get("subobjetivos"):
        chosen["subgoals"] = decision["subobjetivos"][:6]
    chosen["updated"] = sim.stamp()
    chosen["reconsideration_required"] = bool(
        chosen.get("reconsideration_required") and project_needs_review(chosen))
    person["project"] = chosen
    return ProjectTransition("active", action,
                             "continuar" if action == "completar" else action,
                             chosen.get("id"), chosen)
