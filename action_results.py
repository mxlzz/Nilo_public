"""Contrato tipado de resultados de acciones.

El motor verifica consecuencias; un mensaje de cuaderno nunca determina
éxito, estado de evaluación ni medidas. Los datos físicos se obtienen de
muestras y pruebas efectivamente registradas durante esta operación.
"""
from __future__ import annotations

from nilo_runtime.core.outcomes import ActionResult, LegacyExecution
from physics import evaluate_buoyancy, evaluate_containment

def evidence_before(agent):
    """Marcadores mínimos para acreditar que una prueba ocurrió AHORA."""
    return {
        "unmodeled": len(agent.get("unmodeled_attempts", [])),
        "knowledge": set(agent.get("knowledge", {})),
        "tests": {obj.get("id"): len(obj.get("tests", []))
                  for obj in agent.get("items", [])},
        "capability_evidence": agent.get("_last_capability_evidence"),
        "capability_diagnostic": agent.get("_last_capability_diagnostic"),
    }


def result_from_execution(step, legacy, agent, before):
    """Empaquetar efectos del motor; ninguna clasificación consulta la narrativa."""
    executed = LegacyExecution.parse(legacy)
    duration, facts, success, notable = (
        executed.duration_minutes, executed.facts,
        executed.success, executed.notable,
    )
    no_evaluable = len(agent.get("unmodeled_attempts", [])) > before["unmodeled"]
    physical = _physical_evidence(step, agent, before, success)
    if physical is None and success and agent.get("_last_capability_evidence") is not before.get("capability_evidence"):
        proof=agent.get("_last_capability_evidence")
        if isinstance(proof,dict):
            physical={"kind":"capability","subject":proof.get("source_id"),
                      "method":proof.get("method"),"metrics":{"quantity":proof.get("quantity")},
                      "conditions":proof,"precision":"unidades abstractas; medición de estados antes/después"}
    diagnostic=agent.get("_last_capability_diagnostic")
    precondition_failed=(
        step.get("op") in ("interact","drink","experiment") and not success
        and isinstance(diagnostic,dict)
        and diagnostic is not before.get("capability_diagnostic")
        and diagnostic.get("status")=="precondition_failed"
    )
    result=ActionResult.from_legacy(
        step, facts, success, notable, duration, no_evaluable=no_evaluable,
        physical=physical,
        status_override="precondition_failed" if precondition_failed else None,
    )
    # Evidencia transitoria consumida por resultado tipado; no persiste como
    # estado extra en la persona ni afecta operaciones posteriores.
    agent.pop("_last_capability_evidence",None)
    agent.pop("_last_capability_diagnostic",None)
    return result


def _tool(agent, name):
    requested = str(name or "").lower().strip()
    items = agent.get("items", [])
    return next(
        (obj for obj in items
         if obj.get("id", "").lower() == requested
         or obj.get("name", "").lower() == requested),
        next((obj for obj in items
              if requested and requested in obj.get("name", "").lower()), None),
    )


def _physical_evidence(step, agent, before, success):
    op = step.get("op")
    method = str(step.get("method") or "").lower().strip()
    if op == "experiment":
        target = str(step.get("target") or "").lower()
        material = next(
            (name for name, qty in agent.get("inventory", {}).items()
             if qty > 0 and name in target and name in agent.get("materials", {})),
            None,
        )
        if not material or not success or f"{material}|{method}" in before["knowledge"]:
            return None
        if f"{material}|{method}" not in agent.get("knowledge", {}):
            return None
        metric = {"golpear": "dureza", "cargar": "resistencia"}.get(method)
        properties = agent["materials"][material]
        if not metric or metric not in properties:
            return None
        return {
            "kind": "material", "subject": material, "method": method,
            "metrics": {metric: round(float(properties[metric]), 3)},
            "conditions": {"material": material, "metodo": method},
            "precision": "escala estimada del motor, 0–10",
        }

    if op != "use":
        return None
    tool = _tool(agent, step.get("item") or step.get("target"))
    if not tool:
        return None
    # Un resultado anterior NO acredita un ensayo nuevo ni genera otra medida.
    previous_count = before["tests"].get(tool.get("id"), 0)
    trials = tool.get("tests", [])
    if len(trials) <= previous_count:
        return None
    trial = trials[-1]
    # El motor registra "llenar" también cuando la orden original fue
    # "contener" agua. Es la misma operación física, no un ensayo nuevo ficticio.
    fill_alias = (method == "contener" and trial.get("method") == "llenar"
                  and trial.get("target") == "agua")
    if (trial.get("method") != method and not fill_alias) or (
            bool(trial.get("success")) != bool(success)):
        return None
    subject = tool.get("id", "")
    geometry = tool.get("geometry") or {}
    conditions = {
        "objeto": subject,
        "version": tool.get("revision", 1),
        "materiales": list(tool.get("materials", [])),
        "forma": geometry.get("shape", "desconocida"),
        "tamano": geometry.get("size"),
    }
    if method in ("llenar", "contener") and success and trial.get("target") == "agua":
        info = evaluate_containment(tool, "agua", agent.get("materials", {}))
        return {
            "kind": "recipiente", "subject": subject, "method": "llenar",
            "metrics": {"capacidad_util_agua": info["quantity"]},
            "conditions": conditions,
            "precision": "capacidad estática estimada por geometría y permeabilidad; no mide fuga, evaporación ni pérdida temporal; unidades abstractas",
        }
    if method in ("flotar", "navegar") and trial.get("target") == "agua":
        info = evaluate_buoyancy(
            tool, passenger=(method == "navegar"), known=agent.get("materials", {}),
        )
        return {
            "kind": "flotacion", "subject": subject, "method": method,
            "metrics": {"empuje": info["buoyant_capacity"], "carga": info["load"]},
            "conditions": conditions,
            "precision": "modelo simplificado de flotación",
        }
    if tool.get("form") == "ensamblaje" and method in ("carga", "resistir_carga"):
        try:
            load = max(0., min(100., float(step.get("load", 3))))
        except (ValueError, TypeError):
            load = 3.
        return {
            "kind": "ensamblaje", "subject": subject, "method": "carga",
            "metrics": {"carga_aplicada": round(load, 2),
                        "limite_carga": round(float(tool.get("resistance", 0)) * 1.5, 2)},
            "conditions": conditions, "precision": "escala de carga abstracta del motor",
        }
    if tool.get("form") == "ensamblaje" and method in ("transmision", "transmitir_movimiento"):
        try:
            energy = max(0., min(100., float(step.get("input_energy", 0))))
        except (ValueError, TypeError):
            energy = 0.
        mobility = any(j.get("type") in ("articulada", "deslizante")
                       for j in tool.get("joints", []))
        shape = any(part.get("shape") in ("rueda", "eje", "cilindro")
                    for part in tool.get("parts", []))
        output = (round(min(float(tool.get("resistance", 0)) * 1.5, energy * .65), 2)
                  if mobility and shape else 0.)
        return {
            "kind": "ensamblaje", "subject": subject, "method": "transmision",
            "metrics": {"energia_aplicada": energy, "energia_salida": output},
            "conditions": conditions, "precision": "transmisión mecánica simplificada",
        }
    return None
