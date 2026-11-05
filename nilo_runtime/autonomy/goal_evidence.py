"""Validación conservadora de evidencia para objetivos declarados por Nilo.

La pertenencia de una medición al proyecto NO demuestra que satisfaga su objetivo.
Solo se verifican propiedades instrumentadas; las demás exigen reformular el
objetivo, pausarlo o abandonarlo, nunca convertir una prueba ajena en éxito.
"""
from __future__ import annotations
import re
import unicodedata

STOP={'para','desde','hacia','entre','sobre','tras','como','ante','donde',
      'esto','esta','este','unas','unos','otro','otra','cada','alguna',
      'capaz','poder','puedo','antes','despues','nuevo','nueva','actual',
      'hacer','realizar','probar','verificar','evaluar','comprobar',
      'investigar','analizar','observar','determinar','completar',
      'objetivo','proyecto','resultados','materiales','utilidad','fase',
      'mediante','tener','usando','segun','posible','siguiente'}


def plain(value):
    value=unicodedata.normalize('NFKD',str(value or '').casefold())
    return ''.join(ch for ch in value if not unicodedata.combining(ch))


def words(value):
    return {t for t in re.findall(r'[a-z]{4,}',plain(value)) if t not in STOP}


def applicable_measurements(project,person):
    """Solo mediciones verificadas con ID y autoría de este proyecto."""
    ids={str(x.get('measurement_id')) for x in project.get('verified_results',[])
         if x.get('measurement_id') and x.get('action') not in
         {'write','design','propose','compare','conclude','report_issue','manual'}}
    return {m.get('id'):m for m in person.get('measurements',[])
            if m.get('id') in ids and m.get('success') is True
            and m.get('evaluation_status') not in
            ('no_evaluable','failed','verified_failure')}


def _non_instrumented_goal(goal):
    """No pedir una prueba que el mundo no puede producir.

    El estado esquemático de cubierta no demuestra aislamiento climático ni
    protección; inspeccionar no equivale a ensayar una función.
    """
    is_shelter=any(term in goal for term in ('refugio','habitaculo','cobertizo','cabana'))
    if not is_shelter:
        return ''
    if (any(term in goal for term in ('proteccion','proteger','intemperie',
                                       'clima','aislamiento','impermeabilidad','seguridad'))
            or ('abrigo' in goal and any(term in goal for term in
                    ('comprob','evalu','medir','verific','probar','valid','mejorar')))):
        return ('Criterio no instrumentado: no se simula protección frente a clima '
                'o amenazas. La inspección constata el objeto y su estado esquemático, '
                'pero no prueba abrigo funcional. Puede reformularse la pregunta, '
                'pausarse o abandonarse sin declarar un fracaso físico.')
    if 'mejorar' in goal or 'mejora' in goal:
        return ('Criterio no instrumentado: modificar una obra no demuestra una mejora '
                'funcional del refugio. No hay una magnitud de protección medible '
                'para acreditar ese cambio; se pueden documentar versiones sin '
                'atribuirles abrigo comprobado.')
    if 'prueba valida' in goal and not any(term in goal for term in
                                          ('descans','recuperar energia','recuperacion energetica')):
        return ('Criterio no instrumentado: "prueba válida" no especifica qué '
                'propiedad física del refugio debe medir. Inspeccionar o descansar '
                'sin comparación solo registra hechos; no acredita su función.')
    return ''


def _construction_ids(measurement, relation=None):
    return {link.get('id') for link in measurement.get('entity_links',[])
            if isinstance(link,dict) and link.get('category')=='construction'
            and isinstance(link.get('id'),str)
            and (relation is None or link.get('relation')==relation)}


