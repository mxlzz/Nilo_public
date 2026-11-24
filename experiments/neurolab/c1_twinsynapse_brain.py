"""E09.02e: five-neuron Concept→Decision learner with two-speed synapses.

Uses actual dad1.gen neuron rules ANDTYPE0 and STATE + TYPE0 - TYPE1,
and the EXPERIMENTAL TwinSynapse E04 time constants (not exact C1 engine).

Only the evaluator knows what choice is rewarded; the learner receives
a signed feedback indicating a pulse of Reward49 or Punishment50.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import random

from .c1_microcircuit import MicroTrace, MicroWeights, run_once
from .twin_weight import TwinSynapse


@dataclass(frozen=True)
class TwinBrainState:
    synapses: tuple[TwinSynapse, TwinSynapse, TwinSynapse, TwinSynapse]
    trials: int = 0

    def __post_init__(self) -> None:
        if len(self.synapses) != 4 or any(not isinstance(s,TwinSynapse) for s in self.synapses):
            raise ValueError("Se requieren 4 sinapsis STW/LTW")
        if type(self.trials) is not int or self.trials < 0:
            raise ValueError("contador inválido")


@dataclass(frozen=True)
class TwinBrainTrial:
    number: int
    synapses_at_choice: tuple[TwinSynapse,TwinSynapse,TwinSynapse,TwinSynapse]
    trace: MicroTrace
    chosen: str


class TwinBrainLearner:
    def __init__(self, seed: int):
        if type(seed) is not int or seed<0:
            raise ValueError("semilla entera no negativa requerida")
        self.seed=seed

    def initial(self) -> TwinBrainState:
        return TwinBrainState((TwinSynapse(0,0),)*4)

    def respond(self, state: TwinBrainState, stimulus: tuple[int,int]=(255,255)) -> TwinBrainTrial:
        s=state.synapses
        trace=run_once(*stimulus,weights=MicroWeights(
            d0_exc=s[0].stw,d0_inh=s[1].stw,
            d1_exc=s[2].stw,d1_inh=s[3].stw,
        ))
        action=trace.action
        if action is None:
            action=random.Random(self.seed*1000000+state.trials).choice(("D0","D1"))
        return TwinBrainTrial(state.trials,state.synapses,trace,action)

    def feedback(self, state: TwinBrainState, trial: TwinBrainTrial,
                 feedback: int, *, learn: bool=True) -> TwinBrainState:
        if type(feedback) is not int or feedback not in (-1,+1):
            raise ValueError("feedback requiere Reward/Punishment ±1")
        if trial.number != state.trials or trial.synapses_at_choice != state.synapses:
            raise ValueError("feedback obsoleto o correspondiente a otro estado")
        if trial.chosen not in ("D0","D1"):
            raise ValueError("acción inválida")
        target=(0 if trial.chosen=="D0" else 2)+(0 if feedback>0 else 1)
        synapses=tuple(
            syn.step(+1 if learn and trial.trace.concept>0 and i==target else 0)
            if learn else syn
            for i,syn in enumerate(state.synapses)
        )
        return TwinBrainState(synapses,state.trials+1)

    def checkpoint(self,state: TwinBrainState)->str:
        return json.dumps({
            "model":"E09.02e-twin-v1","seed":self.seed,"trials":state.trials,
            "synapses":[asdict(x) for x in state.synapses]
        },sort_keys=True)

    def restore(self,payload:str)->TwinBrainState:
        obj=json.loads(payload)
        if obj.get("model")!="E09.02e-twin-v1" or obj.get("seed")!=self.seed:
            raise ValueError("checkpoint incompatible")
        if set(obj)!={"model","seed","trials","synapses"}:
            raise ValueError("campos no reconocidos")
        return TwinBrainState(tuple(TwinSynapse(**p) for p in obj["synapses"]),obj["trials"])
