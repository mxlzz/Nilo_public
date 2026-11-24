"""H-08b.4: bounded launch and read-only DDE compatibility probe on disposable Windows.
Only authenticated original input; no registry edits, game patches, or retained game files.
"""
import ctypes as c
from ctypes import wintypes as w
import hashlib, json, os, pathlib, re, shutil, subprocess, sys, tempfile, time, urllib.request, zipfile

EXPECTED = "df490a704ae5b6f44016b2ac35e899fe30b7550c7666990edb60c0ebddf025dd"
EXE = "548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7"
GEN = "e2bb4ccf6a4081a128c6c9ffc6eb233452d416717ceef47e78820ca3a152ddd4"
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def emit(**fields): print(json.dumps(fields,ensure_ascii=True),flush=True)

def prepare(root):
    fid=os.environ.pop("NEUROLAB_DATA_FILE_ID","")
    if not re.fullmatch(r"[A-Za-z0-9_-]{10,200}",fid): raise RuntimeError("secret absent")
    archive=root/"data.zip"
    try:
        with urllib.request.urlopen("https://drive.usercontent.google.com/download?id="+fid+"&export=download&confirm=t",timeout=45) as inp,archive.open("wb") as out:
            size=0
            while block:=inp.read(65536):
                size+=len(block)
                if size>14624092: raise ValueError()
                out.write(block)
    except Exception:
        raise RuntimeError("input transfer failed (details suppressed)") from None
    if archive.stat().st_size!=14624092 or digest(archive)!=EXPECTED: raise RuntimeError("archive hash mismatch")
    with zipfile.ZipFile(archive) as z:
        files=[i for i in z.infolist() if not i.is_dir()]
        if len(files)!=1163 or sum(i.file_size for i in files)!=37691719 or z.testzip() is not None:
            raise RuntimeError("archive integrity mismatch")
        for member in files:
            p=pathlib.PurePosixPath(member.filename)
            if p.is_absolute() or ".." in p.parts or "\\" in member.filename or ":" in member.filename:
                raise RuntimeError("unsafe archive entry")
            dst=root.joinpath(*p.parts)
            dst.parent.mkdir(parents=True,exist_ok=True)
            with z.open(member) as src,dst.open("wb") as out: shutil.copyfileobj(src,out)
    game=root/"Creatures"
    if digest(game/"Creatures.exe")!=EXE or digest(game/"Genetics"/"dad1.gen")!=GEN:
        raise RuntimeError("original member mismatch")
    for name in ["mfc42.dll","msvcirt.dll"]:
        found=[p for p in root.rglob("*") if p.is_file() and p.name.lower()==name]
        if len(found)!=1: raise RuntimeError("missing or ambiguous original local dependency: "+name)
        if found[0].parent!=game: shutil.copyfile(found[0],game/found[0].name)
    archive.unlink()
    emit(gate="verified_original",local_dlls=["mfc42.dll","msvcirt.dll"])
    return game

u=c.WinDLL("user32",use_last_error=True)
def fn(name,result,args):
    f=getattr(u,name); f.restype=result; f.argtypes=args; return f
H=c.c_void_p; U=c.c_uint; D=c.c_ulong; P=c.c_size_t
CB=c.WINFUNCTYPE(w.BOOL,H,w.LPARAM)
enum=fn("EnumWindows",w.BOOL,[CB,w.LPARAM])
children=fn("EnumChildWindows",w.BOOL,[H,CB,w.LPARAM])
pid_for=fn("GetWindowThreadProcessId",D,[H,c.POINTER(D)])
getclass=fn("GetClassNameW",c.c_int,[H,w.LPWSTR,c.c_int])
gettitle=fn("GetWindowTextW",c.c_int,[H,w.LPWSTR,c.c_int])
visible=fn("IsWindowVisible",w.BOOL,[H])
send=fn("SendMessageTimeoutW",H,[H,U,P,c.c_ssize_t,U,U,c.POINTER(P)])
def window_snapshot(pid,root):
    windows=[]
    def clean(s): return s.replace(str(root),"<sandbox>")[:240]
    @CB
    def top(hwnd,lparam):
        n=D();pid_for(hwnd,c.byref(n))
        if n.value!=pid or not visible(hwnd): return True
        b=c.create_unicode_buffer(256);gettitle(hwnd,b,256);title=clean(b.value)
        getclass(hwnd,b,256);cls=b.value
        texts=[]
        @CB
        def child(h,l):
            if len(texts)>=8: return False
            getclass(h,b,256)
            if b.value in ("Static","Button"):
                val=c.create_unicode_buffer(256);res=P()
                if send(h,0x000D,256,c.addressof(val),2,150,c.byref(res)) and val.value:
                    texts.append(clean(val.value))
            return True
        if cls=="#32770": children(hwnd,child,0)
        windows.append({"class":cls,"title":title,"dialog_text":texts})
        return len(windows)<8
    enum(top,0)
    return windows

