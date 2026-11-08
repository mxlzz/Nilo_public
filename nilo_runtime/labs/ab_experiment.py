"""Experimentos A/B aislados: misma referencia, modos explícitos y evidencias.

Modos:
- context: comparar exactamente DOS payloads calculados sin red.
- physical: reproducir guiones físicos independientes sobre copias temporales.
- llm: dos deliberaciones reales opcionales; nunca ejecuta decisiones.
- evolution: deliberar + ejecutar en dos mundos temporales, con tope muy bajo.

Nunca se escribe en el mundo fuente, ni se aplica el perfil al motor vivo.
No atribuir al perfil una diferencia aleatoria de muestras de LLM.
"""
from __future__ import annotations

from contextlib import ExitStack
import copy
import hashlib
import json
from pathlib import Path
import threading
import time

from brain import config
from nilo_runtime.agent import gateway
from nilo_runtime.agent.responses import parse_json, normalize_decision
from nilo_runtime.core.lab_settings import baseline, validate
from nilo_runtime.labs.hub import _request, _seed
from nilo_runtime.labs.sandbox import SimulationSandbox
from laboratorio_contexto import contexto_de_deliberacion

_LIVE_LOCK = threading.Lock()
MAX_PHYSICAL_STEPS = 6
MAX_LIVE_TURNS = 2
_MAX_TICKS = 300


class _SilentTrace:
    def __enter__(self): return self
    def __exit__(self, *_): return False
    def records(self): return []


def _sha(obj):
    content=json.dumps(obj,ensure_ascii=False,sort_keys=True,
                       separators=(",",":"),allow_nan=False)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _projection(lab):
    # Mismas variables observables en las dos copias físicas; no usar
    # hash del archivo SQLite (timestamps y journaling no son estado).
    state=lab.state()
    return {key:copy.deepcopy(state[key]) for key in
            ("position","minute","inventory","needs","known",
             "structures","items","sites","map")}


def _worlds(seed, *, source="new", world_path=None, kit=False):
    """Abrir dos sandboxes sin red; copiar la partida fuente por SQLite backup."""
    if source not in ("new","saved"):
        raise ValueError("Origen de experimento desconocido")
    if type(kit) is not bool:
        raise ValueError("El kit debe ser booleano")
    if source=="saved" and (world_path is None or not Path(world_path).is_file()):
        raise ValueError("No hay partida guardada para usar como referencia")
    with ExitStack() as stack:
        labs=[]
        for _ in range(2):
            lab=SimulationSandbox(_SilentTrace)
            stack.callback(lab.close)
            lab.reset("partida" if source=="saved" else "nuevo",
                      seed,kit,source=world_path if source=="saved" else None)
            labs.append(lab)
        a,b=labs
        initial_a,initial_b=_projection(a),_projection(b)
        if initial_a!=initial_b:
            raise ValueError("Las copias del estado inicial no coinciden; ensayo cancelado")
        yield a,b,_sha(initial_a)


def _script(raw):
    if not isinstance(raw,list) or len(raw)>MAX_PHYSICAL_STEPS:
        raise ValueError("El guion debe tener de cero a seis operaciones")
    from action_contracts import SUPPORTED_OPERATIONS
    out=[]
    for action in raw:
        if not isinstance(action,dict) or not isinstance(action.get("op"),str):
            raise ValueError("Cada paso debe incluir una operación")
        if action["op"] not in SUPPORTED_OPERATIONS:
            raise ValueError("Operación no reconocida")
        if len(json.dumps(action,ensure_ascii=False,allow_nan=False))>1500:
            raise ValueError("Acción demasiado extensa")
        out.append(copy.deepcopy(action))
    return out


