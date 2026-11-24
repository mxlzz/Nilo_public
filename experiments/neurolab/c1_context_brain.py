"""E09.02g.5: six-node context-discriminating brain, without body/world.

Units: P0,P1 (one-hot external inputs), C0,C1 (fixed C1 ANDTYPE0
detectors), D0,D1 (C1 Decision SVRule plus WTA). Eight genetically
parameterized Decision dendrites: per D, 2 Concept sources × 2 classes
exc/inhib; the real Norn has 128 dendrites per class and 16 Decision
neurons, so this is a MINIMAL LABORATORY ARCHITECTURE, not an emulator.

Decision reads previous Concept outputs; each dendrite reads previous
post-WTA Decision output. Concept is recomputed last each tick.
The user-supplied C1 exe/genome numerical SVRules/rates are reused
without adjusting them; lab chemicals remain external feedback.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import random

from .c1_decay_math import relax
from .c1_dendrite_tick import DendriteState
from .c1_runtime_math import (
    DECISION_RULE, RuleInputs, dendrite_signal, evaluate, neuron_output,
)
from .c1_synapse_integrated import (
    C1SynapseState, C1SynapticInput, DECISION_EXCITATORY_GENE,
    DECISION_INHIBITORY_GENE, update_c1_synapse,
)


def _byte(v:int,name:str)->int:
    if type(v) is not int or not 0<=v<=255:
        raise ValueError(f"{name}: byte0..255")
    return v


@dataclass(frozen=True)
class ContextBrainState:
    dendrites: tuple[C1SynapseState,...]
    neuron_states: tuple[int,int]=(80,80)
    neuron_outputs: tuple[int,int]=(0,0)
    concept_outputs: tuple[int,int]=(0,0)
    tick:int=0

    def __post_init__(self):
        if not isinstance(self.dendrites,tuple) or len(self.dendrites)!=8 or any(
            not isinstance(x,C1SynapseState) for x in self.dendrites
        ):
            raise ValueError("ocho dendritas C1 tipadas necesarias")
        for field in ("neuron_states","neuron_outputs","concept_outputs"):
            arr=getattr(self,field)
            if not isinstance(arr,tuple) or len(arr)!=2:
                raise ValueError(f"{field}: dos valores requeridos")
            for x in arr:_byte(x,field)
        if type(self.tick) is not int or self.tick<0:
            raise ValueError("tick no negativo requerido")


@dataclass(frozen=True)
class ContextTick:
    before:ContextBrainState
    after:ContextBrainState
    sensory_context:int
    seen_context:int
    old_concepts:tuple[int,int]
    old_decisions:tuple[int,int]
    scores:tuple[int,int]
    winner_outputs:tuple[int,int]
    action:str|None
    owners_cleared:tuple[bool,bool]


class C1ContextBrain:
    def __init__(self,seed:int,*,blind:bool=False):
        if type(seed) is not int or seed<0 or type(blind) is not bool:
            raise ValueError("seed/blind inválidos")
        self.seed=seed
        self.blind=blind

    def initial(self)->ContextBrainState:
        syn=C1SynapseState(DendriteState(),2)
        return ContextBrainState((syn,)*8)

    def step(
        self,state:ContextBrainState,context:int,
        chemicals:tuple[int,int,int,int],
        *,learn:bool=True,
    )->ContextTick:
        if not isinstance(state,ContextBrainState):
            raise TypeError("estado de microred tipado requerido")
        if type(context) is not int or context not in (0,1):
            raise ValueError("context debe ser0 o1")
        if (not isinstance(chemicals,tuple) or len(chemicals)!=4 or any(
            type(v) is not int or not 0<=v<=255 for v in chemicals
        )):
            raise ValueError("cuatro químicos byte requeridos")
        if type(learn) is not bool:
            raise ValueError("learn debe ser bool")
        previous_contexts=state.concept_outputs
        previous_outputs=state.neuron_outputs
        tick=state.tick+1
        scores=[]
        for decision in (0,1):
            # Index: (decision*2 + concept)*2 + (exc=0,inh=1).
            exc=[state.dendrites[(decision*2+c)*2].dendrite.stw for c in (0,1)]
            inh=[state.dendrites[(decision*2+c)*2+1].dendrite.stw for c in (0,1)]
            type0=dendrite_signal(previous_contexts,tuple(exc),attenuation=128).type_value
            type1=dendrite_signal(previous_contexts,tuple(inh),attenuation=128).type_value
            value=evaluate(DECISION_RULE,RuleInputs(
                state=state.neuron_states[decision],type0=type0,type1=type1,
            ))
            scores.append(neuron_output(value,0))
        scores=tuple(scores)
        changes=[]
        cleared=[False,False]
        for i,prior in enumerate(state.dendrites):
            if not learn:
                changes.append(prior)
                continue
            owner=i//4
            source=(i%4)//2
            is_inh=bool(i%2)
            gene=DECISION_INHIBITORY_GENE if is_inh else DECISION_EXCITATORY_GENE
            result=update_c1_synapse(
                prior,gene,C1SynapticInput(
                    source_output=previous_contexts[source],
                    owner_state=state.neuron_states[owner],
                    owner_output=previous_outputs[owner],
                    chemicals=chemicals,
                ),tick=tick,
            )
            changes.append(result.after)
            cleared[owner]=cleared[owner] or result.owner_neuron_cleared
        relaxed=[]
        outputs=[]
        for owner,score in enumerate(scores):
            if cleared[owner]:
                relaxed.append(0)
                outputs.append(0)
            else:
                relaxed.append(relax(score,24,80,tick))
                outputs.append(score)
        maximum=max(outputs)
        winner=None
        if maximum>0:
            eligible=[i for i,x in enumerate(outputs) if x==maximum]
            winner=eligible[0] if len(eligible)==1 else random.Random(
                self.seed*1_000_000+state.tick
            ).choice(eligible)
        winner_outputs=tuple(v if i==winner else 0 for i,v in enumerate(outputs))
        action=("D0" if winner==0 else "D1") if winner is not None else None
        seen=0 if self.blind else context
        # Concept C0, C1 from one dendrite each; the active source is 255,
        # STW=128, attenuation255. The other concept has zero source.
        concepts=tuple(
            dendrite_signal((255 if seen==concept else 0,),
                            (128,),attenuation=255).and_value
            for concept in (0,1)
        )
        after=ContextBrainState(
            tuple(changes),tuple(relaxed),winner_outputs,concepts,tick,
        )
        return ContextTick(
            state,after,context,seen,previous_contexts,previous_outputs,
            scores,winner_outputs,action,tuple(cleared),
        )

    def checkpoint(self,state:ContextBrainState)->str:
        return json.dumps({
            "protocol":"E09g5-context-v1","seed":self.seed,"blind":self.blind,
            "state":asdict(state),
        },sort_keys=True)

    def restore(self,saved:str)->ContextBrainState:
        obj=json.loads(saved)
        if (not isinstance(obj,dict)
            or set(obj)!={"protocol","seed","blind","state"}
            or obj["protocol"]!="E09g5-context-v1"
            or obj["seed"]!=self.seed or obj["blind"]!=self.blind):
            raise ValueError("checkpoint incompatible")
        data=obj["state"]
        if set(data)!={"dendrites","neuron_states","neuron_outputs","concept_outputs","tick"}:
            raise ValueError("campos de estado incompletos")
        return ContextBrainState(
            tuple(C1SynapseState(DendriteState(**d["dendrite"]),d["strength"])
                  for d in data["dendrites"]),
            tuple(data["neuron_states"]),tuple(data["neuron_outputs"]),
            tuple(data["concept_outputs"]),data["tick"],
        )
