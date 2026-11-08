"""Parseo y validación de decisiones emitidas por LLM, sin acceso a red.

Las precondiciones de forma provienen del registro de operaciones. La
ejecución física se valida fuera de esta capa y puede rechazar intenciones.
"""
from __future__ import annotations

import json
import re

from nilo_runtime.core.operations import registered_operations, validate_operation
from research_cycle import normalize_prediction

def parse_json(text):
    text=text.strip()
    if text.startswith('```'):
        text=re.sub(r'^```(?:json)?\s*','',text)
        text=re.sub(r'\s*```$','',text)
    return json.loads(text)


def _optional_text(value, limit):
    """Un null del proveedor es ausencia; no debe persistirse como 'None'."""
    return str("" if value is None else value).strip()[:limit]


def normalize_decision(raw,legacy_rest=False):
    if not isinstance(raw,dict):raise ValueError('La respuesta no es un objeto JSON.')
    ops=set(registered_operations())
    steps=raw.get('plan',[])
    if not isinstance(steps,list):
        raise ValueError('El plan debe ser una lista JSON.')
    plan=[]
    for s in steps[:12]:
        if isinstance(s,dict) and str(s.get('op','')).lower() in ops:
            # La lectura de saves/replays antiguos conserva sus propios
            # contratos; los planes nuevos pasan por la misma verificación
            # de forma que usa el planificador y el despacho físico.
            if not legacy_rest and not validate_operation(s).valid:
                continue
            s=dict(s);s['op']=s['op'].lower()
            if s['op']=='explore':
                # Normalizar alias, sin reemplazar dirección inválida por explore
                # genérico ni revelar al LLM posiciones que desconoce.
                from world import EXPLORATION_DIRECTIONS
                if 'direction' in s and s['direction'] is not None:
                    direction=EXPLORATION_DIRECTIONS.get(str(s['direction']).casefold().strip())
                    if direction:s['direction']=direction
                if isinstance(s.get('region'),dict):
                    region=s['region']
                    try:
                        rx,ry=int(region['x']),int(region['y'])
                        s['region']={'x':rx,'y':ry}
                    except (ValueError,TypeError,KeyError,OverflowError):
                        pass  # Se devuelve el diagnóstico físico, no una exploración ciega.
            if s['op']=='go' and str(s.get('target','')).strip().lower() not in ('agua','orilla','costa','rio','río','lago'):
                try:s['x']=int(s['x']);s['y']=int(s['y'])
                except (ValueError,KeyError,TypeError):continue
            if s['op'] in ('rest','wait') and (s['op']=='wait' or not legacy_rest):
                from bodily_policy import rest_minutes
                minutes=rest_minutes(s)
                if minutes is None:continue
                s['minutes']=minutes
            if "prediction" in s:
                if s["op"] == "design":
                    # La ficha documenta texto libre; no es un ensayo medible.
                    prediction = s["prediction"]
                    if not isinstance(prediction, str) or not prediction.strip():
                        s.pop("prediction", None)
                    else:
                        s["prediction"] = prediction.strip()[:450]
                else:
                    prediction=normalize_prediction(s.get("prediction"))
                    if prediction is None or s["op"] not in {"experiment","use","rest","craft","build","assemble","modify","combine","excavate"}:
                        s.pop("prediction",None)
                    else:s["prediction"]=prediction
            plan.append(s)
    action=_optional_text(raw.get('accion_proyecto') or 'nuevo', 40).lower()
    if action not in ('nuevo','continuar','completar','abandonar','pausar','sin_proyecto'):action='nuevo'
    if not plan and action not in ('completar','abandonar','pausar'):
        raise ValueError('El modelo no propuso acciones utilizables.')
    note=_optional_text(raw.get('cuaderno'), 350)
    if not note:raise ValueError('El modelo no redactó una nota.')
    try:advance=int(raw.get('avance_estimado',0))
    except (ValueError,TypeError):advance=0
    try:review=int(raw.get('revisar_en_minutos',90))
    except (ValueError,TypeError):review=90
    subgoals=raw.get('subobjetivos',[])
    if not isinstance(subgoals,list):subgoals=[]
    subgoals=[str(q).strip()[:110] for q in subgoals[:6] if isinstance(q,str) and q.strip()]
    return {"subobjetivos":subgoals,"cuaderno":note,"pregunta":_optional_text(raw.get('pregunta'), 220),"hipotesis":_optional_text(raw.get('hipotesis'), 240),
            "objetivo":_optional_text(raw.get('objetivo'), 240),"motivo":_optional_text(raw.get('motivo'), 200),"plan":plan,
            "revisar_en_minutos":max(30,min(240,review)),"proyecto_id":_optional_text(raw.get('proyecto_id'), 50),
            "actividades_en_espera":raw.get("actividades_en_espera") if isinstance(raw.get("actividades_en_espera"),list) else None,
            "agenda":raw.get("agenda",[]) if isinstance(raw.get("agenda"),list) else [],
            "accion_proyecto":action,"prueba_cierre":_optional_text(raw.get('prueba_cierre'), 220),"avance_estimado":max(0,min(100,advance)),"estado_actual":_optional_text(raw.get('estado_actual'), 240)}


