"""Cuaderno técnico y solicitudes auditables, sin ejecutar código externo.

Aprobar un fenómeno es autorización editorial, no una implementación física:
solo el código verificado del motor puede producir cambios en el mundo.
"""
from __future__ import annotations
import uuid
from action_contracts import SUPPORTED_OPERATIONS
from diagnostic_support import select_physics_evidence, select_debug_evidence


def ensure_records(person):
    person.setdefault('designs', [])
    person.setdefault('proposals', [])
    person.setdefault('action_outcomes', [])
    person.setdefault('experience_summary', [])
    person.setdefault('life_history', [])
    person.setdefault('life_chapters', {})
    person.setdefault('preferences', {'explorar':.55,'inventar':.50,'investigar':.55,'seguridad':.55})
    return person


def _str(value, maximum=450):return str(value or '').strip()[:maximum]


def register_design(person, step, stamp):
    ensure_records(person)
    name=_str(step.get('name'),90)
    purpose=_str(step.get('purpose'),300)
    basis=_str(step.get('principle'),650)
    if not name or not purpose or not basis:
        return False, 'Faltan nombre, propósito o fundamento verificable del diseño.'
    parts=step.get('components',[])
    if not isinstance(parts,list) or not (1<=len(parts)<=12):
        return False, 'El diseño necesita entre uno y doce componentes descritos.'
    components=[]
    for part in parts:
        if not isinstance(part,dict):continue
        pname=_str(part.get('name'),70);material=_str(part.get('material'),65)
        if pname:components.append({'name':pname,'material':material,'function':_str(part.get('function'),170),
                                     'connection':_str(part.get('connection'),170)})
    if not components:return False,'No se pudo identificar ningún componente.'
    did=_str(step.get('design_id'),40)
    prior=next((d for d in person['designs'] if d['id']==did),None) if did else None
    if not prior and len(person['designs'])>=300:
        return False,'Se alcanzó el límite de fichas; deben archivarse antes de crear más.'
    if prior:
        version=prior['versions'][-1]['version']+1
    else:
        prior={'id':'inv-'+uuid.uuid4().hex[:10],'name':name,'created':stamp,'versions':[],
               'tests':[],'status':'hipotesis','verified':False}
        person['designs'].append(prior);version=1
    prior['name']=name;prior['updated']=stamp
    source=step.get('_journal_id')
    if isinstance(source,str) and source:
        links=prior.setdefault('journal_ids',[])
        if source not in links:links.append(source)
        del links[:-50]
    prior['versions'].append({'version':version,'when':stamp,'purpose':purpose,'principle':basis,
         'components':components,'procedure':_str(step.get('procedure'),900),
         'prediction':_str(step.get('prediction'),450),'expected_test':_str(step.get('expected_test'),80),'requirements':_str(step.get('requirements'),450)})
    prior['versions']=prior['versions'][-20:]
    prior['status']='en desarrollo' if prior['tests'] else 'hipotesis'
    prior['verified']=False if version>1 else prior['verified']
    return True, f"Documenté el diseño '{name}' (versión {version}, referencia {prior['id']}). Sigue siendo una hipótesis hasta que lo pruebe."


def design_materials_error(person, design_id, materials):
    """Un vínculo físico exige igual balance de insumos; no verifica las uniones."""
    from collections import Counter
    design=next((d for d in person.get('designs',[]) if d.get('id')==design_id),None)
    if not design or not design.get('versions'):
        return 'No existe una ficha de diseño vigente con ese design_id.'
    version=design['versions'][-1]
    planned=[str(c.get('material') or '').strip().casefold()
             for c in version.get('components',[]) if isinstance(c,dict)]
    actual=[str(m or '').strip().casefold() for m in materials]
    if not planned or any(not m for m in planned):
        return 'La ficha de diseño no identifica los materiales de todas sus piezas.'
    if Counter(planned)!=Counter(actual):
        def describe(counts):
            return ', '.join(f'{m} ×{q}' for m,q in sorted(counts.items())) or 'ninguno'
        return (f"El diseño '{design.get('name',design_id)}' versión "
                f"{version.get('version','?')} documenta {describe(Counter(planned))}, "
                f"pero la fabricación consume {describe(Counter(actual))}. "
                'Puedo corregir la ficha o fabricar sin design_id. No consumí materiales.')
    return None