DDECB=c.WINFUNCTYPE(H,U,U,H,H,H,H,P,P)
init=fn("DdeInitializeA",U,[c.POINTER(D),DDECB,D,D])
mk=fn("DdeCreateStringHandleA",H,[D,c.c_char_p,c.c_int])
free=fn("DdeFreeStringHandle",w.BOOL,[D,H])
connect=fn("DdeConnect",H,[D,H,H,H])
disconnect=fn("DdeDisconnect",w.BOOL,[H])
last=fn("DdeGetLastError",U,[D])
transaction=fn("DdeClientTransaction",H,[H,D,H,H,U,U,D,c.POINTER(D)])
getdata=fn("DdeGetData",D,[H,H,D,D])
freedata=fn("DdeFreeDataHandle",w.BOOL,[H])
uninit=fn("DdeUninitialize",w.BOOL,[D])
def dde_probe():
    @DDECB
    def cb(*args): return None
    ident=D(); code=init(c.byref(ident),cb,0x10,0)
    if code: return {"initialized":False,"error":code}
    handles=[]; conv=None
    def hs(s):
        h=mk(ident,s.encode("ascii"),1004)
        if not h: raise RuntimeError("DDE string handle")
        handles.append(h);return h
    try:
        service=hs("Vivarium")
        for topic in ("Anything","System"):
            conv=connect(ident,service,hs(topic),None)
            if conv: break
        if not conv: return {"connected":False,"error":last(ident)}
        # Read-only constant query, never a script changing the world.
        item=hs("Macro")
        command=c.create_string_buffer(b"dde: putv 123,")
        result=D()
        ok=transaction(c.cast(command,H),len(command),conv,item,1,0x4090,1500,c.byref(result))
        if not ok: return {"connected":True,"topic":topic,"poke":False,"error":last(ident)}
        h=transaction(None,0,conv,item,1,0x20B0,1500,c.byref(result))
        if not h: return {"connected":True,"topic":topic,"request":False,"error":last(ident)}
        try:
            n=getdata(h,None,0,0)
            if not 0<n<=128: return {"connected":True,"response_length":int(n)}
            b=c.create_string_buffer(n);getdata(h,c.cast(b,H),n,0)
            text=b.raw.rstrip(b"\0").decode("ascii","replace").strip()
            # Report expected numeric response only, no unbounded data dump.
            return {"connected":True,"topic":topic,"constant_query_ok":text=="123","response_length":int(n)}
        finally: freedata(h)
    finally:
        if conv: disconnect(conv)
        for h in handles: free(ident,h)
        uninit(ident)

def install_wing(root):
    # The original WinG DLL explicitly rejected app-local loading in run 45389185789.
    # Only add the original DLL if absent; never replace an existing Windows file.
    matches=[p for p in root.rglob("*") if p.is_file() and p.name.lower()=="wing32.dll"]
    if len(matches)!=1: raise RuntimeError("missing original WinG")
    src=matches[0]
    dst=pathlib.Path(os.environ["WINDIR"])/"SysWOW64"/"WING32.dll"
    if dst.exists():
        if digest(dst)!=digest(src): raise RuntimeError("different system WinG already present; refusing replacement")
        emit(gate="existing_identical_system_wing")
        return None
    with src.open("rb") as inp,dst.open("xb") as out:
        shutil.copyfileobj(inp,out)
    if digest(dst)!=digest(src): raise RuntimeError("system WinG copy mismatch")
    emit(gate="original_wing_added_to_ephemeral_x86_system_directory")
    return dst

def main():
    with tempfile.TemporaryDirectory(prefix="neurolab-launch-") as d:
        root=pathlib.Path(d);game=prepare(root)
        allowed={"SYSTEMROOT","WINDIR","SYSTEMDRIVE","PATH","TEMP","TMP","USERPROFILE","APPDATA","LOCALAPPDATA","COMPUTERNAME","USERNAME","HOMEDRIVE","HOMEPATH","PROGRAMFILES","PROGRAMFILES(X86)","PROGRAMDATA","PUBLIC","COMSPEC"}
        env={k:v for k,v in os.environ.items() if k.upper() in allowed}
        p=None
        wing=None
        try:
            wing=install_wing(root)
            try: p=subprocess.Popen([str(game/"Creatures.exe")],cwd=game,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            except OSError as e:
                emit(gate="launch_failed",winerror=getattr(e,"winerror",None));return
            emit(gate="process_created")
            deadline=time.monotonic()+35; previous=None
            while time.monotonic()<deadline:
                if p.poll() is not None:
                    emit(gate="process_exited",exit_code=p.returncode);return
                snapshot=window_snapshot(p.pid,root)
                if snapshot!=previous:
                    emit(gate="windows",windows=snapshot);previous=snapshot
                result=dde_probe()
                if result.get("connected"):
                    emit(gate="dde",**result)
                    return
                if any(x["class"]=="#32770" for x in snapshot):
                    emit(gate="modal_dialog",dde=result);return
                time.sleep(2)
            emit(gate="timeout",dde=result,windows=previous)
        finally:
            try:
                if p is not None and p.poll() is None:
                    p.terminate();p.wait(timeout=10)
            finally:
                if wing is not None:
                    wing.unlink()
                    emit(gate="temporary_system_wing_removed")
    emit(gate="cleanup_completed")
if __name__=="__main__":
    main()
