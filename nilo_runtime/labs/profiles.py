"""Checkpoint, aplicación y restauración del perfil sin editar código Python."""
from __future__ import annotations
import os
from pathlib import Path
import tempfile
import threading
from uuid import uuid4

from nilo_runtime.core.lab_settings import (
    VERSION,LIMITS,DEFAULT_LIMITS,OPTIONAL_CONTEXT,PROFILE_KEYS,_SLUG,_ID,
    baseline,validate,_bytes,_sha,_read,active_profile,config_overlay,
)
_LOCK=threading.RLock()

def _atomic(path,data):
    """Escribir archivo nuevo y reemplazar solo la ruta autorizada."""
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=".nilo-config-",dir=path.parent)
    try:
        with os.fdopen(fd,"wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp,path)
    finally:
        Path(tmp).unlink(missing_ok=True)


class ProfileStore:
    def __init__(self,root):
        self.root=Path(root).resolve()
        self.dir=self.root/"lab_profiles"
        self.active=self.dir/"active.json"

    def current(self):
        return active_profile(self.root) or baseline()

    def save(self,profile):
        clean=validate(profile)
        path=self.dir/"saved"/(clean["name"]+".json")
        with _LOCK:
            _atomic(path,_bytes(clean))
        return {"name":clean["name"],"sha256":_sha(_bytes(clean)),
                "profile":clean}

    def load(self,name):
        if not isinstance(name,str) or not _SLUG.fullmatch(name):
            raise ValueError("Nombre de perfil inválido")
        value=_read(self.dir/"saved"/(name+".json"))
        if value is None:raise ValueError("El perfil no existe")
        return value

    def entries(self):
        saved=self.dir/"saved"
        entries=[]
        if saved.is_dir():
            for path in sorted(saved.glob("*.json"))[:100]:
                if _SLUG.fullmatch(path.stem):
                    try:
                        p=_read(path)
                        entries.append({"name":p["name"],"sha256":_sha(_bytes(p))})
                    except (OSError,ValueError,TypeError):
                        entries.append({"name":path.stem,"invalid":True})
        backups=self.dir/"backups"
        available=sorted((x.stem for x in backups.glob("*.json")
                          if _ID.fullmatch(x.stem)),reverse=True) if backups.is_dir() else []
        return {"active":self.current(),"saved":entries,"backups":available,
                "baseline":baseline(),"restart_required":True,
                "editable_optional_context":list(OPTIONAL_CONTEXT),
                "limits_range":{k:list(v) for k,v in LIMITS.items()},
                "note":"Solo cambian cuotas, una nota adicional del prompt y la selección de campos opcionales. Las leyes físicas no se editan."}

    def diff(self,profile):
        candidate=validate(profile)
        current=self.current()
        keys=("limits","omit_context","prompt_note")
        return {key:{"before":current[key],"after":candidate[key]}
                for key in keys if current[key]!=candidate[key]}

    def _checkpoint(self):
        """Crear backup antes de escribir: el contenido no incluye credenciales."""
        previous=_read(self.active)
        ident=uuid4().hex
        content={"version":VERSION,"previous":previous,
                 "profile_sha256":_sha(_bytes(previous)) if previous else None}
        path=self.dir/"backups"/(ident+".json")
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open("xb") as stream:
            stream.write(_bytes(content))
            stream.flush()
            os.fsync(stream.fileno())
        return ident

    def _audit(self,action,ident,profile):
        log={"action":action,"checkpoint":ident,
             "profile":profile["name"] if profile else None,
             "sha256":_sha(_bytes(profile)) if profile else None}
        self.dir.mkdir(parents=True,exist_ok=True)
        with (self.dir/"changes.jsonl").open("ab") as handle:
            handle.write(_bytes(log))

    def apply(self,profile):
        clean=validate(profile)
        with _LOCK:
            diff=self.diff(clean)
            previous=self.current()
            if not diff:return {"applied":False,"diff":{},"current":previous,
                                "restart_required":False}
            ident=self._checkpoint()
            _atomic(self.active,_bytes(clean))
            self._audit("apply",ident,clean)
            return {"applied":True,"checkpoint":ident,"diff":diff,
                    "current":clean,"restart_required":True}

    def restore(self,checkpoint):
        if not isinstance(checkpoint,str) or not _ID.fullmatch(checkpoint):
            raise ValueError("Checkpoint inválido")
        path=self.dir/"backups"/(checkpoint+".json")
        if not path.is_file() or path.stat().st_size>18000:
            raise ValueError("Checkpoint no disponible")
        saved=json.loads(path.read_text("utf-8"))
        if type(saved) is not dict or saved.get("version")!=VERSION:
            raise ValueError("Checkpoint ilegible")
        previous=(validate(saved["previous"]) if saved.get("previous") is not None else None)
        checksum=_sha(_bytes(previous)) if previous else None
        if checksum!=saved.get("profile_sha256"):
            raise ValueError("Checkpoint con hash incorrecto")
        with _LOCK:
            undo=self._checkpoint()
            if previous is None:self.active.unlink(missing_ok=True)
            else:_atomic(self.active,_bytes(previous))
            self._audit("restore",undo,previous)
            return {"restored":True,"checkpoint_undo":undo,
                    "current":self.current(),"restart_required":True}