def _design_function_matches(purpose, method, expected_test):
    """Coincidencia conservadora de propósito declarado y método físico real."""
    import unicodedata
    def plain(s):
        return ''.join(c for c in unicodedata.normalize('NFKD',str(s or '').casefold())
                       if not unicodedata.combining(c))
    actual=plain(method)
    expected=plain(expected_test)
    if expected:
        return actual==expected
    goal=plain(purpose)
    tokens={
        'excavar':('excav','perfor'),
        'cortar':('cort','talar'),
        'golpear':('golpe','impact','fractur'),
        'contener':('conten','almacen','guardar'),
        'llenar':('conten','almacen','guardar'),
        'flotar':('flot'),
        'navegar':('naveg','transport'),
        'mover':('mover','desplaz','palanca'),
        'transmision':('transmit','movimiento'),
        'transmitir_movimiento':('transmit','movimiento'),
        'carga':('carga','resist'),
        'resistir_carga':('carga','resist'),
    }
    return any(word in goal for word in tokens.get(actual,()))


def record_design_test(person,step,success,results,stamp,measurement_id=None,
                       *,measurement=None,world=None,notable=None):
    """Relaciona un artefacto real y ensayos pertinentes, sin atribuir funciones inventadas.

    Un diseño histórico no se vincula retroactivamente a un objeto por parecido de nombre.
    El método declarado es opcional, pero la función solo se reconoce cuando el efecto
    está documentado y la pieza física lleva el design_id verificable.
    """
    ensure_records(person)
    op=step.get('op')
    material_id=_str(step.get('design_id'),40)
    object_id=_str(step.get('_built_object_id') or step.get('_used_tool_id'),90)
    objects=list(person.get('items',[]))+(list((world or {}).get('structures',[])))
    if op=='rest' and measurement and measurement.get('condition')=='refugio':
        position=(measurement.get('start') or {}).get('position')
        structure=next((b for b in (world or {}).get('structures',[])
                        if b.get('pos')==position and b.get('category')=='habitaculo'
                        and b.get('shelter_condition')!='insuficiente' and b.get('design_id')),None)
        if not structure:return None
        material_id=structure['design_id']
        object_id=structure['id']
    elif op=='use':
        requested=str(step.get('item') or '').strip().casefold()
        tool=next((o for o in person.get('items',[]) if requested and
                   (str(o.get('id','')).casefold()==requested or str(o.get('name','')).casefold()==requested)),None)
        if not tool:return None
        object_id=tool.get('id')
        material_id=tool.get('design_id') or material_id
        # Una etiqueta design_id declarada no acredita por sí sola asociación física.
        if not tool.get('design_id') or tool.get('design_id')!=material_id:return None
    elif op=='excavate':
        tool=next((o for o in person.get('items',[]) if o.get('id')==object_id),None)
        if not tool or not tool.get('design_id'):return None
        material_id=tool['design_id']
    if not material_id:return None
    # Una acción resuelta sin nuevo efecto observable no verifica otra vez una función.
    if op in ('use','excavate') and notable is False:return None
    design=next((d for d in person['designs'] if d['id']==material_id),None)
    if not design:return None
    version=design.get('versions',[])[-1] if design.get('versions') else {}
    if op in ('use','excavate','rest'):
        actual=next((o for o in objects if o.get('id')==object_id),None)
        if actual is None or actual.get('design_version',1)!=version.get('version',1):
            return None
    if op in ('craft','build','assemble','modify'):
        obj=next((o for o in objects if o.get('id')==object_id and
                  o.get('design_id')==material_id),None)
        if obj is None:return None
        linked=design.setdefault('linked_object_ids',[])
        if object_id not in linked:linked.append(object_id)
    elif op in ('use','excavate'):
        obj=next((o for o in objects if o.get('id')==object_id and
                  o.get('design_id')==material_id),None)
        if obj is None or not success:return None
        method=str(step.get('method') or ('excavar' if op=='excavate' else '')).casefold()
        trial=next((t for t in reversed(obj.get('tests',[]))
                    if t.get('method')==method and t.get('success') is True and
                    t.get('revision',1)==obj.get('revision',1)),None)
        if trial is None:return None
    else:
        obj=next((o for o in objects if o.get('id')==object_id and
                  o.get('design_id')==material_id),None)
        if op!='rest' or obj is None:return None

    verified_function=None
    if op in ('use','excavate') and success and measurement and measurement.get('success'):
        method=str(step.get('method') or ('excavar' if op=='excavate' else '')).casefold()
        if _design_function_matches(version.get('purpose'),method,version.get('expected_test')):
            verified_function=method
    elif op=='rest' and success and measurement:
        energy=(measurement.get('needs_delta') or {}).get('energia',0)
        if energy>0 and measurement.get('start',{}).get('sheltered'):
            verified_function='recuperacion_bajo_cubierta'
    if not verified_function and op=='rest':return None
    entry={'when':stamp,'op':op,'success':bool(success),
           'evidence':_str('; '.join(str(t) for t in results),600),
           'verified_function':bool(verified_function),'function':verified_function,
           'object_id':object_id,'design_version':version.get('version',1)}
    if isinstance(measurement_id,str) and measurement_id:
        entry['measurement_id']=measurement_id
    if any(t.get('measurement_id')==measurement_id and t.get('op')==op
           for t in design.get('tests',[]) if measurement_id):return design
    design['tests'].append(entry)
    design['tests']=design['tests'][-150:]
    if verified_function:
        functions=design.setdefault('verified_functions',[])
        if not any(f.get('name')==verified_function and
                   f.get('design_version')==version.get('version',1) for f in functions):
            functions.append({'name':verified_function,'measurement_id':measurement_id,
                              'object_id':object_id,'design_version':version.get('version',1),
                              'when':stamp})
        # Una recuperación bajo cubierta no demuestra seguridad ni que el refugio
        # mejora el descanso respecto del exterior.
        if verified_function=='recuperacion_bajo_cubierta':
            design['status']='funcion parcialmente comprobada'
            design['verified']=False
        else:
            design['status']='funcion comprobada'
            design['verified']=True
    elif success and op in ('craft','build','assemble','modify'):
        design['status']='prototipo construido'
    elif success:
        if not design.get('verified'):
            design['status']='uso parcial comprobado'
    else:
        if not design.get('verified'):
            design['status']='revisión necesaria'
    return design


