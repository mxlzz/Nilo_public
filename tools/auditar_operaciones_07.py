"""Auditor de etapa 06: impedir tablas/manuales/dispatch duplicados.

Usar: python tools/auditar_operaciones_07.py
No importa Simulation ni ejecuta acciones del mundo.
"""
from __future__ import annotations

import ast
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))

from nilo_runtime.core.operations import (
    ACTION_GUIDE, ACTION_DURATIONS, DOCUMENT_EXECUTORS, VERIFIABLE,
    NAVIGATION_OPERATIONS, get_spec, registered_operations, manual_lines,
)
from action_contracts import SUPPORTED_OPERATIONS, instructions
from capabilities import manifest


def inspect() -> list[str]:
    errors=[]
    core=ROOT/"nilo_runtime"/"core"/"operations.py"
    if not core.exists():
        return ["Falta el registro canónico de operaciones"]
    for path in sorted(ROOT.glob("*.py")):
        tree=ast.parse(path.read_text("utf-8-sig"),filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node,(ast.Assign,ast.AnnAssign)):
                targets=(node.targets if isinstance(node,ast.Assign) else (node.target,))
                for target in targets:
                    if isinstance(target,ast.Name) and target.id in (
                        "ACTION_DURATIONS","ACTION_GUIDE","DOCUMENT_EXECUTORS"
                    ):
                        errors.append(
                            f"{path.name}:{node.lineno}: {target.id} duplicado; "
                            "modificar sólo nilo_runtime/core/operations.py"
                        )
    definitions=registered_operations()
    if not set(ACTION_GUIDE)==set(ACTION_DURATIONS)==set(SUPPORTED_OPERATIONS)==set(definitions):
        errors.append("Discrepancia entre acciones del manual, reloj, parser y registro")
    for op,spec in definitions.items():
        if spec.planned_minutes <= 0 or spec.description!=ACTION_GUIDE[op]:
            errors.append(f"{op}: duración/documentación incoherente")
        if spec.executor not in ("physical", *DOCUMENT_EXECUTORS.values()):
            errors.append(f"{op}: ejecutor inexistente")
        if spec.navigable != (op in NAVIGATION_OPERATIONS):
            errors.append(f"{op}: navegación mal declarada")
        if spec.verified_preconditions != VERIFIABLE.get(op,{}).get("pre"):
            errors.append(f"{op}: precondición duplicada/incoherente")
    lines=instructions().splitlines()
    if lines[1:1+len(definitions)] != manual_lines():
        errors.append("El manual LLM no procede del registro único")
    methods=[m for cap in manifest() for m in cap["methods"]]
    if len(methods)!=len(set(methods)):
        errors.append("Se registraron métodos físicos duplicados")
    if any(method in definitions for method in methods):
        errors.append("Una capacidad concreta se expuso como operación LLM suelta")
    return errors


if __name__=="__main__":
    issues=inspect()
    if issues:
        print("\n".join(issues))
        raise SystemExit(1)
    print("Etapa 06: registro y manual LLM coherentes; sin ACTION_GUIDE/ACTION_DURATIONS duplicados.")
