"""Estadísticas factuales de conducta, sin atribuir motivaciones ni personalidad.

Se registran solo acciones completadas desde que se incorporó este contador.
Una partida importada no recibe reconstrucciones ficticias de su pasado.
"""
from __future__ import annotations

GROUPS = {
    "exploracion": {"explore", "go", "inspect", "descend", "ascend"},
    "experimento": {"experiment", "compare", "conclude", "use"},
    "fabricacion": {"combine", "build", "craft", "assemble", "modify", "dismantle", "excavate"},
    "mantenimiento": {"gather", "forage", "eat", "drink", "rest"},
    "documentacion": {"design", "propose", "report_issue", "write"},
}


def _group(op):
    return next((name for name, operations in GROUPS.items() if op in operations), "otra")


def record_behavior(person, *, op, origin, duration_minutes, position_before,
                    position_after, project_id=None, new_tiles=0,
                    new_knowledge=0, new_materials=(), progress=False):
    """Incorpora una acción terminada. No infiere novedad a partir de prosa del LLM."""
    minute = round(float(person.get("clock_minutes", 0)), 3)
    state = person.setdefault("behavior_metrics", {
        "since_minute": minute, "actions": 0, "by_group": {},
        "by_origin": {}, "time_measured_by_group": {},
        "measured_actions": 0, "progress_actions": 0,
        "new_tiles": 0, "new_knowledge": 0, "novelty_actions": 0,
        "gained_materials": [], "moved_positions": [],
        "revisited_destinations": 0, "project_switches": 0,
        "last_project": None
    })
    group = _group(str(op))
    state["actions"] += 1
    for key, value in (("by_group", group), ("by_origin", str(origin or "llm"))):
        counts = state.setdefault(key, {})
        counts[value] = counts.get(value, 0) + 1
    if isinstance(duration_minutes, (int, float)) and not isinstance(duration_minutes, bool) and duration_minutes >= 0:
        times = state.setdefault("time_measured_by_group", {})
        times[group] = round(times.get(group, 0) + float(duration_minutes), 3)
        state["measured_actions"] += 1
    state["progress_actions"] += int(bool(progress))
    new_tiles = max(0, int(new_tiles))
    new_knowledge = max(0, int(new_knowledge))
    state["new_tiles"] += new_tiles
    state["new_knowledge"] += new_knowledge
    materials = set(state.get("gained_materials", []))
    gained = {str(v) for v in new_materials if v}
    state["gained_materials"] = sorted(materials | gained)
    if new_tiles or new_knowledge or (gained - materials):
        state["novelty_actions"] += 1
    if (position_after is not None and position_before is not None
            and list(position_after) != list(position_before)):
        key = ",".join(str(int(v)) for v in position_after)
        visited = state.setdefault("moved_positions", [])
        if key in visited:
            state["revisited_destinations"] += 1
        else:
            visited.append(key)
    project_id = str(project_id) if project_id else None
    old_project = state.get("last_project")
    if project_id and old_project and project_id != old_project:
        state["project_switches"] += 1
    if project_id:
        state["last_project"] = project_id
    return state


def behavior_summary(person):
    """Cifras acumuladas de instrumentación, no rasgos psicológicos."""
    state = person.get("behavior_metrics")
    if not state or not state.get("actions"):
        return {"estado": "sin_datos", "acciones_registradas": 0,
                "nota": "No se han instrumentado acciones desde esta versión."}
    n = state["actions"]
    return {
        "estado": "parcial_desde_instrumentacion",
        "desde_minuto_simulado": state.get("since_minute"),
        "acciones_registradas": n,
        "acciones_por_clase": dict(state.get("by_group", {})),
        "acciones_por_origen": dict(state.get("by_origin", {})),
        "minutos_medidos_por_clase": dict(state.get("time_measured_by_group", {})),
        "acciones_con_duracion_medida": state.get("measured_actions", 0),
        "acciones_con_progreso_segun_motor": state.get("progress_actions", 0),
        "acciones_con_novedad_observable": state.get("novelty_actions", 0),
        "proporcion_con_novedad_observable": round(state.get("novelty_actions", 0) / n, 3),
        "casillas_nuevas_reveladas": state.get("new_tiles", 0),
        "registros_de_conocimiento_nuevos": state.get("new_knowledge", 0),
        "materiales_distintos_obtenidos": len(state.get("gained_materials", [])),
        "destinos_distintos_al_moverse": len(state.get("moved_positions", [])),
        "regresos_a_destinos_ya_visitados": state.get("revisited_destinations", 0),
        "cambios_entre_proyectos_activos": state.get("project_switches", 0),
    }