def context_pair(hub,profile,*,provider="gemini",seed=7321):
    """Un solo estado observable para baseline y variante; sin proveedores."""
    _seed(seed)
    candidate=validate(profile)
    context=hub._context(seed)
    identity=_sha(context)
    before=_request(baseline(),context,provider)
    if _sha(context)!=identity:
        raise ValueError("El constructor baseline modificó el contexto de referencia")
    after=_request(candidate,context,provider)
    if _sha(context)!=identity:
        raise ValueError("El constructor variante modificó el contexto de referencia")
    if before["enviado_a_llm"] or after["enviado_a_llm"]:
        raise ValueError("Una previsualización no puede marcarse como enviada")
    for view in (before,after):view["seed"]=seed
    return {
        "experiment_type":"context_ab","source":"fresh_isolated_seed",
        "seed":seed,"provider":provider,"reference_sha256":identity,
        "reference_type":"one_identical_frozen_perception",
        "baseline":before,"variant":after,
        "comparison":{
            "baseline_bytes":before["bytes"],"variant_bytes":after["bytes"],
            "delta_bytes":after["bytes"]-before["bytes"],
            "removed_fields":sorted(set(before["campos_enviados"])-set(after["campos_enviados"])),
            "added_fields":sorted(set(after["campos_enviados"])-set(before["campos_enviados"])),
            "changed_request":before["huella_solicitud_calculada"]!=after["huella_solicitud_calculada"],
            "comparable_same_reference":True,
            "actual_model_response":False
        },
        "llm_calls":0,"modified_original_world":False,
        "notes":[
            "Se comparan textos calculados desde el mismo estado, sin red.",
            "El tamaño menor no demuestra que Nilo decida mejor.",
            "Se aplican únicamente omisiones permitidas por el perfil."
        ]}


def physical_pair(*,seed=7321,baseline_steps=None,variant_steps=None,
                  source="new",world_path=None,kit=False):
    """Evolución física guionada con dos copias del mismo mundo, sin LLM.

    Una acción equivocada sigue en el reporte como rechazo: no se inventa éxito.
    Comparar estos efectos NO mide diferencias causadas por una variante de prompt.
    """
    _seed(seed)
    scripts={"baseline":_script(baseline_steps if baseline_steps is not None else []),
             "variant":_script(variant_steps if variant_steps is not None else [])}
    # No solicitar más allá del tiempo límite por rutina: no hay LLM.
    with ExitStack() as stack:
        labs=[]
        for _ in range(2):
            lab=SimulationSandbox(_SilentTrace)
            stack.callback(lab.close)
            lab.reset("partida" if source=="saved" else "nuevo",
                      seed,kit,source=world_path if source=="saved" else None)
            labs.append(lab)
        if source not in ("new","saved"):
            raise ValueError("Origen de experimento desconocido")
        before=[_projection(lab) for lab in labs]
        if before[0]!=before[1]:
            raise ValueError("Las copias físicas no comparten el mismo estado inicial")
        fingerprint=_sha(before[0])
        result={}
        for name,lab in zip(("baseline","variant"),labs):
            entries=[]
            for i,step in enumerate(scripts[name],1):
                started=_projection(lab)
                out=lab.act(step)
                last=out["last"]
                ended=_projection(lab)
                entries.append({
                    "turn":i,"action":step,"status":last["result"].get("status"),
                    "success":last["result"].get("success"),
                    "facts":last["result"].get("facts"),
                    "diagnostic":last["diagnostic"],
                    "measurement":last["measurement"],
                    "before_sha256":_sha(started),"after_sha256":_sha(ended),
                    "time_after":ended["minute"],
                    "limit_reached":last["limit_reached"],
                    "recorded_physical_result":(
                        last["result"] if last["result"].get("status")!="sin_medicion"
                        else None),
                })
                if last["limit_reached"]:
                    break
            final=_projection(lab)
            result[name]={
                "script":scripts[name],"steps":entries,
                "initial_sha256":fingerprint,
                "final_sha256":_sha(final),"final_state":final,
                "incomplete":bool(entries and entries[-1]["limit_reached"])}
        return {
            "experiment_type":"physical_scripted_multiturn",
            "source":"readonly_copy_of_saved_world" if source=="saved" else "fresh_isolated_seed",
            "seed":seed,"kit":kit,"reference_sha256":fingerprint,
            "baseline":result["baseline"],"variant":result["variant"],
            "comparison":{
                "same_initial_state":True,
                "same_final_state":result["baseline"]["final_sha256"]==
                                   result["variant"]["final_sha256"],
                "same_script":scripts["baseline"]==scripts["variant"],
                "different_llm_context_tested":False,
                "llm_driven":False
            },
            "llm_calls":0,"modified_original_world":False,
            "notes":[
                "Se ejecutaron acciones guionadas y reglas reales; ningún modelo decidió.",
                "Las diferencias pueden provenir de secuencias distintas, no de una variante de contexto.",
                "Los resultados sin medición física no acreditan éxito.",
                "Cada rama usó un SQLite temporal y una copia independiente del estado inicial."
            ]
        }


