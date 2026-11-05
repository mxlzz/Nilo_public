"""Necesidades corporales simplificadas; ciclos y rutinas deterministas independientes del LLM.

Las reservas se miden en 0..100. No se simulan lesiones ni muertes todavía:
se registran penalizaciones graduales, recuperables, y riesgos comprobables.
"""
from __future__ import annotations

NEEDS_DEFAULT = {'hidratacion': 82.0, 'nutricion': 78.0, 'energia': 90.0, 'abrigo': 80.0, 'seguridad': 68.0}


def ensure_needs(person):
    n = person.setdefault('needs', {})
    for key, value in NEEDS_DEFAULT.items():
        n.setdefault(key, value)
    person.setdefault('needs_last_minute', float(person.get('clock_minutes', 0)))
    person.setdefault('routine_log', [])
    return n


def _clamp(value):
    return round(max(0.0, min(100.0, float(value))), 2)


def update_needs(person, world, elapsed_minutes, at_shelter=False, near_water=False, active=False, resting=False, legacy_energy_cap=False, legacy_autocare=False):
    """Evolución continua, con diferencia entre reposo planificado e inactividad.

    No inventar alimento: comer solo si existe inventario; bebida desde orilla
    accesible o recipiente verificado. Auto-descanso solo fuera de acciones.
    """
    n = ensure_needs(person)
    dt = max(0.0, min(float(elapsed_minutes), 1440.0)) / 60.0
    if dt <= 0: return []
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
                from motivation import record_maintenance
                record_maintenance(person,'drink','Rutina',autonomous=True)
            elif near_water:
                # Agua disponible no equivale a agua segura. Solo recupera parcialmente
                # sin tratamiento; esto registra la incertidumbre sanitaria.
                n['hidratacion'] = _clamp(n['hidratacion']+23)
                events.append('Bebí agua de una fuente cercana; todavía desconozco su calidad.')
                from motivation import record_maintenance
                record_maintenance(person,'drink','Rutina',autonomous=True)
        if n['nutricion'] <= 45 and person.get('inventory',{}).get('alimento',0) >= 1:
            person['inventory']['alimento'] -= 1
            n['nutricion'] = _clamp(n['nutricion']+36)
            events.append('Comí una porción de alimento almacenado.')
            from motivation import record_maintenance
            record_maintenance(person,'eat','Rutina',autonomous=True)
    if not active and (n['energia'] <= 75 if legacy_energy_cap else n['energia'] < 100):
        # El reposo explícito recupera mucho más que una espera inactiva.
        # Evita confundir deliberaciones, escritura o espera API con un ensayo de descanso.
        hourly = (11 if at_shelter else 7) if resting else 1.2
        n['energia'] = _clamp(n['energia'] + dt * hourly)
        if before['energia']<40 <= n['energia']:
            events.append('Descansé y recuperé energía.')
    # Sin clima ni amenazas modelados, el abrigo y la seguridad no se consumen
    # automáticamente ni se regeneran mágicamente por entrar en un refugio.
    # El refugio sí conserva su ventaja de descanso energético.
    if n['hidratacion'] < 15 or n['nutricion'] < 12 or n['energia'] < 12:
        person['strain'] = True
    else:person['strain'] = False
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
    n = ensure_needs(person)
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
