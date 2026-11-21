"""E09.02g.4: counterbalanced, noisy and delayed chemical feedback.

Six preregistered conditions: both reward orders D0→D1, D1→D0,
crossed with clean delay=1, 10% flipped chemical pulses delay=1,
and clean delay=3. The neuronal C1ContinuousBrain is UNMODIFIED.

The evaluator alone knows the target; it delivers chemical pulses
after a transparent delay queue. It never passes a target/goal to
the brain. All controls, random draws and initial seeds are fixed in
E09_02G_04_ROBUSTEZ_PRE_REGISTRO.md.
"""
from __future__ import annotations

from dataclasses import asdict
import argparse
import json
import random
import statistics

from .c1_continuous_brain import C1ContinuousBrain, ContinuousBrainState
from .e09_continuous_protocol import evaluate, snapshot

ZERO: tuple[int,int,int,int]=(0,0,0,0)
REWARD=(255,0,0,0)
PUNISHMENT=(0,255,0,0)
ORDERS=(("D0","D1"),("D1","D0"))
STRESSORS=(
    ("clean_delay1",0.0,1),
    ("noise10_delay1",0.10,1),
    ("clean_delay3",0.0,3),
)


def pulse_from_action(action: str|None, target: str,
                      *, noise: float, seed: int, tick: int
                      ) -> tuple[tuple[int,int,int,int],bool]:
    if target not in ("D0","D1"):
        raise ValueError("target del evaluador inválido")
    if action not in ("D0","D1",None):
        raise ValueError("acción inválida")
    if type(seed) is not int or seed<0 or type(tick) is not int or tick<1:
        raise ValueError("semilla/tick inválidos")
    if type(noise) is not float or noise not in (0.0,0.10):
        raise ValueError("solo tasas preregistradas 0.0 y 0.10")
    if action is None:
        return ZERO,False
    did_flip=(noise>0 and random.Random(
        seed*2_000_000+tick+93017
    ).random()<noise)
    rewarded=(action==target) != did_flip
    return (REWARD if rewarded else PUNISHMENT),did_flip


def train_with_queue(
    brain:C1ContinuousBrain,
    state:ContinuousBrainState,
    pending:tuple[tuple[int,int,int,int],...],
    target:str,
    ticks:int,
    *,
    noise:float, seed:int, learn:bool,
) -> tuple[ContinuousBrainState,tuple[tuple[int,int,int,int],...],int]:
    if type(ticks) is not int or ticks<0:
        raise ValueError("ticks de fase inválidos")
    if not isinstance(pending,tuple) or len(pending) not in (1,3):
        raise ValueError("cola de químico de longitud1 o3 requerida")
    if any(not isinstance(p,tuple) or len(p)!=4 or any(type(x) is not int or not 0<=x<=255 for x in p) for p in pending):
        raise ValueError("pulsos en cola deben ser 4 bytes")
    flips=0
    for _ in range(ticks):
        arriving=pending[0]
        event=brain.step(state,arriving,learn=learn)
        emitted,flipped=pulse_from_action(
            event.action,target,noise=noise,seed=seed,tick=event.after.tick,
        )
        pending=pending[1:]+(emitted,)
        state=event.after
        flips+=int(flipped)
    return state,pending,flips


def run_seed(
    seed:int, first:str, second:str, *,
    noise:float,delay:int,
) -> dict:
    if (first,second) not in ORDERS or delay not in (1,3):
        raise ValueError("condición no preregistrada")
    brain=C1ContinuousBrain(seed,tie_mode="random_tie")
    control=C1ContinuousBrain(seed,tie_mode="random_tie")
    initial=(ZERO,)*delay
    learned,queue,flipsA=train_with_queue(
        brain,brain.initial(),initial,first,60,
        noise=noise,seed=seed,learn=True,
    )
    frozen,frozen_queue,flipsA_frozen=train_with_queue(
        control,control.initial(),initial,first,60,
        noise=noise,seed=seed,learn=False,
    )
    scoreA=evaluate(brain,learned,first,80)
    scoreFrozen=evaluate(control,frozen,first,80)
    before=snapshot(learned)
    queue_before=queue
    learned,queue,flipsB=train_with_queue(
        brain,learned,queue,second,120,
        noise=noise,seed=seed,learn=True,
    )
    frozen,frozen_queue,flipsB_frozen=train_with_queue(
        control,frozen,frozen_queue,second,120,
        noise=noise,seed=seed,learn=False,
    )
    return {
        "seed":seed,"order":f"{first}->{second}",
        "train":scoreA,"frozen":scoreFrozen,
        "reversal":evaluate(brain,learned,second,80),
        "flipped_pulses_learned":flipsA+flipsB,
        "flipped_pulses_frozen":flipsA_frozen+flipsB_frozen,
        "pending_at_reversal":[list(x) for x in queue_before],
        "after_first":before,
        "after_reversal":snapshot(learned),
        "frozen_final_synapses":[asdict(x) for x in frozen.dendrites],
    }


def run_all()->dict:
    conditions={}
    for first,second in ORDERS:
        for label,noise,delay in STRESSORS:
            key=f"{first}_to_{second}/{label}"
            rows=[
                run_seed(seed,first,second,noise=noise,delay=delay)
                for seed in range(20)
            ]
            n_initial=sum(x["train"]>=.90 for x in rows)
            n_reversal=sum(x["reversal"]>=.90 for x in rows)
            advantage=statistics.mean(x["train"]-x["frozen"] for x in rows)
            conditions[key]={
                "order":f"{first}->{second}",
                "stressor":label,"noise":noise,"delay":delay,
                "mean_train":statistics.mean(x["train"] for x in rows),
                "mean_frozen":statistics.mean(x["frozen"] for x in rows),
                "mean_reversal":statistics.mean(x["reversal"] for x in rows),
                "good_train":n_initial,"good_reversal":n_reversal,
                "advantage_vs_frozen":advantage,
                "total_flipped_pulses_learned":sum(
                    x["flipped_pulses_learned"] for x in rows),
                "passed":n_initial>=18 and n_reversal>=18 and advantage>=.30,
                "per_seed":rows,
            }
    for first,second in ORDERS:
        reference=conditions[f"{first}_to_{second}/clean_delay1"]
        for label,_,_ in STRESSORS[1:]:
            test=conditions[f"{first}_to_{second}/{label}"]
            test["initial_accuracy_loss_vs_clean"]=(
                reference["mean_train"]-test["mean_train"])
            test["reversal_accuracy_loss_vs_clean"]=(
                reference["mean_reversal"]-test["mean_reversal"])
    return {
        "protocol":"E09_02G_04_ROBUSTEZ_PRE_REGISTRO-v1",
        "seeds_per_condition":20,
        "n_conditions":len(conditions),
        "phase_a_ticks":60,"phase_b_ticks":120,
        "holdout_ticks":80,
        "conditions":conditions,
        "scope":"C1-derived five-node circuit; chemistry pulse evaluator only",
    }


def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--strict",action="store_true",
                        help="fail only if all six preregistered gates fail")
    args=parser.parse_args()
    result=run_all()
    print(json.dumps(result,indent=2,sort_keys=True))
    if args.strict and not any(x["passed"] for x in result["conditions"].values()):
        raise SystemExit("E09g.4 negative result (all gates fail)")


if __name__=="__main__":
    main()
