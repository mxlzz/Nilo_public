"""Auditoría estática etapa 15: propietarios y contratos únicos."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

def functions(path):
    tree=ast.parse((ROOT/path).read_text(encoding="utf-8"))
    return {node.name for node in tree.body if isinstance(node,ast.FunctionDef)}

def inspect():
    errors=[]
    brain=functions("brain.py")
    gateway=functions("nilo_runtime/agent/gateway.py")
    response=functions("nilo_runtime/agent/responses.py")
    budget=functions("nilo_runtime/agent/budget.py")
    expected={"build_deliberation_request","request_llm",
              "build_chat_request","request_chat","_post","_response"}
    if expected-gateway:
        errors.append("Falta código del gateway: "+repr(expected-gateway))
    if {"normalize_decision","parse_json"}-response:
        errors.append("El parseo y la validación tienen dueño incompleto")
    if {"compact_context","bounded_context","brief_actions"}-budget:
        errors.append("El presupuesto tiene dueño incompleto")
    if brain & (expected | {"normalize_decision","parse_json","compact_context"}):
        errors.append("brain conserva implementación duplicada")
    if functions("prompt_budget.py"):
        errors.append("prompt_budget conserva un segundo presupuesto")
    from nilo_runtime.agent.prompts import POLICY_RULES, SYSTEM, GROQ_SYSTEM
    from nilo_runtime.agent.budget import SHORT_OPERATIONS
    from nilo_runtime.core.operations import registered_operations
    if len(POLICY_RULES)!=24:
        errors.append("Conjunto de reglas cambiado sin registro")
    if SYSTEM!="\n".join(rule[1] for rule in POLICY_RULES):
        errors.append("Prompt largo fuera de contrato")
    if GROQ_SYSTEM!="\n".join(rule[2] for rule in POLICY_RULES):
        errors.append("Prompt compacto fuera de contrato")
    if set(SHORT_OPERATIONS)!=set(registered_operations()):
        errors.append("Las operaciones compactas no provienen del registro físico")
    if "wait no aporta recuperación energética" not in SYSTEM:
        errors.append("El prompt no refleja la fisiología de wait")
    if "nilo_runtime/agent/gateway.py" not in (ROOT/"laboratorio_casos.py").read_text("utf-8"):
        errors.append("El banco de escenarios no traza el gateway real")
    if "gateway.py:build_deliberation_request" not in (ROOT/"laboratorio_motor.py").read_text("utf-8"):
        errors.append("El laboratorio no traza la construcción real del payload")
    if not (ROOT/"tests/test_deliberacion_15.py").is_file():
        errors.append("Faltan regresiones de la etapa 15")
    return errors

if __name__=="__main__":
    errors=inspect()
    if errors:
        raise SystemExit("\n".join(errors))
    print("Etapa 15: prompt, gateway, presupuesto y parseo únicos.")
