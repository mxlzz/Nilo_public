"""Esquema validado de perfiles Nilo: lectura sin efectos y límites cognitivos.

Las capas agent y labs comparten este contrato sin dependencia invertida.
"""
from __future__ import annotations
import json
from pathlib import Path
import re

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



def config_overlay(root):
    p=active_profile(root)
    if p is None:return {}
    return {**{k:str(v) for k,v in p["limits"].items()},
            "_LAB_OMIT_CONTEXT":tuple(p["omit_context"]),
            "_LAB_PROMPT_NOTE":p["prompt_note"]}
