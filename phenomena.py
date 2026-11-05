"""Frontera explícita entre ensayos fallidos y fenómenos no simulados.

No da agua ni concede efectos por el nombre de una herramienta.
"""
import unicodedata
from nilo_runtime.core.identity import new_uuid
import uuid


def _normalize(value):
    txt=unicodedata.normalize('NFKD', str(value or '').casefold())
    return ''.join(c for c in txt if not unicodedata.combining(c))


def missing_physics(step):
    op=str(step.get('op','')).lower()
    if op not in ('use','experiment'):
        return None
    method=_normalize(step.get('method') or step.get('action'))
    target=_normalize(step.get('target'))
    # Los métodos disponibles se definen explícitamente; las palabras del objetivo
    # solo precisan alcance de fenómenos conocidos que aún carecen de modelo.
    supported={
        'experiment': {'golpear','calentar','mojar','cargar','luz',''},
        'use': {'llenar','contener','flotar','navegar','excavar','golpear',
                'cortar','mover','transmitir_movimiento','transmision',
                'resistir_carga','carga','load','input_energy'}
    }
    thermal=('condens','evapor','destil','humedad','rocio','purific','filtr')
    if any(k in method for k in thermal) or (
          op=='experiment' and any(k in target for k in thermal)):
        return {'phenomenon':'Evaporación y condensación de agua',
                'missing_capability':'Esta operación no calcula condensación, evaporación, purificación, filtración ni cambios de fase. La prueba de calentar solo estima combustibilidad.',
                'missing_effect_or_metric':str(step.get('method') or step.get('target') or '')[:95],
                'known_available_measures':['combustibilidad cualitativa' if op=='experiment' else 'contención y flotación cuando correspondan'],
                'scope':'procedimiento puntual; no invalida otros resultados del objeto',
                'test':'Proponer una prueba con medición verificable, sin atribuir resultados al objeto.'}
    if method and method not in supported[op]:
        return {'phenomenon':str(step.get('method'))[:95],
                'missing_capability':'No existe un método físico registrado para evaluar este procedimiento.',
                'missing_effect_or_metric':str(step.get('method'))[:95],
                'known_available_measures':[],
                'scope':'método solicitado; no demuestra ineptitud del objeto',
                'test':'Proponer variables medibles y comprobaciones antes de ampliar el motor.'}
    return None


def record_unmodeled(person,step,missing,stamp):
    entries=person.setdefault('unmodeled_attempts',[])
    entry={'id':'no-modelo-'+new_uuid().hex[:10], 'when':stamp,
           'op':str(step.get('op',''))[:30],
           'target':str(step.get('item') or step.get('target') or '')[:120],
           'method':str(step.get('method') or step.get('action') or '')[:95],
           'phenomenon':missing['phenomenon'],
           'missing_capability':missing['missing_capability'],
           'test':missing['test'],
           'result':'no_evaluable', 'position':list(person.get('pos',[])),
           'scope':missing.get('scope','procedimiento solicitado'),
           'requested_method':str(step.get('method') or step.get('action') or '')[:95],
           'missing_effect_or_metric':missing.get('missing_effect_or_metric',missing['phenomenon']),
           'known_available_measures':missing.get('known_available_measures',[]),
           'verified_preconditions':missing.get('verified_preconditions',[]),
           'interpretation_limits':'Un método no evaluable no demuestra fracaso físico del objeto.'}
    entries.append(entry)
    return entry


def no_model_message(entry):
    return ('FÍSICA NO IMPLEMENTADA: no puedo evaluar '+entry['phenomenon']+'. '
            +entry['missing_capability']+' No observé un fracaso físico ni obtuve agua. '
            +'Intento registrado: '+entry['id']+'. Puedo solicitar una ampliación fundamentada.')
