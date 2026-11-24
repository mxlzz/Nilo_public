"""H08b.14: one independent disposable Norn per prespecified arm.
Native CAOS delivery feasibility, not learning or intratick experiment.
"""
import os, time, shutil
import h08b_mounted_launch as launch
base=launch.base
ARMS={"sham":(49,0),"reward":(49,32),"punishment":(50,32)}
EXPECTED_ID="31306c6e"
def observe(game,pid,root):
    arm=os.environ.pop("NL_PULSE_ARM","")
    if arm not in ARMS:raise RuntimeError("unregistered arm")
    chem,amount=ARMS[arm]
    def q(cmd,expected=None,kind="number"):
        t0=time.perf_counter_ns()
        r=launch.query_macro(cmd,expected,kind)
        t1=time.perf_counter_ns()
        return {**r,"t0_ns":t0,"t1_ns":t1}
    def norn(cmd,expected=None,kind="number"):
        return q("enum 4 1 0,"+cmd+",next",expected,kind)
    def valid_identity():
        return q("dde: putv totl 4 1 0",1)["ok"] and norn("dde: getb monk",EXPECTED_ID,"moniker")["ok"]
    def sample(label,origin):
        if not valid_identity():return False
        t0=time.perf_counter_ns()
        fields={f"chem{i}":norn(f"dde: putv chem {i}") for i in (49,50,51,54,55)}
        fields["decision_cell0"]=norn("dde: cell 6 0 0",kind="cell")
        t1=time.perf_counter_ns()
        ok=valid_identity() and all(v["ok"] for v in fields.values())
        ok=ok and all(0<=fields[f"chem{i}"]["value"]<=255 for i in (49,50,51,54,55))
        base.emit(gate="pulse_sample",arm=arm,label=label,ok=ok,relative_start_us=(t0-origin)//1000,relative_end_us=(t1-origin)//1000,fields=fields)
        return ok
    base.emit(gate="pulse_protocol",arm=arm,chemical=chem,amount=amount,scope="delivery feasibility only; no learning claim")
    if not q("dde: putv totl 4 1 0",0)["ok"]:
        base.emit(gate="pulse_blocked",reason="world not empty");return
    dest=game/"Genetics"/"NL01.gen"
    if dest.exists():raise RuntimeError("moniker collision")
    shutil.copyfile(game/"Genetics"/"dad1.gen",dest)
    if base.digest(dest)!=base.GEN:raise RuntimeError("genome mismatch")
    birth=q("new: crea tokn nl01 1,mvto 2408 870,dde: putv totl 4 1 0",1)
    base.emit(gate="pulse_birth",arm=arm,**birth)
    if not birth["ok"]:return
    t_birth=time.perf_counter()
    while time.perf_counter()-t_birth<85:
        time.sleep(min(5,max(0,85-(time.perf_counter()-t_birth))))
        if not q("dde: putv 123",123)["ok"]:
            base.emit(gate="pulse_blocked",reason="DDE unavailable");return
    if not valid_identity():
        base.emit(gate="pulse_blocked",reason="identity not established");return
    origin=time.perf_counter_ns()
    if not sample("pre0",origin):return
    time.sleep(.5)
    if not sample("pre1",origin):return
    # Independent consecutive queries: no claim that the two reads are atomic.
    before=norn(f"dde: putv chem {chem}")
    if not before["ok"] or not 0<=before["value"]<=223:
        base.emit(gate="pulse_blocked",reason="invalid or saturated baseline",baseline=before);return
    # Execute exactly once. Read post in same native macro, never retry on ambiguity.
    after=norn(f"chem {chem} {amount},dde: putv chem {chem}")
    base.emit(gate="pulse_delivery",arm=arm,chemical=chem,amount=amount,baseline=before,post=after,
              identity_verified=valid_identity())
    if not after["ok"] or not 0<=after["value"]<=255:return
    delta=after["value"]-before["value"]
    accepted=abs(delta)<=4 if arm=="sham" else 16<=delta<=32
    base.emit(gate="delivery_check",arm=arm,delta=delta,accepted=accepted)
    origin=after["t1_ns"]
    for i,offset in enumerate((.05,.5,2.0)):
        remaining=offset-(time.perf_counter_ns()-origin)/1e9
        if remaining>0:time.sleep(remaining)
        if not sample(f"post{i}",origin):return
    base.emit(gate="pulse_finished",arm=arm,delivery_accepted=accepted,scope="technical pilot only")
if __name__=="__main__":
    launch.observe_one_norn=observe
    launch.main()
