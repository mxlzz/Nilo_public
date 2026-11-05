"""Contratos operativos de Nilo: referencia única de interfaz y comprobaciones.

La descripción visible y los chequeos mecánicos parten de este módulo.
No es una acción del mundo. No proporciona propiedades ocultas ni recetas.
El verificador solo declara anomalías cuando puede contrastar un invariante
con hechos del estado: una prueba fallida nunca demuestra por sí sola un bug.
"""
from __future__ import annotations
import re

# Registro único de documentación, contratos verificables y duración.
from nilo_runtime.core.operations import (
    ACTION_GUIDE, COMMON_RULES, SUPPORTED_OPERATIONS,
    VERIFIABLE, get_spec, manual_lines,
)

def instructions():
    lines=['Operaciones disponibles (usar SOLO estas):']
    lines.extend(manual_lines())
    from capabilities import manifest
    lines.append('Capacidades físicas instaladas en esta versión:')
    for cap in manifest():
        lines.append(f"- {cap['id']} v{cap['version']}: métodos {', '.join(cap['methods'])}.")
    return '\n'.join(lines)+'\n'+COMMON_RULES

def summary():
    from capabilities import manifest
    return {'operaciones':list(ACTION_GUIDE),'capacidades_disponibles':manifest(),
            'regla':'Las condiciones y las consecuencias de cada operación se verifican contra hechos del motor. '
                    'Los rechazos normales no prueban errores; un fenómeno sin modelo permite proponer una ampliación.'}

def spec_for(op):
    try:
        registered=get_spec(op)
    except ValueError:
        return {'operacion':op,'descripcion':None,'contrato':None,
                'resultado':'conforme / uso_incorrecto / limitacion / posible_error / no_verificado'}
    return {'operacion':op,'descripcion':registered.description,
            'contrato':VERIFIABLE.get(op),
            'resultado':'conforme / uso_incorrecto / limitacion / posible_error / no_verificado',
            'duracion_prevista_minutos':registered.planned_minutes,
            'ejecutor':registered.executor,
            'requisitos_de_forma':list(registered.required_fields)}

def _object(world,person,requested):
    target=str(requested or '').strip().casefold()
    if not target:return None
    for item in person.get('items',[])+world.get('structures',[]):
        if str(item.get('id','')).casefold()==target or str(item.get('name','')).casefold()==target:
            return item
    return None

def before(world,person,step):
    """Fotografía mínima antes de ejecutar; jamás incluye claves ni secretos."""
    op=step.get('op','')
    target=(step.get('item') or step.get('object') or step.get('target')) if op in ('use','modify') else (step.get('target') or step.get('item') or step.get('object'))
    item=_object(world,person,target)
    own=(item in person.get('items',[])) if item else False
    pos=list(person.get('pos',[0,0,0]))
    visible=False
    if item and own:visible=True
    elif item and len(item.get('pos',[]))==3:
        ox,oy,oz=item['pos']
        visible=(oz==pos[2] and max(abs(ox-pos[0]),abs(oy-pos[1]))<=4
            and (f'{ox},{oy},{oz}' in world.get('revealed',[]) or
                 (ox,oy)==tuple(pos[:2])))
    requested=str(target or '').strip().casefold()
    # Solo es una expectativa fuerte cuando el objetivo identifica inequívocamente
    # una ficha existente. Los terrenos se resuelven por sus propias reglas.
    expected_inspect=(op=='inspect' and visible)
    if op=='inspect' and not expected_inspect:
        try:
            if 'x' in step and 'y' in step:
                tx,ty=int(step['x']),int(step['y'])
            else:
                match=re.search(r'[(\\[]\\s*(\\d{1,2})\\s*[,;]\\s*(\\d{1,2})\\s*[)\\]]',requested)
                tx,ty=(int(match.group(1)),int(match.group(2))) if match else (None,None)
            if tx is not None and 0<=tx<37 and 0<=ty<21 and max(abs(tx-pos[0]),abs(ty-pos[1]))<=4:
                known=f'{tx},{ty},{pos[2]}' in world.get('revealed',[])
                building=any(tuple(obj.get('pos',[]))==(tx,ty,pos[2]) for obj in world.get('structures',[]))
                expected_inspect=bool(known or building)
        except (TypeError,ValueError,KeyError):
            pass
    inventory=dict(person.get('inventory',{}))
    object_revisions={str(i.get('id')):i.get('revision',1)
                      for i in world.get('structures',[])+person.get('items',[])}
    return {'op':op,'target':requested,'expected_inspect':expected_inspect,
            'inventory':inventory,'structures':len(world.get('structures',[])),
            'items':len(person.get('items',[])),'revisions':object_revisions,
            'knowledge':list(person.get('knowledge',{}).keys()),
            'object_id':item.get('id') if item else None,
            'object_available':bool(item and (own or visible)),
            'position':pos}

