"""Puerta única para solicitudes Gemini y OpenAI-compatible/Groq.

Construcción de payloads auditable sin red, transporte intercambiable y
decodificación estricta; no modifica el mundo ni ejecuta acciones.
"""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from urllib.parse import urlsplit

from nilo_runtime.agent.prompts import SYSTEM, GROQ_SYSTEM, CHAT_SYSTEM
from nilo_runtime.agent.budget import (
    brief_actions, compact_context, bounded_context, context_stats,
)
from nilo_runtime.agent.responses import parse_json
from providers import error_from_http, ProviderFailure
from action_contracts import instructions as action_instructions
from nilo_runtime.agent.trace_context import (transport_started, transport_finished,
    observe_context, response_text_received, response_phase)

def _post(url, payload, headers, provider):
    """Único límite de red; la identificación del proveedor nunca depende de URL."""
    # Serializar una única vez; la copia técnica es idéntica a Request.data.
    # No registrar headers: contienen claves API.
    body = json.dumps(payload,ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url, data=body, headers=headers, method="POST")
    transport_started(body,provider)
    try:
        with urllib.request.urlopen(request,timeout=40) as reply:
            result = json.load(reply)
    except urllib.error.HTTPError as exc:
        transport_finished("http_error", code=exc.code)
        raise error_from_http(exc,provider) from None
    except ValueError:
        # Recibimos bytes, pero la respuesta no se pudo decodificar como JSON.
        transport_finished("invalid_http_response")
        raise
    except Exception:
        transport_finished("transport_error")
        raise
    transport_finished("response_received")
    return result

def _response(result, provider, *, chat=False):
    """Decodificar una sola respuesta, sin interpolar texto ni deducir éxito."""
    try:
        if provider=="gemini":
            c=result["candidates"][0]
            txt="".join(part.get("text","") for part in c.get("content",{}).get("parts",[])
                        if isinstance(part,dict))
            usage=result.get("usageMetadata",{})
            tokens={"entrada":usage.get("promptTokenCount",0),
                    "salida":usage.get("candidatesTokenCount",0)}
        else:
            txt=result["choices"][0]["message"].get("content") or ""
            usage=result.get("usage",{})
            tokens={"entrada":usage.get("prompt_tokens",0),
                    "salida":usage.get("completion_tokens",0)}
    except (TypeError, KeyError, IndexError, AttributeError):
        raise ProviderFailure(provider+": respuesta sin estructura válida","invalid") from None
    if not isinstance(txt,str) or not txt.strip():
        raise ProviderFailure(provider+": respuesta vacía del modelo","invalid")
    # Texto exacto generado (antes de strip y recorte de chat); no se guarda
    # el JSON HTTP global que incluye metadatos del proveedor.
    response_text_received(txt)
    return (txt.strip()[:2000] if chat else txt),tokens

def _endpoint(cfg):
    provider=cfg.get("PROVIDER","gemini")
    if provider=="gemini":
        return "https://generativelanguage.googleapis.com/v1beta/models/"+cfg.get("MODEL","gemini-3.1-flash-lite")+":generateContent"
    if provider not in ("groq","openai_compatible"):
        raise ValueError("Proveedor desconocido")
    base=("https://api.groq.com/openai/v1" if provider=="groq"
          else cfg.get("OPENAI_BASE_URL","https://api.openai.com/v1")).rstrip("/")
    parsed=urlsplit(base)
    local=parsed.scheme=="http" and parsed.hostname in ("127.0.0.1","localhost")
    if (parsed.scheme!="https" and not local) or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("La API debe usar HTTPS, salvo el servidor local.")
    return base+"/chat/completions"

def _headers(cfg):
    provider=cfg.get("PROVIDER","gemini")
    if provider=="gemini":
        return {"x-goog-api-key":cfg["GEMINI_API_KEY"],"Content-Type":"application/json"}
    headers={"Authorization":"Bearer "+(
        cfg["GROQ_API_KEY"] if provider=="groq" else cfg["OPENAI_API_KEY"]),
        "Content-Type":"application/json"}
    if provider=="groq":
        headers["User-Agent"]="Mozilla/5.0 (compatible; Nilo/0.3; API client)"
    return headers

