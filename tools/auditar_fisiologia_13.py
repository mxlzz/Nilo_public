"""Nilo 0.7 · Auditoría de propietarios de fisiología y resguardo (etapa 13)."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
PHYSIOLOGY={"ensure_needs","update_needs","needs_summary","perceived_needs",
            "_sensation_level","_fatigue_sensation"}
POLICY={"rest_minutes","wait_minutes","fatigue_multiplier",
        "should_collapse","can_wake","body_strained"}


def parse(path):
    tree=ast.parse(path.read_text(encoding="utf-8"))
    functions={n.name for n in tree.body if isinstance(n,ast.FunctionDef)}
    return functions,tree


def inspect():
    errors=[]
    need_path=ROOT/"nilo_runtime/physiology/needs.py"
    policy_path=ROOT/"nilo_runtime/physiology/policy.py"
    cover_path=ROOT/"nilo_runtime/worlds/shelter.py"
    if not all(p.is_file() for p in (need_path,policy_path,cover_path)):
        return ["Falta algún propietario de fisiología, política o cubierta."]
    nf,nt=parse(need_path)
    pf,pt=parse(policy_path)
    sf,st=parse(cover_path)
    if not PHYSIOLOGY <= nf:
        errors.append("Fisiología incompleta: "+str(sorted(PHYSIOLOGY-nf)))
    if not POLICY <= pf:
        errors.append("Política corporal incompleta: "+str(sorted(POLICY-pf)))
    if not {"shelter_properties","sheltered"} <= sf:
        errors.append("Falta una única evaluación del resguardo físico")
    for path,tree in ((need_path,nt),(policy_path,pt),(cover_path,st)):
        for n in ast.walk(tree):
            modules=([a.name for a in n.names] if isinstance(n,ast.Import)
                     else [n.module or ""] if isinstance(n,ast.ImportFrom) else [])
            for m in modules:
                if m in {"world","brain","agent","motivation","nilo",
                         "survival","bodily_policy","island_views",
                         "experiment_log","nilo_runtime.application"}:
                    errors.append(f"Dependencia invertida en {path.name}: {m}")
    survival=(ROOT/"survival.py").read_text("utf-8")
    bodily=(ROOT/"bodily_policy.py").read_text("utf-8")
    if "def ensure_needs(" in survival or "def needs_summary(" in survival:
        errors.append("La fachada survival duplica el núcleo corporal")
    if "def rest_minutes(" in bodily or "def fatigue_multiplier(" in bodily:
        errors.append("La política corporal está duplicada en bodily_policy")
    if "if legacy_autocare:" not in survival or "from motivation import record_maintenance" not in survival:
        errors.append("La compatibilidad histórica de autocuidado se perdió")
    view=(ROOT/"nilo_runtime/perception/island.py").read_text("utf-8")
    facade=(ROOT/"island_views.py").read_text("utf-8")
    measurements=(ROOT/"experiment_log.py").read_text("utf-8")
    if "from nilo_runtime.worlds.shelter import sheltered" not in view:
        errors.append("El entorno no usa el propietario único de refugio")
    if "from nilo_runtime.perception.island import map_snapshot, survival_conditions" not in facade:
        errors.append("island_views dejó de delegar en la proyección de isla")
    if "site_sheltered(world,person['pos'])" not in measurements:
        errors.append("Las mediciones usan clasificación de refugio distinta del motor")
    if "shelter_condition" in view:
        errors.append("Las etiquetas de refugio habilitan aún energía")
    const=(ROOT/"construction.py").read_text("utf-8")
    if "obj['shelter_condition']=" in const or "obj.setdefault('shelter_condition'" in const:
        errors.append("La construcción todavía inventa un nivel de abrigo")
    clock=(ROOT/"nilo_runtime/application/clockwork.py").read_text("utf-8")
    if "waiting=(bool(pending" not in clock:
        errors.append("Wait continúa siendo descanso fisiológico")
    if "should_collapse(energy)" not in clock or "can_wake(energy)" not in clock:
        errors.append("El reloj implementa umbrales propios de conciencia")
    if not (ROOT/"tests/test_fisiologia_13.py").is_file():
        errors.append("Faltan tests de frontera física y sensaciones")
    return errors


if __name__=="__main__":
    errors=inspect()
    if errors:raise SystemExit("\n".join(errors))
    print("Etapa 13: fisiología, descanso y resguardo físico con únicos propietarios.")
