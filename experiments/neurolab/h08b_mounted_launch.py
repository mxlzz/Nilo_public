"""H-08b.7: original Build 47, verified mounted original CD, no patches.
Reuse validated original input and window/DDE observer. No installer is executed.
"""
import os, pathlib, subprocess, tempfile, time, winreg, ctypes as c, re, shutil
import h08b_original_launch as base

def dismiss_tip(pid):
    clicked=False
    @base.CB
    def top(hwnd,lparam):
        nonlocal clicked
        n=base.D();base.pid_for(hwnd,c.byref(n))
        if n.value!=pid or not base.visible(hwnd):return True
        b=c.create_unicode_buffer(256)
        base.getclass(hwnd,b,256)
        if b.value!="#32770":return True
        base.gettitle(hwnd,b,256)
        if b.value!="Tip of the Day":return True
        buttons=[]
        @base.CB
        def child(h,l):
            base.getclass(h,b,256)
            if b.value=="Button":
                t=c.create_unicode_buffer(256);res=base.P()
                if base.send(h,0x000D,256,c.addressof(t),2,150,c.byref(res)) and t.value=="&Close":buttons.append(h)
            return True
        base.children(hwnd,child,0)
        if len(buttons)==1:
            clicked=bool(base.post(buttons[0],0x00F5,0,0))
            return False
        return True
    base.enum(top,0)
    return clicked

def query_macro(command,expected=None,kind='number'):
    @base.DDECB
    def cb(*args):return None
    ident=base.D();code=base.init(c.byref(ident),cb,0x10,0)
    if code:return {"ok":False,"stage":"init","error":int(code)}
    handles=[];conv=None
    def hs(s):
        h=base.mk(ident,s.encode("ascii"),1004)
        if not h:raise RuntimeError("DDE handle")
        handles.append(h);return h
    try:
        conv=base.connect(ident,hs("Vivarium"),hs("Anything"),None)
        if not conv:return {"ok":False,"stage":"connect","error":base.last(ident)}
        item=hs("Macro")
        b=c.create_string_buffer(command.encode("ascii"))
        res=base.D()
        if not base.transaction(c.cast(b,base.H),len(b),conv,item,1,0x4090,1500,c.byref(res)):
            return {"ok":False,"stage":"poke","error":base.last(ident)}
        h=base.transaction(None,0,conv,item,1,0x20B0,1500,c.byref(res))
        if not h:return {"ok":False,"stage":"request","error":base.last(ident)}
        try:
            n=base.getdata(h,None,0,0)
            if not 0<n<=128:return {"ok":False,"stage":"length","bytes":int(n)}
            buf=c.create_string_buffer(n);base.getdata(h,c.cast(buf,base.H),n,0)
            val=buf.raw.rstrip(b"\0").decode("ascii","replace").strip()
            # Strict parsers for known numeric/identity/cell response formats.
            if kind=="moniker":
                if not re.fullmatch(r"[0-9a-fA-F]{8}\|?",val):
                    return {"ok":False,"stage":"moniker_format","bytes":int(n)}
                value=val.rstrip("|").lower()
            elif kind=="cell":
                if not re.fullmatch(r"[0-9]+(?:[|, ]+[0-9]+){6}[|, ]*",val):
                    return {"ok":False,"stage":"cell_format","bytes":int(n)}
                value=[int(x) for x in re.findall(r"[0-9]+",val)]
            else:
                if not re.fullmatch(r"[0-9]{1,10}\|?",val):
                    return {"ok":False,"stage":"format","bytes":int(n)}
                value=int(val.rstrip("|"))
            return {"ok":expected is None or value==expected,"value":value,"bytes":int(n)}
        finally:base.freedata(h)
    finally:
        if conv:base.disconnect(conv)
        for h in handles:base.free(ident,h)
        base.uninit(ident)

