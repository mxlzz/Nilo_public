"""Contrato HTTP v1: comandos del observador separados del transporte y del motor.

No importa el servidor ni modifica leyes físicas al consultar. Las rutas
existentes se mantienen y las operaciones se llaman por interfaces explícitas.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs

from interface_prefs import load as load_interface_prefs, save as save_interface_prefs
from nilo_runtime.application.deps import HERE, SUPPORTED_SPEEDS, ProvidersUnavailable

API_VERSION=1
GET_PATHS=frozenset((
    "/api/state","/api/version","/api/summary-history","/api/unread",
    "/api/record","/api/measurement","/api/ui-preferences","/api/diagnostic"))
POST_PATHS=frozenset((
    "/api/settings","/api/chat","/api/read-news","/api/read","/api/read-all",
    "/api/read-summary","/api/review-rule","/api/retry-llm","/api/ui-preferences",
    "/api/review-bootstrap","/api/review-mark","/api/summary-generate",
    "/api/summary-ack"))
LARGE_REQUESTS=frozenset((
    "/api/review-bootstrap","/api/review-mark","/api/summary-generate"))


@dataclass(frozen=True)
class ApiResponse:
    body: object
    status: int=200


class ApiError(ValueError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status=status


def _one(query, key, max_chars=100):
    values=query.get(key,[])
    if len(values)>1:
        raise ApiError("Parámetro duplicado: "+key)
    v=values[0] if values else ""
    if not isinstance(v,str) or len(v)>max_chars:
        raise ApiError("Parámetro inválido: "+key)
    return v


def _text(data,key,maximum,default=""):
    v=data.get(key,default)
    if not isinstance(v,str) or len(v)>maximum:
        raise ApiError("Campo inválido: "+key)
    return v


def _get(sim,path,query,root):
    if path=="/api/version":
        return {"api_version":API_VERSION,"schema_version":5,
                "engine_version":sim.sessions.identity.get("engine_version","no_registrada")}
    if path=="/api/state":
        return sim.public_state()
    if path=="/api/summary-history":
        return {"summaries":sim.observer_summary_history()}
    if path=="/api/unread":
        category=_one(query,"category",40)
        if category not in ("journal","news"):
            raise ApiError("Categoría de archivo inválida")
        with sim.lock:
            return {"category":category,
                    "total":sim.archive.count_unread(category),
                    "entries":sim.archive.unread(category,limit=80)}
    if path=="/api/record":
        category=_one(query,"category",40)
        rid=_one(query,"id",100)
        try:return sim.linked_record(category,rid)
        except ValueError as exc:raise ApiError(str(exc),404) from exc
    if path=="/api/measurement":
        mid=_one(query,"id",60)
        try:return sim.measurement_record(mid)
        except ValueError as exc:raise ApiError(str(exc),404) from exc
    if path=="/api/diagnostic":
        rid=_one(query,"id",80)
        try:return sim.diagnostic_package(rid)
        except ValueError as exc:raise ApiError(str(exc),404) from exc
    if path=="/api/ui-preferences":
        with sim.lock:
            return load_interface_prefs(root)
    raise ApiError("No encontrado",404)


def _post(sim,path,data,root):
    if path=="/api/review-bootstrap":
        return sim.bootstrap_reviews(data.get("seen",{}))
    if path=="/api/review-mark":
        return sim.mark_tab_reviewed(data.get("tab"),data.get("keys",[]))
    if path=="/api/summary-generate":
        try:return sim.observer_summary(data.get("candidates",[]),data.get("continuation"))
        except (ProvidersUnavailable,RuntimeError) as exc:
            raise ApiError(str(exc)[:450],503) from exc
    if path=="/api/summary-ack":
        return sim.acknowledge_observer_summary(_text(data,"id",80))
    if path=="/api/ui-preferences":
        with sim.lock:
            return save_interface_prefs(root,data)
    if path=="/api/retry-llm":
        result=sim.retry_llm()
        return ApiResponse(result,200 if result["ok"] else 409)
    if path=="/api/review-rule":
        return sim.review_rule(_text(data,"id",80),_text(data,"decision",15),
                               _text(data,"reason",700))
    if path in ("/api/read-news","/api/read"):
        category="news" if path=="/api/read-news" else _text(data,"category",40)
        rid=_text(data,"id",60)
        if data.get("single") is True:
            return sim.mark_one_read(category,rid)
        return sim.mark_read(category,rid)
    if path=="/api/read-all":
        categories=data.get("categories",["journal","news"])
        if not isinstance(categories,list) or len(categories)>2:
            raise ApiError("Categorías inválidas")
        return sim.mark_all_read(categories)
    if path=="/api/read-summary":
        return sim.mark_summarized_read()
    if path=="/api/chat":
        sim.start_chat(_text(data,"message",3000))
        return ApiResponse({"ok":True},202)
    if path=="/api/settings":
        speed=data.get("speed")
        if speed is not None and (type(speed) is not int or speed not in SUPPORTED_SPEEDS):
            raise ApiError("Velocidad inválida")
        paused=data.get("paused")
        if paused is not None and type(paused) is not bool:
            raise ApiError("Pausa inválida")
        auto_pause=data.get("auto_pause_on_wait")
        if auto_pause is not None and type(auto_pause) is not bool:
            raise ApiError("Ajuste de pausa inválido")
        sim.change_speed(speed,paused,auto_pause)
        return {"ok":True}
    raise ApiError("No encontrado",404)


def dispatch(sim,method,path,*,query="",data=None,root=HERE):
    """Resolver el contrato y clasificar errores de usuario, nunca exponer trazas.

    Errores inesperados quedan para el borde HTTP como 500 sin texto interno.
    """
    try:
        if method=="GET":
            if path not in GET_PATHS:raise ApiError("No encontrado",404)
            q=parse_qs(query,keep_blank_values=True,max_num_fields=16)
            result=_get(sim,path,q,Path(root))
        elif method=="POST":
            if path not in POST_PATHS:raise ApiError("No encontrado",404)
            if not isinstance(data,dict):raise ApiError("Se esperaba un objeto JSON")
            result=_post(sim,path,data,Path(root))
        else:
            raise ApiError("Método no admitido",405)
        if isinstance(result,ApiResponse):return result
        return ApiResponse(result)
    except ApiError as exc:
        return ApiResponse({"error":str(exc)},exc.status)
    except (ValueError,TypeError,KeyError) as exc:
        return ApiResponse({"error":str(exc)[:300]},400)
