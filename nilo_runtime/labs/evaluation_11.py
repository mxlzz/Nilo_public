"""Etapa 11 · Evaluación verificable de A/B, sin inferir calidad cognitiva.

Trabaja con el resultado real del laboratorio; en modo offline no llama al LLM.
Los informes no contienen payload, cuaderno, respuesta ni clave API: solo
conteos, tamaños, IDs técnicos y huellas de los cuerpos completos.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json

SCHEMA = "nilo.lab.evaluation.v1"
REQUIRED = frozenset(("posición", "necesidades", "proyecto_actual", "regla"))
PROVIDERS = frozenset(("gemini", "groq"))

from cognitive_projection import _INTERNAL_BODY_FIELDS


def _contains_internal_reserves(value):
    if isinstance(value, dict):
        return (bool(_INTERNAL_BODY_FIELDS.intersection(value))
                or any(_contains_internal_reserves(v) for v in value.values()))
    if isinstance(value, list):
        return any(_contains_internal_reserves(v) for v in value)
    return False


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _size(text):
    return len(text.encode("utf-8"))


def _roles(provider, request):
    if provider == "gemini":
        system = request["systemInstruction"]["parts"][0]["text"]
        user = request["contents"][0]["parts"][0]["text"]
        if "SITUACIÓN REAL: " not in user:
            raise ValueError("Gemini: falta el contexto literal de usuario")
        return {"system": _size(system), "user": _size(user)}
    if provider == "groq":
        roles = request["messages"]
        if len(roles) != 2 or [x["role"] for x in roles] != ["system", "user"]:
            raise ValueError("Groq: roles inesperados")
        return {x["role"]: _size(x["content"]) for x in roles}
    raise ValueError("Proveedor fuera del protocolo de evaluación")


def _branch(provider, view):
    wire = view["solicitud_serializada"]
    if _sha(wire) != view["huella_solicitud_calculada"]:
        raise ValueError("La solicitud no coincide con su SHA-256 original")
    request = json.loads(wire)
    if request != view["solicitud_json"]:
        raise ValueError("La solicitud serializada no coincide con el payload")
    if view["enviado_a_llm"] is not False:
        raise ValueError("Una previsualización no puede figurar como enviada")
    sent = view["datos_enviados"]
    if not isinstance(sent, dict):
        raise ValueError("Falta el contexto estructurado recibido por el modelo")
    absent = sorted(REQUIRED - set(sent))
    # 'regla' puede estar en la política general aunque la proyección elegida
    # la haya excluido por un límite histórico; siempre auditarlo, sin inventar.
    return {
        "context_mode": view["modo_contexto"],
        "model": view["model"],
        "bytes_request": _size(wire),
        "bytes_by_role": _roles(provider, request),
        "request_sha256": _sha(wire),
        "context_field_count": len(sent),
        "fields": sorted(sent),
        "absent_required_fields": absent,
        "internal_body_measurements_exposed": _contains_internal_reserves(sent),
        "needs_numeric_reserve_exposed": (
            isinstance(sent.get("necesidades"), dict)
            and ("valores" in sent["necesidades"]
                 or any(isinstance(sent["necesidades"].get(k), (int, float))
                        and not isinstance(sent["necesidades"].get(k), bool)
                        for k in ("energia", "nutricion", "hidratacion")))
        ),
    }


def analyze_context_ab(result):
    """Auditar dos solicitudes literales del MISMO estado, sin respuesta LLM."""
    if result.get("experiment_type") != "context_ab" or result.get("llm_calls") != 0:
        raise ValueError("Se requiere una comparación de contexto sin red")
    if result.get("modified_original_world") is not False:
        raise ValueError("La partida original se ha declarado modificada")
    provider = result["provider"]
    if provider not in PROVIDERS:
        raise ValueError("Proveedor inválido")
    comparison = result["comparison"]
    if comparison.get("comparable_same_reference") is not True:
        raise ValueError("Las percepciones no parten de la misma referencia")
    a = _branch(provider, result["baseline"])
    b = _branch(provider, result["variant"])
    if a["context_mode"] != "baseline":
        raise ValueError("La rama A debe seguir siendo el baseline")
    if result.get("context_mode", "baseline") != b["context_mode"]:
        raise ValueError("Modo B incompatible con la solicitud")
    if a["model"] != b["model"]:
        raise ValueError("Comparación con modelos diferentes")
    if (a["needs_numeric_reserve_exposed"] or b["needs_numeric_reserve_exposed"]
            or a["internal_body_measurements_exposed"]
            or b["internal_body_measurements_exposed"]):
        raise ValueError("Reservas corporales internas expuestas")
    a_fields, b_fields = set(a.pop("fields")), set(b.pop("fields"))
    return {
        "schema": SCHEMA, "kind": "offline_context_ab",
        "seed": result["seed"], "provider": provider,
        "model": a["model"], "reference_sha256": result["reference_sha256"],
        "variant_projection_sha256": result.get("variant_projection_sha256"),
        "same_initial_world": True,
        "same_cognitive_projection": comparison.get("identical_cognitive_projections", True),
        "same_sent_evidence": comparison.get("same_sent_evidence"),
        "sent_evidence_differences": comparison.get("sent_evidence_differences", {}),
        "baseline": a, "variant": b,
        "request_bytes_delta": b["bytes_request"] - a["bytes_request"],
        "request_bytes_change_pct": round(
            (b["bytes_request"] - a["bytes_request"]) * 100 / a["bytes_request"], 2),
        "removed_fields": sorted(a_fields - b_fields),
        "added_fields": sorted(b_fields - a_fields),
        "both_preserve_required_fields": not (a["absent_required_fields"]
                                               or b["absent_required_fields"]),
        "sample_size": 0, "llm_calls": 0,
        "behavior_evaluated": False,
        "causal_claim_allowed": False,
        "limitations": [
            "Las diferencias de tamaño son bytes UTF-8, no tokens del proveedor.",
            "La previsualización no incluye respuestas ni prueba autonomía o creatividad.",
            "La memoria recuperada puede variar entre proyecciones; comparar su SHA, no atribuir lectura al LLM.",
            "Mismo estado inicial no implica igual evidencia efectivamente seleccionada para ambos prompts.",
        ],
    }


def _plan_signature(steps):
    if not isinstance(steps, list):
        return None
    # La huella incorpora el plan íntegro, incluidos los argumentos físicos.
    # El contenido permanece privado: únicamente se retorna el SHA-256.
    if any(not isinstance(step, dict) for step in steps):
        return None
    return _sha(json.dumps(steps, ensure_ascii=False, sort_keys=True,
                           separators=(",", ":"), allow_nan=False))


def _live_branch(row):
    turns = row.get("turns") or []
    entries, signatures = [], []
    for turn in turns:
        response = turn.get("response") if isinstance(turn, dict) else None
        response = response if isinstance(response, dict) else {}
        normalized = response.get("normalized") if isinstance(response.get("normalized"), dict) else None
        tokens = response.get("tokens") if isinstance(response.get("tokens"), dict) else {}
        plan = normalized.get("plan") if normalized else None
        signatures.append(_plan_signature(plan) if plan is not None else None)
        effect = turn.get("world_effect") if isinstance(turn.get("world_effect"), dict) else {}
        warnings = response.get("validation_warnings") or []
        operation_rows = effect.get("operation_results") or []
        counts = Counter(row.get("state", "sin_estado") for row in operation_rows
                         if isinstance(row, dict))
        entries.append({
            "turn": turn.get("turn"),
            "request_sha256": turn.get("sent_preview_sha256"),
            "context_sha256": turn.get("pre_context_sha256"),
            "cognitive_projection_sha256": turn.get("cognitive_projection_sha256"),
            "transport_error_present": "transport_error" in turn,
            "response_invalid": bool(response.get("validation_error")) or (
                bool(response) and normalized is None),
            "semantic_warning_count": len(warnings),
            "semantic_warning_codes": sorted({
                row.get("code") for row in warnings
                if isinstance(row, dict) and isinstance(row.get("code"), str)
            }),
            "normalized_plan_actions": len(plan) if isinstance(plan, list) else None,
            "operation_types": sorted({s["op"] for s in plan
                                       if isinstance(s, dict) and isinstance(s.get("op"), str)})
                                       if isinstance(plan, list) else [],
            "project_action_declared": normalized.get("accion_proyecto") if normalized else None,
            "project_transition": effect.get("project_transition"),
            "reported_prompt_tokens": tokens.get("entrada", tokens.get("prompt_tokens")),
            "reported_output_tokens": tokens.get("salida", tokens.get("completion_tokens")),
            "physical_execution_attempted": effect.get("applied") is True,
            "physical_plan_unfinished": effect.get("pending_or_unfinished"),
            "submitted_operations": effect.get("submitted_operations"),
            "admitted_operations": effect.get("admitted_operations"),
            "observed_operation_states": dict(sorted(counts.items())),
            "recorded_successes": effect.get("recorded_successes"),
            "recorded_failures": effect.get("recorded_failures"),
            "recorded_blocks": effect.get("recorded_blocks"),
            "recorded_not_evaluable": effect.get("recorded_not_evaluable"),
        })
    successful = [s for s in signatures if s is not None]
    return {
        "turns": entries, "attempt_count": len(turns),
        "normalized_decisions": len(successful),
        "adjacent_identical_plan_signatures": sum(
            x == y for x, y in zip(signatures, signatures[1:])
            if x is not None and y is not None),
        "declared_operation_types": sorted({name for row in entries
                                             for name in row["operation_types"]}),
        "semantic_warnings": sum(row["semantic_warning_count"] for row in entries),
        "recorded_project_pauses": sum(
            bool(isinstance(row.get("project_transition"),dict)
                and row["project_transition"].get("previous_status_after")=="pausado"
                and row["project_transition"].get("previous_status")=="activo")
            for row in entries),
        "recorded_physical_failures": sum(row["recorded_failures"] or 0 for row in entries),
        "recorded_precondition_blocks": sum(row["recorded_blocks"] or 0 for row in entries),
        "recorded_not_evaluable": sum(row["recorded_not_evaluable"] or 0 for row in entries),
    }


def analyze_live_ab(result):
    """Resumir respuestas reales capturadas; no adjudicar causalidad ni éxito físico."""
    if result.get("experiment_type") not in (
        "llm_two_branch_deliberation", "llm_two_branch_multiturn"):
        raise ValueError("Se requiere un experimento A/B con deliberaciones")
    if result.get("explicit_live_consent") is not True:
        raise ValueError("No consta consentimiento para las consultas reales")
    if result.get("modified_original_world") is not False:
        raise ValueError("Se modificó la partida original")
    a, b = _live_branch(result["baseline"]), _live_branch(result["variant"])
    if result.get("llm_calls", 0) > result.get("max_llm_calls", 0):
        raise ValueError("Presupuesto de LLM superado")
    return {
        "schema": SCHEMA, "kind": "observed_live_ab",
        "provider": result["provider"], "seed": result["seed"],
        "reference_sha256": result["reference_sha256"],
        "context_mode": result.get("context_mode", "baseline"),
        "llm_calls": result["llm_calls"], "max_llm_calls": result["max_llm_calls"],
        "baseline": a, "variant": b,
        "behavior_evaluated": a["normalized_decisions"] + b["normalized_decisions"] > 0,
        "causal_claim_allowed": False,
        "limitations": [
            "Los planes y las respuestas de un LLM son estocásticos.",
            "Una acción declarada no equivale a una ejecución física satisfactoria.",
            "La inclusión de una memoria en el contexto no prueba que el LLM la haya usado.",
            "Una o dos decisiones por rama no establecen tendencias de comportamiento.",
        ],
    }
