"""Lente contextual de reglas del motor para el laboratorio (solo observación).

Diferencia tres niveles de prueba:
- contrato documentado, independiente de una ejecución;
- comprobación de formato recalculada para inspección (NO ejecutada);
- resultados, verificación contractual y líneas trazadas en una prueba real.

No altera estado, acciones, memoria o prompt. Ausencia de una traza nunca
significa que una rama del motor no haya sido evaluada.
"""
from __future__ import annotations

from action_contracts import spec_for
from nilo_runtime.core.operations import get_spec, validate_operation, registered_operations

_MAX_TRACE = 100
_AUTOMATIC = frozenset(("agenda", "espera", "rutina", "motor"))


def operation_reference(operation):
    """Catálogo vigente: descripción contractual, NO valores verificados."""
    if not isinstance(operation, str) or operation not in registered_operations():
        raise ValueError("Operación no registrada en el motor")
    record = spec_for(operation)
    spec = get_spec(operation)
    return {
        "operation": operation,
        "description": record["descripcion"],
        "executor": record["ejecutor"],
        "planned_minutes": record["duracion_prevista_minutos"],
        "navigable": spec.navigable,
        "required_fields": record["requisitos_de_forma"],
        "verified_preconditions": spec.verified_preconditions,
        "verified_postconditions": spec.verified_postconditions,
        "contract": record.get("contrato"),
        "evidence_level": "documented_rule_not_executed",
        "note": (
            "El contrato describe reglas previstas; su presencia no acredita "
            "que todas las condiciones se evaluaran en esta ejecución."
        ),
    }


def inspect_rule(operation, *, step=None, diagnostic=None, result=None,
                 measurement=None, trace=None, source="reference"):
    """Reporte legible sin confundir inferencias, documentación y observaciones.

    source=simulation: resultado/diagnóstico y traza del sandbox real.
    source=historical: únicamente checkpoint previo, sin resultado atribuido.
    source=reference: regla estática sin ejecución.
    """
    ref = operation_reference(operation)
    if source not in ("reference", "simulation", "historical"):
        raise ValueError("Origen de prueba desconocido")
    if step is not None and (
            not isinstance(step, dict) or step.get("op") != operation):
        raise ValueError("La acción inspeccionada no coincide con la operación")
    syntax = None
    if step is not None:
        test = validate_operation(step, check_required=False)
        missing = [field for field in ref["required_fields"]
                   if not step.get(field)]
        syntax = {
            "valid": test.valid,
            "code": test.code,
            "reason": test.reason,
            "missing_required_fields": missing,
            "evidence_level": "rechecked_now_not_original_validation",
            "note": ("Se revalidó el tipo y forma con la compatibilidad actual; "
                     "los campos requeridos faltantes se informan aparte. "
                     "No demuestra la validación efectivamente usada en el run."),
        }

    report = {
        "operation": operation,
        "source": source,
        "reference": ref,
        "recorded_step": step,
        "shape_check": syntax,
        "actual": None,
        "instrumented_functions": [],
        "limitations": [],
    }
    if source == "reference":
        report["limitations"].append(
            "Solo ficha documental: no se observó ninguna operación.")
        return report
    if source == "historical":
        report["limitations"].extend((
            "El checkpoint anterior no demuestra qué ramas condicionales se ejecutaron.",
            "Esta vista no atribuye diagnósticos por proximidad horaria u operación parecida.",
            "El motor actual puede diferir del registrado en la partida.",
        ))
        return report

    # La fuente simulation es exclusivamente resultado de SimulationSandbox.act.
    diag = diagnostic if isinstance(diagnostic, dict) else None
    act = (diag.get("action_result") if diag else None)
    if not isinstance(act, dict):
        act = result if isinstance(result, dict) else None
    # Un resultado de una prueba anterior no se puede presentar como propio.
    if (diag is not None and diag.get("op") not in (None, operation)) or (
            isinstance(act, dict) and act.get("op") not in (None, operation)):
        act = None
        diag = None
        report["limitations"].append(
            "El diagnóstico disponible pertenece a otra operación; no se atribuyó.")
    if act is not None and act.get("status") == "sin_medicion" and diag is None:
        # SimulationSandbox prepara este placeholder cuando no existe salida
        # instrumentada: no presentarlo como resultado físico del motor.
        act = None
        report["limitations"].append(
            "El sandbox completó la prueba sin diagnóstico físico; "
            "'sin_medicion' es un marcador del visor, no una evaluación de la operación.")
    if act is not None:
        physical = act.get("physical") or {}
        if not isinstance(physical, dict):
            physical = {}
        conditions = physical.get("conditions")
        report["actual"] = {
            "status": act.get("status"),
            "success": act.get("success"),
            "facts": act.get("facts") if isinstance(act.get("facts"), list) else [],
            "physical_conditions": conditions if isinstance(conditions, dict) else None,
            "physical_result": diag.get("physical_result") if diag else None,
            "contract_verifier": (
                {
                    "status": diag.get("contract_status"),
                    "code": diag.get("contract_code"),
                    "expected": diag.get("contract_expected"),
                    "observed": diag.get("contract_observed"),
                } if diag and "contract_status" in diag else None
            ),
            "measurement": measurement,
            "evidence_level": "actual_simulation_output",
        }
        if conditions is None:
            report["limitations"].append(
                "El motor no expuso un desglose de condiciones físicas para esta operación.")
    else:
        report["limitations"].append(
            "La prueba no produjo un resultado físico atribuible a esta operación.")

    if isinstance(trace, list):
        for entry in trace[:_MAX_TRACE]:
            if isinstance(entry, dict):
                report["instrumented_functions"].append({
                    key: entry.get(key)
                    for key in ("file", "function", "text", "count", "first", "last", "line_count")
                    if key in entry
                })
        if len(trace) > _MAX_TRACE:
            report["limitations"].append("Traza acotada a 100 funciones.")
        if not report["instrumented_functions"]:
            report["limitations"].append(
                "No se registraron funciones instrumentadas: no equivale a ausencia de ejecución.")
    else:
        report["limitations"].append(
            "No hay traza de funciones instrumentadas para esta prueba.")
    report["limitations"].append(
        "Una línea ejecutada no demuestra qué valor tuvo cada condición booleana.")
    return report