def observe_one_norn(game,pid,root):
    n=query_macro("dde: putv totl 4 1 0",0)
    if not n.get("ok"):
        base.emit(gate="controlled_birth_blocked",count=n);return
    # A disposable copy of the verified genome; no genetic mutation.
    dest=game/"Genetics"/"NL01.gen"
    if dest.exists():raise RuntimeError("test moniker collision")
    shutil.copyfile(game/"Genetics"/"dad1.gen",dest)
    if base.digest(dest)!=base.GEN:raise RuntimeError("copied genome hash mismatch")
    base.emit(gate="controlled_genome",sha256=base.GEN)
    # C1 documented NEW: CREA TOKN <four chars> sex, with move to the
    # original Hatchery's first egg placement (x=2408,y=870).
    # Exactly one request; never retry a mutating macro.
    birth=query_macro("new: crea tokn nl01 1,mvto 2408 870,dde: putv totl 4 1 0",1)
    base.emit(gate="controlled_birth",**birth)
    if not birth.get("ok"):return
    time.sleep(2)
    # Always address the same unique Norn by enumeration; verify identity each round.
    prefix="enum 4 1 0,"
    suffix=",next"
    def query(cmd,kind="number",expected=None):
        t0=time.perf_counter_ns()
        r=query_macro(prefix+cmd+suffix,expected,kind)
        r["latency_us"]=(time.perf_counter_ns()-t0)//1000
        return r
    identity=query("dde: getb monk","moniker")
    base.emit(gate="norn_identity",**identity)
    if not identity.get("ok"):return
    for round_ in range(3):
        if query_macro("dde: putv totl 4 1 0",1).get("ok") is not True:break
        if query("dde: getb monk","moniker",identity["value"]).get("ok") is not True:break
        fields={}
        for chemical in (49,50,51,54,55):
            fields["chem"+str(chemical)]=query("dde: putv chem "+str(chemical))
        fields["decision_cell0"]=query("dde: cell 6 0 0","cell")
        if query("dde: getb monk","moniker",identity["value"]).get("ok") is not True:break
        base.emit(gate="read_only_norn_sample",round=round_,fields=fields)
        time.sleep(0.25)
    base.emit(gate="observation_finished",scope="feasibility only; no reinforcement stimulus or intratick inference")
    # End the independent DDE sampling before attaching; debugger perturbs timing.
    trace_cycles(pid,root,game)

def trace_cycles(pid,root,game):
    cdb=pathlib.Path(os.environ.get("ProgramFiles(x86)","C:/Program Files (x86)"))/"Windows Kits"/"10"/"Debuggers"/"x86"/"cdb.exe"
    if not cdb.is_file():
        base.emit(gate="trace_blocked",reason="x86 SDK debugger unavailable");return
    commands=[".echo NL_TRACE_BEGIN","r @$t0=0"]
    # Each observation point was verified against the original PE.
    # The callsite has not executed yet; ESI is the Norn pointer for regular
    # and outer alternate paths. ECX is the chemical or brain object for
    # the inner alternate paths. No modification of state except breakpoints.
    points=[
        ("W",0x247b0,["0","0","0"]),
        ("RB",0x7583,["@esi","poi(@esi+0x2c20)","@ecx"]),
        ("RC",0x7595,["@esi","poi(@esi+0x2c20)","@ecx"]),
        ("RP",0x759a,["@esi","poi(@esi+0x2c20)","poi(@esi+0x2c1c)"]),
        ("ALT",0x764b,["@esi","poi(@esi+0x2c20)","poi(@esi+0x2c18)"]),
        ("AC",0x5d32,["@ecx","poi(@esp)","0"]),
        ("AB",0x5daf,["@ecx","poi(@esp)","0"]),
    ]
    for name,off,args in points:
        # Bounded observation, detach at a fixed number of logged hits.
        command=f'.printf \"NL_EVT {name} %08x %u %08x\\n\", '+", ".join(args)+'; r @$t0=@$t0+1; .if (@$t0>=120) { qd } .else { gc }'
        # Escape inner quotes for the breakpoint command string.
        commands.append(f'bp Creatures+0x{off:x} "'+command.replace('"','\\"')+'"')
    commands.append("g")
    cmd=root/"cycles.txt"; cmd.write_text("\n".join(commands)+"\n",encoding="ascii")
    log=root/"cycles.log";start=time.perf_counter_ns()
    try:
        with log.open("wb") as out:
            proc=subprocess.run([str(cdb),"-G","-p",str(pid),"-cf",str(cmd)],cwd=game,stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,timeout=18)
        status="exited"
    except subprocess.TimeoutExpired:
        status="timeout"
    raw=log.read_bytes().decode("utf-8","replace")
    parsed=re.findall(r"(?m)^\s*NL_EVT (W|RB|RC|RP|ALT|AC|AB) ([0-9a-fA-F]{8}) (\d+) ([0-9a-fA-F]{8})\s*$",raw)
    aliases={}
    def alias(s):
        if int(s,16)==0:return None
        return aliases.setdefault(s.lower(),"P"+str(len(aliases)+1))
    events=[{"event":k,"object":alias(p),"tick":int(t),"component":alias(v)} for k,p,t,v in parsed[:120]]
    base.emit(gate="cycle_trace",status=status,elapsed_ms=(time.perf_counter_ns()-start)//1000000,
              started=bool(re.search(r"(?m)^\s*NL_TRACE_BEGIN\s*$",raw)),events=events,
              errors=bool(re.search(r"Syntax error|Unable to resolve|Couldn't resolve|Couldn't set breakpoint|Unable to insert breakpoint",raw,re.I)),
              scope="debugger-observed order only, not uninstrumented cadence")

