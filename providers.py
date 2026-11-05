"""Ruteador de LLM con respaldo, enfriamiento y estadísticas persistentes.

Los resultados físicos se validan en el motor: este módulo solo obtiene decisiones/texto.
No guarda nunca claves ni respuestas crudas de error en el estado persistido.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import hashlib
import json
import random
import re
import time
import urllib.error


class ProviderFailure(Exception):
    def __init__(self, message, category='temporary', status=None, retry_after=None):
        super().__init__(message)
        self.category = category
        self.status = status
        self.retry_after = retry_after


class ProvidersUnavailable(Exception):
    def __init__(self, message, retry_at):
        super().__init__(message)
        self.retry_at = float(retry_at)


def _seconds(value):
    if value is None:
        return None
    try:
        return max(1.0, float(value))
    except (TypeError, ValueError):
        pass
    match = re.fullmatch(r'\s*(?:(\d+)h)?(?:(\d+)m)?(?:(\d+(?:\.\d+)?)s)?\s*', str(value))
    if match and any(match.groups()):
        return max(1.0, float(match[1] or 0)*3600+float(match[2] or 0)*60+float(match[3] or 0))
    try:
        when = parsedate_to_datetime(str(value)).timestamp()
        return max(1.0, when - time.time())
    except (ValueError, TypeError, OverflowError, IndexError):
        return None


def _daily_reset_seconds(provider):
    # Cuota Gemini RPD: medianoche horario Pacífico; para Groq, ventana diaria.
    if provider == 'gemini':
        try:
            now = datetime.now(ZoneInfo('America/Los_Angeles'))
            tomorrow = (now + timedelta(days=1)).date()
            then = datetime(tomorrow.year, tomorrow.month, tomorrow.day, tzinfo=now.tzinfo)
            return max(60, then.timestamp() - time.time() + 60)
        except ZoneInfoNotFoundError:
            # Windows puede carecer de la base horaria IANA.
            return 24 * 3600
    return 24 * 3600


def error_from_http(exc, provider='gemini'):
    """Extrae solo metadatos seguros: ningún cuerpo HTTP completo sale al navegador."""
    code = exc.code
    retry = _seconds(exc.headers.get('retry-after')) if exc.headers else None
    blob = exc.read(2500).decode('utf-8', 'replace')
    try:
        payload = json.loads(blob)
        err = payload.get('error', payload)
        phrase = str(err.get('message', ''))[:700] if isinstance(err, dict) else ''
        details = err.get('details', []) if isinstance(err, dict) else []
        for entry in details if isinstance(details, list) else []:
            if not isinstance(entry, dict):
                continue
            if not retry:
                retry = _seconds(entry.get('retryDelay'))
            phrase += ' ' + ' '.join(str(entry.get(k,''))[:180] for k in ('quotaId','quotaMetric','reason'))
    except (TypeError, ValueError):
        phrase = blob[:500]
    low = phrase.lower()
    is_daily = any(x in low for x in ('perday', 'per_day', 'per day', 'requests per day', 'rpd', 'daily', 'quota_exceeded', 'quota exhausted'))
    if provider == 'groq' and exc.headers:
        try:
            is_daily |= int(exc.headers.get('x-ratelimit-remaining-requests','-1')) == 0
        except ValueError:
            pass
        if is_daily and retry is None:
            retry = _seconds(exc.headers.get('x-ratelimit-reset-requests'))
    if code == 429:
        category = 'daily_quota' if is_daily else 'rate_limit'
    elif code in (408, 425, 500, 502, 503, 504):
        category = 'temporary'
    elif code in (401, 403):
        category = 'auth'
    elif code == 413:
        category = 'too_large'
    else:
        category = 'invalid'
    if category == 'daily_quota':
        retry = max(retry or 0, _daily_reset_seconds(provider) if provider == 'gemini' else 60)
    # Mensaje compacto: no repetir detalles potencialmente sensibles.
    labels = {'daily_quota':'cuota diaria agotada', 'rate_limit':'demasiadas consultas seguidas',
              'temporary':'servicio temporalmente no disponible', 'auth':'clave o acceso no autorizado',
              'invalid':'solicitud no aceptada', 'too_large':'contexto demasiado grande'}
    return ProviderFailure(f'{provider}: {labels[category]} (HTTP {code})',category,code,retry)


def candidate_configs(cfg):
    """Prioridad explícita: Gemini principal, otros modelos del MISMO proyecto, Groq.

    No se crean cuentas ni claves nuevas. Los límites de Gemini se aplican por
    proyecto/modelo; una credencial reemplazada no hereda el cooldown de otra.
    """
    result=[]
    primary=cfg.get('PROVIDER','gemini').lower()
    if primary == 'gemini' and cfg.get('GEMINI_API_KEY'):
        first=cfg.get('MODEL') or 'gemini-3.1-flash-lite'
        others=re.split(r'[,;\s]+',cfg.get('GEMINI_FALLBACK_MODELS',
                             'gemini-3.5-flash-lite,gemini-3.8-flash').strip())
        fingerprint=hashlib.sha256(cfg['GEMINI_API_KEY'].encode('utf-8')).hexdigest()[:12]
        for model in dict.fromkeys([first,*others]):
            if not re.fullmatch(r'gemini-[a-zA-Z0-9._-]+',model or ''):
                continue
            result.append(('gemini',dict(cfg,PROVIDER='gemini',MODEL=model,
                         _health_key=f'gemini:{model}:{fingerprint}')))
    if primary == 'openai_compatible' and cfg.get('OPENAI_API_KEY'):
        result.append(('openai_compatible',dict(cfg,PROVIDER='openai_compatible')))
    # Un presupuesto de prompt nuevo requiere reevaluar el fallo 413
    # anterior, pero nunca elimina cuotas reales de Gemini.
    groq_key=hashlib.sha256(cfg.get('GROQ_API_KEY','').encode('utf-8')).hexdigest()[:12]
    groq_model=cfg.get('GROQ_MODEL') or 'openai/gpt-oss-20b'
    groq_health_key=f'groq:{groq_model}:{groq_key}:compact-v2'
    if primary == 'groq' and cfg.get('GROQ_API_KEY'):
        result.append(('groq',dict(cfg,PROVIDER='groq',MODEL=groq_model,_health_key=groq_health_key)))
    backup=cfg.get('BACKUP_PROVIDER','groq').lower()
    if backup == 'groq' and primary != 'groq' and cfg.get('GROQ_API_KEY'):
        result.append(('groq',dict(cfg,PROVIDER='groq',MODEL=groq_model,_health_key=groq_health_key)))
    return result


def routing_signature(cfg):
    """Firma sin secretos: detectar cambios de clave/modelo y liberar esperas obsoletas."""
    identities=[]
    for name,pcfg in candidate_configs(cfg):
        key=pcfg.get('_health_key',name)
        if name!='gemini':
            secret=pcfg.get('GROQ_API_KEY' if name=='groq' else 'OPENAI_API_KEY','')
            key+=':'+hashlib.sha256(secret.encode('utf-8')).hexdigest()[:12]
        identities.append(key)
    return hashlib.sha256(json.dumps(identities).encode('utf-8')).hexdigest()


def configured(cfg):
    return bool(candidate_configs(cfg))


def _health(s, name):
    store=s.setdefault('provider_health',{})
    h=store.setdefault(name,{'cooldown_until':0,'consecutive_errors':0,'attempts_total':0,
                             'success_total':0,'failures_total':0,'today':'',
                             'attempts_today':0,'success_today':0,'failures_today':0,
                             'last_error':'','last_status':0,'last_success':0})
    day=datetime.now().strftime('%Y-%m-%d')
    if h.get('today')!=day:
        h.update(today=day,attempts_today=0,success_today=0,failures_today=0)
    return h


def _backoff(failure, h, name):
    prev=int(h.get('consecutive_errors',0))
    wait=failure.retry_after or 0
    if failure.category == 'daily_quota':wait=max(wait,_daily_reset_seconds(name)) if name=='gemini' else max(wait, 3600)
    elif failure.category == 'rate_limit':wait=max(wait,min(900, 60 * 2**min(prev,4)))
    elif failure.category == 'temporary':wait=max(wait,min(180, 20*2**min(prev,3)))
    elif failure.category == 'auth':wait=max(wait,3600)
    elif failure.category == 'too_large':wait=max(wait,900)
    else:wait=max(wait,600)
    return min(float(wait), 90000)


def route(cfg, state, lock, handler, purpose='deliberación', sleep=time.sleep):
    """handler(provider_cfg)-> result; validación incluida, para fallback ante JSON inválido.

    La red NO se ejecuta con el lock de SQLite tomado. El acceso a contadores sí.
    """
    candidates=candidate_configs(cfg)
    if not candidates:
        raise ProvidersUnavailable('No hay ninguna API configurada.',time.time()+300)
    now=time.time()
    tried=[]
    next_at=[]
    for name,pcfg in candidates:
        health_key=pcfg.get('_health_key',name)
        with lock:
            h=_health(state,health_key)
            ready=float(h.get('cooldown_until',0))
            if ready>now:
                next_at.append(ready)
                continue
        # Solo un reintento corto para fallos transitorios; no saturar al proveedor.
        for attempt in range(2):
            with lock:
                h=_health(state,health_key)
                h['attempts_total']+=1;h['attempts_today']+=1
            try:
                result=handler(pcfg)
            except ProviderFailure as exc:
                failure=exc
            except (urllib.error.URLError,TimeoutError,ConnectionError,OSError) as exc:
                failure=ProviderFailure(f'{name}: problema de conexión', 'temporary')
            except (ValueError,KeyError,TypeError,IndexError, json.JSONDecodeError) as exc:
                # Nunca persistir el texto crudo del LLM ni secretos; solo
                # enumerar fallas de contrato conocidas y la clase de fallo.
                detail='respuesta incompatible'
                if isinstance(exc,json.JSONDecodeError):
                    detail='JSON incompleto o inválido'
                elif isinstance(exc,ValueError):
                    safe={'La respuesta no es un objeto JSON.':'JSON no es objeto',
                          'El modelo no propuso acciones utilizables.':'sin acciones utilizables',
                          'El modelo no redactó una nota.':'sin entrada de cuaderno'}
                    detail=safe.get(str(exc),'respuesta incompatible')
                failure=ProviderFailure(f'{name}: {detail}','invalid')
            except Exception:
                failure=ProviderFailure(f'{name}: respuesta inesperada', 'invalid')
            else:
                with lock:
                    h=_health(state,health_key)
                    h['success_total']+=1;h['success_today']+=1
                    h['consecutive_errors']=0;h['cooldown_until']=0
                    h['last_error']='';h['last_status']=0
                    h['last_success']=time.time()
                    state['last_provider']=name
                    state['last_provider_model']=pcfg.get('MODEL','')
                    state['last_provider_purpose']=purpose
                return result,name,pcfg.get('MODEL','')
            with lock:
                h=_health(state,health_key)
                h['failures_total']+=1;h['failures_today']+=1
                h['last_error']=str(failure)[:130]
                h['last_status']=failure.status or 0
            # Un solo reintento rápido para 5xx/conexión, no para 429 ni validación.
            if attempt == 0 and failure.category == 'temporary':
                sleep(1 + random.random()*0.3)
                continue
            with lock:
                h=_health(state,health_key)
                wait=_backoff(failure,h,name)
                h['consecutive_errors']=int(h.get('consecutive_errors',0))+1
                h['cooldown_until']=time.time()+wait
                next_at.append(h['cooldown_until'])
            tried.append(str(failure))
            break
    # Sin opciones, respetar enfriamientos; no repetir en bucle cada segundo.
    earliest=min(next_at) if next_at else time.time()+180
    summary='; '.join(tried) or 'Todos los proveedores están en pausa temporal.'
    raise ProvidersUnavailable(summary, earliest)


def public_info(cfg,state):
    providers=candidate_configs(cfg)
    names=[n for n,_ in providers]
    summary=[]
    now=time.time()
    for name,pcfg in providers:
        health_key=pcfg.get('_health_key',name)
        h=_health(state,health_key)
        left=max(0,round(h.get('cooldown_until',0)-now))
        summary.append({'name':name,'health_key':health_key,'model':pcfg.get('MODEL',''),
                        'status':'en espera' if left else 'disponible',
                        'retry_seconds':left,'attempts':h['attempts_today'],
                        'successes':h['success_today'],'failures':h['failures_today'],
                        'last_error':h.get('last_error','')})
    active=state.get('last_provider','')
    return {'last_provider':active,'last_model':state.get('last_provider_model',''),
            'fallback_enabled':len(providers)>1,
            'providers':summary,'any_ready':any(p['status']=='disponible' for p in summary)}
