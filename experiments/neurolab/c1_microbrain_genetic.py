"""E09.02g.2: five-node C1-gene-derived decision learning experiment.

P0, P1 (abstract external signals) -> C (fixed ANDTYPE0) -> D0,D1,
where each Decision has one excitatory and one inhibitory C1 dendrite.

C1-derived: concept/decision SVRules and attenuation, dendritic chemical
gating, STW/LTW, strength rates, WTA maximum.
LAB ABSTRACTIONS: 1 dendrite/class vs the real 128/class, fixed concept
synapses, reset baseline decision state 80 each trial, feedback as
instant chemical pulse, four explicit WTA timing/tie interpretations.

This is NOT a faithful 952-neuron or autonomous Norn. No body or world.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import random

from .c1_dendrite_tick import DendriteState
from .c1_runtime_math import (
    DECISION_RULE, RuleInputs, dendrite_signal, evaluate,
)
from .c1_synapse_integrated import (
    C1SynapseState, C1SynapticInput, DECISION_EXCITATORY_GENE,
    DECISION_INHIBITORY_GENE, update_c1_synapse,
)


@dataclass(frozen=True)
class MicroBrainState:
    dendrites: tuple[C1SynapseState, C1SynapseState,
                     C1SynapseState, C1SynapseState]
    trials: int = 0

    def __post_init__(self):
        if len(self.dendrites)!=4 or any(
            not isinstance(d,C1SynapseState) for d in self.dendrites
        ):
            raise ValueError("cuatro dendritas C1 tipadas requeridas")
        if type(self.trials) is not int or self.trials<0:
            raise ValueError("contador de ensayos inválido")


@dataclass(frozen=True)
class C1Choice:
    trial: int
    state_at_choice: MicroBrainState
    concept: int
    decision_scores: tuple[int,int]
    action: str
    tie: bool


@dataclass(frozen=True)
class C1BrainTransition:
    before: MicroBrainState
    after: MicroBrainState
    choice: C1Choice
    chemistry: tuple[int,int,int,int]
    owner_outputs: tuple[int,int]
    cleared_owners: tuple[bool,bool]


class MicroC1Brain:
    def __init__(self, seed: int, *, timing: str, tie_mode: str):
        if type(seed) is not int or seed<0:
            raise ValueError("seed entera no negativa")
        if timing not in ("post_wta_gated","pre_wta_all"):
            raise ValueError("timing inválido")
        if tie_mode not in ("first_index","random_tie"):
            raise ValueError("tie_mode inválido")
        self.seed=seed
        self.timing=timing
        self.tie_mode=tie_mode

    def initial(self) -> MicroBrainState:
        initial=C1SynapseState(DendriteState(0,0,0),2)
        return MicroBrainState((initial,)*4)

    def respond(self,state:MicroBrainState)->C1Choice:
        concept=dendrite_signal((255,255),(128,128),attenuation=255).and_value
        if concept!=253:
            raise AssertionError("el Concept C1 de dos fuentes debe ser 253")
        scores=[]
        for offset in (0,2):
            exc=state.dendrites[offset].dendrite.stw
            inh=state.dendrites[offset+1].dendrite.stw
            st0=dendrite_signal((concept,),(exc,),attenuation=128).type_value
            st1=dendrite_signal((concept,),(inh,),attenuation=128).type_value
            scores.append(evaluate(DECISION_RULE,RuleInputs(
                state=80,type0=st0,type1=st1,
            )))
        scores=tuple(scores)
        if scores[0] > scores[1]:
            action="D0"
        elif scores[1] > scores[0]:
            action="D1"
        elif self.tie_mode=="first_index":
            action="D0"
        else:
            action=random.Random(self.seed*1_000_000+state.trials).choice(("D0","D1"))
        return C1Choice(state.trials,state,concept,scores,action,
                        scores[0]==scores[1])

    def feedback(self,state:MicroBrainState,choice:C1Choice,
                 chemicals:tuple[int,int,int,int],*,learn:bool=True) -> C1BrainTransition:
        if choice.state_at_choice!=state or choice.trial!=state.trials:
            raise ValueError("elección obsoleta")
        if (not isinstance(chemicals,tuple) or len(chemicals)!=4
                or any(type(chem) is not int or not 0<=chem<=255 for chem in chemicals)):
            raise ValueError("cuatro concentraciones químicas byte requeridas")
        if self.timing=="post_wta_gated":
            outputs=(choice.decision_scores[0] if choice.action=="D0" else 0,
                     choice.decision_scores[1] if choice.action=="D1" else 0)
        else:
            outputs=choice.decision_scores
        if not learn:
            next_state=MicroBrainState(state.dendrites,state.trials+1)
            return C1BrainTransition(state,next_state,choice,chemicals,outputs,(False,False))

        changes=[]
        cleared=[False,False]
        for index,previous in enumerate(state.dendrites):
            owner_index=index//2
            gene=DECISION_EXCITATORY_GENE if index%2==0 else DECISION_INHIBITORY_GENE
            result=update_c1_synapse(
                previous,gene,
                C1SynapticInput(
                    source_output=choice.concept,
                    owner_state=choice.decision_scores[owner_index],
                    owner_output=outputs[owner_index],
                    chemicals=chemicals,
                ),
                tick=state.trials+1,
            )
            changes.append(result.after)
            cleared[owner_index]=cleared[owner_index] or result.owner_neuron_cleared
        new_state=MicroBrainState(tuple(changes),state.trials+1)
        return C1BrainTransition(state,new_state,choice,chemicals,outputs,tuple(cleared))

    def checkpoint(self,state:MicroBrainState)->str:
        return json.dumps({
            "version":"E09.02g.2-v1","seed":self.seed,
            "timing":self.timing,"tie_mode":self.tie_mode,
            "trials":state.trials,"dendrites":[asdict(d) for d in state.dendrites],
        },sort_keys=True)

    def restore(self,data:str)->MicroBrainState:
        obj=json.loads(data)
        if (not isinstance(obj,dict)
            or set(obj)!={"version","seed","timing","tie_mode","trials","dendrites"}
            or obj["version"]!="E09.02g.2-v1" or obj["seed"]!=self.seed
            or obj["timing"]!=self.timing or obj["tie_mode"]!=self.tie_mode):
            raise ValueError("checkpoint incompatible")
        dendrites=tuple(
            C1SynapseState(DendriteState(**d["dendrite"]),d["strength"])
            for d in obj["dendrites"]
        )
        return MicroBrainState(dendrites,obj["trials"])
