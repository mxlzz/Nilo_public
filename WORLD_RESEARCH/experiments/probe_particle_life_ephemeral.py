"""Instrument the official MIT Particle-Life Python demonstration in temp checkout.

This adds controlled seeding, bounded time and diagnostics, and changes only
ONE existing parameter for the ablation. Does NOT reimplement physics.
Protocol: ETAPA_0_H17_PROTOCOLO_PARTICLE_LIFE.md
"""
from __future__ import annotations
import json
import pathlib
import sys


def patch(root):
    p=pathlib.Path(root)/"particle_life.py"
    s=p.read_text(encoding="utf-8")
    if "import random" not in s:
        raise AssertionError("upstream has changed, do not guess")
    s=s.replace(
        "import random",
        "import random\nimport os\nimport math\nimport json\nimport hashlib\nrandom.seed(7321)",
        1
    )
    old="rule(yellow, yellow, -0.1)"
    assert s.count(old)==1, "Original self-attraction rule not found"
    s=s.replace(old,'rule(yellow, yellow, float(os.getenv("H17_YELLOW_SELF_G","-0.1")))')
    assert s.count("run = True")==1
    s=s.replace("run = True",'''initial_positions = [[a["x"],a["y"]] for a in atoms]
frame_count = 0
run = True''',1)
    assert s.count("pygame.display.flip()")==1
    s=s.replace("pygame.display.flip()",'''pygame.display.flip()
    frame_count += 1
    if frame_count >= 80:
        def close_pair_count(particles, radius=8.0):
            return sum(
                (a["x"]-b["x"])**2+(a["y"]-b["y"])**2 < radius**2
                for i,a in enumerate(particles)
                for b in particles[i+1:]
            )
        def mean_nearest(particles):
            return sum(
                min(math.hypot(a["x"]-b["x"],a["y"]-b["y"])
                    for j,b in enumerate(particles) if i!=j)
                for i,a in enumerate(particles)
            ) / len(particles)
        all_positions = [[a["x"],a["y"]] for a in atoms]
        digest = lambda x: hashlib.sha256(json.dumps(
            x,separators=(",",":")).encode()).hexdigest()
        output = {
            "test":"H17 original Particle Life code, controlled initial state",
            "seed":7321,"frames":frame_count,
            "self_attraction_g":float(os.getenv("H17_YELLOW_SELF_G","-0.1")),
            "count":len(atoms),"count_yellow":len(yellow),
            "initial_sha256":digest(initial_positions),
            "final_sha256":digest(all_positions),
            "yellow_close_pairs_within8":close_pair_count(yellow),
            "yellow_mean_nearest_distance":mean_nearest(yellow),
            "finite_positions":all(math.isfinite(q) for p in all_positions for q in p),
        }
        print("WORLD_EVAL_JSON "+json.dumps(output,sort_keys=True),flush=True)
        run=False''',1)
    p.write_text(s,encoding="utf-8")
    print("H17 instrumented upstream file in temporary checkout; no source copied to repo",flush=True)


def read_log(p):
    lines=pathlib.Path(p).read_text(errors="replace").splitlines()
    d=[json.loads(x[len("WORLD_EVAL_JSON "):]) for x in lines
       if x.startswith("WORLD_EVAL_JSON ")]
    assert len(d)==1,(p,"missing instrumented results")
    return d[0]


def verify(files):
    baseline,control,replay=[read_log(x) for x in files]
    report={
        "test":"H17 hypothesis verification of Particle-Life spatial organization",
        "active":baseline,"ablated":control,"replay":replay,
        "same_initial_state":len({x["initial_sha256"] for x in (baseline,control,replay)})==1,
        "active_exactly_reproducible":baseline["final_sha256"]==replay["final_sha256"],
        "attraction_reduces_neighbor_distance":baseline["yellow_mean_nearest_distance"]<control["yellow_mean_nearest_distance"],
        "attraction_increases_close_pairs":baseline["yellow_close_pairs_within8"]>control["yellow_close_pairs_within8"],
        "different_final_positions":baseline["final_sha256"]!=control["final_sha256"],
        "limits":"Clustering over 80 frames is not abiogenesis, ecological plausibility, mutation, mass balance or indefinite novelty. Official physics code unchanged except ablating one coefficient."
    }
    print("WORLD_EVAL_JSON "+json.dumps(report,sort_keys=True),flush=True)
    assert report["same_initial_state"]
    assert report["active_exactly_reproducible"]
    assert report["different_final_positions"]
    assert all(x["finite_positions"] and x["count"]==200 and
               x["count_yellow"]==100 and x["frames"]==80
               for x in (baseline,control,replay))
    assert baseline["self_attraction_g"]==-.1 and control["self_attraction_g"]==0
    assert report["attraction_reduces_neighbor_distance"]
    assert report["attraction_increases_close_pairs"]


if __name__=="__main__":
    if sys.argv[1]=="patch":
        patch(sys.argv[2])
    elif sys.argv[1]=="check":
        verify(sys.argv[2:])
    else:raise SystemExit("Usage: script patch ROOT | check ACTIVE.log CONTROL.log REPLAY.log")