def _network_decision(preview,provider,*,poster=None):
    """Ejecutar exactamente el payload previsualizado, sin archivos ni reintentos."""
    cfg=dict(config())
    cfg["PROVIDER"]=provider
    cfg["MODEL"]=preview["model"]
    key="GEMINI_API_KEY" if provider=="gemini" else "GROQ_API_KEY"
    if not isinstance(cfg.get(key),str) or not cfg[key].strip():
        raise ValueError("Falta la clave del proveedor elegido; no se realizaron consultas")
    # Nunca usar URL, modelo arbitrario, headers o claves desde HTTP del usuario.
    url=gateway._endpoint(cfg)
    headers=gateway._headers(cfg)
    post=poster or gateway._post
    raw=post(url,preview["solicitud_json"],headers,provider)
    text,tokens=gateway._response(raw,provider)
    report={
        "provider":provider,"model":preview["model"],
        "request_sha256":preview["huella_solicitud_calculada"],
        "request_body_utf8":preview["solicitud_serializada"],
        "response_text":text,"tokens":tokens,"parsed":None,
        "normalized":None,"validation_error":None,"executed_in_world":False,
        "request_count":1,
    }
    try:
        parsed=parse_json(text)
        report["parsed"]=parsed
        report["normalized"]=normalize_decision(parsed)
    except (ValueError,KeyError,TypeError,OverflowError) as exc:
        report["validation_error"]=type(exc).__name__+": "+str(exc)[:350]
    return report


def _drive_decision(lab,normalized):
    """Aplicar la decisión REAL, no un guion inventado, solo en SQLite temporal."""
    if not isinstance(normalized,dict):
        return {"applied":False,"reason":"Respuesta LLM sin plan normalizado"}
    sim=lab.sim
    before=_projection(lab)
    sim.plan_ready(copy.deepcopy(normalized),"llm",{})
    accepted=bool(sim.s["person"].get("plan") or sim.s["person"].get("pending"))
    ticks=0
    if accepted:
        for _ in range(_MAX_TICKS):
            sim.tick(3.0)
            ticks+=1
            p=sim.s["person"]
            if not p.get("pending") and not p.get("plan"):break
            if p.get("unconscious"):break
    sim.write()
    after=_projection(lab)
    unfinished=bool(sim.s["person"].get("pending") or sim.s["person"].get("plan"))
    return {"applied":True,"plan_accepted":accepted,
            "ticks":ticks,"pending_or_unfinished":unfinished,
            "before_sha256":_sha(before),"after_sha256":_sha(after),
            "position":after["position"],"time_after":after["minute"],
            "needs":after["needs"],"inventory":after["inventory"]}


