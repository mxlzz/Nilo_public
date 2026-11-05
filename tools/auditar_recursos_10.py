"""Etapa 10: propiedad única de reservas y controles de conservación."""
from __future__ import annotations
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
OWNED={"gather_material","nearest_known","forage_source","forage_action",
       "harvest_at","cut_wood","transfer_units"}
FORBIDDEN={"world","brain","island_planning","environments","nilo",
           "nilo_runtime.application","nilo_runtime.web","providers"}

def inspect():
    failures=[]
    path=ROOT/"nilo_runtime/worlds/resources.py"
    if not path.is_file():return ["Falta worlds/resources.py"]
    tree=ast.parse(path.read_text(encoding="utf-8"))
    found={n.name for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    missing=OWNED-found
    if missing:failures.append("Operaciones de recursos ausentes: "+str(sorted(missing)))
    for node in ast.walk(tree):
        names=([n.name for n in node.names] if isinstance(node,ast.Import)
               else [node.module or ""] if isinstance(node,ast.ImportFrom) else [])
        for name in names:
            if any(name==bad or name.startswith(bad+".") for bad in FORBIDDEN):
                failures.append(f"Dependencia invertida: {name}")
    legacy=ast.parse((ROOT/"world.py").read_text(encoding="utf-8"))
    duplicates=OWNED & {n.name for n in legacy.body if isinstance(n,ast.FunctionDef)}
    if duplicates:failures.append("Definiciones dobles en world.py: "+str(sorted(duplicates)))
    direct_names={"deposits","forage_deposits"}
    if not (ROOT/"tests/test_recursos_10.py").is_file():
        failures.append("Faltan tests de conservación y extracción")
    return failures

if __name__=="__main__":
    issues=inspect()
    if issues:raise SystemExit("\n".join(issues))
    print("Etapa 10: único módulo de recursos, transferencias balanceadas y sin ciclos.")
