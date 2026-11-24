"""Recompute H08b.12 paired snapshots without proprietary input.
Usage: python experiments/neurolab/h08b_phase_check.py <evidence.json>
Only complete ordered cycles are accepted. Formula fixed in H3/H4.
"""
import argparse, collections, json, pathlib

def check(data):
    trace=data["trace"]["events"]
    phases=data["phase_samples"]["states"]
    er=collections.defaultdict(list); sr=collections.defaultdict(list)
    for row in trace:
        if row["event"]!="W": er[row["tick"]].append(row)
    for row in phases: sr[row["tick"]].append(row)
    matches=[]
    for tick,events in er.items():
        if [e["event"] for e in events]!=["ALT","AC","AP","AB","AQ"]:continue
        rows=sr[tick]
        if [e["phase"] for e in rows]!=["AC","AP","AB","AQ"]:continue
        a,p,b,q=rows
        if not all(e["chemistry"]==a["chemistry"] and e["brain"]==a["brain"] for e in rows):continue
        if any(len(e["values"])!=11 or any(type(x)!=int or not 0<=x<=255 for x in e["values"]) for e in rows):continue
        alt,ac,ap,ab,aq=events
        if not (alt["component"]==a["brain"]==ac["component"]==ap["component"]==ab["object"]==aq["object"]):continue
        if not (a["chemistry"]==ac["object"]==ap["object"]==ab["component"]==aq["component"]):continue
        pre,post,entry,exit=[e["values"] for e in rows]
        pred=lambda x:(x*255)>>8
        matches.append({"tick":tick,"reward":post[5]==pred(pre[0]),
                        "punishment":post[6]==pred(pre[1]),
                        "reinforcement":post[9]==pred(pre[2]),
                        "punishment_nonzero":pre[1]>0,
                        "post_equals_entry":post==entry,
                        "entry_equals_exit":entry==exit})
    return {"complete":len(matches),"ticks":[m["tick"] for m in matches],
            **{k:sum(m[k] for m in matches) for k in ["reward","punishment","reinforcement","punishment_nonzero","post_equals_entry","entry_equals_exit"]}}

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("evidence",type=pathlib.Path)
    args=parser.parse_args()
    print(json.dumps(check(json.loads(args.evidence.read_text())),indent=2))