def main():
    cd=os.environ.pop("NL_MOUNTED_CD","")
    if len(cd)!=3 or cd[1:]!=":\\" or not cd[0].isalpha():
        raise RuntimeError("verified mounted CD drive required")
    with tempfile.TemporaryDirectory(prefix="neurolab-mounted-launch-") as d:
        root=pathlib.Path(d); game=base.prepare(root)
        allowed={"SYSTEMROOT","WINDIR","SYSTEMDRIVE","PATH","TEMP","TMP","USERPROFILE","APPDATA","LOCALAPPDATA","COMPUTERNAME","USERNAME","HOMEDRIVE","HOMEPATH","PROGRAMFILES","PROGRAMFILES(X86)","PROGRAMDATA","PUBLIC","COMSPEC"}
        env={k:v for k,v in os.environ.items() if k.upper() in allowed}
        p=wing=config=None
        added_cd=False
        try:
            wing=base.install_wing(root)
            config=base.configure_original_paths(game)
            # Original CD remains mounted; official distribution launch option is -embedding.
            # https://steamdb.info/app/1818340/config/
            # Original 0x411AE2..0x411AFA queries HKLM32 CD Drive with
            # default "D:"; 0x411B02 concatenates a backslash. Match format.
            key=config[0]
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,key,0,winreg.KEY_QUERY_VALUE|winreg.KEY_SET_VALUE|winreg.KEY_WOW64_32KEY) as k:
                try: old,_=winreg.QueryValueEx(k,"CD Drive")
                except FileNotFoundError: pass
                else: raise RuntimeError("refusing to overwrite existing CD Drive")
                winreg.SetValueEx(k,"CD Drive",0,winreg.REG_SZ,cd[:2]);added_cd=True
            base.emit(gate="original_cd_drive_configured",registry_view="HKLM32",format="drive_letter_colon")
            try:
                p=subprocess.Popen([str(game/"Creatures.exe"),"-embedding"],cwd=game,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            except OSError as e:
                base.emit(gate="launch_failed",winerror=getattr(e,"winerror",None));return
            base.emit(gate="process_created",mode="documented_embedding_with_mounted_original_CD")
            deadline=time.monotonic()+65; previous=None;result={};tip_closed=False
            while time.monotonic()<deadline:
                if p.poll() is not None:
                    base.emit(gate="process_exited",exit_code=p.returncode);return
                snapshot=base.window_snapshot(p.pid,root)
                if snapshot!=previous:
                    base.emit(gate="windows",windows=snapshot);previous=snapshot
                if any(x["class"]=="#32770" for x in snapshot):
                    if not tip_closed and dismiss_tip(p.pid):
                        tip_closed=True;base.emit(gate="original_tip_closed");time.sleep(2);continue
                    base.emit(gate="modal_dialog",windows=snapshot);return
                result=query_macro("dde: putv 123",123)
                if result.get("stage")!="connect" or snapshot:
                    base.emit(gate="dde_constant",**result)
                if result.get("ok"):
                    for name,command in [("norns","dde: putv totl 4 1 0"),("grendels","dde: putv totl 4 2 0")]:
                        base.emit(gate="world_count",kind=name,**query_macro(command))
                    observe_one_norn(game,p.pid,root)
                    return
                time.sleep(2)
            base.emit(gate="timeout",dde=result,windows=previous)
        finally:
            try:
                if p is not None and p.poll() is None:
                    p.terminate();p.wait(timeout=10)
            finally:
                try:
                    if config is not None:
                        if added_cd:
                            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,config[0],0,winreg.KEY_SET_VALUE|winreg.KEY_WOW64_32KEY) as k:
                                winreg.DeleteValue(k,"CD Drive")
                            base.emit(gate="temporary_cd_drive_value_removed")
                        base.remove_original_paths(config)
                finally:
                    if wing is not None:
                        wing.unlink()
                        base.emit(gate="temporary_system_wing_removed")
    base.emit(gate="cleanup_completed")

if __name__=="__main__":main()
