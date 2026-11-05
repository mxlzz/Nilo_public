"""Perfiles seguros y reversibles del laboratorio Nilo 0.7.

Único archivo de configuración aplicado: lab_profiles/active.json. Jamás se
editarán archivos Python, config.env, claves API ni partidas existentes.
Aplicar exige reiniciar Nilo para que la nueva configuración entre en vigor.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import threading
from uuid import uuid4

VERSION=1
LIMITS={
    "MAX_LLM_CALLS_PER_DAY":(1,500),
    "MAX_CHAT_CALLS_PER_DAY":(1,100),
    "MIN_REAL_SECONDS_BETWEEN_CALLS":(10,300),
}
DEFAULT_LIMITS={
    "MAX_LLM_CALLS_PER_DAY":100,
    "MAX_CHAT_CALLS_PER_DAY":40,
    "MIN_REAL_SECONDS_BETWEEN_CALLS":15,
}
# Nunca permitir omitir posición, necesidades, reglas, proyecto activo,
# mediciones físicas ni la procedencia esencial de las conclusiones.
OPTIONAL_CONTEXT=(
    "propuestas_pendientes",
    "fenomenos_pendientes_de_modelo",
    "estrategias_que_ya_no_funcionaron",
    "comparaciones_validas",
    "predicciones_contrastadas",
    "inconsistencias_recoleccion_previas",
    "preferencias_en_espera",
    "antecedentes_relacionados",
    "investigaciones_pausadas_relacionadas",
)
PROFILE_KEYS=frozenset(("version","name","limits","omit_context","prompt_note"))
_SLUG=re.compile(r"^[a-z0-9][a-z0-9_-]{0,39}$")
_ID=re.compile(r"^[a-f0-9]{32}$")
_LOCK=threading.RLock()


def baseline():
    return {"version":VERSION,"name":"baseline",
            "limits":dict(DEFAULT_LIMITS),"omit_context":[],"prompt_note":""}


def validate(profile):
    if not isinstance(profile,dict) or set(profile)!=PROFILE_KEYS:
        raise ValueError("El perfil necesita version, name, limits, omit_context y prompt_note.")
    if type(profile["version"]) is not int or profile["version"]!=VERSION:
        raise ValueError("Versión del perfil no admitida")
    name=profile["name"]
    if not isinstance(name,str) or not _SLUG.fullmatch(name):
        raise ValueError("Nombre inválido: usá a-z, números, guiones o guiones bajos.")
    limits=profile["limits"]
    if not isinstance(limits,dict) or set(limits)!=set(LIMITS):
        raise ValueError("El perfil necesita los tres límites configurables.")
    for key,(lo,hi) in LIMITS.items():
        value=limits[key]
        if type(value) is not int or not lo<=value<=hi:
            raise ValueError(f"{key} debe ser entero entre {lo} y {hi}.")
    omitted=profile["omit_context"]
    if (not isinstance(omitted,list) or len(omitted)>len(OPTIONAL_CONTEXT)
            or any(not isinstance(item,str) or item not in OPTIONAL_CONTEXT
                   for item in omitted) or len(set(omitted))!=len(omitted)):
        raise ValueError("Solo se pueden omitir campos opcionales reconocidos.")
    note=profile["prompt_note"]
    if (not isinstance(note,str) or len(note)>700 or
            "\x00" in note or "\r" in note):
        raise ValueError("La nota de sistema debe tener hasta 700 caracteres.")
    return {"version":VERSION,"name":name,"limits":dict(limits),
            "omit_context":sorted(omitted),"prompt_note":note}


def _bytes(obj):
    return (json.dumps(obj,ensure_ascii=False,sort_keys=True,allow_nan=False,
                       separators=(",",":"))+"\n").encode("utf-8")


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _read(path):
    path=Path(path)
    if not path.is_file():return None
    if path.stat().st_size>18000:
        raise ValueError("Perfil superior al tamaño permitido")
    obj=json.loads(path.read_text("utf-8"),parse_constant=lambda _:(
        _ for _ in ()).throw(ValueError("Número no finito")))
    return validate(obj)


def active_profile(root):
    """Sin efecto lateral; si el archivo está corrupto, fallar explícitamente."""
    file=Path(root)/"lab_profiles"/"active.json"
    return _read(file)


def _atomic(path,data):
    """Escribir archivo nuevo y reemplazar únicamente la ruta autorizada."""
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


def config_overlay(root):
    """Solo valores explícitamente autorizados; no tocar config.env ni API keys."""
    p=active_profile(root)
    if p is None:return {}
    return {**{k:str(v) for k,v in p["limits"].items()},
            "_LAB_OMIT_CONTEXT":tuple(p["omit_context"]),
            "_LAB_PROMPT_NOTE":p["prompt_note"]}