def build_deliberation_request(cfg,context):
    """Preparar la solicitud sin red, aplicando presupuesto al payload completo."""
    from cognitive_projection import project_context
    observe_context("percepcion",context)
    context=project_context(context)
    observe_context("proyeccion",context)
    # El perfil cambia únicamente el payload; nunca la memoria del mundo.
    from nilo_runtime.core.lab_settings import OPTIONAL_CONTEXT
    omission=cfg.get("_LAB_OMIT_CONTEXT") or ()
    if any(x not in OPTIONAL_CONTEXT for x in omission):
        raise ValueError("No se puede omitir contexto obligatorio")
    if omission:
        context={k:v for k,v in context.items() if k not in omission}
    observe_context("perfil",context)
    note=cfg.get("_LAB_PROMPT_NOTE") or ""
    if not isinstance(note,str) or len(note)>700 or "\r" in note or "\x00" in note:
        raise ValueError("Nota de sistema del laboratorio inválida")
    extra=("\nNOTA ADICIONAL DEL PERFIL DE LABORATORIO: "+note) if note else ""

    provider=cfg.get('PROVIDER','gemini')
    model=cfg.get('MODEL','gemini-3.1-flash-lite')
    # El modo modular es un ensayo explícito. La instalación sigue en baseline.
    mode=cfg.get("_LAB_CONTEXT_MODE", "baseline")
    if type(mode) is not str or mode not in ("baseline", "modular"):
        raise ValueError("Modo de contexto experimental desconocido")
    if mode == "modular":
        from nilo_runtime.agent.context_modules import modular_context, modular_instructions
        selected=modular_context(context,provider=provider)
        observe_context("compactacion",selected)
        system,manual=modular_instructions(context,provider)
        system+=extra
    elif provider=='groq':
        selected=compact_context(context,char_budget=18000)
        observe_context("compactacion",selected)
        selected=bounded_context(selected,4100)
        system=GROQ_SYSTEM+'\n'+brief_actions()+extra
    elif provider=='gemini':
        selected=compact_context(context,char_budget=25000)
        observe_context("compactacion",selected)
        selected=bounded_context(selected,9100)
        system=SYSTEM+'\n'+action_instructions()+extra
    elif cfg.get('_compact_context'):
        selected=compact_context(context,char_budget=23000)
        observe_context("compactacion",selected)
        selected=bounded_context(selected,6900)
        system=SYSTEM+'\n'+action_instructions()+extra
    else:
        # El proveedor OpenAI-compatible conserva el mismo límite de percepción;
        # jamás recibe puntajes internos por omitir el contexto compacto.
        selected=compact_context(context,char_budget=25000)
        observe_context("compactacion",selected)
        selected=bounded_context(selected,9100)
        system=SYSTEM+'\n'+action_instructions()+extra
    observe_context("presupuesto",selected)
    data=json.dumps(selected,ensure_ascii=False,separators=(',',':'))
    if provider=='gemini':
        url=_endpoint(cfg)
        payload={"systemInstruction":{"parts":[{"text":system if mode=="modular" else SYSTEM+extra}]},
                 "contents":[{"role":"user","parts":[{"text":(manual if mode=="modular" else action_instructions())+'\nSITUACIÓN REAL: '+data}]}],
                 "generationConfig":{"temperature":0.85,"maxOutputTokens":2300,"responseMimeType":"application/json"}}
        headers=_headers(cfg)
    elif provider in ('openai_compatible','groq'):
        url=_endpoint(cfg)
        payload={"model":model,"messages":[{"role":"system","content":system},
                 {"role":"user","content":data}],"temperature":0.8,
                 "max_completion_tokens":1550 if provider=='groq' else 2500,
                 "response_format":{"type":"json_object"}}
        if provider=='groq':payload['reasoning_effort']='low'
        headers=_headers(cfg)
    else:raise ValueError('Proveedor desconocido')
    if provider=='groq':
        for budget in (4100,3000,2200,1600):
            selected=bounded_context(selected,budget)
            payload['messages'][1]['content']=json.dumps(
                selected,ensure_ascii=False,separators=(',',':'))
            if len(json.dumps(payload,ensure_ascii=False).encode('utf-8'))<=14500:
                break
        else:
            from providers import ProviderFailure
            raise ProviderFailure('groq: solicitud supera presupuesto interno','too_large')
        observe_context("limite_proveedor",selected)
    observe_context("solicitud_preparada",selected)
    return url,payload,headers