def check_goal(project,person,proof=""):
    """Retorna (validez, ids que justifican el objetivo, razón de rechazo).

    No es un evaluador semántico universal. Los objetivos no instrumentados
    se retienen como NO VERIFICADOS en vez de completar falsamente.
    """
    goal=plain(project.get('title',''))
    limit=_non_instrumented_goal(goal)
    if limit:
        return False,[],limit
    measured=applicable_measurements(project,person)
    # Continuidad material: una ampliación del proyecto actual puede acreditar
    # una construcción original registrada en otro proyecto, SOLO si ambas
    # mediciones vinculan el mismo ID físico. Nunca por nombre o texto libre.
    if 'construir' in goal and any(v in goal for v in ('modificar','ampliar')):
        modified=set().union(*(_construction_ids(m,'modificada')
                               for m in measured.values() if m.get('op')=='modify'))
        if modified:
            for m in person.get('measurements',[]):
                if (m.get('op')=='build' and m.get('success') is True
                        and m.get('evaluation_status') not in
                        ('no_evaluable','failed','verified_failure')
                        and modified.intersection(_construction_ids(m,'creada'))):
                    measured.setdefault(m.get('id'),m)
    if not measured:
        return False,[],'No hay mediciones físicas exitosas y disponibles asociadas a este proyecto.'
    all_rows=list(measured.values())
    evidence=[]

    def require(predicate,reason):
        # Si Nilo cita una medicion pertinente, usarla antes que una antigua.
        # El objetivo debe seguir pasando todos sus controles independientes.
        candidates=[m for m in all_rows if predicate(m)]
        match=next((m for m in candidates if any(
            _cites_record(proof,r) and r.get('measurement_id')==m.get('id')
            for r in project.get('verified_results',[])
            if isinstance(r,dict))),None)
        if match is None:match=candidates[0] if candidates else None
        if match:
            evidence.append(match['id'])
            return True
        return reason

    if 'sin perdida' in goal or 'sin fugas' in goal or 'estanqueidad' in goal or 'hermetic' in goal:
        return False,[],('No existe una medición cuantitativa de pérdida cero o '
                         'estanqueidad perfecta para acreditar este objetivo.')
    if any(t in goal for t in ('potabil','potabl','purific')):
        ok=require(lambda m:(m.get('physical') or {}).get('properties',{}).get('potabilidad') is True,
                   'No existe una prueba estructurada de potabilidad.')
        return (True,list(dict.fromkeys(evidence)),'') if ok is True else (False,[],ok)

    # Las cláusulas combinadas necesitan pruebas de CADA parte.
    if 'fabricar' in goal or 'construir' in goal or 'crear' in goal:
        res=require(lambda m:m.get('op') in ('craft','build','assemble')
                    and (not ('recipiente' in goal) or 'recipiente' in
                         plain(' '.join(m.get('verified_facts') or []))),
                    'No consta fabricación o construcción verificable del objeto buscado.')
        if res is not True:return False,[],res
    if (any(term in goal for term in ('modificar','ampliar'))
            and any(term in goal for term in ('refugio','estructura','habitaculo','cobertizo'))):
        res=require(lambda m:m.get('op')=='modify'
                    and bool(_construction_ids(m,'modificada')),
                    'No consta una modificación verificable de una obra identificada.')
        if res is not True:return False,[],res
    if 'recipiente' in goal and any(x in goal for x in ('contener','retener','retencion','almacenar','sostener')):
        is_solid=any(x in goal for x in ('solido','alimento','arcilla','piedra'))
        is_water=any(x in goal for x in ('liquido','agua','fluido'))
        if not (is_solid or is_water):
            return False,[],'El objetivo no precisa qué material debe contener el recipiente.'
        res=require(lambda m:m.get('op')=='use'
            and m.get('method') in ('contener','llenar')
            and (plain(m.get('target')) not in ('agua','liquido') if is_solid else
                 plain(m.get('target'))=='agua')
            and any(t in plain(' '.join(m.get('verified_facts') or []))
                    for t in ('sostuvo','llene','retencion')),
            'No hay un ensayo positivo de contención del material especificado.')
        if res is not True:return False,[],res
        if 'mineral' in goal and not any('recipiente_mineral' in
            plain(' '.join(measured[i].get('verified_facts') or []))
            for i in evidence):
            return False,[],'La prueba no identifica el recipiente mineral solicitado.'
    if 'descans' in goal or 'recuperar energia' in goal or 'recuperar energias' in goal:
        res=require(lambda m:m.get('op')=='rest' and
                    (m.get('needs_delta') or {}).get('energia',0)>0,
                    'No existe un descanso registrado con recuperación de energía.')
        if res is not True:return False,[],res
    if any(t in goal for t in ('regresar','volver','desplazarse','llegar','retornar')):
        if 'refugio' in goal:
            res=require(lambda m:m.get('op')=='go' and
                        'refugio' in plain(' '.join(m.get('verified_facts') or [])),
                        'No se verificó la llegada al refugio.')
            if res is not True:return False,[],res
        else:
            res=require(lambda m:m.get('op')=='go',
                        'No hay una llegada o desplazamiento verificable.')
            if res is not True:return False,[],res
    is_terrain_survey=('reconoc' in goal and
        any(t in goal for t in ('terreno','territorio','entorno','zona')))
    wants_water_discovery=('agua' in goal and any(t in goal for t in
        ('encontrar','localizar','hallar','hallazgo')))
    if 'explor' in goal or 'mapear' in goal or 'cartograf' in goal or is_terrain_survey:
        res=require(lambda m:m.get('op')=='explore' and m.get('success') is True
                    and (not is_terrain_survey or
                         any('observe por primera vez' in plain(f)
                             for f in m.get('verified_facts',[]))),
                    'No hay exploración verificable del terreno registrado.')
        if res is not True:return False,[],res
        if not wants_water_discovery and any(t in goal for t in
            ('encontrar','descubrir','identificar','hallar','hallazgo')):
            return False,[],'Explorar no demuestra haber encontrado el objeto buscado.'
    if any(t in goal for t in ('planificar','preparar el proximo plan','preparar el siguiente')):
        return False,[],'La ejecución de un plan futuro no está instrumentada como objetivo verificable.'

    # Localizar agua es una excepción acotada: requiere desplazamiento real
    # exitoso y constancia del hallazgo en los hechos verificados del motor.
    # Los registros históricos de go aún no guardan el destino como dato tipado.
    if wants_water_discovery:
        def water_verified(m):
            facts=plain(' '.join(m.get('verified_facts') or []))
            op=m.get('op')
            if op=='inspect':
                return 'agua' in plain(m.get('target')) and 'agua' in facts
            if op=='go':
                return 'agua' in facts and 'orilla' in facts
            if op=='explore':
                # Observar agua por primera vez es evidencia de un hallazgo;
                # ninguna descripcion de estabilidad o potabilidad lo es.
                return 'observe por primera vez' in facts and 'agua' in facts
            if op=='drink':
                return 'bebi' in facts and 'agua' in facts
            return False
        res=require(water_verified,
                    'No hay observación, inspección o llegada verificada a una fuente de agua.')
        if res is not True:return False,[],res

    # Una observación sobre el mismo asunto no verifica la propiedad
    # enunciada. Solo las ramas con condiciones físicas explícitas acreditan.
    if not evidence:
        return False,[],'El objetivo no tiene un criterio físico verificable instrumentado.'
    facts=' '.join(' '.join(measured[mid].get('verified_facts') or [])
                   for mid in evidence)
    # Un objetivo de contención o fabricación con objeto específico no puede
    # acreditarse con un objeto de otro material.
    if 'recipiente' in goal and 'mineral' in goal and 'mineral' not in plain(facts):
        return False,[],'La prueba no corresponde al recipiente mineral.'
    return True,list(dict.fromkeys(evidence)),''


