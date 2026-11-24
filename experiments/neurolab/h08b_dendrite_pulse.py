"""H08b.17: native Decision lobe transition with prespecified pulse, comparison to fixed C1 model."""
import os,sys,pathlib,subprocess,time,re,shutil
import h08b_mounted_launch as launch
base=launch.base
# Use existing model from repository, not a fitted replica.
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]))
from experiments.neurolab.c1_synapse_integrated import (
    C1SynapseState,C1SynapticInput,DECISION_EXCITATORY_GENE,
    DECISION_INHIBITORY_GENE,update_c1_synapse)
from experiments.neurolab.c1_dendrite_tick import DendriteState

def trace(pid,root,game,arm):
    cdb=pathlib.Path(os.environ.get("ProgramFiles(x86)","C:/Program Files (x86)"))/"Windows Kits"/"10"/"Debuggers"/"x86"/"cdb.exe"
    if not cdb.is_file():base.emit(gate="slot_blocked",reason="debugger unavailable");return
    # Debugger variables, no debuggee memory writes. Addresses only in private log.
    def printf(tag,fmt,args):
        return '.printf "'+tag+" "+fmt+'\\n", '+", ".join(args)
    def slots(phase,typ,ptr):
        return ('.for (r @$t7=0; @$t7<0x80; r @$t7=@$t7+1) { '
                +f'r @$t8=@$t{ptr}+@$t7*0xc; '
                +printf(f"NL_SLOT {phase} {typ}","%u %08x %u %u %u %u %u",
                   ["@$t7","poi(@$t8)","by(poi(@$t8)+2)"]+[f"by(@$t8+{k})" for k in range(6,10)])
                +" }")
    def bp(offset,command):
        return f'bp Creatures+0x{offset:x} "'+command.replace('"','\\"')+'"'
    commands=[".echo NL_DENDRITE_BEGIN","r @$t0=0","r @$t1=0","r @$t2=0","r @$t3=0"]
    rb="r @$t1=@ecx+0x4b8; r @$t2=poi(@esi+0x2c20); gc"
    pre_check=("r @$t4=poi(@$t1+0x9c)+0x10; r @$t5=poi(@$t4+4); r @$t6=poi(@$t4+8); "
       +printf("NL_CONTEXT","%u %u %u %u %u %u %u %08x %u",
          ["@$t2","by(@$t4+2)","by(@$t4+3)"]+[f"by(@$t1+0x{k:x})" for k in range(0xc3,0xc7)]+
          ["poi(@$t1+0x190+0x9c)","poi(@$t1+0x190+0xa4)"])+"; "
       +slots("PRE",0,5)+"; "+slots("PRE",1,6)+"; r @$t3=1; gc")
    # Exposure gate is based only on entry CHEM, never on post weights.
    if arm!="sham":
        receptor=0xc3 if arm=="reward" else 0xc4
        pre_check=f".if (by(@$t1+0x{receptor:x})>0) {{ "+pre_check+" } .else { gc }"
    pre=(".if (@ecx==@$t1) { .if (poi(@$t1+0xa4)==0x10) { "
       "r @$t4=poi(@$t1+0x9c)+0x10; "
       ".if (by(@$t4+0xc)==0x80) { .if (by(@$t4+0xd)==0x80) { "+pre_check+
       " } .else { .echo NL_LAYOUT_BAD; qd } } .else { .echo NL_LAYOUT_BAD; qd } "
       "} .else { .echo NL_LAYOUT_BAD; qd } } .else { gc }")
    post=(".if (@$t3==1) { .if (@ebx==@$t1) { "
       +".if (poi(@$t4+4)==@$t5) { .if (poi(@$t4+8)==@$t6) { "
       +slots("POST",0,5)+"; "+slots("POST",1,6)+"; .echo NL_DENDRITE_END; qd"
       +" } .else { .echo NL_LAYOUT_BAD; qd } } .else { .echo NL_LAYOUT_BAD; qd } "
       +"} .else { gc } } .else { gc }")
    commands.extend([bp(0x7583,rb),bp(0x3e00,pre),bp(0x48a0,post),"g"])
    cmd=root/"dendrite.txt";cmd.write_text("\n".join(commands)+"\n",encoding="ascii")
    log=root/"dendrite.log";ret=None
    try:
        with log.open("wb") as f:
            proc=subprocess.run([str(cdb),"-G","-p",str(pid),"-cf",str(cmd)],cwd=game,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,timeout=25)
        ret=proc.returncode
    except subprocess.TimeoutExpired:pass
    raw=log.read_bytes().decode("utf-8","replace")
    ctx=re.findall(r"NL_CONTEXT\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([0-9a-fA-F]{8})\s+(\d+)(?=\s|$)",raw)
    rows=re.findall(r"NL_SLOT\s+(PRE|POST)\s+([01])\s+(\d+)\s+([0-9a-fA-F]{8})\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)(?=\s|$)",raw)
    categories=[k for k,p in [("syntax",r"Syntax error|Extra character|Illegal"),("access",r"Unable to read|Memory access error|Memory access violation"),("breakpoint",r"Unable to insert breakpoint|Unable to resolve"),("operand",r"Operand error"),("layout",r"NL_LAYOUT_BAD\s*(?:\r?\n|$)")] if re.search(p,raw,re.I)]
    base.emit(gate="slot_trace_transport",arm=arm,contexts=len(ctx),parsed_rows=len(rows),returncode=ret,categories=categories)
    if len(ctx)!=1:return
    tick,output,state,c0,c1,c2,c3,srcbase,srccount=ctx[0]
    tick,output,state,c0,c1,c2,c3,srccount=map(int,[tick,output,state,c0,c1,c2,c3,srccount]);srcbase=int(srcbase,16)
    if not 0<srccount<=2048 or not all(0<=v<=255 for v in [output,state,c0,c1,c2,c3]):return
    groups={}
    for phase,typ,slot,src,inp,sus,stw,ltw,strength in rows:
        k=(int(typ),int(slot),phase)
        groups.setdefault(k,[]).append((int(src,16),*map(int,[inp,sus,stw,ltw,strength])))
    accepted=[];invalid=[]
    for typ in (0,1):
        gene=(DECISION_EXCITATORY_GENE,DECISION_INHIBITORY_GENE)[typ]
        for i in range(128):
            pre=groups.get((typ,i,"PRE"),[]);post=groups.get((typ,i,"POST"),[])
            if len(pre)!=1 or len(post)!=1:invalid.append([typ,i,"missing_or_duplicate"]);continue
            a,b=pre[0],post[0]
            if a[0]!=b[0] or not 0<=a[0]-srcbase<16*srccount or (a[0]-srcbase)%16!=0 or a[1]!=b[1] or any(not 0<=x<=255 for x in (*a[1:],*b[1:])):
                invalid.append([typ,i,"source_or_byte_mismatch"]);continue
            old=C1SynapseState(DendriteState(*a[2:5]),a[5])
            pred=update_c1_synapse(old,gene,C1SynapticInput(source_output=a[1],owner_output=output,owner_state=state,chemicals=(c0,c1,c2,c3)),tick=tick).after
            prediction=[pred.dendrite.susceptibility,pred.dendrite.stw,pred.dendrite.ltw,pred.strength]
            accepted.append({"type":typ,"slot":i,"source_index":(a[0]-srcbase)//16,"source_output":a[1],
                             "before":list(a[2:]),"after":list(b[2:]),"predicted":prediction,
                             "match":prediction==list(b[2:]),"eligible":a[2]>0 and a[5]>0,
                             "changed":a[2:]!=b[2:]})
    base.emit(gate="slot_comparison",arm=arm,tick=tick,owner_output=output,owner_state=state,chem=[c0,c1,c2,c3],
              accepted=len(accepted),matched=sum(x["match"] for x in accepted),
              nontrivial=sum(x["changed"] for x in accepted),
              eligible=sum(x["eligible"] for x in accepted),
              invalid=invalid,rows=accepted,scope="one original lobe transition, not proof of learning")