def request_llm(cfg, context):
    url,payload,headers=build_deliberation_request(cfg,context)
    provider=cfg.get("PROVIDER","gemini")
    if provider=="gemini":
        sent=json.loads(payload["contents"][0]["parts"][0]["text"].split("SITUACIÓN REAL: ",1)[1])
    else:
        sent=json.loads(payload["messages"][1]["content"])
    stats=context_stats(context,sent,provider,payload)
    raw=_post(url,payload,headers,provider)
    text,tokens=_response(raw,provider)
    tokens["contexto"]=stats
    try:
        parsed=parse_json(text)
    except (ValueError,TypeError):
        response_phase("invalid_json")
        raise
    response_phase("json_parsed")
    return parsed,tokens


def build_chat_request(cfg,context,messages,system_instruction=None):
    """Mismo payload que el chat real, comprobable sin llamar a la red."""
    from cognitive_projection import project_context
    observe_context("percepcion",context)
    context=project_context(context)
    observe_context("proyeccion",context)
    system_instruction=system_instruction or CHAT_SYSTEM
    provider=cfg.get('PROVIDER','gemini')
    model=cfg.get('MODEL','gemini-3.1-flash-lite')
    history=[{'role':v['role'],'text':v['text'][:1200]} for v in messages[-10:] if v.get('role') in ('user','assistant')]
    if provider=='groq' or cfg.get('_compact_context'):
        # Resumir contexto regular; conservar las entradas pendientes para preguntas
        # «qué me perdí», en lotes gestionados por el motor.
        keep={k:v for k,v in context.items() if k in ('momento','posición','necesidades','proyecto_actual',
               'unread_summary','pending','pendientes','resumen_pendientes','resumen_de_lo_no_leido','instruccion_de_resumen','regla','ultimo_resumen')}
        if len(json.dumps(keep,ensure_ascii=False,default=str))<350:
            keep.update({k:v for k,v in list(context.items())[:8]})
        context=keep
        history=history[-4:]
        history=[dict(m,text=m['text'][:550]) for m in history]
    observe_context("filtro_chat",context)
    grounded='CONTEXTO COMPROBADO (no lo contradigas): '+json.dumps(context,ensure_ascii=False,default=str)
    if provider=='gemini':
        url=_endpoint(cfg)
        while history and history[0]['role']!='user':history.pop(0)
        contents=[]
        for i,m in enumerate(history):
            role='model' if m['role']=='assistant' else 'user'
            msg=(grounded+'\n\n' if i==0 else '')+m['text']
            if contents and contents[-1]['role']==role:
                contents[-1]['parts'][0]['text']+='\n'+msg
            else:
                contents.append({'role':role,'parts':[{'text':msg}]})
        if not contents:
            contents=[{'role':'user','parts':[{'text':grounded}]}]
        payload={'systemInstruction':{'parts':[{'text':system_instruction}]},'contents':contents,'generationConfig':{'temperature':0.75,'maxOutputTokens':450}}
        headers=_headers(cfg)
    elif provider in ('openai_compatible','groq'):
        url=_endpoint(cfg)
        # El estado observado viaja como dato de usuario; ningún cuaderno,
        # comentario o evento humano se promueve a instrucción de sistema.
        msgs=[{'role':'system','content':system_instruction},
              {'role':'user','content':grounded}]+[
                  {'role':h['role'],'content':h['text']} for h in history]
        payload={'model':model,'messages':msgs,'temperature':.75,'max_completion_tokens':450 if provider=='groq' else 650}
        if provider=='groq':payload['reasoning_effort']='low'
        headers=_headers(cfg)
    else:raise ValueError('Proveedor desconocido')
    observe_context("solicitud_preparada",context)
    return url,payload,headers


def request_chat(cfg,context,messages,system_instruction=None):
    url,payload,headers=build_chat_request(cfg,context,messages,system_instruction)
    provider=cfg.get('PROVIDER','gemini')
    result=_post(url,payload,headers,provider)
    reply,tokens=_response(result,provider,chat=True)
    response_phase("chat_returned")
    return reply,tokens
