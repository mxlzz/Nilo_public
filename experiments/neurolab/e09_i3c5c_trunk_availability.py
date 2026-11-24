"""I3c.5c: preregistered replay of *existing* unreinforced I3c.5a trunks.

PRE-REG: docs/neurolab/E09_02I_I3C5C_DISPONIBILIDAD_TRONCO_PRE_REGISTRO.md
Pure observation: no changes to C1 neural rules, gene values, chemicals or warmup.
20 existing seeds are a diagnostic cohort, never an independent G05 validation.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

from .c1_context_brain import C1ContextBrain
from .e09_coupled_brain import initial_coupled
from .e09_i3_metabolic_protocol import selected_genes
from .e09_i3b1_forks import witness_step

SEEDS = tuple(range(1200, 1220))
TARGETS = (0, 1)
TRUNK_TICK = 124
REFERENCE_SHA = "31559f090dc473ec5502308de2ecfee17e6e2daa07cd451fa4e61b23440225fc"
REFERENCE_FILE = (
    Path(__file__).resolve().parents[2]
    / "docs/neurolab/resultados/e09i3c5c_original_trunk_hashes.json"
)
INPUTS = tuple((i // 8) % 2 for i in range(120))


def _digest(obj):
    return sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def frozen_reference(path=REFERENCE_FILE):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("protocol") != "NL-EXP-I3c5c-v1":
        raise AssertionError("incorrect original reference protocol")
    original = data["trunks"]
    if (not isinstance(original, dict)
            or set(original) != {
                f"{seed}:{target}" for seed in SEEDS for target in TARGETS
            }
            or any(not isinstance(h, str) or len(h) != 64
                   for h in original.values())):
        raise AssertionError("reference is not complete 40-trunk cohort")
    if _digest(original) != REFERENCE_SHA or data["dict_sha256"] != REFERENCE_SHA:
        raise AssertionError("frozen original artifact hashes changed")
    return original


def _frame(state, action):
    links = state.brain.dendrites
    return {
        "tick": state.brain.tick,
        "strength_positive": sum(x.strength > 0 for x in links),
        "strength_zero": sum(x.strength == 0 for x in links),
        "stw_positive": sum(x.dendrite.stw > 0 for x in links),
        "ltw_positive": sum(x.dendrite.ltw > 0 for x in links),
        "sus_positive": sum(x.dendrite.susceptibility > 0 for x in links),
        "strengths": [x.strength for x in links],
        "stws": [x.dendrite.stw for x in links],
        "ltws": [x.dendrite.ltw for x in links],
        "action": action,
    }


def run_trunk(seed, target, receptors=None, reactions=None, original=None):
    if type(seed) is not int or seed not in SEEDS or target not in TARGETS:
        raise ValueError("outside frozen I3c5a cohort")
    if receptors is None or reactions is None:
        receptors, reactions = selected_genes()
    if original is None:
        original = frozen_reference()
    brain = C1ContextBrain(seed)
    state = initial_coupled(brain, receptors)
    history = [_frame(state, None)]
    for context in INPUTS + (target,) * 4:
        state, action = witness_step(
            brain, state, context, receptors, reactions,
            gain=1, learn=True,
        )
        history.append(_frame(state, action))
    if (len(history) != TRUNK_TICK + 1 or
            state.brain.tick != TRUNK_TICK or
            state.chemistry.tick != TRUNK_TICK):
        raise AssertionError("replay step drift")
    key = f"{seed}:{target}"
    actual_sha = _digest(brain.checkpoint(state.brain))
    if original.get(key) != actual_sha:
        raise AssertionError(f"{key}: diverged from archived I3c5a trunk hash")
    if history[0]["strength_positive"] != 8:
        raise AssertionError("initial connection count drift")
    all_exhausted = next(
        (x["tick"] for x in history if x["strength_zero"] == 8), None
    )
    recovered = any(
        x["strength_positive"] > 0 for x in history
        if all_exhausted is not None and x["tick"] > all_exhausted
    )
    return {
        "seed": seed, "target": target,
        "checkpoint_sha256": actual_sha,
        "first_all_strength_zero_tick": all_exhausted,
        "ever_recovered_strength_after_first_exhaustion": recovered,
        "strength_positive_cell_ticks": sum(
            x["strength_positive"] for x in history
        ),
        "frames": history,
    }


def run_all(seeds=SEEDS):
    if (not isinstance(seeds, tuple) or not seeds
            or len(set(seeds)) != len(seeds)
            or any(type(s) is not int or s not in SEEDS for s in seeds)):
        raise ValueError("invalid unique frozen seed subset")
    original = frozen_reference()
    receptors, reactions = selected_genes()
    trunks = [
        run_trunk(seed, target, receptors, reactions, original)
        for seed in seeds for target in TARGETS
    ]
    by_exhaustion = Counter(
        str(x["first_all_strength_zero_tick"]) for x in trunks
    )
    at_final = Counter(
        str(t["frames"][-1]["strength_positive"]) for t in trunks
    )
    if any(len(t["frames"]) != 125 for t in trunks):
        raise AssertionError("incomplete tick trace")
    return {
        "protocol": "NL-EXP-I3c5c-v1",
        "seeds": list(seeds), "unique_trunks": len(trunks),
        "samples_per_trunk": TRUNK_TICK + 1,
        "original_cohort_not_independent": True,
        "frozen_original_hash_dict_sha256": REFERENCE_SHA,
        "all_checkpoint_hashes_replayed": True,
        "first_all_zero_tick_counts": dict(sorted(by_exhaustion.items())),
        "active_links_at_tick124_counts": dict(sorted(at_final.items())),
        "recoveries_after_first_total_exhaustion": sum(
            t["ever_recovered_strength_after_first_exhaustion"] for t in trunks
        ),
        "max_strength_positive_cell_ticks": max(
            t["strength_positive_cell_ticks"] for t in trunks
        ),
        "G05_G09_G00H": "OPEN — diagnostic replay, not independent learning test",
        "trunks": trunks,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_all()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    print(json.dumps({
        k: result[k] for k in (
            "protocol", "seeds", "unique_trunks", "samples_per_trunk",
            "first_all_zero_tick_counts", "active_links_at_tick124_counts",
            "recoveries_after_first_total_exhaustion",
            "all_checkpoint_hashes_replayed", "G05_G09_G00H",
        )
    }, sort_keys=True))


if __name__ == "__main__":
    main()
