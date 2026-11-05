"""Puerta única para solicitudes Gemini y OpenAI-compatible/Groq.

Construcción de payloads auditable sin red, transporte intercambiable y
decodificación estricta; no modifica el mundo ni ejecuta acciones.
"""
from __future__ import annotations

import json
import urllib.request
import urllib.error

from nilo_runtime.agent.prompts import SYSTEM, GROQ_SYSTEM, CHAT_SYSTEM
from nilo_runtime.agent.budget import (
    brief_actions, compact_context, bounded_context, context_stats,
)
from nilo_runtime.agent.responses import parse_json
from providers import error_from_http, ProviderFailure
from action_contracts import instructions as action_instructions

def _post(url, payload, headers, provider):
    """Único límite de red; la identificación del proveedor nunca depende de URL."""
    request = urllib.request.Request(
        url, data=json.dumps(payload,ensure_ascii=False).encode("utf-8"),
        headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request,timeout=40) as reply:
            return json.load(reply)
    except urllib.error.HTTPError as exc:
        raise error_from_http(exc,provider) from None

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
    return (txt.strip()[:2000] if chat else txt),tokens

def _endpoint(cfg):
    provider=cfg.get("PROVIDER","gemini")
    if provider=="gemini":
        return "https://generativelanguage.googleapis.com/v1beta/models/"+cfg.get("MODEL","gemini-3.1-flash-lite")+":generateContent"
    if provider not in ("groq","openai_compatible"):
        raise ValueError("Proveedor desconocido")
    base=("https://api.groq.com/openai/v1" if provider=="groq"
          else cfg.get("OPENAI_BASE_URL","https://api.openai.com/v1")).rstrip("/")
    if not (base.startswith("https://") or
            base.startswith("http://127.0.0.1") or base.startswith("http://localhost")):
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
    context=project_context(context)

    provider=cfg.get('PROVIDER','gemini')
    model=cfg.get('MODEL','gemini-3.1-flash-lite')
    if provider=='groq':
        selected=bounded_context(compact_context(context,char_budget=18000),4100)
        system=GROQ_SYSTEM+'\n'+brief_actions()
    elif provider=='gemini':
        selected=bounded_context(compact_context(context,char_budget=25000),9100)
        system=SYSTEM+'\n'+action_instructions()
    elif cfg.get('_compact_context'):
        selected=bounded_context(compact_context(context,char_budget=23000),6900)
        system=SYSTEM+'\n'+action_instructions()
    else:
        # El proveedor OpenAI-compatible conserva el mismo límite de percepción;
        # jamás recibe puntajes internos por omitir el contexto compacto.
        selected=bounded_context(compact_context(context,char_budget=25000),9100)
        system=SYSTEM+'\n'+action_instructions()
    data=json.dumps(selected,ensure_ascii=False,separators=(',',':'))
    if provider=='gemini':
        url=_endpoint(cfg)
        payload={"systemInstruction":{"parts":[{"text":SYSTEM}]},
                 "contents":[{"role":"user","parts":[{"text":action_instructions()+'\nSITUACIÓN REAL: '+data}]}],
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
    return parse_json(text),tokens


def build_chat_request(cfg,context,messages,system_instruction=None):
    """Mismo payload que el chat real, comprobable sin llamar a la red."""
    from cognitive_projection import project_context
    context=project_context(context)
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
        payload={'systemInstruction':{'parts':[{'text':system_instruction}]},'contents':contents,'generationConfig':{'temperature':0.75,'maxOutputTokens':450}}
        headers=_headers(cfg)
    elif provider in ('openai_compatible','groq'):
        url=_endpoint(cfg)
        msgs=[{'role':'system','content':system_instruction+'\n'+grounded}]+[{'role':h['role'],'content':h['text']} for h in history]
        payload={'model':model,'messages':msgs,'temperature':.75,'max_completion_tokens':450 if provider=='groq' else 650}
        if provider=='groq':payload['reasoning_effort']='low'
        headers=_headers(cfg)
    else:raise ValueError('Proveedor desconocido')
    return url,payload,headers


def request_chat(cfg,context,messages,system_instruction=None):
    url,payload,headers=build_chat_request(cfg,context,messages,system_instruction)
    provider=cfg.get('PROVIDER','gemini')
    result=_post(url,payload,headers,provider)
    reply,tokens=_response(result,provider,chat=True)
    return reply,tokens
