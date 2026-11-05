"""Necesidades corporales simplificadas; ciclos y rutinas deterministas independientes del LLM.

Las reservas se miden en 0..100. No se simulan lesiones ni muertes todavía:
se registran penalizaciones graduales, recuperables, y riesgos comprobables.
"""
from __future__ import annotations

import math
from .policy import body_strained

NEEDS_DEFAULT = {'hidratacion': 82.0, 'nutricion': 78.0, 'energia': 90.0, 'abrigo': 80.0, 'seguridad': 68.0}


def ensure_needs(person):
    n = person.setdefault('needs', {})
    for key, value in NEEDS_DEFAULT.items():
        n.setdefault(key, value)
    person.setdefault('needs_last_minute', float(person.get('clock_minutes', 0)))
    person.setdefault('routine_log', [])
    return n


def _clamp(value):
    if isinstance(value,bool):
        raise ValueError("Reserva corporal booleana inválida.")
    value=float(value)
    if not math.isfinite(value):
        raise ValueError("La reserva corporal debe ser finita.")
    return round(max(0.0,min(100.0,value)),2)


def update_needs(person, world, elapsed_minutes, at_shelter=False, near_water=False,
                 active=False, resting=False, legacy_energy_cap=False,
                 legacy_autocare=False, *, waiting=False, legacy_record=None):
    """Evolución continua, con diferencia entre reposo planificado e inactividad.

    No inventar alimento: comer solo si existe inventario; bebida desde orilla
    accesible o recipiente verificado. Auto-descanso solo fuera de acciones.
    """
    if isinstance(elapsed_minutes,bool):
        raise ValueError("Tiempo corporal inválido.")
    duration=float(elapsed_minutes)
    if not math.isfinite(duration):
        raise ValueError("El tiempo corporal debe ser finito.")
    dt = max(0.0,min(duration,1440.0))/60.0
    if dt <= 0:return []
    n = ensure_needs(person)
    # Prevalidar todas las reservas antes del primer cambio.
    for field in NEEDS_DEFAULT:
        _clamp(n[field])
    before = {k: n[k] for k in n}
    rates = {'hidratacion':.55, 'nutricion':.32, 'energia':1.15 if active else .4,
             'abrigo':0.0, 'seguridad':0.0}
    for k, rate in rates.items():n[k] = _clamp(n[k] - dt * rate)
    events = []
    # Autoconsumo previo reservado a reproducir reglas históricas.
    if legacy_autocare:
        if n['hidratacion'] <= 45:
            vessel = next((it for it in person.get('items',[]) if it.get('contents',{}).get('material')=='agua'
                           and it.get('contents',{}).get('quantity',0) >= .18), None)
            if vessel:
                vessel['contents']['quantity'] = round(max(0,vessel['contents']['quantity']-.18),2)
                n['hidratacion'] = _clamp(n['hidratacion']+27)
                events.append('Bebí parte del agua que había conseguido almacenar.')
                if legacy_record is not None:
                    legacy_record(person,'drink','Rutina',autonomous=True)
            elif near_water:
                # Agua disponible no equivale a agua segura. Solo recupera parcialmente
                # sin tratamiento; esto registra la incertidumbre sanitaria.
                n['hidratacion'] = _clamp(n['hidratacion']+23)
                events.append('Bebí agua de una fuente cercana; todavía desconozco su calidad.')
                if legacy_record is not None:
                    legacy_record(person,'drink','Rutina',autonomous=True)
        if n['nutricion'] <= 45 and person.get('inventory',{}).get('alimento',0) >= 1:
            person['inventory']['alimento'] -= 1
            n['nutricion'] = _clamp(n['nutricion']+36)
            events.append('Comí una porción de alimento almacenado.')
            if legacy_record is not None:
                legacy_record(person,'eat','Rutina',autonomous=True)
    if not active and not (waiting and not legacy_autocare and not legacy_energy_cap) and (n['energia'] <= 75 if legacy_energy_cap else n['energia'] < 100):
        # El reposo explícito recupera mucho más que una espera inactiva.
        # Evita confundir deliberaciones, escritura o espera API con un ensayo de descanso.
        hourly = (11 if at_shelter else 7) if resting else 1.2
        n['energia'] = _clamp(n['energia'] + dt * hourly)
        if before['energia']<40 <= n['energia']:
            events.append('Descansé y recuperé energía.')
    # Sin clima ni amenazas modelados, el abrigo y la seguridad no se consumen
    # automáticamente ni se regeneran mágicamente por entrar en un refugio.
    # El refugio sí conserva su ventaja de descanso energético.
    person['strain'] = body_strained(n)
    return events


def _sensation_level(reserve):
    """Sensación presente de sed/hambre: no una instrucción de autocuidado."""
    if reserve >= 90: return 'ninguna'
    if reserve >= 60: return 'normal_sin_urgencia'
    if reserve >= 30: return 'progresiva'
    if reserve >= 15: return 'intensa'
    return 'critica'


def _fatigue_sensation(energy, unconscious=False):
    """Coherente con tensión corporal <12 y colapso involuntario <=5."""
    if unconscious or energy <= 5: return 'inconsciente'
    if energy < 12: return 'tension_corporal'
    if energy < 30: return 'intensa'
    if energy < 60: return 'progresiva'
    if energy < 90: return 'normal_sin_urgencia'
    return 'ninguna'


def needs_summary(person):
    # Una consulta de lectura no completa reservas ni registros persistidos.
    raw=person.get('needs') or {}
    n=dict(raw) if isinstance(raw,dict) else {}
    for key,default in NEEDS_DEFAULT.items():
        n.setdefault(key,default)
    return {'valores': dict(n), 'criticas':([k for k in ('hidratacion','nutricion') if n[k] < 15]
                        + (['energia'] if n['energia'] <= 5 else [])),
            'tension_corporal':bool(person.get('strain')),
            'sensaciones':{
                'sed':_sensation_level(n['hidratacion']),
                'hambre':_sensation_level(n['nutricion']),
                'cansancio':_fatigue_sensation(n['energia'],bool(person.get('unconscious')))
            }}


# La percepción usada para decidir no expone el estado numérico del motor.
# Los intervalos siguen siendo internos; el observador conserva needs_summary().
_HUNGER_WORDS = {
    'ninguna':'completamente saciado',
    'normal_sin_urgencia':'sin hambre',
    'progresiva':'algo de hambre',
    'intensa':'mucha hambre',
    'critica':'hambre extrema'
}
_THIRST_WORDS = {
    'ninguna':'bien hidratado',
    'normal_sin_urgencia':'sin sed',
    'progresiva':'algo de sed',
    'intensa':'mucha sed',
    'critica':'sed extrema'
}
_FATIGUE_WORDS = {
    'ninguna':'con mucha energía',
    'normal_sin_urgencia':'descansado',
    'progresiva':'algo cansado',
    'intensa':'muy cansado',
    'tension_corporal':'agotamiento severo',
    'inconsciente':'inconsciente'
}


def perceived_needs(person):
    """Estados cualitativos disponibles para Nilo, sin valores ni umbrales.

    Función sin efectos físicos ni migración de partidas. No prohíbe acciones
    voluntarias de autocuidado y deja las cifras al registro experimental.
    """
    summary=needs_summary(person)
    sensations=summary['sensaciones']
    result={
        'alimentacion':_HUNGER_WORDS[sensations['hambre']],
        'hidratacion':_THIRST_WORDS[sensations['sed']],
        'energia':_FATIGUE_WORDS[sensations['cansancio']]
    }
    if summary['tension_corporal']:
        result['señal_adicional']='tensión corporal presente'
    return result
