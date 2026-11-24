"""H-08b.7: original Build 47, verified mounted original CD, no patches.
Reuse validated original input and window/DDE observer. No installer is executed.
"""
import os, pathlib, subprocess, tempfile, time, winreg
import h08b_original_launch as base

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
                p=subprocess.Popen([str(game/"Creatures.exe")],cwd=game,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            except OSError as e:
                base.emit(gate="launch_failed",winerror=getattr(e,"winerror",None));return
            base.emit(gate="process_created",mode="default_with_mounted_original_CD")
            deadline=time.monotonic()+50; previous=None;result={}
            while time.monotonic()<deadline:
                if p.poll() is not None:
                    base.emit(gate="process_exited",exit_code=p.returncode);return
                snapshot=base.window_snapshot(p.pid,root)
                if snapshot!=previous:
                    base.emit(gate="windows",windows=snapshot);previous=snapshot
                if any(x["class"]=="#32770" for x in snapshot):
                    base.emit(gate="modal_dialog",windows=snapshot);return
                result=base.dde_probe()
                if result.get("connected"):
                    base.emit(gate="dde",**result)
                    if result.get("constant_query_ok"): return
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
