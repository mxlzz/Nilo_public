"""NeuroLab I3c.3a: natural-source migration frequency under fixed N inputs.

Preregistered BEFORE implementation:
 docs/neurolab/E09_02I_I3C3A_TRAYECTORIA_PRE_REGISTRO.md

NO reward, correct action, teacher, chemical metabolism or historical PRNG.
Only paired B (migration disabled) and B+ (migration enabled) on
identical four-contact microbrain, 256 scripted ticks, 20 new seeds.
A failed/no-migration result is preserved. Never tune the script.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from hashlib import sha256
import argparse
import json
from pathlib import Path
import random

from .e09_i3c3_dynamic_context import DynamicContextBrain

SEEDS=tuple(range(800,820))
TICKS=256
TAPE_LENGTH=4096
CHECKPOINT_TICK=128


def scripted_context(t:int)->int:
    if type(t) is not int or not 0<=t<TICKS:
        raise ValueError("tick outside preregistered 0..255")
    return (t//8)%2


def scripted_chemicals(t:int)->tuple[int,int,int,int]:
    if type(t) is not int or not 0<=t<TICKS:
        raise ValueError("tick outside preregistered 0..255")
    return (24,0,0,0) if t%16<8 else (0,24,0,0)


def explicit_wiring(seed:int)->tuple[int,int,int,int]:
    if type(seed) is not int or seed not in SEEDS:
        raise ValueError("seed not preregistered")
    return ((0x1000,0x2000,0x2000,0x1000) if seed%2==0
            else (0x2000,0x1000,0x1000,0x2000))


def tape_from_local_generator(seed:int)->tuple[int,...]:
    """N fixture; generated locally once, then supplied as raw RandStream."""
    if type(seed) is not int or seed not in SEEDS:
        raise ValueError("seed outside cohort")
    rng=random.Random(810000+seed)
    return tuple(rng.randrange(32768) for _ in range(TAPE_LENGTH))


def _snapshot(state):
    return {
        "tick":state.tick,
        "action_scores_state":list(state.neuron_states),
        "winner_outputs":list(state.neuron_outputs),
        "concept_outputs":list(state.concept_outputs),
        "source_pointers":[hex(c.source_pointer) for c in state.links],
        "strength":[c.synapse.strength for c in state.links],
        "stw":[c.synapse.dendrite.stw for c in state.links],
        "ltw":[c.synapse.dendrite.ltw for c in state.links],
        "random_cursor":state.random_tape.cursor,
    }


def _run_branch(brain,seed,tape):
    state=brain.initial(wiring=explicit_wiring(seed),random_draws=tape)
    initial_tape=state.random_tape.draws
    history=[]
    ticks=[]
    checkpoint=None
    migration_counts=Counter()
    action_counts=Counter()
    for t in range(TICKS):
        ctx=scripted_context(t)
        chems=scripted_chemicals(t)
        step=brain.step(state,ctx,chems)
        state=step.after
        history.append(step)
        migration_counts.update(event.reason for event in step.migration)
        action_counts.update((step.action if step.action is not None else "None",))
        first_pointer_change=any(
            a.source_pointer!=b.source_pointer
            for a,b in zip(step.before.links,step.after.links)
        )
        if first_pointer_change!=any(e.migrated for e in step.migration):
            raise AssertionError("source pointer changed without Type1 witness")
        if not brain.migration_enabled and (
                state.random_tape.cursor!=0 or step.migration):
            raise AssertionError("disabled brain migrated or drew randomness")
        ticks.append({
            "tick":t+1,
            "context":ctx,
            "chemicals":list(chems),
            "action":step.action,
            "migration":[asdict(x) for x in step.migration],
            "accepted_this_tick":sum(x.migrated for x in step.migration),
            **_snapshot(state),
        })
        if t+1==CHECKPOINT_TICK:
            checkpoint=brain.checkpoint(state)
    if checkpoint is None:
        raise AssertionError("checkpoint missing")

    # Independent exact continuation from byte-identical serialized state.
    restored=brain.restore(checkpoint)
    if checkpoint!=brain.checkpoint(restored):
        raise AssertionError("checkpoint altered by restore")
    for t in range(CHECKPOINT_TICK,TICKS):
        resumed=brain.step(
            restored,scripted_context(t),scripted_chemicals(t)
        )
        if resumed!=history[t]:
            raise AssertionError(
                f"checkpoint replay differs from uninterrupted branch at tick {t+1}")
        restored=resumed.after
    if restored!=state:
        raise AssertionError("checkpoint final state differs")
    if state.random_tape.draws!=initial_tape:
        raise AssertionError("migration mutated raw RNG tape")
    return {
        "mode":"B+" if brain.migration_enabled else "B",
        "n_ticks":len(ticks),
        "migration_reason_counts":dict(sorted(migration_counts.items())),
        "actions":dict(sorted(action_counts.items())),
        "accepted_total":sum(row["accepted_this_tick"] for row in ticks),
        "first_accepted_tick":next(
            (row["tick"] for row in ticks if row["accepted_this_tick"]),None
        ),
        "n_exhausted_final":sum(
            c.synapse.strength==0 for c in state.links
        ),
        "initial_wiring":[hex(x) for x in explicit_wiring(seed)],
        "final_wiring":[hex(c.source_pointer) for c in state.links],
        "random_cursor_final":state.random_tape.cursor,
        "rng_seed_N":810000+seed,
        "rng_tape_size":len(tape),
        "rng_tape_digest":sha256(json.dumps(tape).encode()).hexdigest(),
        "final_checkpoint_sha256":sha256(brain.checkpoint(state).encode()).hexdigest(),
        "checkpoint_replay_full_transitions":True,
        "per_tick":ticks,
    }


def run_seed(seed:int):
    if type(seed) is not int or seed not in SEEDS:
        raise ValueError("seed outside frozen independent cohort")
    tape=tape_from_local_generator(seed)
    b=DynamicContextBrain(seed,migration_enabled=False)
    bp=DynamicContextBrain(seed,migration_enabled=True)
    result_b=_run_branch(b,seed,tape)
    result_bp=_run_branch(bp,seed,tape)
    if result_b["accepted_total"]!=0 or result_b["random_cursor_final"]!=0:
        raise AssertionError("B control consumed draws or rewired")
    first_divergence=None
    first_accepted=result_bp["first_accepted_tick"]
    for before,after in zip(result_b["per_tick"],result_bp["per_tick"]):
        # Ignore tape cursor; duplicate rejects can use random without
        # changing any synapse or neuronal state.
        comparable=("winner_outputs","concept_outputs",
                    "action_scores_state","source_pointers","strength",
                    "stw","ltw","action")
        diverged=any(before[key]!=after[key] for key in comparable)
        if diverged and first_divergence is None:
            first_divergence=before["tick"]
        if diverged and first_accepted is None:
            raise AssertionError("B/B+ neural divergence without accepted migration")
        if diverged and before["tick"]<first_accepted:
            raise AssertionError("neural divergence precedes actual Type1 acceptance")
    return {
        "seed":seed,
        "initial_wiring":result_b["initial_wiring"],
        "first_neural_divergence":first_divergence,
        "branches":{"B":result_b,"B+":result_bp},
        "no_pre_migration_neural_divergence":True,
    }


def run_all(seeds=SEEDS):
    if (not isinstance(seeds,tuple) or not seeds
            or any(type(x) is not int or x not in SEEDS for x in seeds)
            or len(set(seeds))!=len(seeds)):
        raise ValueError("nonempty unique subset of pre-registered seeds")
    rows=[run_seed(seed) for seed in seeds]
    totals={}
    for mode in ("B","B+"):
        reason=Counter()
        actions=Counter()
        for row in rows:
            reason.update(row["branches"][mode]["migration_reason_counts"])
            actions.update(row["branches"][mode]["actions"])
        totals[mode]={
            "migration_reasons":dict(sorted(reason.items())),
            "actions":dict(sorted(actions.items())),
            "accepted":sum(row["branches"][mode]["accepted_total"] for row in rows),
            "seeds_with_accepted":sum(
                row["branches"][mode]["accepted_total"]>0 for row in rows),
            "exhausted_final":sum(
                row["branches"][mode]["n_exhausted_final"] for row in rows),
            "draws_consumed":sum(
                row["branches"][mode]["random_cursor_final"] for row in rows),
        }
    return {
        "protocol":"E09_02I_I3C3A_TRAYECTORIA_PRE_REGISTRO-v1",
        "study_type":"synthetic no-reward engineering stress, not learning",
        "seeds":list(seeds),"n_seeds":len(seeds),
        "ticks_per_seed":TICKS,
        "chem_schedule":"24 on CHEM0 for t mod16<8, else 24 on CHEM1",
        "context_schedule":"(t//8)%2",
        "tape_length":TAPE_LENGTH,
        "rng":"local Python random.Random(810000+seed), N fixture only; raw draws persisted",
        "migration_scheduler":"post-WTA winner output nonzero, two registered sources (N)",
        "totals":totals,
        "per_seed":rows,
        "gate_trace":"PASS: all source changes witnessed by Type1 and B/B+ neural equality before first migration",
        "gate_checkpoint":"PASS: full transitions identical from tick128 restore",
        "gate_G05_G09":"NOT TESTED",
        "limitations":"No chemistry pool, no behavioral reinforcement, no historical CRT RNG or Norn world; zero or positive migration occurrence cannot prove learning",
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    payload=json.dumps(run_all(),indent=2,sort_keys=True)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(payload,encoding="utf-8")
    print(payload,end="")


if __name__=="__main__":
    main()
