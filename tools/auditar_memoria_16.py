"""Auditor de propietarios, memoria observable y fuentes ID de etapa 16."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

def functions(path):
    tree=ast.parse((ROOT/path).read_text(encoding="utf-8"))
    return {x.name for x in tree.body if isinstance(x,ast.FunctionDef)}

def audit():
    issues=[]
    expected={
        "nilo_runtime/cognition/memory.py":{"recall_relevant"},
        "nilo_runtime/cognition/research.py":{
            "terms","same_research","register_research","consolidate_research"},
        "nilo_runtime/cognition/predictions.py":{
            "begin_prediction","finish_prediction","normalize_prediction"},
        "nilo_runtime/cognition/evidence.py":{
            "reference_index","reference","measured_records",
            "projected_conclusions","projected_research"},
        "nilo_runtime/cognition/topics.py":{"canonical","topic"},
    }
    for path,functions_expected in expected.items():
        missing=functions_expected-functions(path)
        if missing:
            issues.append(path+": faltan "+repr(sorted(missing)))
    for facade in ("episodic_memory.py","cognition.py","research_cycle.py"):
        if functions(facade):
            issues.append("Fachada con ejecutores duplicados: "+facade)
    from episodic_memory import recall_relevant
    from cognition import register_research
    from research_cycle import begin_prediction
    from experiment_log import canonical, topic
    from nilo_runtime.cognition import evidence, memory, research, predictions, topics
    if recall_relevant is not memory.recall_relevant:
        issues.append("Recuperación episódica no usa propietario único")
    if register_research is not research.register_research:
        issues.append("Investigación no usa propietario único")
    if begin_prediction is not predictions.begin_prediction:
        issues.append("Predicciones duplicadas")
    if topic is not topics.topic or canonical is not topics.canonical:
        issues.append("Topic físico duplicado")
    if "visible" not in " ".join(functions("nilo_runtime/cognition/memory.py")):
        # Comprobar en código real el filtro conocido de world.revealed.
        if 'not in revealed' not in (
            ROOT/"nilo_runtime/cognition/memory.py").read_text("utf-8"):
            issues.append("Recuerdos sin filtro de terreno conocido")
    for path in ("experiment_log.py","laboratory.py"):
        if "measured_records(" not in (ROOT/path).read_text("utf-8"):
            issues.append("Los consumidores no validan IDs por registro: "+path)
    core=(ROOT/"nilo_runtime/agent/budget.py").read_text("utf-8")
    if "'investigaciones_activas'" not in core:
        issues.append("Se omiten investigaciones actuales del contexto LLM")
    if not (ROOT/"tests/test_memoria_16.py").is_file():
        issues.append("Faltan tests de etapa 16")
    return issues

if __name__=="__main__":
    problems=audit()
    if problems:
        raise SystemExit("\n".join(problems))
    print("Etapa 16: memoria/research/hipótesis, proveniencia por ID y proyecciones únicos.")