def live_pair(hub,profile,*,provider="gemini",seed=7321,turns=1,
              confirm=False,source="new",world_path=None,kit=False,
              poster=None,sleep_fn=None):
    """Llamadas reales sólo ante confirmación. Hasta dos deliberaciones por rama.

    En 1 turno: devuelve respuestas sin ejecutar. En 2 turnos: ejecuta cada
    respuesta en su copia física, observa de nuevo y consulta otra vez.
    Modelos no deterministas: un A/B no prueba superioridad ni causalidad.
    """
    _seed(seed)
    candidate=validate(profile)
    if provider not in ("gemini","groq"):
        raise ValueError("Proveedor no admitido")
    if type(turns) is not int or not 1<=turns<=MAX_LIVE_TURNS:
        raise ValueError("Solo se admiten una o dos deliberaciones por rama")
    if confirm is not True:
        raise ValueError("Las consultas LLM requieren confirmación explícita")
    if source not in ("new","saved"):
        raise ValueError("Origen de ensayo inválido")
    if source=="saved" and (world_path is None or not Path(world_path).is_file()):
        raise ValueError("No hay una partida local guardada disponible")
    # No solapar dos runs en servidor ThreadingHTTPServer. En el navegador
    # el botón informa dos o cuatro consultas y requiere confirmación manual.
    if not _LIVE_LOCK.acquire(blocking=False):
        raise ValueError("Ya hay un experimento con proveedor en ejecución")
    try:
        with ExitStack() as stack:
            labs=[]
            for _ in range(2):
                lab=SimulationSandbox(_SilentTrace)
                stack.callback(lab.close)
                lab.reset("partida" if source=="saved" else "nuevo",
                          seed,kit,source=world_path if source=="saved" else None)
                labs.append(lab)
            initial=[_projection(lab) for lab in labs]
            if initial[0]!=initial[1]:
                raise ValueError("Las copias iniciales del mundo no coinciden")
            fingerprint=_sha(initial[0])
            cfg=config()
            token_wait=max(15,int(cfg.get("MIN_REAL_SECONDS_BETWEEN_CALLS",15)))
            pause=sleep_fn or time.sleep
            rows={"baseline":[],"variant":[]}
            total=0
            blocked={"baseline":False,"variant":False}
            for round_i in range(turns):
                for name,lab,p in zip(("baseline","variant"),labs,(baseline(),candidate)):
                    if blocked[name]:continue
                    ctx=contexto_de_deliberacion(lab.sim)
                    preview=_request(p,ctx,provider)
                    # Pausa ENTRE solicitudes reales, no al construir JSON.
                    if total:pause(token_wait)
                    response=_network_decision(preview,provider,poster=poster)
                    total+=1
                    step={
                        "turn":round_i+1,"profile":p["name"],
                        "pre_context_sha256":_sha(ctx),
                        "sent_preview_sha256":preview["huella_solicitud_calculada"],
                        "response":response,"world_effect":None,
                    }
                    if turns>1:
                        try:
                            step["world_effect"]=_drive_decision(lab,response["normalized"])
                        except (ValueError,KeyError,TypeError) as exc:
                            step["execution_error"]=type(exc).__name__+": "+str(exc)[:250]
                            blocked[name]=True
                        if step["world_effect"] and step["world_effect"].get("pending_or_unfinished"):
                            blocked[name]=True
                    rows[name].append(step)
            return {
                "experiment_type":"llm_two_branch_deliberation" if turns==1
                    else "llm_two_branch_multiturn",
                "source":"readonly_copy_of_saved_world" if source=="saved"
                    else "fresh_isolated_seed",
                "seed":seed,"provider":provider,
                "reference_sha256":fingerprint,
                "baseline":{"profile":baseline()["name"],"turns":rows["baseline"]},
                "variant":{"profile":candidate["name"],"turns":rows["variant"]},
                "llm_calls":total,"max_llm_calls":2*turns,
                "original_world_modified":False,
                "explicit_live_consent":True,
                "limitations":[
                    "Se usaron el mismo mundo inicial y proveedor; las salidas del modelo son estocásticas.",
                    "Una sola muestra por configuración no demuestra una mejora ni explica causalidad.",
                    "No se reintentan errores automáticamente ni se escribe en la partida original.",
                    "Al comparar más de un turno, el contexto ya depende de acciones anteriores diferentes.",
                    "Las decisiones pueden ser rechazadas por el motor; lo registrado es evidencia, no éxito supuesto.",
                    "Se registra el texto de entrada, salida y costos en tokens reportados, no las claves de API."
                ]
            }
    finally:
        _LIVE_LOCK.release()
