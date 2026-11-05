"""Auditor de propietarios y fronteras de efectos físicos (etapa 12)."""
from __future__ import annotations
import ast
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent


def functions(path):
    parsed=ast.parse(path.read_text(encoding="utf-8"))
    return {n.name for n in parsed.body if isinstance(n,ast.FunctionDef)},parsed


def inspect():
    failures=[]
    fabrication=ROOT/"nilo_runtime/worlds/fabrication.py"
    intervention=ROOT/"nilo_runtime/worlds/intervention.py"
    resources=ROOT/"nilo_runtime/worlds/resources.py"
    tooluse=ROOT/"nilo_runtime/worlds/tool_use.py"
    if not all(p.is_file() for p in (fabrication,intervention,resources,tooluse)):
        return ["Faltan módulos de interacción, intervención o balance"]
    fabs,ft=functions(fabrication)
    ints,it=functions(intervention)
    stocks,rt=functions(resources)
    uses,ut=functions(tooluse)
    if not {"use_action","dig_with_tool","adjacent_rock"} <= uses:
        failures.append("Falta único módulo para uso físico de herramientas")
    if not {"combine_action","fabricate_action"} <= fabs:
        failures.append("Falta dueño único de fabricación y combinación")
    if not {"execute_prepared","_preflight"} <= ints:
        failures.append("Falta preflight y confirmación aislada de reformas")
    if not {"exchange_units","material_counts","check_materials"} <= stocks:
        failures.append("Falta presupuesto material conservativo")
    for path,tree in ((fabrication,ft),(intervention,it),(tooluse,ut)):
        for n in ast.walk(tree):
            names=([x.name for x in n.names] if isinstance(n,ast.Import)
                   else [n.module or ""] if isinstance(n,ast.ImportFrom) else [])
            for name in names:
                if name in {"world","construction","mechanics","nilo","inventions",
                            "vessels","structural_loads","capabilities"}:
                    failures.append(f"Dependencia circular del dominio: {path.name}->{name}")
    world=(ROOT/"world.py").read_text(encoding="utf-8")
    if "elif op=='combine':\n        return combine_action(" not in world:
        failures.append("Combinación todavía duplicada en dispatcher")
    if "elif op in ('build','craft'):\n        from inventions" not in world:
        failures.append("Fabricación todavía duplicada en dispatcher")
    if "return use_action(w,p,step" not in world:
        failures.append("Las pruebas de herramientas siguen duplicadas en world.py")
    construction=(ROOT/"construction.py").read_text(encoding="utf-8")
    if "def _apply_intervention_mutating(" not in construction:
        failures.append("Falta preparación aislada de reformas")
    if "return execute_prepared(" not in construction:
        failures.append("La reforma aún se ejecuta sobre la entidad original")
    if "for m,n in cost.items():inv[m]-=n" in construction:
        failures.append("La reforma saltea el balance conservativo")
    mechanics=(ROOT/"mechanics.py").read_text(encoding="utf-8")
    if "exchange_units(inv,dict(required))" not in mechanics:
        failures.append("El ensamblaje debita lotes individualmente")
    if not (ROOT/"tests/test_interacciones_12.py").exists():
        failures.append("Faltan pruebas focalizadas etapa 12")
    return failures


if __name__=="__main__":
    issues=inspect()
    if issues:raise SystemExit("\n".join(issues))
    print("Etapa 12: transformación material, preflight y reforma aislados.")
