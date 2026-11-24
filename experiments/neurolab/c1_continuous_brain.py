"""E09.02g.3: continuous 5-neuron C1-inspired brain clock.

Original C1 exe evidence:
  VA 0x403C92: output lobes processed 6,7,8 in order;
  VA 0x403ED1: each neuron's *prior* output/state captured for SVRules;
  VA 0x4048CC: WTA after output-lobe neuron updates.

P0/P1 -> Concept C (fixed ANDTYPE0) is updated AFTER Decision,
so Decision reads C's prior-tick output. Dendrite susceptibility reads
prior-tick post-WTA Decision output. Decision neuron STATE persists and
relaxes with its actual genotype neural_decay=24, rest=80.

LAB LIMITATIONS: only 1 dendrite per class vs 128 in real C1 Decision;
concept detector is fixed; chemical pulses supplied by external
evaluator; no embodied needs/metabolism, Attention or migration.
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
    C1SynapseState, C1SynapticInput,
    DECISION_EXCITATORY_GENE, DECISION_INHIBITORY_GENE,
    update_c1_synapse,
)


def _byte(value: int, name: str) -> int:
    if type(value) is not int or not 0<=value<=255:
        raise ValueError(f"{name} requiere byte")
    return value


@dataclass(frozen=True)
class ContinuousBrainState:
    dendrites: tuple[C1SynapseState, C1SynapseState,
                     C1SynapseState, C1SynapseState]
    neuron_states: tuple[int,int]=(80,80)
    neuron_outputs: tuple[int,int]=(0,0)
    concept_output: int=0
    tick: int=0

    def __post_init__(self):
        if len(self.dendrites)!=4 or any(
            not isinstance(d,C1SynapseState) for d in self.dendrites
        ):
            raise ValueError("cuatro sinapsis tipadas requeridas")
        for label in ("neuron_states","neuron_outputs"):
            vals=getattr(self,label)
            if not isinstance(vals,tuple) or len(vals)!=2:
                raise ValueError(f"{label} debe tener dos bytes")
            for val in vals:
                _byte(val,label)
        _byte(self.concept_output,"concept_output")
        if type(self.tick) is not int or self.tick<0:
            raise ValueError("tick debe ser no negativo")


@dataclass(frozen=True)
class ContinuousTickTrace:
    before: ContinuousBrainState
    after: ContinuousBrainState
    chemicals_in: tuple[int,int,int,int]
    concept_previous: int
    decision_outputs_previous: tuple[int,int]
    decision_scores: tuple[int,int]
    winner_outputs: tuple[int,int]
    action: str | None
    had_tie: bool
    cleared_owners: tuple[bool,bool]


class C1ContinuousBrain:
    def __init__(self, seed: int, *, tie_mode: str):
        if type(seed) is not int or seed<0:
            raise ValueError("semilla entera no negativa")
        if tie_mode not in ("first_index","random_tie"):
            raise ValueError("tie_mode inválido")
        self.seed=seed
        self.tie_mode=tie_mode

    def initial(self)->ContinuousBrainState:
        start=C1SynapseState(DendriteState(),2)
        return ContinuousBrainState((start,)*4)

    def step(
        self, state:ContinuousBrainState,chemicals:tuple[int,int,int,int],
        *,learn:bool=True,
    )->ContinuousTickTrace:
        if not isinstance(state,ContinuousBrainState):
            raise TypeError("estado continuo tipado necesario")
        if (not isinstance(chemicals,tuple) or len(chemicals)!=4
                or any(type(v) is not int or not 0<=v<=255 for v in chemicals)):
            raise ValueError("se requieren cuatro químicos byte")
        if not isinstance(learn,bool):
            raise ValueError("learn debe ser bool")
        tick=state.tick+1
        previous_concept=state.concept_output
        previous_outputs=state.neuron_outputs

        # Decision (lobe 6) executes BEFORE Concept (lobe 8).
        # Both D cells read the same PRIOR concept output and OWN prior state.
        scores=[]
        for index in (0,1):
            a=state.dendrites[2*index].dendrite.stw
            b=state.dendrites[2*index+1].dendrite.stw
            exc=dendrite_signal((previous_concept,),(a,),attenuation=128).type_value
            inh=dendrite_signal((previous_concept,),(b,),attenuation=128).type_value
            new_state=evaluate(DECISION_RULE,RuleInputs(
                state=state.neuron_states[index],type0=exc,type1=inh,
            ))
            scores.append(neuron_output(new_state,0))
        scores=tuple(scores)

        updated=[]
        cleared=[False,False]
        for index,dendrite in enumerate(state.dendrites):
            if not learn:
                updated.append(dendrite)
                continue
            owner=index//2
            gen=DECISION_EXCITATORY_GENE if index%2==0 else DECISION_INHIBITORY_GENE
            # SV snapshot uses LAST TICK'S WTA-masked output and old
            # state, rather than the current winning action.
            result=update_c1_synapse(
                dendrite,gen,
                C1SynapticInput(
                    source_output=previous_concept,
                    owner_state=state.neuron_states[owner],
                    owner_output=previous_outputs[owner],
                    chemicals=chemicals,
                ),tick=tick,
            )
            updated.append(result.after)
            cleared[owner]=cleared[owner] or result.owner_neuron_cleared

        new_neuron_states=[]
        candidate_outputs=[]
        for index,score in enumerate(scores):
            if cleared[index]:
                new_neuron_states.append(0)
                candidate_outputs.append(0)
            else:
                # C1 saves the output THEN relaxes the internal STATE.
                new_neuron_states.append(relax(score,24,80,tick))
                candidate_outputs.append(score)

        maximum=max(candidate_outputs)
        winner=None
        if maximum>0:
            high=[i for i,v in enumerate(candidate_outputs) if v==maximum]
            if len(high)==1 or self.tie_mode=="first_index":
                winner=high[0]
            else:
                winner=random.Random(self.seed*1_000_000+state.tick).choice(high)
        winner_outputs=tuple(
            value if winner==i else 0 for i,value in enumerate(candidate_outputs)
        )
        action=("D0" if winner==0 else "D1") if winner is not None else None

        # C (lobe 8) is processed only after all Decision cells and WTA.
        # Fixed Perception inputs P0=P1=255 through LTW/STW128:
        current_concept=dendrite_signal(
            (255,255),(128,128),attenuation=255,
        ).and_value
        assert current_concept==253
        after=ContinuousBrainState(
            tuple(updated),tuple(new_neuron_states),winner_outputs,
            current_concept,tick,
        )
        return ContinuousTickTrace(
            state,after,chemicals,previous_concept,previous_outputs,
            scores,winner_outputs,action,maximum>0 and
            candidate_outputs[0]==candidate_outputs[1],tuple(cleared),
        )

    def checkpoint(self,state:ContinuousBrainState)->str:
        return json.dumps({
            "protocol":"E09g3-continuous-v1","seed":self.seed,"tie_mode":self.tie_mode,
            "state":asdict(state),
        },sort_keys=True)

    def restore(self,saved:str)->ContinuousBrainState:
        record=json.loads(saved)
        if (not isinstance(record,dict)
            or set(record)!={"protocol","seed","tie_mode","state"}
            or record["protocol"]!="E09g3-continuous-v1"
            or record["seed"]!=self.seed or record["tie_mode"]!=self.tie_mode):
            raise ValueError("checkpoint incompatible")
        data=record["state"]
        if set(data)!={"dendrites","neuron_states","neuron_outputs","concept_output","tick"}:
            raise ValueError("estado de checkpoint incompleto")
        return ContinuousBrainState(
            tuple(C1SynapseState(DendriteState(**d["dendrite"]),d["strength"])
                  for d in data["dendrites"]),
            tuple(data["neuron_states"]),tuple(data["neuron_outputs"]),
            data["concept_output"],data["tick"],
        )
