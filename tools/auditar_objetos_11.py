"""Auditor estructural de formas, catálogos y piezas (etapa 11)."""
from __future__ import annotations
import ast
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
OBJECTS={"infer_form","is_portable","item_effects","make_item",
         "classify_structure","structure_symbol","enrich_structure"}
COMPONENTS={"normalize_parts","normalize_joints","connected_parts"}
FORBIDDEN={"world","nilo","mechanics","construction","brain",
           "nilo_runtime.application","nilo_runtime.web","providers"}

def funcs(path):
    tree=ast.parse(path.read_text(encoding="utf-8"))
    return {n.name for n in tree.body if isinstance(n,ast.FunctionDef)},tree

def inspect():
    errors=[]
    op=ROOT/"nilo_runtime/worlds/objects.py"
    cp=ROOT/"nilo_runtime/worlds/components.py"
    if not op.exists() or not cp.exists():
        return ["Faltan propietarios para objetos y/o componentes"]
    os,ot=funcs(op)
    cs,ct=funcs(cp)
    if OBJECTS-os:errors.append("Objetos incompletos: "+str(sorted(OBJECTS-os)))
    if COMPONENTS-cs:errors.append("Componentes incompletos: "+str(sorted(COMPONENTS-cs)))
    ws,_=funcs(ROOT/"world.py")
    if OBJECTS & ws:errors.append("Funciones de objetos duplicadas en world.py")
    for path,tree in ((op,ot),(cp,ct)):
        for node in ast.walk(tree):
            names=([n.name for n in node.names] if isinstance(node,ast.Import)
                   else [node.module or ""] if isinstance(node,ast.ImportFrom) else [])
            for name in names:
                if any(name==x or name.startswith(x+".") for x in FORBIDDEN):
                    errors.append(f"Dependencia invertida en {path.name}: {name}")
    s=(ROOT/"construction.py").read_text(encoding="utf-8")
    if "setdefault('components',_components" in s:
        errors.append("Migración eager consume IDs cuando ya existen piezas")
    if "from world import item_effects" in s:
        errors.append("Dependencia circular construction -> world para poderes")
    world=(ROOT/"world.py").read_text(encoding="utf-8")
    if "physical_item(name,purpose" not in world:
        errors.append("El craft aún usa inferencia de forma por nombre")
    return errors

if __name__=="__main__":
    errors=inspect()
    if errors:raise SystemExit("\n".join(errors))
    print("Etapa 11: catálogos, objetos y componentes con propietarios únicos.")
