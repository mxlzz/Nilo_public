"""I3c.7d: compare DIRECT-zero-loss and METABOLIC-nominal-loss contracts.

PREREG: docs/neurolab/E09_02I_I3C7D_COMPARABILIDAD_ATROFIA_PRE_REGISTRO.md
Three trajectories from one reused fixture seed0. Read-only mechanisms:
no new model, seed cohort, chemicals, reward signal, gain, or learning claim.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from .c1_context_brain import C1ContextBrain
from .c1_synapse_integrated import (
    C1SynapticInput, DECISION_EXCITATORY_GENE,
    DECISION_INHIBITORY_GENE, update_c1_synapse,
)
from .e09_context_protocol import ZERO, REWARD, PUNISHMENT
from .e09_i3_metabolic_protocol import selected_genes
from .e09_historical_locus import initialize_brain_chem_loci

FIXTURE_SEED=0
TICKS=20
SNAPSHOTS=(0,4,5,9,10,16,20)
MODES=("Z","L","F")
NOMINAL=(0,0,16,16)


def _witness(state,chemicals,tick):
    expected=[]
    events=[]
    for i,syn in enumerate(state.dendrites):
        gene=(DECISION_INHIBITORY_GENE if i%2
              else DECISION_EXCITATORY_GENE)
        tr=update_c1_synapse(
            syn,gene,C1SynapticInput(
                source_output=state.concept_outputs[(i%4)//2],
                owner_state=state.neuron_states[i//4],
                owner_output=state.neuron_outputs[i//4],
                chemicals=chemicals,
            ),tick=tick,
        )
        expected.append(tr.after)
        events.append({
            "lost_connection":tr.strength.lost_connection,
            "did_lose":tr.strength.did_lose,
            "did_gain":tr.strength.did_gain,
        })
    return tuple(expected),events


def run():
    receptors,_=selected_genes()
    nominal=initialize_brain_chem_loci(receptors,6)
    if nominal!=NOMINAL:
        raise AssertionError("original genome Decision CHEM nominals changed")
    if (ZERO!=(0,0,0,0) or REWARD!=(255,0,0,0)
            or PUNISHMENT!=(0,255,0,0)
            or REWARD[2:]!=(0,0) or PUNISHMENT[2:]!=(0,0)):
        raise AssertionError("historic direct controls no longer disable chemical atrophy")
    traces={}
    initial=C1ContextBrain(FIXTURE_SEED).initial()
    for mode in MODES:
        brain=C1ContextBrain(FIXTURE_SEED)
        state=initial
        chem=ZERO if mode=="Z" else nominal
        learn=mode!="F"
        counts={"gain":0,"lose":0,"lost_connection":0,"witness_checks":0}
        snapshots={"0":{
            "strengths":[s.strength for s in state.dendrites],
            "live":sum(s.strength>0 for s in state.dendrites),
            "stw":[s.dendrite.stw for s in state.dendrites],
            "ltw":[s.dendrite.ltw for s in state.dendrites],
        }}
        events={}
        for tick in range(1,TICKS+1):
            expected,contract=_witness(state,chem,tick)
            tr=brain.step(state,0,chem,learn=learn)
            if tr.after.tick!=tick:
                raise AssertionError("tick drift")
            if learn:
                if tr.after.dendrites!=expected:
                    raise AssertionError("original C1 numeric witness mismatch")
                counts["witness_checks"]+=8
                counts["gain"]+=sum(x["did_gain"] for x in contract)
                counts["lose"]+=sum(x["did_lose"] for x in contract)
                counts["lost_connection"]+=sum(
                    x["lost_connection"] for x in contract
                )
            elif tr.after.dendrites!=initial.dendrites:
                raise AssertionError("learn=False must freeze dendrite updates")
            events[str(tick)]={
                "gain":sum(x["did_gain"] for x in contract) if learn else 0,
                "lose":sum(x["did_lose"] for x in contract) if learn else 0,
                "lost_connection":sum(x["lost_connection"] for x in contract)
                    if learn else 0,
                "cleared_owners":list(tr.owners_cleared),
            }
            state=tr.after
            if tick in SNAPSHOTS:
                snapshots[str(tick)]={
                    "strengths":[s.strength for s in state.dendrites],
                    "live":sum(s.strength>0 for s in state.dendrites),
                    "stw":[s.dendrite.stw for s in state.dendrites],
                    "ltw":[s.dendrite.ltw for s in state.dendrites],
                }
        traces[mode]={
            "neural_chem":list(chem),
            "learn":learn,
            "ticks":TICKS,
            "counts":counts,
            "snapshots":snapshots,
            "events":events,
        }
    for t in (0,4,5,9,10,16,20):
        want_z=2
        want_l=(2 if t<5 else 1 if t<10 else 0)
        for mode,want in (("Z",want_z),("L",want_l),("F",2)):
            if traces[mode]["snapshots"][str(t)]["strengths"]!=[want]*8:
                raise AssertionError(f"strength regime mismatch for {mode} at {t}")
    if (traces["L"]["events"]["5"]["lose"]!=8
            or traces["L"]["events"]["10"]["lost_connection"]!=8
            or traces["Z"]["counts"]["lose"]!=0
            or traces["F"]["counts"]["lose"]!=0
            or traces["L"]["counts"]["witness_checks"]!=160):
        raise AssertionError("original loss cadence mismatch")
    return {
        "protocol":"NL-AUDIT-I3c7d-v1",
        "type":"post hoc code-path/source comparability; not behavioral holdout",
        "fixture_seed":FIXTURE_SEED,
        "nominal_from_original_gen":list(nominal),
        "direct_control_tokens":{
            "ZERO":list(ZERO),"REWARD":list(REWARD),"PUNISHMENT":list(PUNISHMENT),
        },
        "mechanical_regimes":traces,
        "interpretation":"Direct E09g.5 supplies CHEM2/3=0, disabling the lose-strength rule; synthetic I3 initializes CHEM2/3=16 via original receptor nominal and without endogeneous emitters it remains >0. Frozen readout learn=False also disables atrophy/relaxation, not just reward-driven changes. Therefore direct-vs-metabolic benchmarks differ in loss regime as well as reward intensity and timing.",
        "limitations":"Demonstrates one isolated fixed-sensory no-feedback 20-tick core and source constants. It does not claim exact chemical trajectories in living C1 or attribute all E09g.5 success to loss-regime changes.",
        "G05_G09_G00H":"OPEN",
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    result=run()
    raw=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(raw,encoding="utf-8")
    print(raw,end="")


if __name__=="__main__":
    main()