def submit_proposal(person,step,stamp,available_physics):
    ensure_records(person)
    phenomenon=_str(step.get('phenomenon'),120)
    rationale=_str(step.get('rationale'),950)
    question=_str(step.get('experiment'),650)
    gap=_str(step.get('missing_capability'),500)
    if not all((phenomenon,rationale,question,gap)):
        return False,'Necesito describir el fenómeno, la limitación, el fundamento y una prueba.'
    if any(x.get('type','physics')=='physics' and
           x.get('phenomenon','').casefold()==phenomenon.casefold() and
           x.get('status') in ('pendiente','aprobada','aceptada_pendiente_de_motor')
           for x in person['proposals']):
        return False,'Ya tengo una propuesta pendiente o aceptada para ese fenómeno.'
    # Solo un ensayo no_evaluable del mismo fenómeno respalda la ausencia de
    # modelo. Una palabra compartida o un ID inventado no justifican el vínculo.
    linked,association=select_physics_evidence(step,person.get('unmodeled_attempts',[]))
    proposal={'evidence_quality':'respaldada_por_no_evaluable' if linked else 'hipotesis_sin_prueba_de_fisica',
              'id':'sol-'+uuid.uuid4().hex[:10],'when':stamp,'phenomenon':phenomenon,
              'type':'physics','rationale':rationale,'experiment':question,'missing_capability':gap,
              'context':_str(step.get('context'),400),'evidence_ids':[a['id'] for a in linked],
              'evidence':linked,'evidence_relation':association,
              'status':'pendiente','review':None,
              'engine_ready':phenomenon.casefold() in {x.casefold() for x in available_physics}}
    if isinstance(step.get('_journal_id'),str):proposal['journal_id']=step['_journal_id']
    project_id=(person.get('project') or {}).get('id')
    if project_id:proposal['project_id']=project_id
    person['proposals'].append(proposal)
    return True,f"Presenté una propuesta fundamentada para estudiar '{phenomenon}'. Queda pendiente de evaluación; no altera la física."


