"""Sandbox interactivo sobre la MISMA Simulation de la aplicación.

El sandbox anterior usaba un ejecutor físico paralelo y un reloj aproximado.
Éste invoca normalize_decision → plan_ready → tick → diagnósticos del motor real
en un SQLite TEMPORAL. No se conecta a Gemini/Groq ni escribe el save origen.
"""
from __future__ import annotations

import copy
from contextlib import closing
import json
from pathlib import Path
import random
import sqlite3
import tempfile
import threading

from action_contracts import ACTION_GUIDE, SUPPORTED_OPERATIONS
from brain import normalize_decision, build_deliberation_request, context_for, config
from nilo_runtime.application.engine import Simulation
from world import valid, tile


class SimulationSandbox:
    def __init__(self, trace_factory):
        self.lock=threading.RLock()
        self.trace_factory=trace_factory
        self._temp=None
        self.sim=None
        self.history=[]
        self.last=None
        self.reset("nuevo",7321,True)

    @property
    def world(self):
        return self.sim.s["world"]

    @property
    def person(self):
        return self.sim.s["person"]

    def close(self):
        with self.lock:
            if self.sim is not None:
                self.sim.conn.close()
                self.sim=None
            if self._temp is not None:
                self._temp.cleanup()
                self._temp=None

    def reset(self, mode="nuevo", seed=7321, kit=False, *, source=None):
        if mode not in ("nuevo","partida"):
            raise ValueError("Origen de mundo no reconocido")
        if type(seed) is not int or not 0<=seed<=1000000000:
            raise ValueError("La semilla debe estar entre 0 y 1.000.000.000")
        # Construir la nueva instancia primero. Si un save no valida,
        # el sandbox anterior sigue disponible sin cambios.
        with self.lock:
            temp=tempfile.TemporaryDirectory(prefix="nilo-lab-simulation-")
            path=Path(temp.name)/"ensayo.sqlite3"
            sim=None
            try:
                if mode=="partida":
                    origin=Path(source).resolve() if source is not None else None
                    if origin is None or not origin.is_file():
                        raise ValueError("No existe una partida guardada")
                    with closing(sqlite3.connect(
                            origin.as_uri()+"?mode=ro",uri=True)) as src:
                        with closing(sqlite3.connect(path)) as dst:
                            src.backup(dst)
                            dst.commit()
                    label="Copia independiente en SQLite del último estado guardado"
                else:
                    label="Mundo nuevo, semilla "+str(seed)
                sim=Simulation(db_path=path,world_seed=seed,
                               rng_seed=(None if mode=="partida" else 9821))
                sim.think=lambda:None
                sim.timeline_capture_enabled=False
                sim.s["speed"]=60
                sim.s["paused"]=False
                sim.s["auto_wait_frozen"]=False
                sim.s["mode"]="demo"
                sim.s["person"]["pending"]=None
                sim.s["person"]["plan"]=[]
                if kit:
                    for material,qty in (("madera",16),("piedra",16),
                                         ("arcilla",10),("fibra",10),
                                         ("mineral oscuro",8),("alimento",6)):
                        inventory=sim.s["person"]["inventory"]
                        inventory[material]=max(qty,inventory.get(material,0))
                    label+=" · materiales de prueba añadidos"
                sim.write()
            except BaseException:
                if sim is not None:sim.conn.close()
                temp.cleanup()
                raise
            old_sim,old_temp=self.sim,self._temp
            self.sim,self._temp=sim,temp
            self.origin=label
            self.history=[]
            self.last=None
            if old_sim is not None:old_sim.conn.close()
            if old_temp is not None:old_temp.cleanup()
            return self.state()

    def state(self):
        with self.lock:
            w,p=self.world,self.person
            x,y,z=p["pos"]
            known=set(w.get("revealed",[]))
            cells=[]
            for yy in range(y-7,y+8):
                row=[]
                for xx in range(x-7,x+8):
                    inside=valid(xx,yy)
                    discovered=inside and f"{xx},{yy},{z}" in known
                    ch=tile(w,xx,yy,z) if discovered else "?"
                    if (xx,yy)==(x,y):ch="@"
                    row.append({"x":xx,"y":yy,"ch":ch,
                                "known":bool(discovered),
                                "selectable":bool(inside and discovered)})
                cells.append(row)
            structures=[{"id":o.get("id"),"name":o.get("name"),
                         "pos":o.get("pos"),"version":o.get("revision",1)}
                        for o in w.get("structures",[])]
            items=[{"id":o.get("id"),"name":o.get("name"),"form":o.get("form"),
                    "revision":o.get("revision",1)} for o in p.get("items",[])]
            sites=[{"name":name,"pos":[q["x"],q["y"],q.get("z",0)]}
                   for name,q in w.get("sites",{}).items()
                   if f"{q['x']},{q['y']},{q.get('z',0)}" in known]
            return {"origin":self.origin,"position":list(p["pos"]),
                    "minute":round(p.get("clock_minutes",0),2),
                    "inventory":{k:v for k,v in p["inventory"].items() if v},
                    "needs":dict(p.get("needs",{})),"map":cells,
                    "known":len(known),"structures":structures,"items":items,
                    "sites":sites,"history":self.history[-15:][::-1],
                    "last":self.last,
                    "actions":[{"name":k,"description":v}
                               for k,v in ACTION_GUIDE.items()]}

    def act(self,step):
        if not isinstance(step,dict) or not isinstance(step.get("op"),str):
            raise ValueError("La acción debe tener una operación válida")
        if step["op"] not in SUPPORTED_OPERATIONS:
            raise ValueError("Operación no disponible en el motor")
        if len(json.dumps(step,ensure_ascii=False,allow_nan=False))>4000:
            raise ValueError("Acción demasiado extensa")
        with self.lock:
            sim=self.sim
            p=sim.s["person"]
            before_measure=len(p.get("measurements",[]))
            prior_seq=sim.conn.execute(
                "SELECT COALESCE(MAX(seq),0) FROM history WHERE category='diagnostic'"
            ).fetchone()[0]
            before_events=len(sim.s.get("events",[]))
            decision=normalize_decision({
                "objetivo":"Ensayo técnico del observador, aislado del mundo vivo",
                "cuaderno":"Laboratorio: acción seleccionada manualmente, sin proveedor LLM.",
                "motivo":"Verificación de operación con Simulation real.",
                "accion_proyecto":"sin_proyecto","plan":[step],
                "revisar_en_minutos":180})
            with self.trace_factory() as trace:
                sim.plan_ready(decision,"demo",{})
                accepted=bool(p.get("plan"))
                ticks=0
                if accepted:
                    for _ in range(500):
                        sim.tick(3.0)
                        ticks+=1
                        if not p.get("plan") and not p.get("pending"):break
                        if p.get("unconscious"):break
                sim.write()
            row=sim.conn.execute(
                "SELECT payload FROM history WHERE category='diagnostic' "
                "AND seq>? ORDER BY seq DESC LIMIT 1",(prior_seq,)
            ).fetchone()
            diag=json.loads(row[0]) if row else None
            # Un resultado solo existe si lo registró el motor.
            actual=(diag.get("action_result") if isinstance(diag,dict) else None)
            if not isinstance(actual,dict):
                facts=[e.get("text","") for e in sim.s.get("events",[])[before_events:]
                       if isinstance(e,dict) and e.get("text")]
                actual={"op":step["op"],"status":"sin_medicion",
                        "success":False,"facts":facts[-2:] or [
                            "No hubo una acción física instrumentada en este ensayo."],
                        "duration_minutes":0}
            measurement=(p.get("measurements") or [])[before_measure:]
            last_measure=measurement[-1] if measurement else None
            measured=({"id":last_measure["id"],
                       "inventory_delta":last_measure.get("inventory_delta",{}),
                       "needs_delta":last_measure.get("needs_delta",{})}
                      if last_measure else None)
            self.last={"step":copy.deepcopy(step),"result":actual,
                       "diagnostic":diag,"measurement":measured,
                       "trace":trace.records(),"ticks":ticks,
                       "engine":"Simulation.plan_ready / Simulation.tick",
                       "limit_reached":ticks>=500 and bool(p.get("pending") or p.get("plan"))}
            self.history.append({
                "op":step["op"],"success":actual.get("success") is True,
                "status":actual.get("status"),"facts":list(actual.get("facts") or [])[:2]})
            return self.state()

    def payload(self,provider="gemini"):
        if provider not in ("gemini","groq"):
            raise ValueError("Proveedor de previsualización no soportado")
        with self.lock:
            with self.trace_factory() as trace:
                context=context_for(self.world,self.person,[],
                                    "Laboratorio · minuto "+str(round(
                                        self.person["clock_minutes"],2)))
                cfg=dict(config())
                cfg["PROVIDER"]=provider
                cfg["MODEL"]=("gemini-3.1-flash-lite" if provider=="gemini"
                              else "openai/gpt-oss-20b")
                cfg["GEMINI_API_KEY"]="simulacion-sin-red"
                cfg["GROQ_API_KEY"]="simulacion-sin-red"
                _,payload,_=build_deliberation_request(cfg,context)
            if provider=="gemini":
                sent=json.loads(payload["contents"][0]["parts"][0]["text"].split(
                    "SITUACIÓN REAL: ",1)[1])
            else:
                sent=json.loads(payload["messages"][1]["content"])
            return {"provider":provider,"context":sent,
                    "sections_omitted":sorted(set(context)-set(sent)),
                    "trace":trace.records(),
                    "note":"Mismo constructor del motor; no se envió ninguna solicitud LLM."}
