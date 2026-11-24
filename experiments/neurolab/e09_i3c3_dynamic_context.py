"""NeuroLab E09.02i-I3c.3: four-slot dynamic Concept source adapter.

PREREGISTERED BEFORE CODE:
 docs/neurolab/E09_02I_I3C3_ADAPTADOR_DINAMICO_PRE_REGISTRO.md

N-LINE CONVENTIONS (NOT original C1 claims):
 - Concept sources 0x1000/0x2000 are synthetic identity labels.
 - Two registered sources always eligible in Type1 migration; historical
   active-source pool is not established by this reduced model.
 - Migration is attempted POST-WTA for a recipient with nonzero winner
   output when a slot is exhausted. C1 direct callers show output gating,
   but complete scheduler/candidate population is not reconstructed.
 - New connection initials LTW0 strength2 are SYNTHETIC laboratory values.
 - RandStream holds injected CRT-like raw draws; no global migration RNG.
 - WTA tie-breaker reuses deterministic C1ContextBrain lab convention.

Six units, FOUR decision synapses. Existing C1 synapse/rule/migration
functions are reused WITHOUT modifying them or baseline C1ContextBrain.
No evaluator target, reward, mapping or expected action enters step().
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, replace
import json
import random

from .c1_decay_math import relax
from .c1_dendrite_tick import DendriteState
from .c1_runtime_math import (
    DECISION_RULE, RuleInputs, dendrite_signal, evaluate, neuron_output,
)
from .c1_synapse_integrated import (
    C1SynapseState, C1SynapticInput,
    DECISION_EXCITATORY_GENE, DECISION_INHIBITORY_GENE, update_c1_synapse,
)
from .c1_migration import (
    SourceNeuron, Dendrite, MigrationConfig, MigrationState,
    RandStream, decision_migrate,
)

SOURCE_REGISTRY=(SourceNeuron(0x1000),SourceNeuron(0x2000))
SOURCE_POINTERS=(0x1000,0x2000)
DEFAULT_SYNTHETIC_MIGRATION_CONFIG=MigrationConfig(0,0,2,2)
SLOT_IDENTITIES=((0,"exc"),(0,"inh"),(1,"exc"),(1,"inh"))
SCHEMA="E09-I3c3-DYNAMIC-4-v1"


def _byte(value,name):
    if type(value) is not int or not 0<=value<=255:
        raise ValueError(f"{name}: expected byte 0..255")
    return value


def _validate_chem(chemicals):
    if (not isinstance(chemicals,tuple) or len(chemicals)!=4
            or any(type(x) is not int or not 0<=x<=255 for x in chemicals)):
        raise ValueError("exactly four chemical byte inputs required")


@dataclass(frozen=True)
class DynamicConnection:
    owner:int
    kind:str
    source_pointer:int
    synapse:C1SynapseState

    def __post_init__(self):
        if type(self.owner) is not int or self.owner not in (0,1):
            raise ValueError("invalid Decision owner")
        if self.kind not in ("exc","inh") or not isinstance(self.kind,str):
            raise ValueError("invalid excitatory/inhibitory class")
        if type(self.source_pointer) is not int or self.source_pointer not in SOURCE_POINTERS:
            raise ValueError("unknown Concept source identity")
        if not isinstance(self.synapse,C1SynapseState):
            raise TypeError("C1SynapseState required")


@dataclass(frozen=True)
class DynamicBrainState:
    seed:int
    links:tuple[DynamicConnection,...]
    neuron_states:tuple[int,int]=(80,80)
    neuron_outputs:tuple[int,int]=(0,0)
    concept_outputs:tuple[int,int]=(0,0)
    tick:int=0
    random_tape:RandStream=RandStream(())

    def __post_init__(self):
        if type(self.seed) is not int or self.seed<0:
            raise ValueError("seed must be nonnegative integer")
        if not isinstance(self.links,tuple) or len(self.links)!=4:
            raise ValueError("exactly four Decision connections required")
        if any(not isinstance(x,DynamicConnection)
                or (x.owner,x.kind)!=SLOT_IDENTITIES[i]
                for i,x in enumerate(self.links)):
            raise ValueError("invalid order/identity of four connection slots")
        for attr in ("neuron_states","neuron_outputs","concept_outputs"):
            values=getattr(self,attr)
            if not isinstance(values,tuple) or len(values)!=2:
                raise ValueError(f"{attr}: exactly 2 values required")
            for x in values:
                _byte(x,attr)
        if type(self.tick) is not int or self.tick<0:
            raise ValueError("nonnegative logical tick required")
        if not isinstance(self.random_tape,RandStream):
            raise TypeError("RandStream required, not implicit global random")


@dataclass(frozen=True)
class MigrationWitness:
    owner:int
    kind:str
    from_pointer:int
    to_pointer:int
    reason:str
    migrated:bool
    recipient_output:int
    cursor_before:int
    cursor_after:int


@dataclass(frozen=True)
class DynamicBrainTick:
    before:DynamicBrainState
    after:DynamicBrainState
    context:int
    scores:tuple[int,int]
    class_signals:tuple[int,int,int,int]
    winner_outputs:tuple[int,int]
    action:str|None
    owners_cleared:tuple[bool,bool]
    migration:tuple[MigrationWitness,...]


def concept_index(pointer:int)->int:
    if type(pointer) is not int or pointer not in SOURCE_POINTERS:
        raise ValueError("unknown Concept source pointer")
    return SOURCE_POINTERS.index(pointer)


def class_signal(previous_concepts,connection):
    """Same C1 type contribution as baseline, with ONE source per class."""
    source=concept_index(connection.source_pointer)
    return dendrite_signal(
        (previous_concepts[source],),
        (connection.synapse.dendrite.stw,),
        attenuation=128,
    ).type_value


def attempt_type1(
    connection:DynamicConnection,
    *,recipient_output:int,random_tape:RandStream,
    config:MigrationConfig=DEFAULT_SYNTHETIC_MIGRATION_CONFIG,
):
    """Delegate Type1 itself to existing migration module, never reimplement.

    A single dendrite is its whole class in this four-slot experimental
    brain. No class-level duplicates are possible after migration.
    """
    if not isinstance(connection,DynamicConnection):
        raise TypeError("typed connection required")
    _byte(recipient_output,"recipient_output")
    if not isinstance(random_tape,RandStream) or not isinstance(config,MigrationConfig):
        raise TypeError("RandStream and MigrationConfig required")
    old=connection.synapse
    state=MigrationState((
        Dendrite(
            connection.source_pointer,
            old.dendrite.stw,old.dendrite.ltw,old.strength,
            susceptibility=old.dendrite.susceptibility,
        ),
    ),loose_counter=int(old.strength==0))
    outcome=decision_migrate(
        state,SOURCE_REGISTRY,config,random_tape,
        recipient_output=recipient_output,
    )
    new_connection=connection
    if outcome.migrated:
        if outcome.state.loose_counter!=0:
            raise AssertionError("migrated singleton class retains loose counter")
        new_d=outcome.state.dendrites[0]
        new_connection=replace(
            connection,source_pointer=new_d.source_pointer,
            synapse=C1SynapseState(
                DendriteState(
                    new_d.susceptibility,new_d.stw,new_d.ltw,
                ),new_d.strength,
            ),
        )
    elif outcome.state!=state:
        raise AssertionError("failed Type1 migration mutated connection")
    witness=MigrationWitness(
        connection.owner,connection.kind,connection.source_pointer,
        new_connection.source_pointer,outcome.reason,outcome.migrated,
        recipient_output,random_tape.cursor,outcome.random.cursor,
    )
    return new_connection,outcome.random,witness


class DynamicContextBrain:
    """Isolated variant B: 6 logical units, four dynamic decision contacts."""

    def __init__(
        self,seed:int,*,blind:bool=False,migration_enabled:bool=True,
        migration_config:MigrationConfig=DEFAULT_SYNTHETIC_MIGRATION_CONFIG,
    ):
        if type(seed) is not int or seed<0:
            raise ValueError("seed must be nonnegative integer")
        if type(blind) is not bool or type(migration_enabled) is not bool:
            raise ValueError("blind and migration_enabled must be bool")
        if not isinstance(migration_config,MigrationConfig):
            raise TypeError("MigrationConfig required")
        self.seed=seed
        self.blind=blind
        self.migration_enabled=migration_enabled
        self.migration_config=migration_config

    def initial(
        self,*,wiring:tuple[int,int,int,int],
        random_draws:tuple[int,...]=(),
    )->DynamicBrainState:
        """Explicit assignment; never infer evaluative target from mapping."""
        if (not isinstance(wiring,tuple) or len(wiring)!=4
                or any(type(ptr) is not int or ptr not in SOURCE_POINTERS
                       for ptr in wiring)):
            raise ValueError("explicit 4-slot Concept source wiring required")
        syn=C1SynapseState(DendriteState(),2)
        return DynamicBrainState(
            self.seed,
            tuple(
                DynamicConnection(owner,kind,ptr,syn)
                for (owner,kind),ptr in zip(SLOT_IDENTITIES,wiring)
            ),random_tape=RandStream(random_draws),
        )

    def _ensure_state(self,state:DynamicBrainState):
        if not isinstance(state,DynamicBrainState) or state.seed!=self.seed:
            raise ValueError("state seed/schema incompatible with brain")

    def step(
        self,state:DynamicBrainState,context:int,
        chemicals:tuple[int,int,int,int],*,learn:bool=True,
    )->DynamicBrainTick:
        self._ensure_state(state)
        if type(context) is not int or context not in (0,1):
            raise ValueError("context must be 0 or 1")
        _validate_chem(chemicals)
        if type(learn) is not bool:
            raise ValueError("learn must be boolean")
        tick=state.tick+1
        prev_concepts=state.concept_outputs
        signals=tuple(class_signal(prev_concepts,conn)
                      for conn in state.links)
        scores=[]
        for owner in (0,1):
            exc,inh=signals[owner*2:owner*2+2]
            value=evaluate(
                DECISION_RULE,RuleInputs(
                    state=state.neuron_states[owner],type0=exc,type1=inh,
                ),
            )
            scores.append(neuron_output(value,0))
        scores=tuple(scores)

        next_connections=[]
        cleared=[False,False]
        for conn in state.links:
            if not learn:
                next_connections.append(conn)
                continue
            gene=(DECISION_EXCITATORY_GENE if conn.kind=="exc"
                  else DECISION_INHIBITORY_GENE)
            source=concept_index(conn.source_pointer)
            update=update_c1_synapse(
                conn.synapse,gene,C1SynapticInput(
                    source_output=prev_concepts[source],
                    owner_state=state.neuron_states[conn.owner],
                    owner_output=state.neuron_outputs[conn.owner],
                    chemicals=chemicals,
                ),tick=tick,
            )
            next_connections.append(replace(conn,synapse=update.after))
            cleared[conn.owner]|=update.owner_neuron_cleared

        neuron_states=[]
        candidate_outputs=[]
        for owner,score in enumerate(scores):
            if cleared[owner]:
                neuron_states.append(0)
                candidate_outputs.append(0)
            else:
                neuron_states.append(relax(score,24,80,tick))
                candidate_outputs.append(score)
        maximum=max(candidate_outputs)
        winner=None
        if maximum>0:
            eligible=[i for i,v in enumerate(candidate_outputs) if v==maximum]
            winner=eligible[0] if len(eligible)==1 else random.Random(
                self.seed*1_000_000+state.tick,
            ).choice(eligible)
        winner_outputs=tuple(
            val if idx==winner else 0
            for idx,val in enumerate(candidate_outputs)
        )
        action=("D0" if winner==0 else "D1") if winner is not None else None

        seen=0 if self.blind else context
        next_concepts=tuple(
            dendrite_signal(
                (255 if seen==source else 0,),
                (128,),attenuation=255,
            ).and_value for source in (0,1)
        )

        migration=[]
        tape=state.random_tape
        if learn and self.migration_enabled:
            for i,conn in enumerate(next_connections):
                # This is a declared N scheduler convention. The source
                # candidate set is the two REGISTERED sources, not an
                # authenticated historical active-source subset.
                moved,tape,event=attempt_type1(
                    conn,recipient_output=winner_outputs[conn.owner],
                    random_tape=tape,config=self.migration_config,
                )
                next_connections[i]=moved
                migration.append(event)
        after=DynamicBrainState(
            self.seed,tuple(next_connections),
            tuple(neuron_states),winner_outputs,next_concepts,tick,tape,
        )
        return DynamicBrainTick(
            state,after,context,scores,signals,winner_outputs,action,
            tuple(cleared),tuple(migration),
        )

    def checkpoint(self,state:DynamicBrainState)->str:
        self._ensure_state(state)
        return json.dumps({
            "protocol":SCHEMA,
            "seed":self.seed,
            "blind":self.blind,
            "migration_enabled":self.migration_enabled,
            "migration_config":asdict(self.migration_config),
            "state":asdict(state),
        },sort_keys=True,separators=(",",":"))

    def restore(self,encoded:str)->DynamicBrainState:
        if not isinstance(encoded,str):
            raise TypeError("checkpoint must be JSON string")
        try:
            obj=json.loads(encoded)
        except (ValueError,TypeError) as exc:
            raise ValueError("malformed checkpoint") from exc
        if (not isinstance(obj,dict) or set(obj)!={
                "protocol","seed","blind","migration_enabled",
                "migration_config","state"}
                or obj["protocol"]!=SCHEMA or obj["seed"]!=self.seed
                or obj["blind"] is not self.blind
                or obj["migration_enabled"] is not self.migration_enabled
                or obj["migration_config"]!=asdict(self.migration_config)):
            raise ValueError("unknown or incompatible checkpoint schema")
        data=obj["state"]
        if not isinstance(data,dict) or set(data)!={
                "seed","links","neuron_states","neuron_outputs",
                "concept_outputs","tick","random_tape"
        }:
            raise ValueError("invalid checkpoint state shape")
        if (data["seed"]!=self.seed or not isinstance(data["links"],list)
                or len(data["links"])!=4):
            raise ValueError("wrong state seed or number of connections")
        links=[]
        for i,raw in enumerate(data["links"]):
            if not isinstance(raw,dict) or set(raw)!={
                    "owner","kind","source_pointer","synapse"}:
                raise ValueError("invalid connection schema")
            s=raw["synapse"]
            if not isinstance(s,dict) or set(s)!={"dendrite","strength"}:
                raise ValueError("invalid synapse schema")
            d=s["dendrite"]
            if not isinstance(d,dict) or set(d)!={
                    "susceptibility","stw","ltw"}:
                raise ValueError("invalid dendrite schema")
            link=DynamicConnection(
                raw["owner"],raw["kind"],raw["source_pointer"],
                C1SynapseState(DendriteState(**d),s["strength"]),
            )
            if (link.owner,link.kind)!=SLOT_IDENTITIES[i]:
                raise ValueError("connection slot order incompatible")
            links.append(link)
        random_raw=data["random_tape"]
        if (not isinstance(random_raw,dict)
                or set(random_raw)!={"draws","cursor"}
                or not isinstance(random_raw["draws"],list)):
            raise ValueError("invalid random tape checkpoint")
        tape=RandStream(tuple(random_raw["draws"]),random_raw["cursor"])
        state=DynamicBrainState(
            data["seed"],tuple(links),
            tuple(data["neuron_states"]),
            tuple(data["neuron_outputs"]),
            tuple(data["concept_outputs"]),
            data["tick"],tape,
        )
        if self.checkpoint(state)!=json.dumps(
                obj,sort_keys=True,separators=(",",":")):
            raise ValueError("noncanonical or lossy checkpoint")
        return state


def synthetic_probe()->dict:
    """Audit only state, wiring, migration oracles, continuation. NO learning."""
    brain=DynamicContextBrain(500)
    state=brain.initial(
        wiring=(0x1000,0x1000,0x2000,0x2000),
        random_draws=tuple((1,0,0)*64),
    )
    observed=[]
    for context in (0,0,1,1,0,1,1,0,0,1,0,1):
        tr=brain.step(state,context,(0,0,0,0))
        state=tr.after
        observed.append({
            "tick":state.tick,"action":tr.action,
            "pointers":[hex(x.source_pointer) for x in state.links],
            "migration":[asdict(x) for x in tr.migration],
            "tape_cursor":state.random_tape.cursor,
        })
    saved=brain.checkpoint(state)
    restored=brain.restore(saved)
    if saved!=brain.checkpoint(restored):
        raise AssertionError("checkpoint roundtrip changed bytes")
    for ctx in (1,0,0,1):
        a=brain.step(state,ctx,(0,0,0,0))
        b=brain.step(restored,ctx,(0,0,0,0))
        if a!=b:
            raise AssertionError("checkpoint continuation not identical")
        state,restored=a.after,b.after

    disconnected=DynamicConnection(
        0,"exc",0x1000,C1SynapseState(DendriteState(),0),
    )
    yes,yes_tape,yes_event=attempt_type1(
        disconnected,recipient_output=255,
        random_tape=RandStream((1,0,0)),
    )
    dup,dup_tape,dup_event=attempt_type1(
        disconnected,recipient_output=255,
        random_tape=RandStream((0,)),
    )
    inactive,inactive_tape,inactive_event=attempt_type1(
        disconnected,recipient_output=0,
        random_tape=RandStream(()),
    )
    if not (yes.source_pointer==0x2000 and yes.synapse.strength==2
            and yes_tape.cursor==3 and yes_event.migrated
            and dup==disconnected and dup_tape.cursor==1
            and not dup_event.migrated
            and inactive==disconnected and inactive_tape.cursor==0):
        raise AssertionError("Type1 migration oracle failed")
    return {
        "protocol":"E09_02I_I3C3_ADAPTADOR_DINAMICO_PRE_REGISTRO-v1",
        "n_units":6,"n_decision_connections":4,
        "source_ids":["0x1000","0x2000"],
        "initialization":"synthetic N: LTW0, strength2",
        "migration_scheduler":"N convention: post-WTA, nonzero owner output",
        "probe_ticks":len(observed),
        "resume_ticks":4,
        "checkpoint_roundtrip_identical":True,
        "checkpoint_resume_identical":True,
        "type1_accepted":asdict(yes_event),
        "type1_duplicate_rejected":asdict(dup_event),
        "type1_inactive_rejected":asdict(inactive_event),
        "probe_trace":observed,
        "gate_learning":"NOT EVALUATED; G05/G09 OPEN",
        "historical_fidelity":"PARTIAL; source activation, CRT RNG and recipient scheduler are N conventions",
    }


def main():
    import argparse
    from pathlib import Path
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    text=json.dumps(synthetic_probe(),indent=2,sort_keys=True)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(text,encoding="utf-8")
    print(text,end="")


if __name__=="__main__":
    main()
