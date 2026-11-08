"""Centro de ajustes de Nilo: perfiles seguros y ensayos sobre motor real.

Nunca toca partidas ni archivos Python. Simulaciones en SQLite temporal.
Una previsualización del contexto NO es una llamada al proveedor LLM.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
from uuid import uuid4

from brain import config
from nilo_runtime.agent.gateway import build_deliberation_request
from nilo_runtime.application.engine import Simulation
from nilo_runtime.labs.profiles import (
    ProfileStore, validate, baseline, OPTIONAL_CONTEXT,
)
from nilo_runtime.storage.backups import backup_file, restore_as_copy
from nilo_runtime.labs.literal_segments import index_request


def _seed(value):
    if type(value) is not int or not 0<=value<=1000000000:
        raise ValueError("Semilla fuera de rango")
    return value


def _request(profile,context,provider,*,context_mode="baseline"):
    if context_mode not in ("baseline","modular"):
        raise ValueError("Modo de contexto experimental desconocido")
    if provider not in ("gemini","groq"):
        raise ValueError("Proveedor de vista previa no soportado")
    p=validate(profile)
    cfg=dict(config())
    cfg["PROVIDER"]=provider
    cfg["MODEL"]=("gemini-3.1-flash-lite" if provider=="gemini"
                  else "openai/gpt-oss-20b")
    cfg["GEMINI_API_KEY"]="vista-previa-sin-red"
    cfg["GROQ_API_KEY"]="vista-previa-sin-red"
    cfg["_LAB_OMIT_CONTEXT"]=tuple(p["omit_context"])
    cfg["_LAB_PROMPT_NOTE"]=p["prompt_note"]
    cfg["_LAB_CONTEXT_MODE"]=context_mode
    _,payload,_=build_deliberation_request(cfg,context)
    # Misma serialización que gateway._post, aunque SIN enviar HTTP.
    wire=json.dumps(payload,ensure_ascii=False)
    index=index_request(wire.encode("utf-8"),provider=provider,
                        purpose="deliberacion")
    if provider=="gemini":
        sent=json.loads(payload["contents"][0]["parts"][0]["text"].split(
            "SITUACIÓN REAL: ",1)[1])
        system=payload["systemInstruction"]["parts"][0]["text"]
    else:
        sent=json.loads(payload["messages"][1]["content"])
        system=payload["messages"][0]["content"]
    return {"provider":provider,"model":cfg["MODEL"],"profile":p["name"],
            "modo_contexto":context_mode,
            "prompt_sha256":hashlib.sha256(system.encode("utf-8")).hexdigest(),
            "mensaje_sistema":system,"solicitud_json":payload,
            "campos_enviados":sorted(sent),
            "campos_omitidos_por_perfil":sorted(
                set(context).intersection(p["omit_context"])),
            "campos_omitidos_por_motor":sorted(set(context)-set(sent)),
            "datos_enviados":sent,
            "bytes":len(wire.encode("utf-8")),
            "solicitud_serializada":wire,
            "huella_solicitud_calculada":index["body_sha256"],
            "mensaje_literal_por_rol":index["messages"],
            "segmentacion_verificada":all(
                "".join(part["literal"] for part in message["segments"])
                == message["text"] for message in index["messages"]),
            "procedencia":"previsualizacion_calculada_sin_red",
            "enviado_a_llm":False,
            "nota":"Constructor real del motor; ningún proveedor fue consultado."}


class LabHub:
    def __init__(self,root,world_path=None):
        self.store=ProfileStore(root)
        self.root=Path(root).resolve()
        self.world=Path(world_path).resolve() if world_path is not None else None

    def list(self):
        data=self.store.entries()
        root=self.store.dir/"world_backups"
        data["world_backups"]=sorted(
            [p.name for p in root.glob("*.sqlite3") if len(p.stem)==32
             and all(ch in "0123456789abcdef" for ch in p.stem)],
            reverse=True)[:100] if root.is_dir() else []
        return data

    def load(self,name):
        return self.store.load(name)

    def _context(self,seed):
        from laboratorio_contexto import contexto_de_deliberacion
        with tempfile.TemporaryDirectory(prefix="nilo-hub-21-") as td:
            sim=Simulation(db_path=Path(td)/"prueba.sqlite3",
                           world_seed=_seed(seed),rng_seed=9821)
            try:
                sim.think=lambda:None
                return contexto_de_deliberacion(sim)
            finally:sim.conn.close()

    def preview(self,profile,*,provider="gemini",seed=7321,context_mode="baseline"):
        result=_request(profile,self._context(seed),provider,context_mode=context_mode)
        result["seed"]=seed
        return result

    def compare(self,profile,*,provider="gemini",seed=7321,scenario=None,
                context_mode="baseline"):
        candidate=validate(profile)
        context=self._context(seed)
        before=_request(baseline(),context,provider)
        after=_request(candidate,context,provider,context_mode=context_mode)
        before["seed"]=seed
        after["seed"]=seed
        result={
            "profile":candidate["name"],"provider":provider,"seed":seed,
            "modo_baseline":"baseline","modo_variante":context_mode,
            "diff":self.store.diff(candidate),
            "baseline_bytes":before["bytes"],"variant_bytes":after["bytes"],
            "baseline_fields":before["campos_enviados"],
            "variant_fields":after["campos_enviados"],
            "new_prompt_sha256":after["prompt_sha256"],
            "before":before,"after":after,
            "physical_params_modified":False,
            "limitacion":"Esta etapa habilita cuotas y variantes del contexto/prompt; no modifica leyes físicas."
        }
        if scenario is not None:
            from laboratorio_casos import INDEX,run
            if not isinstance(scenario,str) or scenario not in INDEX:
                raise ValueError("Escenario de comparación desconocido")
            first=run(scenario,seed=_seed(seed))
            second=run(scenario,seed=_seed(seed))
            result["scenario"]={
                "id":scenario,"initial":first["inicio"],
                "baseline":first["cambios"],"variant":second["cambios"],
                "expected_baseline":first["cumple_expectativa"],
                "expected_variant":second["cumple_expectativa"],
                "same_physical_effects":first["cambios"]==second["cambios"],
                "interpretacion":"Ambos ensayos usan Simulation real, la misma semilla y operaciones. "
                  "Las variantes solo afectan la futura deliberación, no las acciones ya fijadas."
            }
        return result

    def save(self,profile):
        return self.store.save(profile)

    def apply(self,profile,confirm=False):
        if confirm is not True:
            raise ValueError("La aplicación requiere confirmación explícita")
        return self.store.apply(profile)

    def restore(self,checkpoint,confirm=False):
        if confirm is not True:
            raise ValueError("La restauración requiere confirmación explícita")
        return self.store.restore(checkpoint)

    def backup_world(self,confirm=False):
        if confirm is not True:raise ValueError("El respaldo requiere confirmación")
        if self.world is None or not self.world.is_file():
            raise ValueError("No hay partida principal para respaldar")
        target=self.store.dir/"world_backups"/(uuid4().hex+".sqlite3")
        report=backup_file(self.world,target)
        return {"created":True,"name":target.name,
                "location":str(target),"result":report,
                "original_untouched":True}

    def restore_world_copy(self,backup_name,confirm=False):
        if confirm is not True:raise ValueError("La restauración requiere confirmación")
        if not isinstance(backup_name,str) or len(backup_name)!=40 or not backup_name.endswith(".sqlite3"):
            raise ValueError("Nombre de respaldo inválido")
        from string import hexdigits
        if any(x not in hexdigits[:16] for x in backup_name[:-8]):
            raise ValueError("Nombre de respaldo inválido")
        source=self.store.dir/"world_backups"/backup_name
        destination=self.store.dir/"world_restores"/(uuid4().hex+".sqlite3")
        destination.parent.mkdir(parents=True,exist_ok=True)
        manifest=restore_as_copy(source,destination)
        return {"restored_as_copy":True,"name":destination.name,
                "location":str(destination),"original_untouched":True,
                "result":manifest}
