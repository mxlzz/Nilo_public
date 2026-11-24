"""E09.02i-I3c.4a: posthoc read-only migration turnover/LTW observer.

PRE-REGISTERED AFTER original negative I3c4 but BEFORE instrumentation:
 docs/neurolab/E09_02I_I3C4A_TURNOVER_PRE_REGISTRO.md

Read-only subclass calls EXACT original DynamicContextBrain.step, records
its immutable before/after trace, then asserts exact SHA256 of unchanged
I3c4 run_seed() output against 20 frozen corrected CI artifact hashes.
No tuning, no new inputs or interventions; not a second confirmatory cohort.
"""
from __future__ import annotations

from collections import Counter,defaultdict
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from statistics import mean,median
from unittest.mock import patch
import argparse
import json

from . import e09_i3c4_yoked_metabolic as original
from .e09_i3c3_dynamic_context import DynamicContextBrain

ROOT=Path(__file__).resolve().parents[2]
HASHES_PATH=ROOT/"docs/neurolab/resultados/e09i3c4_golden_seed_hashes.json"
PHASES=("first","reversed")
MODES=("B","Y","P","F")


class WitnessBrain(DynamicContextBrain):
    registry=[]

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        index=len(type(self).registry)
        if index>=4:
            raise AssertionError("unexpected extra brain in I3c4")
        self.mode=MODES[index]
        type(self).registry.append(self)
        self.phase_index=-1
        self.previous_learn=False
        self.accepted=[]
        self.by_reason={phase:Counter() for phase in PHASES}
        self.train_states={}

    def step(self,state,context,chemicals,*,learn=True):
        if learn and not self.previous_learn:
            self.phase_index+=1
            if self.phase_index>=len(PHASES):
                raise AssertionError("unexpected learning phase after reversal")
        self.previous_learn=learn
        before=state
        transition=super().step(
            state,context,chemicals,learn=learn,
        )
        if learn:
            phase=PHASES[self.phase_index]
            self.train_states[phase]=transition.after
            self.by_reason[phase].update(event.reason
                                             for event in transition.migration)
            for i,event in enumerate(transition.migration):
                conn_before=before.links[i]
                conn_after=transition.after.links[i]
                changed=(conn_before.source_pointer!=conn_after.source_pointer)
                if changed!=event.migrated:
                    raise AssertionError("unwitnessed source-pointer change")
                if event.migrated:
                    if (event.from_pointer!=conn_before.source_pointer
                            or event.to_pointer!=conn_after.source_pointer
                            or conn_after.synapse.dendrite.ltw!=0):
                        raise AssertionError("accepted Type1 did not produce expected new connection")
                    self.accepted.append({
                        "phase":phase,"tick":transition.after.tick,
                        "owner":conn_before.owner,"class":conn_before.kind,
                        "from_pointer":hex(event.from_pointer),
                        "to_pointer":hex(event.to_pointer),
                        "cursor_before":event.cursor_before,
                        "cursor_after":event.cursor_after,
                        "recipient_output":event.recipient_output,
                        "pre_strength":conn_before.synapse.strength,
                        "post_strength":conn_after.synapse.strength,
                        "pre_STW":conn_before.synapse.dendrite.stw,
                        "post_STW":conn_after.synapse.dendrite.stw,
                        "pre_LTW":conn_before.synapse.dendrite.ltw,
                        "post_LTW":conn_after.synapse.dendrite.ltw,
                        "input_chem_0_1":[chemicals[0],chemicals[1]],
                    })
        return transition


def golden_hashes():
    data=json.loads(HASHES_PATH.read_text(encoding="utf-8"))
    if (data["source"]["workflow_id"]!=44960526007
            or data["source"]["artifact_id"]!=14729775966
            or data["hash_canonicalization"]!=
               "sha256(json.dumps(row,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('utf-8'))"
            or sorted(data["seeds"])!=[str(i) for i in original.SEEDS]):
        raise AssertionError("unexpected original fingerprint fixture")
    if any(len(h)!=64 for h in data["seeds"].values()):
        raise AssertionError("invalid golden hash")
    return data["seeds"]