def record_action_outcome(person, step, success, facts, stamp, position):
    """Registro comprobable de un intento, independiente de la explicación del LLM."""
    ensure_records(person)
    entry={'id':'act-'+uuid.uuid4().hex[:12], 'when':stamp,
           'op':_str(step.get('op'),32),
           'target':_str(step.get('target') or step.get('item') or step.get('name') or
                        (f"({step.get('x')},{step.get('y')})" if 'x' in step else ''),130),
           'pos':list(position), 'success':bool(success),
           'facts':[_str(f,350) for f in facts[:5]]}
    person['action_outcomes'].append(entry)
    person['action_outcomes']=person['action_outcomes'][-120:]
    return entry


def submit_debug_report(person, step, stamp):
    """Una anomalía OBSERVADA, no un error declarado automáticamente.

    Las evidencias provienen solo de resultados efectivamente ejecutados por el motor.
    Nilo puede tener una sospecha equivocada: eso se resuelve en la evaluación.
    """
    ensure_records(person)
    title=_str(step.get('title'),125)
    expected=_str(step.get('expected'),650)
    observed=_str(step.get('observed'),650)
    rationale=_str(step.get('rationale'),750)
    kind=_str(step.get('issue_kind'),24).lower()
    if kind not in ('uso','limitacion','error'):kind='sin_clasificar'
    documented=_str(step.get('related_action'),32).lower()
    manual_reference=documented if documented in SUPPORTED_OPERATIONS else None
    if not all((title,expected,observed,rationale)):
        return False,'Necesito título, resultado esperado, observación y por qué solicito la revisión.'
    if any(p.get('type')=='debug' and p.get('title','').casefold()==title.casefold()
           and p.get('status')=='pendiente' for p in person['proposals']):
        return False,'Ya existe una propuesta de revisión abierta sobre este mismo problema.'
    evidence,association=select_debug_evidence(step,person.get('action_outcomes',[]))
    pending_revision=next((r for r in person['proposals']
        if r.get('type')=='debug' and r.get('title','').casefold()==title.casefold()
        and r.get('status')=='requiere_ampliacion'),None)
    if pending_revision:
        prior={k:pending_revision.get(k) for k in ('expected','observed','rationale')}
        previous_ids={r['id'] for r in pending_revision.get('evidence',[])}
        updates=any(prior[k]!=v for k,v in [('expected',expected),('observed',observed),('rationale',rationale)])
        new_evidence=[dict(e) for e in evidence if e['id'] not in previous_ids]
        if not updates and not new_evidence:
            return False,'La revisión necesita información nueva o evidencias adicionales antes de reenviarla.'
        pending_revision.setdefault('review_history',[]).append(pending_revision['review'])
        if isinstance(step.get('_journal_id'),str):
            links=pending_revision.setdefault('journal_ids',[])
            if step['_journal_id'] not in links:links.append(step['_journal_id'])
            del links[:-50]
        pending_revision.update({'expected':expected,'observed':observed,'rationale':rationale,
            'issue_kind':kind,'manual_reference':manual_reference,
            'related_action':_str(step.get('related_action'),32), 'updated':stamp,
            'evidence':(pending_revision.get('evidence',[])+new_evidence)[-12:],
            'evidence_relation':(
                'referencia_explicita' if association=='referencia_explicita'
                else pending_revision.get('evidence_relation',association)),
            'status':'pendiente','review':None})
        return True,f"Amplié la propuesta '{title}' y la devolví a evaluación, sin afirmar que existe un bug."
    report={'id':'bug-'+uuid.uuid4().hex[:10], 'type':'debug','when':stamp,
            'title':title,'expected':expected,'observed':observed,
            'issue_kind':kind,'manual_reference':manual_reference,
            'rationale':rationale,'related_action':_str(step.get('related_action'),32),
            'evidence':[dict(e) for e in evidence], 'evidence_relation':association,
            'status':'pendiente', 'review':None}
    if isinstance(step.get('_journal_id'),str):report['journal_id']=step['_journal_id']
    project_id=(person.get('project') or {}).get('id')
    if project_id:report['project_id']=project_id
    person['proposals'].append(report)
    found=f' con {len(evidence)} resultado(s) comprobable(s) asociado(s)' if evidence else ' sin acciones comprobables asociadas'
    return True, f"Registré una posible inconsistencia: '{title}'{found}. Es una solicitud de evaluación, no un bug confirmado."


