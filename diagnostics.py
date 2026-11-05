"""Diagnóstico verificable y paquetes de revisión para Nilo.

Frontera deliberada: detectar invariantes no requiere LLM; el reporte
no declara un bug corregido, no ejecuta código ni cambia leyes físicas.
El paquete sólo usa evidencia registrada, no inspecciona secretos del mundo.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from copy import deepcopy


CHECKS = {
    "position_invalid": "Posición fuera de la topología representada",
    "inventory_negative": "Inventario con cantidad negativa",
    "need_out_of_range": "Necesidad fuera del intervalo físico admitido",
    "result_status_mismatch": "Estado estructurado incompatible con el resultado",
}


def _hash(value):
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def inspect_invariants(world, person, action_result, position, environment_id="isla_v1"):
    """Inspecciones internas de integridad, sin interpretar hechos narrados.

    No supone que un ensayo fallido es un bug. Sólo comprueba invariantes de
    representación inequívocos, tras una acción del motor.
    """
    issues = []
    if environment_id == "isla_v1":
        levels = world.get("levels", {})
        x, y, z = position if isinstance(position, (list, tuple)) and len(position) == 3 else (None, None, None)
        grid = levels.get(str(z))
        in_grid = (isinstance(x, int) and isinstance(y, int) and
                   isinstance(grid, list) and 0 <= y < len(grid) and
                   0 <= x < len(grid[y]))
        if not in_grid:
            issues.append({"check_id": "position_invalid", "observed": list(position)
                           if isinstance(position, (list, tuple)) else str(position)})

    for name, qty in person.get("inventory", {}).items():
        if isinstance(qty, (int, float)) and qty < 0:
            issues.append({"check_id": "inventory_negative",
                           "observed": {"material": str(name)[:80], "quantity": qty}})
    for name, number in person.get("needs", {}).items():
        if isinstance(number, (int, float)) and not (0 <= number <= 100):
            issues.append({"check_id": "need_out_of_range",
                           "observed": {"need": str(name)[:70], "value": number}})
    if action_result is not None:
        status = action_result.status
        success = action_result.success
        if status not in ("verified_success", "verified_failure", "no_evaluable", "precondition_failed") or (
            status == "verified_success" and not success) or (
            status in ("verified_failure", "no_evaluable", "precondition_failed") and success):
            issues.append({"check_id": "result_status_mismatch",
                           "observed": {"status": status, "success": success}})
    return issues


def record_invariant_issue(person, issue, outcome, stamp, environment_id):
    """Registrar una sola solicitud pendiente por invariante y operación.

    Se vincula exclusivamente a resultados act- existentes. Un informe
    automático no equivale a confirmar la causa del problema.
    """
    check_id = issue.get("check_id")
    if check_id not in CHECKS or not outcome or not outcome.get("id"):
        return None
    for proposal in person.get("proposals", []):
        if (proposal.get("type") == "debug" and proposal.get("check_id") == check_id
                and proposal.get("related_action") == outcome.get("op")
                and proposal.get("status") in ("pendiente", "requiere_ampliacion",
                    "error_confirmado_pendiente_de_correccion")):
            return None
    proposal = {
        "id": "bug-" + uuid.uuid4().hex[:10], "type": "debug",
        "issue_kind": "error", "manual_reference": str(outcome.get('op',''))[:32],
        "origin": "motor", "check_id": check_id, "when": stamp,
        "title": "Chequeo de integridad: " + CHECKS[check_id],
        "expected": "El estado debe satisfacer el invariante " + check_id + ".",
        "observed": json.dumps(issue.get("observed"), ensure_ascii=False)[:650],
        "rationale": "Chequeo determinista del motor. El origen del fallo requiere revisión independiente.",
        "related_action": str(outcome.get("op", ""))[:32],
        "evidence": [deepcopy(outcome)], "status": "pendiente",
        "review": None, "environment_id": environment_id,
    }
    person.setdefault("proposals", []).append(proposal)
    return proposal


def record_contract_issue(person, contract, outcome, stamp, environment_id):
    """Informa únicamente una contradicción mecánica acreditada por el contrato.

    No presenta los rechazos normales como fallos, no modifica código, ni
    considera un informe automático como diagnóstico confirmado.
    """
    if contract.get('status')!='posible_error' or not outcome.get('id'):
        return None
    op=str(outcome.get('op') or '')[:40]
    code=str(contract.get('code') or '')[:80]
    if not code:return None
    for existing in person.get('proposals',[]):
        if (existing.get('type')=='debug' and existing.get('check_id')=='contract_'+code
            and existing.get('related_action')==op
            and existing.get('status') in ('pendiente','requiere_ampliacion',
                                           'error_confirmado_pendiente_de_correccion')):
            return None
    data={
        'id':'bug-'+uuid.uuid4().hex[:10], 'type':'debug',
        'issue_kind':'error','origin':'motor','check_id':'contract_'+code,
        'manual_reference':op,'when':stamp,
        'title':'Posible contradicción del contrato: '+code.replace('_',' '),
        'expected':str(contract.get('expected') or '')[:650],
        'observed':json.dumps(contract.get('observed'),ensure_ascii=False,default=str)[:650],
        'rationale':'Contraste determinista entre estado anterior y posterior. La causa aún requiere revisión.',
        'related_action':op,'evidence':[deepcopy(outcome)],
        'status':'pendiente','review':None,'environment_id':environment_id
    }
    person.setdefault('proposals',[]).append(data)
    return data


def review_packet(person, proposal_id, scenario_id=None, environment_id=None, version=None):
    """Paquete JSON auditable. No contiene mundo oculto, claves, chat ni configuración.

    Incluye un bosquejo de reproducción a partir de acciones acreditadas, pero
    SIN afirmar replay exacto: faltan mundo inicial/RNG/reloj por acción.
    """
    proposal = next((p for p in person.get("proposals", []) if p.get("id") == proposal_id), None)
    if proposal is None:
        raise ValueError("No existe esa solicitud.")
    kind = proposal.get("type", "physics")
    if kind not in ("debug", "physics"):
        raise ValueError("Tipo de propuesta no reconocido.")
    source = "motor" if proposal.get("origin") == "motor" else "nilo"
    records = (person.get("action_outcomes", []) if kind == "debug"
               else person.get("unmodeled_attempts", []))
    valid = {r.get("id"): r for r in records if isinstance(r, dict) and r.get("id")}

    # Vincular IDs que siguen en la ventana de historial o evidencia previamente
    # archivada con la propuesta (no sustituirlos con referencias inventadas).
    attached = [r for r in proposal.get("evidence", []) if isinstance(r, dict) and r.get("id")]
    requested = [r.get("id") for r in attached]
    if kind == "physics":
        requested = list(dict.fromkeys([*proposal.get("evidence_ids", []), *requested]))
    verified = []
    for rid in requested:
        record = valid.get(rid)
        if record is None:
            record = next((a for a in attached if a.get("id") == rid), None)
        if record is not None and rid not in [v["id"] for v in verified]:
            verified.append(deepcopy(record))
    evidence = []
    for r in verified[:12]:
        if kind == "debug":
            evidence.append({k: r[k] for k in (
                "id", "when", "op", "target", "pos", "success", "facts",
                "evaluation_status", "physical_result", "action_result",
            ) if k in r})
        else:
            evidence.append({k: r[k] for k in (
                "id", "when", "op", "target", "method", "phenomenon",
                "missing_capability", "test", "result", "position",
            ) if k in r})
    if kind == "debug":
        statement = {k: proposal.get(k) for k in (
            "title", "expected", "observed", "rationale", "related_action",
            "check_id") if proposal.get(k) is not None}
        observed_states = sorted({r.get("evaluation_status", "sin_estado_estructurado")
                                  for r in evidence})
        reproduction = {
            "status": "orientativo_sin_snapshot_inicial",
            "acciones_observadas": [
                {"op": r.get("op"), "target": r.get("target"), "pos": r.get("pos"),
                 "status": r.get("evaluation_status")} for r in evidence],
            "pasos_recomendados": [
                "Partir de una copia aislada de la partida y el mismo escenario.",
                "Comprobar condiciones materiales, posición y estado previo de la acción.",
                "Repetir la operación y comparar estado estructurado y cambios físicos.",
                "Ejecutar tests y replay de regresión antes de aceptar correcciones.",
            ],
            "estados_observados": observed_states,
        }
    else:
        statement = {k: proposal.get(k) for k in (
            "phenomenon", "missing_capability", "rationale", "experiment", "context")
            if proposal.get(k) is not None}
        reproduction = {
            "status": "requiere_implementacion_de_fisica",
            "pasos_recomendados": [
                "Definir magnitudes, condiciones y resultados verificables del fenómeno.",
                "Agregar pruebas de límites y regresión en rama aislada.",
                "Evaluar la propuesta sin convertir una aprobación en ley activa.",
            ],
        }
    payload = {
        "format": "nilo-diagnostic-v1", "proposal_id": proposal_id,
        "kind": kind, "origin": source, "status": proposal.get("status"),
        "created": proposal.get("when"), "scenario_id": scenario_id,
        "environment_id": environment_id or proposal.get("environment_id"),
        "engine_version": version, "statement": statement,
        "evidence_ids": [e["id"] for e in evidence], "evidence": evidence,
        "review": proposal.get("review"), "reproduction": reproduction,
        "evidence_level": ("registro_verificado" if evidence else "sin_evidencia_adjunta"),
        # La existencia del registro está verificada; su pertinencia causal
        # puede seguir siendo hipotética cuando solo coincide la operación.
        "evidence_association": proposal.get(
            "evidence_relation",
            "invariante_motor" if source == "motor" else "legado_sin_clasificar"),
        "code_change_allowed": False, "automatic_patch": False,
    }
    # El hash verifica integridad de este JSON, no certifica la veracidad
    # de la interpretación de Nilo ni reemplaza una firma digital.
    return {"digest_sha256": _hash(payload), **payload}
