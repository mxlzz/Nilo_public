"""Puerta de arquitectura 07: motor de sesión independiente de HTTP/UI.

No importa engine, nilo.py ni ejecuta providers, sólo inspecciona AST.
"""
from __future__ import annotations
import ast
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
APP=ROOT/"nilo_runtime"/"application"
STORAGE=ROOT/"nilo_runtime"/"storage"
WEB=ROOT/"nilo_runtime"/"web"
MIXINS={
    "session.py":{"__init__","_initialize_storage","migrate","write","domain_snapshot","stamp"},
    "records.py":{"event","review_rule","diagnostic_package","measurement_record",
        "mark_read","mark_one_read","mark_all_read","mark_summarized_read",
        "catchup","bootstrap_reviews","mark_tab_reviewed","observer_summary",
        "acknowledge_observer_summary","observer_summary_history","journal",
        "remember_strategy","linked_record","public_state"},
    "decisions.py":{"validate_plan","improve_plan","followup_without_llm","plan_ready",
        "_run_entropy_worker","think","retry_llm","start_chat"},
    "clockwork.py":{"tick","_tick_slice","describe_action","change_speed","run"},
}


def audits():
    errors=[]
    for root in (APP,STORAGE):
        for file in sorted(root.glob("*.py")):
            try:
                tree=ast.parse(file.read_text(encoding="utf-8-sig"),filename=str(file))
            except SyntaxError as ex:
                errors.append(f"{file}: fuente inválida: {ex}")
                continue
            for node in ast.walk(tree):
                imported=[]
                if isinstance(node,ast.Import):
                    imported=[alias.name for alias in node.names]
                elif isinstance(node,ast.ImportFrom):
                    imported=[node.module or ""]
                for name in imported:
                    if (name=="nilo" or name.startswith("nilo_runtime.web")
                            or name in ("http","http.server","webbrowser")
                            or name.startswith("http.server")):
                        errors.append(f"{file.name}:{node.lineno}: dependencia UI/fachada inversa: {name}")
    current=set()
    for filename,expected in MIXINS.items():
        file=APP/filename
        if not file.is_file():
            errors.append("Falta el caso de uso "+filename)
            continue
        tree=ast.parse(file.read_text("utf-8-sig"),filename=str(file))
        classes=[n for n in tree.body if isinstance(n,ast.ClassDef)]
        if len(classes)!=1:
            errors.append(filename+": solo debe declarar un mixin de aplicación")
            continue
        actual={n.name for n in classes[0].body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
        if expected!=actual:
            errors.append(filename+": difiere contrato: "+repr(sorted(expected^actual)))
        repeated=current&actual
        if repeated:
            errors.append(filename+": métodos duplicados: "+repr(sorted(repeated)))
        current.update(actual)
    f=APP/"engine.py"
    tree=ast.parse(f.read_text("utf-8-sig"),filename=str(f))
    classes=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=="Simulation"]
    if len(classes)!=1 or any(isinstance(node,ast.FunctionDef) for node in classes[0].body):
        errors.append("Simulation core debe componer casos de uso sin implementar segundo motor")
    root=ROOT/"nilo.py"
    if len(root.read_text("utf-8-sig").splitlines())>110:
        errors.append("nilo.py volvió a crecer: conservar solo fachada CLI/legado")
    if not (WEB/"http.py").is_file():
        errors.append("Falta servidor optativo separado")
    return errors


if __name__=="__main__":
    errors=audits()
    if errors:
        print("\n".join(errors))
        raise SystemExit(1)
    print("Etapa 07: fachada pequeña, ciclo UI/motor roto, casos de uso únicos y almacenamiento independiente.")