def review_proposal(person, proposal_id, decision, reason, stamp):
    ensure_records(person)
    proposal=next((x for x in person['proposals'] if x['id']==proposal_id),None)
    if not proposal:raise ValueError('No existe esa propuesta.')
    if proposal['status']!='pendiente':raise ValueError('La propuesta ya fue evaluada.')
    if proposal.get('type')=='debug':
        states={'bug':'error_confirmado_pendiente_de_correccion',
                'limite':'limitacion_valida','capacidad':'capacidad_no_implementada',
                'interpretacion':'interpretacion_equivocada','ampliar':'requiere_ampliacion'}
    else:
        states={'aprobar':'aceptada_pendiente_de_motor',
                'rechazar':'rechazada','ampliar':'requiere_ampliacion'}
    if decision not in states:raise ValueError('La decisión no está permitida para esta propuesta.')
    if not reason.strip():raise ValueError('Indica el motivo de la decisión.')
    proposal['status']=states[decision]
    proposal['review']={'when':stamp,'decision':decision,'reason':_str(reason,700)}
    return proposal


def record_personal_experience(person,step,success,notable,facts,stamp,*,
                               position=None,measurement_id=None,action_id=None,legacy=False):
    ensure_records(person)
    op=step.get('op','')
    if op not in ('explore','descend','ascend','inspect','craft','build','use','experiment','assemble','modify','dismantle','forage','drink','propose','report_issue','design'):
        return
    if not (notable or not success):return
    # Las reproducciones de reglas anteriores conservan exactamente su
    # estructura histórica y su huella, sin enriquecer registros antiguos.
    entry={'when':stamp,'action':op,'successful':bool(success),
           'fact':_str(facts[0] if facts else '',200)}
    if not legacy:
        entry['id']=f"exp-{len(person['life_history'])+1}"
        target=_str(step.get('item') or step.get('target') or step.get('name'),100)
        if target:entry['target']=target
        object_id=step.get('_built_object_id') or step.get('_used_tool_id')
        if isinstance(object_id,str) and object_id:entry['object_id']=object_id
        if (isinstance(position,(list,tuple)) and len(position)==3
                and all(isinstance(n,int) and not isinstance(n,bool) for n in position)):
            entry['position_at_end']=list(position)
        if isinstance(measurement_id,str) and measurement_id:
            entry['measurement_id']=measurement_id
        if isinstance(action_id,str) and action_id:
            entry['action_id']=action_id
        project_id=(person.get('project') or {}).get('id')
        if isinstance(project_id,str) and project_id:entry['project_id']=project_id
    person['experience_summary'].append(entry)
    person['life_history'].append(entry)  # Registro íntegro: no se trunca al reducir contexto LLM.
    day=int(float(person.get('clock_minutes',0))//1440)+1
    chapter=str((day-1)//30+1)
    summary=person['life_chapters'].setdefault(chapter,{'desde_dia':((day-1)//30)*30+1,
         'acciones':{},'exitos':0,'fallos':0,'hitos':[]})
    summary['acciones'][op]=summary['acciones'].get(op,0)+1
    summary['exitos' if success else 'fallos']+=1
    if notable and len(summary['hitos'])<100:
        summary['hitos'].append(entry)
    # Resumen estructurado, no texto inventado y no se suprime la historia técnica.
    person['experience_summary']=person['experience_summary'][-240:]
    mapping={'explore':'explorar','descend':'explorar','ascend':'explorar','craft':'inventar',
             'build':'inventar','assemble':'inventar','use':'investigar','experiment':'investigar',
             'modify':'inventar','dismantle':'inventar','design':'inventar','propose':'investigar'}
    trait=mapping.get(op)
    if trait:
        current=person['preferences'].get(trait,.5)
        # Experiencias exitosas favorecen repetir la actividad; fallos reiterados
        # disminuyen gradualmente la preferencia, nunca la convierten en misión fija.
        person['preferences'][trait]=round(max(.18,min(.88,current+(.006 if success else -.010))),3)