def observe(game,pid,root):
    q=launch.query_macro
    if not q("dde: putv totl 4 1 0",0)["ok"]:return
    dest=game/"Genetics"/"NL01.gen"
    if dest.exists():raise RuntimeError("moniker collision")
    shutil.copyfile(game/"Genetics"/"dad1.gen",dest)
    if base.digest(dest)!=base.GEN:raise RuntimeError("genome mismatch")
    birth=q("new: crea tokn nl01 1,mvto 2408 870,dde: putv totl 4 1 0",1)
    base.emit(gate="slot_birth",**birth)
    if not birth["ok"]:return
    end=time.perf_counter()+85
    while time.perf_counter()<end:
        time.sleep(min(5,max(0,end-time.perf_counter())))
        if not q("dde: putv 123",123)["ok"]:return
    if not q("dde: putv totl 4 1 0",1)["ok"] or not q("enum 4 1 0,dde: getb monk,next","31306c6e","moniker")["ok"]:
        base.emit(gate="slot_blocked",reason="identity");return
    arm=os.environ.pop("NL_PULSE_ARM","")
    if arm not in ("sham","reward","punishment"):raise RuntimeError("unregistered arm")
    chem,amount={"sham":(49,0),"reward":(49,32),"punishment":(50,32)}[arm]
    before=q(f"enum 4 1 0,dde: putv chem {chem},next")
    if not before.get("ok") or not 0<=before["value"]<=223:
        base.emit(gate="slot_blocked",arm=arm,reason="baseline");return
    t0=time.perf_counter_ns()
    after=q(f"enum 4 1 0,chem {chem} {amount},dde: putv chem {chem},next")
    t1=time.perf_counter_ns()
    valid=q("dde: putv totl 4 1 0",1)["ok"] and q("enum 4 1 0,dde: getb monk,next","31306c6e","moniker")["ok"]
    delta=after.get("value",-999)-before["value"]
    accepted=bool(valid and after.get("ok") and 0<=after["value"]<=255 and (abs(delta)<=4 if arm=="sham" else 16<=delta<=32))
    base.emit(gate="slot_pulse_delivery",arm=arm,chemical=chem,amount=amount,before=before,after=after,delta=delta,accepted=accepted,identity_verified=valid,t0_ns=t0,t1_ns=t1)
    if accepted:trace(pid,root,game,arm)
if __name__=="__main__":
    launch.observe_one_norn=observe
    launch.main()
