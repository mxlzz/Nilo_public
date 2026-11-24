"""H08b.15: prespecified Decision eligibility survey, no reward intervention."""
import os,time,shutil
import h08b_mounted_launch as launch
base=launch.base
def observe(game,pid,root):
    session=os.environ.pop("NL_SURVEY_SESSION","")
    if session not in ("A","B","C"):raise RuntimeError("invalid session")
    def q(cmd,expected=None,kind="number"):
        t0=time.perf_counter_ns()
        r=launch.query_macro(cmd,expected,kind)
        return {**r,"t0_ns":t0,"t1_ns":time.perf_counter_ns()}
    def norn(cmd,expected=None,kind="number"):
        return q("enum 4 1 0,"+cmd+",next",expected,kind)
    def identity():
        return q("dde: putv totl 4 1 0",1)["ok"] and norn("dde: getb monk","31306c6e","moniker")["ok"]
    if not q("dde: putv totl 4 1 0",0)["ok"]:
        base.emit(gate="survey_blocked",session=session,reason="world not empty");return
    dest=game/"Genetics"/"NL01.gen"
    if dest.exists():raise RuntimeError("moniker collision")
    shutil.copyfile(game/"Genetics"/"dad1.gen",dest)
    if base.digest(dest)!=base.GEN:raise RuntimeError("genome mismatch")
    birth=q("new: crea tokn nl01 1,mvto 2408 870,dde: putv totl 4 1 0",1)
    base.emit(gate="survey_birth",session=session,**birth)
    if not birth["ok"]:return
    origin=time.perf_counter_ns()
    for offset in (85,87,90):
        while (remaining:=offset-(time.perf_counter_ns()-origin)/1e9)>0:
            time.sleep(min(5,remaining))
            if not q("dde: putv 123",123)["ok"]:
                base.emit(gate="survey_blocked",session=session,reason="DDE unavailable");return
        if not identity():
            base.emit(gate="survey_blocked",session=session,reason="identity");return
        start=time.perf_counter_ns()
        before={str(i):norn(f"dde: putv chem {i}") for i in (49,50,51)}
        rows=[]
        for cell in range(16):
            for typ in (0,1):
                r=norn(f"dde: cell 6 {cell} {typ}",kind="cell")
                valid=False
                if r.get("ok"):
                    v=r["value"]
                    if len(v)==7:
                        output,state,count,sus,stw,ltw,strength=v
                        valid=0<=output<=255 and 0<=state<=255 and 0<=count<=255 and all(0<=x<=count*255 for x in (sus,stw,ltw,strength))
                rows.append({"cell":cell,"type":typ,**r,"valid":valid})
                if not valid:
                    base.emit(gate="survey_window",session=session,offset=offset,valid=False,rows=rows,before=before,reason="invalid cell response");return
        after={str(i):norn(f"dde: putv chem {i}") for i in (49,50,51)}
        valid=identity() and all(r["ok"] and 0<=r["value"]<=255 for r in [*before.values(),*after.values()])
        candidates=[(r["cell"],r["type"]) for r in rows if r["value"][2]>0 and r["value"][3]>0 and r["value"][6]>0]
        base.emit(gate="survey_window",session=session,offset=offset,valid=valid,rows=rows,before=before,after=after,candidates=candidates,elapsed_us=(time.perf_counter_ns()-start)//1000)
        if not valid:return
    base.emit(gate="survey_finished",session=session)
if __name__=="__main__":
    launch.observe_one_norn=observe
    launch.main()