def _cites_record(proof, result):
    """Exigir ID completo como token o descripción VERIFICADA íntegra.

    Una frase corta o el prefijo de otro ID no acredita un resultado ajeno.
    """
    mid=result.get('measurement_id')
    if isinstance(mid,str) and mid and re.search(
            r'(?<![a-zA-Z0-9_-])'+re.escape(mid)+r'(?![a-zA-Z0-9_-])',proof):
        return True
    recorded=str(result.get('result') or '').strip()
    return bool(recorded and plain(proof).strip()==plain(recorded).strip())


def select_closure_evidence(project,person,proof):
    """Prueba citada por Nilo + cobertura física de los requisitos."""
    if not isinstance(project,dict) or not isinstance(proof,str) or len(proof.strip())<12:
        return None
    references=project.get('verified_results',[])
    if not any(_cites_record(proof,r) for r in references):
        return None
    valid,ids,reason=check_goal(project,person,proof)
    if not valid:return None
    # La prueba que Nilo citó debe formar parte del conjunto que realmente
    # acredita el objetivo, no otra acción cualquiera del mismo proyecto.
    cited={str(r.get('measurement_id')) for r in references
           if _cites_record(proof,r)}
    if not cited.intersection(ids):return None
    return {'evidence_ids':ids,'method':'criterios_de_objetivo_v1',
            'summary':'Objetivo contrastado con mediciones específicas del proyecto.'}
