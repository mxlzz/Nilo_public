"""Contrasta continuidad RNG/IDs a través de procesos Python independientes.

Simula cerrar y reabrir SQLite, distintos PYTHONHASHSEED y random.seed global.
No lee ninguna partida real, ni se conecta a proveedores LLM.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent

CHILD = r"""
import json
from pathlib import Path
import random
import sys

from nilo import Simulation, initial_state
from nilo_runtime.core.identity import new_uuid, physical_suffix
from world import execute_action

mode, filename, external_seed = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3])
random.seed(external_seed)

if mode == "build":
    state = initial_state(world_seed=7321)
    person, world = state["person"], state["world"]
    person["inventory"]["madera"]=8
    legacy=execute_action(world,person,
        {"op":"build", "name":"estructura ensayo", "purpose":"apoyo",
         "materials":["madera"]}, random.Random(444))
    assert legacy[2], legacy[1]
    print(json.dumps({"id":world["structures"][-1]["id"]}))
    raise SystemExit()

def allocate(sim, stage):
    with sim.entropy.bind():
        ids=[new_uuid().hex for _ in range(7 if stage=="a" else 4)]
        physical=[physical_suffix(16) for _ in range(2)]
        move=[sim.rng.random() for _ in range(3)]
    return {"uuid":ids, "physical":physical, "motion":move}

if mode == "resume":
    sim=Simulation(db_path=filename,world_seed=7321,rng_seed=123)
    try:
        assert sim.entropy_origin == "restored_exact", sim.entropy_origin
        result=allocate(sim,"b")
    finally:
        sim.conn.close()
else:
    sim=Simulation(db_path=filename,world_seed=7321,rng_seed=9821)
    try:
        allocate(sim,"a")
        sim.write()
        result=allocate(sim,"b") if mode=="continuous" else {"prepared":True}
    finally:
        sim.conn.close()
print(json.dumps(result,sort_keys=True))
"""


def run(mode: str, path: Path, global_seed: int, hashseed: int) -> dict:
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = str(hashseed)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    for key in list(env):
        if any(part in key.upper() for part in
               ("API_KEY", "GEMINI", "GROQ", "OPENAI", "ANTHROPIC", "TOKEN", "SECRET")):
            env.pop(key, None)
    cmd=[sys.executable,"-B","-c",CHILD,mode,str(path),str(global_seed)]
    proc=subprocess.run(cmd,cwd=str(ROOT),env=env,capture_output=True,
                        text=True,timeout=90,check=False)
    if proc.returncode:
        raise RuntimeError(
            f"Subproceso {mode} falló:\n{proc.stderr[-4000:]}"
        )
    return json.loads(proc.stdout.strip())


def verify() -> dict:
    with tempfile.TemporaryDirectory(prefix="nilo-07-multirun-") as scratch:
        root=Path(scratch)
        build_a=run("build",root/"unused1",19,7)
        build_b=run("build",root/"unused2",7654,97)
        if build_a != build_b:
            raise AssertionError("Issue #143: build depende de RNG global")
        prepare=run("prepare",root/"save.sqlite3",11,5)
        if prepare != {"prepared":True}:
            raise AssertionError("No se generó el save de prueba")
        resumed=run("resume",root/"save.sqlite3",789,99)
        continuous=run("continuous",root/"control.sqlite3",9876,101)
        if resumed != continuous:
            raise AssertionError("El RNG o los IDs divergen tras reiniciar Python")
        return {
            "processes": 5,
            "world_seed": 7321,
            "rng_seed": 9821,
            "global_seed_independent": True,
            "python_hashseed_independent": True,
            "resumed_equals_continuous": True,
            "build_id": build_a["id"],
            "physical_ids_checked": len(resumed["physical"]),
            "uuid_ids_checked": len(resumed["uuid"]),
        }


if __name__ == "__main__":
    print(json.dumps(verify(),indent=2,ensure_ascii=False))