def observe_seed(seed,golden):
    if type(seed) is not int or seed not in original.SEEDS:
        raise ValueError("only original I3c4 seeds are diagnostic")
    WitnessBrain.registry=[]
    with patch.object(original,"DynamicContextBrain",WitnessBrain):
        baseline=original.run_seed(seed)
    observed=WitnessBrain.registry
    if tuple(x.mode for x in observed)!=MODES:
        raise AssertionError("observer changed arm construction order")
    encoded=json.dumps(
        baseline,sort_keys=True,separators=(",",":"),ensure_ascii=True
    )
    digest=sha256(encoded.encode("utf-8")).hexdigest()
    if digest!=golden[str(seed)]:
        raise AssertionError("observer I3c4 run_seed diverged from immutable original CI")
    results={}
    for obj in observed:
        outcomes={}
        for phase in PHASES:
            entries=[e for e in obj.accepted if e["phase"]==phase]
            reasons=obj.by_reason[phase]
            expected=baseline[phase]["train"][obj.mode]
            if (len(entries)!=expected["migration_acceptances"]
                    or reasons.get("accepted",0)!=len(entries)):
                raise AssertionError("observer Type1 events mismatch original I3c4 per-arm count")
            if obj.mode in ("B","F") and entries:
                raise AssertionError("observer found migration in immutable control")
            winner=Counter((e["owner"],e["class"]) for e in entries)
            directions=Counter(
                (e["from_pointer"],e["to_pointer"]) for e in entries
            )
            histories=defaultdict(list)
            for e in entries:
                histories[(e["owner"],e["class"])].append(e["tick"])
            intervals=[
                b-a for ticks in histories.values()
                for a,b in zip(ticks,ticks[1:])
            ]
            if obj.mode=="F":
                # F is frozen during BOTH training and holdout, so it never
                # invokes step(learn=True). Its four links remain identical
                # to the initial state; original I3c4 enforces this.
                last=obj.initial(
                    wiring=original.explicit_wiring(seed),
                    random_draws=(),
                )
            else:
                last=obj.train_states[phase]
            outcomes[phase]={
                "accepted_contact_events":len(entries),
                "migration_active_ticks":len(set(e["tick"] for e in entries)),
                "by_slot":{
                    f"D{owner}-{kind}":winner[(owner,kind)]
                    for owner in (0,1) for kind in ("exc","inh")
                },
                "direction":{
                    f"{a}->{b}":n for (a,b),n in sorted(directions.items())
                },
                "intervals_between_migrations":{
                    "count":len(intervals),
                    "mean":mean(intervals) if intervals else None,
                    "median":median(intervals) if intervals else None,
                    "min":min(intervals) if intervals else None,
                    "max":max(intervals) if intervals else None,
                },
                "positive_LTW_before_migration":sum(
                    e["pre_LTW"]>0 for e in entries),
                "LTW_units_present_before_migration":sum(
                    e["pre_LTW"] for e in entries),
                "positive_STW_before_migration":sum(
                    e["pre_STW"]>0 for e in entries),
                "sum_STW_prior_migration":sum(
                    e["pre_STW"] for e in entries),
                "previous_strength_positive":sum(
                    e["pre_strength"]>0 for e in entries),
                "connections_with_positive_LTW_at_training_end":sum(
                    c.synapse.dendrite.ltw>0 for c in last.links),
                "LTW_total_at_training_end":sum(
                    c.synapse.dendrite.ltw for c in last.links),
                "strength_zero_at_training_end":sum(
                    c.synapse.strength==0 for c in last.links),
                "reasons":dict(sorted(reasons.items())),
                "events":entries,
            }
            if outcomes[phase]["migration_active_ticks"] != (
                    expected["migration_active_ticks"]):
                raise AssertionError("observer ticks with migration mismatch original")
        results[obj.mode]=outcomes
    return {
        "seed":seed,
        "original_i3c4_sha256":digest,
        "observed_original_exactly":True,
        "modes":results,
        "original_holdout":{
            phase:{
                mode:baseline[phase]["holdout"][mode]["overall"]
                for mode in MODES
            } for phase in PHASES
        },
    }


def run_all(seeds=original.SEEDS):
    if (not isinstance(seeds,tuple) or not seeds
            or any(type(s) is not int or s not in original.SEEDS
                   for s in seeds)
            or len(set(seeds))!=len(seeds)):
        raise ValueError("unique seeds from original I3c4 only")
    golden=golden_hashes()
    rows=[observe_seed(seed,golden) for seed in seeds]
    totals={}
    for mode in MODES:
        totals[mode]={}
        for phase in PHASES:
            entries=[row["modes"][mode][phase] for row in rows]
            totals[mode][phase]={
                name:sum(e[name] for e in entries)
                for name in (
                    "accepted_contact_events","migration_active_ticks",
                    "positive_LTW_before_migration",
                    "LTW_units_present_before_migration",
                    "positive_STW_before_migration",
                    "sum_STW_prior_migration",
                    "previous_strength_positive",
                    "connections_with_positive_LTW_at_training_end",
                    "LTW_total_at_training_end",
                    "strength_zero_at_training_end",
                )
            }
            if totals[mode][phase]["accepted_contact_events"]!=sum(
                e["reasons"].get("accepted",0) for e in entries):
                raise AssertionError("Type1 totals inconsistent with reasons")
    return {
        "protocol":"E09_02I_I3C4A_TURNOVER_PRE_REGISTRO-v1",
        "status":"posthoc read-only observation, same 900..919 cohort",
        "original_workflow_id":44960526007,
        "original_artifact_id":14729775966,
        "seeds":list(seeds),
        "n_seeds":len(seeds),
        "original_hashes_verified":True,
        "all_original_outputs_identical":True,
        "totals":totals,
        "per_seed":rows,
        "gate":"G-I3c4a-REPLAY and ACCOUNTING only, no new learning claim",
        "G05_G09":"OPEN",
        "limitations":"Original outcomes observed before this audit, so findings are exploratory; migration is lab N, initial LTW0/strength2 and synthetic chemical rate40/dose80.",
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    text=json.dumps(run_all(),indent=2,sort_keys=True)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(text,encoding="utf-8")
    print(text,end="")


if __name__=="__main__":
    main()