def classify(world,person,step,prior,result):
    """Resultado estructurado de la ejecución, derivado de hechos, no de prosa."""
    op=step.get('op','')
    status=getattr(result,'status',None)
    success=bool(getattr(result,'success',False))
    data={'operation':op,'status':'no_verificado','code':'sin_regla_especifica',
          'expected':None,'observed':None,'evidence_kind':'contract_v1'}
    def mark(kind,code,expected,observed):
        data.update(status=kind,code=code,expected=expected,observed=observed)
        return data
    if status=='precondition_failed':
        return mark('uso_incorrecto','precondicion_no_satisfecha',
                    'Objetos, materiales, cantidad, proximidad y capacidad físicamente disponibles',
                    'El método no se ejecutó por una condición inválida. No demuestra fallo físico del recipiente.')
    if status=='no_evaluable':
        record=person.get('unmodeled_attempts',[])
        latest=record[-1] if record else {}
        data.update({'scope':latest.get('scope'),
                     'requested_method':latest.get('requested_method'),
                     'missing_effect_or_metric':latest.get('missing_effect_or_metric'),
                     'known_available_measures':latest.get('known_available_measures',[]),
                     'evidence_id':latest.get('id'),
                     'interpretation_limits':latest.get('interpretation_limits')})
        return mark('limitacion','fisica_no_implementada',
                    'La operación solo evalúa fenómenos físicos representados',
                    'El motor ha señalado que la física de este fenómeno no está implementada.')
    if op not in VERIFIABLE:return data
    if op=='interact':
        if not success:
            return mark('no_verificado','interaccion_no_completada',
                        'Solo se ejecutan operaciones físicas viables',
                        'No hubo intercambio de materiales.')
        physical=getattr(result,'physical',None) or {}
        proof=physical.get('conditions') or {}
        amount=proof.get('quantity')
        if physical.get('kind')!='capability' or not isinstance(amount,(int,float)) or amount<=0:
            return mark('posible_error','intercambio_sin_evidencia',
                        'Toda transferencia exitosa requiere cantidad real registrada',
                        {'evidencia':physical})
        if proof.get('method')=='transferir':
            old=proof.get('before') or {}
            new=proof.get('after') or {}
            if (not all(k in old and k in new for k in ('source','destination')) or
                abs((old.get('source',0)+old.get('destination',0))-
                    (new.get('source',0)+new.get('destination',0)))>0.001):
                return mark('posible_error','transferencia_no_conservativa',
                            'Los balances del origen y destino deben conservar la suma',
                            {'antes':old,'despues':new})
        if proof.get('method')=='probar_carga':
            return mark('conforme','carga_estatica_ensayada',
                        'El ensayo informa si los materiales reales fueron soportados',
                        {'cantidad':amount,'soportado':proof.get('supported'),
                         'limite_medido':proof.get('limit'),'revision':proof.get('revision')})
        return mark('conforme','intercambio_verificado',
                    'La capacidad aporta un efecto físico medido',
                    {'cantidad':amount,'capacidad':proof.get('capability'),'version':proof.get('version')})
    if op=='inspect':
        if prior.get('expected_inspect'):
            return mark('conforme' if success else 'posible_error',
                'objeto_disponible' if success else 'inspeccion_contradictoria',
                'Un objeto registrado, visible y al alcance puede inspeccionarse',
                'Inspección exitosa' if success else 'El motor rechazó una inspección que cumple esas condiciones.')
        if not success:return mark('uso_incorrecto','objetivo_no_observable',
                'Un ID existente y visible, o un terreno observado dentro del alcance',
                'No se encontró el objetivo en las condiciones indicadas; no significa que haya desaparecido.')
    elif op=='gather':
        from world import gather_material
        requested=gather_material(step.get('target'))
        if requested is None:return mark('uso_incorrecto','material_desconocido',
            'Usar un material o un depósito admitido para gather','El objetivo no corresponde a un recurso admitido.')
        diff=person.get('inventory',{}).get(requested,0)-prior.get('inventory',{}).get(requested,0)
        unexpected={k:person.get('inventory',{}).get(k,0)-prior['inventory'].get(k,0)
                    for k in person.get('inventory',{}) if k!=requested
                    and person.get('inventory',{}).get(k,0)>prior['inventory'].get(k,0)}
        if success and (diff<=0 or unexpected):return mark('posible_error','recoleccion_inconsistente',
            f'Si gather informa extracción de {requested}, aumenta solo ese recurso',
            {'incremento_solicitado':diff,'otros_incrementos':unexpected})
        if success:return mark('conforme','extraccion_verificada',f'Incrementar {requested}',{'incremento':diff})
        return mark('uso_incorrecto','extraccion_no_completada',
            'Fuente alcanzable con recursos y extracción completada','La extracción no se completó.')
    elif op=='build':
        if success:
            changes=(len(world.get('structures',[]))-prior['structures'],
                     len(person.get('items',[]))-prior['items'])
            if max(changes)<=0:return mark('posible_error','construccion_sin_objeto',
                'Una fabricación exitosa incorpora un objeto material al mundo o inventario',
                {'obras_nuevas':changes[0],'objetos_nuevos':changes[1]})
            return mark('conforme','construccion_materializada','Crear una obra u objeto nuevo',changes)
        return mark('uso_incorrecto','construccion_rechazada',
            'Recursos y espacio físicamente disponibles','La construcción no cumplió alguna condición de ejecución.')
    elif op=='modify':
        if success:
            rid=prior.get('object_id')
            obj=_object(world,person,rid)
            old_rev=prior.get('revisions',{}).get(str(rid),1)
            if obj is not None and obj.get('revision',1)<=old_rev:
                return mark('posible_error','modificacion_sin_revision',
                    'Una modificación exitosa incrementa la revisión del objeto',
                    {'id':rid,'revision_anterior':old_rev,'revision_actual':obj.get('revision',1)})
            return mark('conforme','modificacion_registrada',
                'Una modificación material debe actualizar la versión del objeto',
                {'id':rid,'revision_actual':obj.get('revision') if obj else None})
        return mark('uso_incorrecto','modificacion_rechazada',
            'Objeto, componentes, proximidad y materiales adecuados',
            'La intervención no cumple las condiciones de modificación.')
    elif op=='use':
        if success and not prior.get('object_available'):
            return mark('posible_error','uso_sin_herramienta',
                'Una prueba real requiere una herramienta disponible','La operación informó éxito sin objeto accesible.')
        if not success and not prior.get('object_available'):
            return mark('uso_incorrecto','herramienta_no_disponible',
                'Herramienta identificable y al alcance','No hay objeto utilizable identificado.')
        return mark('conforme' if success else 'no_verificado',
                    'prueba_registrada' if success else 'resultado_fisico_negativo',
                    'El éxito depende de materiales, forma y condiciones',
                    'El resultado físico de esta prueba no demuestra por sí solo una anomalía.')
    elif op=='experiment':
        target=str(step.get('target','')).casefold()
        has_sample=any(q>0 and m in target for m,q in prior.get('inventory',{}).items())
        method=str(step.get('method') or 'golpear').casefold()
        represented=method in ('golpear','calentar','mojar','cargar','luz')
        if not has_sample:return mark('uso_incorrecto','muestra_ausente',
            'Disponer del material a ensayar','No había muestra en inventario.')
        if not represented:return mark('limitacion','metodo_sin_modelo',
            'Solo los métodos documentados tienen interpretación física',
            f'El método {method} no está representado.')
        return mark('conforme' if success else 'no_verificado',
                    'ensayo_registrado' if success else 'ensayo_sin_resultado',
                    'Registrar una observación del ensayo','La operación no fue necesariamente una comprobación numérica.')
    return data
