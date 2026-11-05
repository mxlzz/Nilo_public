"""Etapa 23: evaluación de decisiones realmente archivadas por proveedores LLM.

Nunca llama a un proveedor ni abre partidas en escritura. Los informes excluyen
prompt, texto del cuaderno, decisiones textuales, chats y claves. La presencia de
un modelo configurado NO cuenta como prueba de una deliberación real.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import closing
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluar_corridas import (
    EvaluationError, _connect, _tables, _history, _sessions, analyze,
)

FORMAT = "nilo-autonomia-23-v1"
SIGNATURE_FIELDS = ("op", "target", "method", "item", "material", "name",
                    "direction", "region", "x", "y", "z", "duration", "minutes")


def _safe_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _signature(fields):
    """Intención operacional, sin cuaderno ni motivo narrativo."""
    digest = json.dumps(fields, sort_keys=True, ensure_ascii=False,
                        separators=(",", ":"), default=str)
    return hashlib.sha256(digest.encode("utf-8")).hexdigest()[:16]


def _plan_signature(decision):
    if not isinstance(decision, dict):
        return None
    plan = decision.get("plan")
    if not isinstance(plan, list):
        return None
    actions = []
    for step in plan:
        if isinstance(step, dict):
            actions.append({k: step[k] for k in SIGNATURE_FIELDS if k in step})
    return _signature({
        "accion_proyecto": decision.get("accion_proyecto"),
        "proyecto_id": decision.get("proyecto_id"),
        "acciones": actions,
    })


def _action_signature(row):
    if not isinstance(row, dict):
        return None
    return _signature({k: row[k] for k in SIGNATURE_FIELDS if k in row})


def _runs(values):
    streaks = []
    previous, length = None, 0
    for signature in values:
        if signature is not None and signature == previous:
            length += 1
        else:
            if length >= 2:
                streaks.append(length)
            previous, length = signature, 1 if signature is not None else 0
    if length >= 2:
        streaks.append(length)
    return {"streaks_at_least_two": len(streaks),
            "repeated_transitions": sum(n - 1 for n in streaks),
            "longest_identical_streak": max(streaks, default=0)}


def analyze_autonomy(path):
    """Solo evidencia observacional; decisiones archivadas no garantizan progreso."""
    path = Path(path)
    base = analyze(path)
    with closing(_connect(path)) as db:
        tables = _tables(db)
        groups, _ = _history(db, tables)
        sessions, usages = _sessions(db, tables)

    decisions = groups.get("llm_decision", [])
    outcomes = groups.get("diagnostic", [])
    chats = groups.get("chat", [])
    real_models = Counter()
    for row in decisions:
        if isinstance(row, dict):
            provider, model = row.get("provider"), row.get("model")
            if provider and model:
                real_models[(str(provider), str(model))] += 1

    counted = sum(int(row.get("calls") or 0) for row in usages
                  if row.get("purpose") == "deliberacion")
    archived = len(decisions)
    real_verified = bool(archived and real_models and counted >= archived)
    decision_signatures = [_plan_signature(row.get("decision")) for row in decisions]
    failed = [row for row in outcomes if row.get("success") is False]
    consecutive_failures = [
        _action_signature(row) if row.get("success") is False else None
        for row in outcomes
    ]
    physical_ids = {
        row.get("id") for row in groups.get("measurement", [])
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    }
    linked = sum(
        (row.get("physical_result") or {}).get("measurement_id") in physical_ids
        for row in outcomes if isinstance(row, dict)
        and isinstance(row.get("physical_result"), dict)
    )
    if groups.get("llm_decision") and archived != counted:
        discrepancy = "Contador de usos y decisiones archivadas no coinciden."
    else:
        discrepancy = None
    observed = base["autonomy"]["observed_behavior_summary"]
    novelty = observed.get("novelty_actions")
    new_tiles = observed.get("new_tiles")
    actions = observed.get("actions")
    warnings = list(base["warnings"])
    if discrepancy:
        warnings.append(discrepancy)
    if not real_verified:
        warnings.append("No hay evidencia suficiente de deliberaciones reales archivadas y contabilizadas.")
    if len(base["identity"]["versions"]) != 1:
        warnings.append("Partida con versión ausente o mixta; no atribuir al código 0.7.")
    if len(sessions) != 1:
        warnings.append("Múltiples sesiones o ninguna: el archivo acumula tramos no aislables.")
    if chats:
        warnings.append("Hay mensajes de chat archivados; no se presume corrida sin intervención.")
    if not outcomes:
        warnings.append("Sin diagnósticos de acciones: no evaluar progreso ni reiteración física.")
    if any(not isinstance(row.get("decision"), dict) for row in decisions):
        warnings.append("Hay decisiones LLM sin estructura recuperable.")
    return {
        "format": FORMAT,
        "source": {"file": path.name, "read_only": True,
                   "scope": "acumulado_de_partida; sin atribución causal"},
        "verified_real_llm": real_verified,
        "identity": base["identity"],
        "providers_observed": [
            {"provider": provider, "model": model, "archived_decisions": n}
            for (provider, model), n in sorted(real_models.items())
        ],
        "llm": {"decisions_archived": archived,
                "successful_deliberations_counted": counted,
                "contexts_hashed": sum(bool(row.get("context_sha256")) for row in decisions),
                "repeated_plan_signatures": _runs(decision_signatures)},
        "behavior": {
            "actions_archived": len(outcomes),
            "actions_from_llm": sum(row.get("origin") == "llm" for row in outcomes),
            "unattributed_actions": sum(not row.get("origin") for row in outcomes),
            "failed_actions": len(failed),
            "consecutive_identical_failed_actions": _runs(consecutive_failures),
            "physically_measured_actions": linked,
            "novelty_actions_since_instrumentation": novelty,
            "new_tiles_since_instrumentation": new_tiles,
            "behavior_actions_since_instrumentation": actions,
            "directed_exploration_with_discovery": base["actions"]["directed_exploration_with_discoveries"],
            "exploration": base["actions"]["operations_exploration"],
            "experimentation": base["actions"]["operations_experiment"],
            "fabrication_and_design": base["actions"]["operations_creative"],
            "projects_archived": base["autonomy"]["projects_archived"],
            "investigations_archived": base["autonomy"]["investigations_archived"],
            "unmodeled_physical_outcomes": base["actions"]["evaluation_status"].get("no_evaluable", 0),
        },
        "coverage": {
            "sessions": len(sessions),
            "recorded_chat_entries": len(chats),
            "known_actual_models": bool(real_models),
            "verified_provenance_actions": base["actions"]["by_origin_verified"],
            "per_version_metrics_available": False,
        },
        "warnings": warnings,
    }


def compare_autonomy(reports):
    if len(reports) < 2 or len(reports) > 8:
        raise EvaluationError("Se necesitan entre dos y ocho partidas.")
    if len({r["source"]["file"] for r in reports}) != len(reports):
        raise EvaluationError("Las partidas deben tener nombres distintos.")
    identities = [r["identity"] for r in reports]
    providers = [{(v["provider"], v["model"]) for v in r["providers_observed"]}
                 for r in reports]
    checks = {
        "real_llm_in_all": all(r["verified_real_llm"] for r in reports),
        "same_world_seed": len({str(i["world_seed"]) for i in identities}) == 1,
        "same_rng_seed": all(i["first_session_rng_seed"] is not None for i in identities)
        and len({i["first_session_rng_seed"] for i in identities}) == 1,
        "same_initial_snapshot": all(i["first_session_state_sha256"] for i in identities)
        and len({i["first_session_state_sha256"] for i in identities}) == 1,
        "same_simulated_duration": len({i["simulated_minutes"] for i in identities}) == 1,
        "same_llm_call_count": len({r["llm"]["decisions_archived"] for r in reports}) == 1,
        "single_session_each": all(r["coverage"]["sessions"] == 1 for r in reports),
        "no_archived_chat": all(r["coverage"]["recorded_chat_entries"] == 0 for r in reports),
        "providers_recorded": all(bool(v) for v in providers),
    }
    return {
        "conditions": checks,
        "descriptive_only": True,
        "causal_claim_allowed": False,
        "reason": ("El servicio LLM no garantiza respuestas equivalentes ni "
                   "control de temperatura y condiciones solo por semilla; "
                   "las diferencias descriptivas no demuestran mejora causal."),
    }


def report_text(reports, comparison=None):
    out = ["# Nilo 0.7 — Evaluación autónoma, etapa 23", "",
           "Resultados de SQLite en solo lectura; sin cuadernos, prompts ni chats.", "",
           "| Partida | LLM verificado | Deliberaciones | Acciones | Fallos | Repeticiones de plan | Novedades |",
           "| --- | --- | ---: | ---: | ---: | ---: | ---: |"]
    for row in reports:
        behavior, llm = row["behavior"], row["llm"]
        out.append(
            f"| {row['source']['file']} | {'sí' if row['verified_real_llm'] else 'no'} "
            f"| {llm['decisions_archived']} | {behavior['actions_archived']} "
            f"| {behavior['failed_actions']} "
            f"| {llm['repeated_plan_signatures']['repeated_transitions']} "
            f"| {behavior['novelty_actions_since_instrumentation']} |"
        )
    out.append("")
    for row in reports:
        out += ["## " + row["source"]["file"], "",
                "Proveedores observados: " + json.dumps(row["providers_observed"], ensure_ascii=False) + ".",
                "Indicadores observacionales: " + json.dumps(row["behavior"], ensure_ascii=False, sort_keys=True) + ".",
                "Advertencias: " + ("; ".join(row["warnings"]) or "ninguna") + ".", ""]
    if comparison:
        out += ["## Comparabilidad", "",
                json.dumps(comparison["conditions"], ensure_ascii=False, sort_keys=True),
                "", "**No se puede acreditar causalidad:** " + comparison["reason"], ""]
    return "\n".join(out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sqlite", nargs="+", type=Path)
    parser.add_argument("--json", dest="out_json", type=Path)
    parser.add_argument("--markdown", dest="out_md", type=Path)
    args = parser.parse_args(argv)
    try:
        if len(args.sqlite) > 8:
            raise EvaluationError("Máximo ocho partidas.")
        reports = [analyze_autonomy(path) for path in args.sqlite]
        comparison = compare_autonomy(reports) if len(reports) > 1 else None
        output = {"format": FORMAT, "runs": reports, "comparison": comparison}
        if args.out_json:
            args.out_json.write_text(json.dumps(output, ensure_ascii=False, indent=2)
                                     + "\n", encoding="utf-8")
        if args.out_md:
            args.out_md.write_text(report_text(reports, comparison) + "\n", encoding="utf-8")
        print(json.dumps({"verified_real_llm": [r["verified_real_llm"] for r in reports],
                          "runs": len(reports), "comparative": comparison is not None}))
        return 0
    except (EvaluationError, OSError, ValueError) as exc:
        parser.exit(1, "Error de evaluación: " + str(exc) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
