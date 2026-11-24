"""I3c.5a: preregistered delayed-credit observations of unchanged C1 8-synapse brain.

BEFORE CODE: docs/neurolab/E09_02I_I3C5A_CREDITO_DIFERIDO_PRE_REGISTRO.md
Fixed synthetic N-line bridge; not historical C1, not a G05 learning success.
All five branches fork from one immutable no-feedback trunk at logical tick 124.
No true label enters the neural step, and no gain/strength/decay is tuned.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
from pathlib import Path

from .c1_context_brain import C1ContextBrain
from .c1_synapse_integrated import (
    C1SynapticInput, DECISION_EXCITATORY_GENE, DECISION_INHIBITORY_GENE,
    update_c1_synapse,
)
from .e09_coupled_brain import initial_coupled
from .e09_i3_metabolic_protocol import selected_genes, add_environment_precursors
from .e09_i3b1_forks import witness_step
from .e09_context_protocol import MAPPING_A, MAPPING_B

SEEDS = tuple(range(1200, 1220))
TARGETS = (0, 1)
MAPS = {"A": MAPPING_A, "B": MAPPING_B}
MODES = ("N", "D0", "D1", "D2", "D3")
TRUNK_TICK = 124
END_TICK = 256
OBSERVED_GATES = (128, 256)
BOOTSTRAP_SEED = 60515
BOOTSTRAP_REPS = 2000


def initial_trunk(seed, target, receptors, reactions):
    """Identical unreinforced decision state for every timing branch."""
    if type(seed) is not int or seed not in SEEDS or target not in TARGETS:
        raise ValueError("seed or target outside frozen cohort")
    brain = C1ContextBrain(seed)
    state = initial_coupled(brain, receptors)
    action = None
    for context in tuple((i // 8) % 2 for i in range(120)) + (target,) * 4:
        state, action = witness_step(brain, state, context, receptors, reactions)
    if state.brain.tick != TRUNK_TICK or state.chemistry.tick != TRUNK_TICK:
        raise AssertionError("shared trunk timing drift")
    return brain, state, action


def optional_precursor(state, action, correct):
    """External evaluator: NEVER sends outcome when no action exists."""
    if action is None:
        return state, 0
    if action not in ("D0", "D1") or type(correct) is not bool:
        raise ValueError("invalid evaluator action/outcome")
    return add_environment_precursors(state, correct=correct), 1


def inspect_synapses(state):
    """Independent numerical witness on same OLD state, without mutations."""
    old = state.brain
    chemistry = state.chemistry.decision_chem
    expected = []
    effects = []
    susceptibility = []
    for index, syn in enumerate(old.dendrites):
        owner = index // 4
        source = (index % 4) // 2
        gene = (DECISION_INHIBITORY_GENE if index % 2
                else DECISION_EXCITATORY_GENE)
        transition = update_c1_synapse(
            syn, gene,
            C1SynapticInput(
                source_output=old.concept_outputs[source],
                owner_state=old.neuron_states[owner],
                owner_output=old.neuron_outputs[owner],
                chemicals=chemistry,
            ), tick=old.tick + 1,
        )
        expected.append(transition.after)
        effects.append(transition.numeric.reinforcement_effect)
        susceptibility.append(syn.dendrite.susceptibility)
    return tuple(expected), tuple(effects), tuple(susceptibility)


def _digest(obj):
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _slot_group(index, target, original_action):
    source = (index % 4) // 2
    owner = index // 4
    chosen = 0 if original_action == "D0" else (
        1 if original_action == "D1" else None
    )
    return source == target, (source == target and owner == chosen)


def _distance(synapses, reference, target):
    out = {
        "target_stw_abs": 0, "distractor_stw_abs": 0,
        "target_ltw_abs": 0, "distractor_ltw_abs": 0,
        "strength0": sum(s.strength == 0 for s in synapses),
        "ltw_positive_strength0": sum(
            s.strength == 0 and s.dendrite.ltw > 0 for s in synapses
        ),
    }
    for i, (actual, neutral) in enumerate(zip(synapses, reference)):
        group = "target" if (i % 4) // 2 == target else "distractor"
        for weight in ("stw", "ltw"):
            out[group + "_" + weight + "_abs"] += abs(
                getattr(actual.dendrite, weight)
                - getattr(neutral.dendrite, weight)
            )
    return out


def _trace_branch(
    brain, trunk, action, target, correct, mode, receptors, reactions,
):
    if mode not in MODES:
        raise ValueError("unknown preregistered branch")
    injection_index = None if mode == "N" else int(mode[1])
    current = trunk
    delivered = 0
    frames = []
    positions = {}
    effects_by_slot = [0] * 8
    positive_by_slot = [0] * 8
    susceptibility_positive = [0] * 8
    chem_auc = [0, 0]
    chem_max = [0, 0]
    for index in range(END_TICK - TRUNK_TICK):
        if injection_index == index:
            current, n = optional_precursor(current, action, correct)
            delivered += n
        old = current
        expected, effects, susceptibility = inspect_synapses(old)
        if any(effect < 0 for effect in effects):
            raise AssertionError("unexpected negative reinforcement effect")
        for s in range(8):
            effects_by_slot[s] += effects[s]
            positive_by_slot[s] += int(effects[s] > 0)
            susceptibility_positive[s] += int(susceptibility[s] > 0)
        chem = old.chemistry.decision_chem[:2]
        for c in range(2):
            chem_auc[c] += chem[c]
            chem_max[c] = max(chem_max[c], chem[c])
        current, _ = witness_step(
            brain, current, 1-target, receptors, reactions,
            gain=1, learn=True,
        )
        if current.brain.dendrites != expected:
            raise AssertionError(
                f"tick {current.brain.tick}: unmodified synapse witness mismatch"
            )
        if current.brain.tick != TRUNK_TICK + index + 1:
            raise AssertionError("timestep mismatch")
        positions[current.brain.tick] = current.brain.dendrites
        frames.append({
            "tick": current.brain.tick,
            "chem0": chem[0], "chem1": chem[1],
            "effects": list(effects),
            "sus_positive": [int(s > 0) for s in susceptibility],
            "strength0": sum(s.strength == 0 for s in current.brain.dendrites),
        })
    if current.brain.tick != END_TICK:
        raise AssertionError("terminal tick mismatch")
    seen = current
    readout_action = None
    for _ in range(4):
        seen, readout_action = witness_step(
            brain, seen, target, receptors, reactions, learn=False,
        )
    if seen.brain.dendrites != current.brain.dendrites:
        raise AssertionError("readout altered synapses")
    return {
        "mode": mode, "delivered": delivered,
        "injection_post_target_index": injection_index if delivered else None,
        "effect_by_slot": effects_by_slot,
        "positive_effect_count_by_slot": positive_by_slot,
        "positive_susceptibility_count_by_slot": susceptibility_positive,
        "chemical_auc": chem_auc, "chemical_max": chem_max,
        "final_readout_action": readout_action,
        "frames": frames,
    }, positions


def run_episode(seed, target, mapping_name, receptors=None, reactions=None):
    if type(seed) is not int or seed not in SEEDS or target not in TARGETS:
        raise ValueError("invalid frozen episode")
    if mapping_name not in MAPS:
        raise ValueError("unknown mapping")
    if receptors is None or reactions is None:
        receptors, reactions = selected_genes()
    brain, trunk, action = initial_trunk(seed, target, receptors, reactions)
    correct = None if action is None else action == MAPS[mapping_name][target]
    branches = {}
    positional = {}
    for mode in MODES:
        info, positions = _trace_branch(
            brain, trunk, action, target, correct, mode, receptors, reactions,
        )
        branches[mode] = info
        positional[mode] = positions
    reference = branches["N"]["effect_by_slot"]
    reference_positions = positional["N"]
    for mode in MODES:
        item = branches[mode]
        raw = item.pop("effect_by_slot")
        positive = item.pop("positive_effect_count_by_slot")
        sus = item.pop("positive_susceptibility_count_by_slot")
        signed = [x - y for x, y in zip(raw, reference)]
        attributable = [max(0, d) for d in signed]
        result = {
            "effect_raw_target": 0, "effect_raw_distractor": 0,
            "effect_raw_candidate": 0, "effect_attributed_target": 0,
            "effect_attributed_distractor": 0, "effect_attributed_candidate": 0,
            "effect_signed_target": 0, "effect_signed_distractor": 0,
            "effect_positive_count_target": 0,
            "effect_positive_count_distractor": 0,
            "sus_positive_count_target": 0, "sus_positive_count_distractor": 0,
        }
        for i in range(8):
            is_target, is_candidate = _slot_group(i, target, action)
            group = "target" if is_target else "distractor"
            result["effect_raw_" + group] += raw[i]
            result["effect_attributed_" + group] += attributable[i]
            result["effect_signed_" + group] += signed[i]
            result["effect_positive_count_" + group] += positive[i]
            result["sus_positive_count_" + group] += sus[i]
            if is_candidate:
                result["effect_raw_candidate"] += raw[i]
                result["effect_attributed_candidate"] += attributable[i]
        total = (result["effect_attributed_target"]
                 + result["effect_attributed_distractor"])
        result["target_fraction_attributed"] = (
            result["effect_attributed_target"] / total if total else None
        )
        result["candidate_fraction_attributed"] = (
            result["effect_attributed_candidate"] / total if total else None
        )
        item.update(result)
        item["gates"] = {
            str(tick): _distance(
                positional[mode][tick], reference_positions[tick], target,
            ) for tick in OBSERVED_GATES
        }
        item["final_readout_correct"] = (
            int(item["final_readout_action"] == MAPS[mapping_name][target])
        )
        if item["delivered"] != int(mode != "N" and action is not None):
            raise AssertionError("precursor count differs from preregistration")
        if action is None and positional[mode] != reference_positions:
            raise AssertionError("no-action branch changed neural trajectory")
    return {
        "seed": seed, "target": target, "mapping": mapping_name,
        "trunk_tick": trunk.brain.tick,
        "trunk_checkpoint_sha256": _digest(brain.checkpoint(trunk.brain)),
        "action": action, "correct": correct,
        "branches": branches,
    }


def _seed_mean(episodes, mode, measure):
    values = [
        row["branches"][mode][measure] for row in episodes
        if row["branches"][mode][measure] is not None
    ]
    return statistics.mean(values) if values else None


def _paired_bootstrap(seed_rows, mode1, mode2, metric):
    differences = []
    for row in seed_rows:
        a = _seed_mean(row["episodes"], mode1, metric)
        b = _seed_mean(row["episodes"], mode2, metric)
        if a is not None and b is not None:
            differences.append(a-b)
    if not differences:
        return {"n_seeds": 0, "mean": None, "ci95": None}
    center = statistics.mean(differences)
    rng = random.Random(BOOTSTRAP_SEED)
    estimates = sorted(
        statistics.mean(rng.choice(differences) for _ in differences)
        for _ in range(BOOTSTRAP_REPS)
    )
    return {
        "n_seeds": len(differences),
        "mean": center,
        "ci95": [
            estimates[int(0.025 * BOOTSTRAP_REPS)],
            estimates[int(0.975 * BOOTSTRAP_REPS) - 1],
        ],
    }


def run_seed(seed, receptors=None, reactions=None):
    if type(seed) is not int or seed not in SEEDS:
        raise ValueError("seed outside preregistered cohort")
    if receptors is None or reactions is None:
        receptors, reactions = selected_genes()
    episodes = [
        run_episode(seed, target, name, receptors, reactions)
        for target in TARGETS for name in ("A", "B")
    ]
    return {
        "seed": seed,
        "n_trunks": len(episodes),
        "missing_actions": sum(e["action"] is None for e in episodes),
        "episodes": episodes,
    }


def run_all(seeds=SEEDS):
    if (not isinstance(seeds, tuple) or not seeds or
            len(set(seeds)) != len(seeds) or
            any(type(s) is not int or s not in SEEDS for s in seeds)):
        raise ValueError("unique seed subset of frozen cohort required")
    receptors, reactions = selected_genes()
    rows = [run_seed(s, receptors, reactions) for s in seeds]
    seed_hashes = {str(row["seed"]): _digest(row) for row in rows}
    contrasts = {
        f"D0_minus_D{d}": _paired_bootstrap(
            rows, "D0", f"D{d}", "target_fraction_attributed"
        ) for d in (1, 2, 3)
    }
    return {
        "protocol": "NL-EXP-I3c5a-v1",
        "study_type": "preregistered synthetic timing/credit mechanistic forks, not G05",
        "seeds": list(seeds), "n_seeds": len(rows),
        "n_trunks": 4 * len(rows), "n_branches": 20 * len(rows),
        "shared_trunk_tick": TRUNK_TICK, "final_tick": END_TICK,
        "modes": list(MODES), "boost_gain": 1,
        "precursor_dose": 80, "synthetic_rates": 40,
        "missing_actions": sum(row["missing_actions"] for row in rows),
        "per_seed_sha256": seed_hashes,
        "timing_contrasts": contrasts,
        "G05_G09_G00H": "OPEN: behavioral causal learning NOT evaluated",
        "limitations": "Timing changes per-tick chemistry; exposure not equalized. Positive difference from neutral is operational, not proof of correct assignment. Strength-zero LTW may not be functional.",
        "per_seed": rows,
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
            "protocol", "seeds", "n_trunks", "n_branches",
            "missing_actions", "timing_contrasts", "G05_G09_G00H",
            "per_seed_sha256",
        )
    }, sort_keys=True))


if __name__ == "__main__":
    main()
