"""H-08b.7: original Build 47, verified mounted original CD, no patches.
Reuse validated original input and window/DDE observer. No installer is executed.
"""
import os, pathlib, subprocess, tempfile, time, winreg, ctypes as c, re
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

def query_read_only(command,expected=None):
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
            # A numeric response is expected. No arbitrary response bytes enter CI logs.
            if not re.fullmatch(r"[0-9]{1,10}\|?",val):
                return {"ok":False,"stage":"format","bytes":int(n)}
            value=int(val.rstrip("|"))
            return {"ok":expected is None or value==expected,"value":value,"bytes":int(n)}
        finally:base.freedata(h)
    finally:
        if conv:base.disconnect(conv)
        for h in handles:base.free(ident,h)
        base.uninit(ident)

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
                result=query_read_only("dde: putv 123",123)
                if result.get("stage")!="connect" or snapshot:
                    base.emit(gate="dde_constant",**result)
                if result.get("ok"):
                    # Read-only counts, no target selection, mutation or hatching.
                    for name,command in [("norns","dde: putv totl 4 1 0"),("grendels","dde: putv totl 4 2 0")]:
                        base.emit(gate="world_count",kind=name,**query_read_only(command))
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
