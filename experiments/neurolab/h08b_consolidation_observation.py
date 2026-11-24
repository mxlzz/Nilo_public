"""H08b.19: first prespecified natural LTW consolidation opportunity."""
import os,sys,pathlib,subprocess,time,re,shutil
from dataclasses import replace
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
    commands=[".echo NL_DENDRITE_BEGIN","r @$t0=0","r @$t1=0","r @$t2=0","r @$t3=0","r @$t9=0","r @$t10=0"]
    rb="r @$t1=@ecx+0x4b8; r @$t2=poi(@esi+0x2c20); gc"
    pre_check=("r @$t4=poi(@$t1+0x9c)+0x10; r @$t5=poi(@$t4+4); r @$t6=poi(@$t4+8); "
       +printf("NL_CONTEXT","%u %u %u %u %u %u %u %08x %u",
          ["@$t2","by(@$t4+2)","by(@$t4+3)"]+[f"by(@$t1+0x{k:x})" for k in range(0xc3,0xc7)]+
          ["poi(@$t1+0x190+0x9c)","poi(@$t1+0x190+0xa4)"])+"; "
       +slots("PRE",0,5)+"; "+slots("PRE",1,6)+"; r @$t3=1; gc")
    target_type=1
    miss=".if (@$t9>=0n60) { .echo NL_NO_OPPORTUNITY; qd } .else { gc }"
    scan=("r @$t10=0; r @$t11=poi(@$t4+8); "
        +".for (r @$t7=0; @$t7<0x80; r @$t7=@$t7+1) { "
        +"r @$t8=@$t11+@$t7*0xc; "
        +".if (by(@$t8+9)>0) { .if (by(@$t8+7)>by(@$t8+8)) { r @$t10=1; .break } } }; "
        +".if (@$t10==1) { "+printf("NL_SELECTED","%u %u",["@$t9","@$t7"])+"; "+pre_check+
        " } .else { "+miss+" }")
    pre_check=("r @$t9=@$t9+1; "+printf("NL_SCAN","%u",["@$t9"])+"; "
        +".if (@$t2>0) { .if ((@$t2%0x80)==0) { .if ((@$t2%3)!=0) { .if ((@$t2%5)!=0) { "
        +scan+" } .else { "+miss+" } } .else { "+miss+" } } .else { "+miss+" } } .else { "+miss+" }")
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
            proc=subprocess.run([str(cdb),"-G","-p",str(pid),"-cf",str(cmd)],cwd=game,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,timeout=40)
        ret=proc.returncode
    except subprocess.TimeoutExpired:pass
    raw=log.read_bytes().decode("utf-8","replace")
    ctx=re.findall(r"NL_CONTEXT\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([0-9a-fA-F]{8})\s+(\d+)(?=\s|$)",raw)
    rows=re.findall(r"NL_SLOT\s+(PRE|POST)\s+([01])\s+(\d+)\s+([0-9a-fA-F]{8})\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)(?=\s|$)",raw)
    categories=[k for k,p in [("syntax",r"Syntax error|Extra character|Illegal"),("access",r"Unable to read|Memory access error|Memory access violation"),("breakpoint",r"Unable to insert breakpoint|Unable to resolve"),("operand",r"Operand error"),("layout",r"NL_LAYOUT_BAD\s*(?:\r?\n|$)")] if re.search(p,raw,re.I)]
    selected=re.findall(r"NL_SELECTED\s+(\d+)\s+(\d+)(?=\s|$)",raw)
    scans=re.findall(r"NL_SCAN\s+(\d+)(?=\s|$)",raw)
    base.emit(gate="slot_trace_transport",arm=arm,contexts=len(ctx),parsed_rows=len(rows),returncode=ret,categories=categories,scanned=max(map(int,scans),default=0),selected=[[int(a),int(b)] for a,b in selected],no_opportunity="NL_NO_OPPORTUNITY" in raw and len(ctx)==0)
    if len(ctx)!=1 or len(selected)!=1:return
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
            cf_gene=replace(gene,rates=replace(gene.rates,ltw_rate=0))
            cf=update_c1_synapse(old,cf_gene,C1SynapticInput(source_output=a[1],owner_output=output,owner_state=state,chemicals=(c0,c1,c2,c3)),tick=tick).after
            cf_prediction=[cf.dendrite.susceptibility,cf.dendrite.stw,cf.dendrite.ltw,cf.strength]
            prediction=[pred.dendrite.susceptibility,pred.dendrite.stw,pred.dendrite.ltw,pred.strength]
            accepted.append({"type":typ,"slot":i,"source_index":(a[0]-srcbase)//16,"source_output":a[1],
                             "before":list(a[2:]),"after":list(b[2:]),"predicted":prediction,
                             "match":prediction==list(b[2:]),"counterfactual":cf_prediction,"eligible":a[2]>0 and a[5]>0,
                             "changed":a[2:]!=b[2:]})
    base.emit(gate="slot_comparison",arm=arm,selected_slot=int(selected[0][1]),selected_type=target_type,tick=tick,owner_output=output,owner_state=state,chem=[c0,c1,c2,c3],
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
    trace(pid,root,game,"LTW")
if __name__=="__main__":
    launch.observe_one_norn=observe
    launch.main()
