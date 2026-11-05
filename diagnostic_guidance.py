"""Diagnóstico prudente, basado exclusivamente en resultados ya registrados.

No crea propuestas, ni cambia la física ni decide objetivos por el agente.
"""
from __future__ import annotations
from collections import defaultdict

KINDS = {
    "uso_incorrecto": ("uso_incorrecto", "Revisar precondiciones, ubicación o procedimiento"),
    "limitacion": ("limitacion_modelada", "Reconsiderar condiciones del ensayo"),
    "posible_error": ("posible_error_contrato", "Revisar evidencia antes de reportar"),
}


def review_recent_attempts(person, limit=7):
    """Agrupar intentos equivalentes y separar fallo, contrato y fenómeno ausente.

    Se registran IDs auténticos. Un fallo físico no prueba carencia de motor.
    """
    recent = person.get("action_outcomes", [])[-60:]
    groups = defaultdict(list)
    for a in recent:
        if not isinstance(a, dict) or not a.get("id"):
            continue
        status = a.get("evaluation_status")
        contract = a.get("contract_status")
        if status == "no_evaluable":
            category = "fenomeno_no_evaluable"
            guidance = "Considerar una ampliación solo si el proyecto la necesita"
        elif contract in KINDS:
            category, guidance = KINDS[contract]
        elif status == "verified_failure":
            category = "fallo_fisico"
            guidance = "Cambiar materiales, método o condiciones y comparar resultados"
        else:
            continue
        code = str(a.get("contract_code") or "")
        key = (a.get("op"), a.get("target"), category, code)
        groups[key].append((a, guidance))
    result = []
    for (op, target, category, code), records in groups.items():
        most_recent = records[-1][0]
        result.append({
            "accion": op,
            "objetivo": target,
            "clasificacion": category,
            "codigo_contrato": code or None,
            "repeticiones": len(records),
            "ids_reales": [a.get("id") for a, _ in records[-4:]],
            "estado": most_recent.get("evaluation_status"),
            "observacion": str(most_recent.get("contract_observed") or
                               (most_recent.get("facts") or [""])[0])[:160],
            "opciones": records[-1][1],
            "requiere_nueva_evidencia": len(records) > 1,
        })
    return result[-max(0, limit):]
