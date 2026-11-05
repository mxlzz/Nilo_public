"""Memoria de investigaciones y evaluación determinista de avances para Nilo 03.2.
No genera hechos. Reúne preguntas relacionadas sin borrar su historial.
"""
from __future__ import annotations
import re, difflib, unicodedata
from copy import deepcopy
from nilo_runtime.cognition.topics import topic as experimental_topic

STOP={'el','la','los','las','un','una','de','del','a','al','en','con','sin','por','para','si','que','cual','como',
      'puedo','podria','puede','podra','es','ser','hacer','usando','utilizar','uso','sobre','se','mas','menos','y','o',
      'me','mi','mis','este','esta','ese','esa','esto','ahi','hay','su','sus','lo','le','material','materiales'}
SYN={
  'piedras':'roca','piedra':'roca','rocas':'roca','rocoso':'roca','rocosas':'roca',
  'fracturar':'romper','fractura':'romper','partir':'romper','quebrar':'romper','fragmentar':'romper',
  'cavar':'excavar','excavacion':'excavar','perforar':'excavar','perforacion':'excavar',
  'martillo':'mazo','martillos':'mazo','mazos':'mazo','golpeo':'golpear','golpes':'golpear',
  'dureza':'resistencia','resistente':'resistencia','resistentes':'resistencia',
  'artefacto':'herramienta','herramientas':'herramienta','utiles':'herramienta',
  'entrar':'acceder','entrada':'acceder','acceso':'acceder','llegar':'acceder',
  'ruina':'ruinas','cuevas':'cueva','subterraneo':'cueva',
  'maderas':'madera','arboles':'arbol','arboleda':'arbol',
}

def terms(text):
    normalized=unicodedata.normalize('NFKD',str(text).lower())
    plain=''.join(ch for ch in normalized if not unicodedata.combining(ch))
    return set(SYN.get(t,t) for t in re.findall(r'[a-z]{3,}',plain) if t not in STOP)


def topic(question):
    t=terms(question)
    if 'ruinas' in t:return 'lugar:ruinas'
    if 'cueva' in t:return 'lugar:cueva'
    if ('excavar' in t or 'romper' in t or 'acceder' in t) and 'roca' in t:return 'roca:abrir_paso'
    if 'mazo' in t and 'roca' in t:return 'roca:impacto'
    if 'herramienta' in t and 'roca' in t:return 'roca:herramientas'
    if 'roca' in t and 'resistencia' in t:return 'roca:propiedades'
    if 'madera' in t and 'roca' in t:return 'materiales:mixtos'
    if 'madera' in t:return 'material:madera'
    if 'arcilla' in t:return 'material:arcilla'
    if 'mineral' in t:return 'material:mineral'
    if 'roca' in t:return 'material:roca'
    if 'herramienta' in t:return 'tecnica:herramientas'
    if 'explorar' in t:return 'lugar:exploracion'
    return ''


def same_research(a,b):
    ta_topic,tb_topic=experimental_topic(a),experimental_topic(b)
    if ta_topic and ta_topic==tb_topic:return True
    a=str(a or '');b=str(b or '')
    if not a or not b:return False
    ta,tb=terms(a),terms(b)
    if not ta or not tb:return False
    jaccard=len(ta&tb)/len(ta|tb)
    ta_topic=topic(a);tb_topic=topic(b)
    # Agrupar problemas equivalentes, sin confundir preguntas genéricas.
    return (bool(ta_topic and ta_topic==tb_topic and jaccard>=.24) or
            (len(ta&tb)>=2 and jaccard>=.43) or
            jaccard>=.64 or difflib.SequenceMatcher(None,a.lower(),b.lower()).ratio()>=.86)


def consolidate_research(person):
    """Migración idempotente: documentos viejos quedan preservados como integrados."""
    research=person.setdefault('research',[])
    canon=[];merged=0
    for entry in research:
        if not isinstance(entry,dict):continue
        if entry.get('state')=='integrada':continue
        q=str(entry.get('question',''))
        anchor=next((r for r in canon if same_research(r.get('question'),q)),None)
        if anchor is None:
            canon.append(entry)
            continue
        if anchor is entry:continue
        entry['state']='integrada';entry['merged_into']=anchor.get('id')
        if person.get('active_research')==q:
            person['active_research']=anchor.get('question')
        anchor.setdefault('related_questions',[])
        if q not in anchor['related_questions']:
            anchor['related_questions'].append(q)
            anchor['related_questions']=anchor['related_questions'][-15:]
        seen={(v.get('when'),str(v.get('facts'))) for v in anchor.get('evidence',[]) if isinstance(v,dict)}
        for e in entry.get('evidence',[]):
            fingerprint=(e.get('when'),str(e.get('facts'))) if isinstance(e,dict) else None
            if fingerprint and fingerprint not in seen:
                # La fusión temática preserva la fuente; no acredita un ensayo
                # por el parecido de palabras entre dos preguntas.
                merged_evidence=deepcopy(e)
                merged_evidence.setdefault('source_research_id',entry.get('id'))
                merged_evidence.setdefault('evidence_kind','registro_legacy_no_verificado')
                anchor.setdefault('evidence',[]).append(merged_evidence)
                seen.add(fingerprint)
        anchor['evidence']=anchor.get('evidence',[])[-30:]
        merged+=1
    person['research_consolidated_v032']=True
    return merged


def register_research(person,question,hypothesis,stamp,create_id):
    research=person.setdefault('research',[])
    key=experimental_topic(' '.join((question,hypothesis)))
    if key and any(c.get('topic')==key and c.get('status')=='comprobada' for c in person.get('conclusions',[])):
        return next((r for r in reversed(research) if experimental_topic(r.get('question',''))==key),None),False
    current=next((r for r in research if r.get('state')=='abierta' and same_research(r.get('question'),question)),None)
    # Una investigación archivada o pausada se puede retomar sin duplicar
    # el ID si se trata realmente de la misma pregunta.
    if current is None:
        current=next((r for r in reversed(research)
                      if r.get('state') in ('pausada','archivada_sin_resolver','archivada_con_proyecto')
                      and same_research(r.get('question'),question)),None)
    project_id=(person.get('project') or {}).get('id')
    if current:
        if current.get('state')!='abierta':
            current.setdefault('reaperturas',[]).append({'when':stamp,'project_id':project_id})
            current['state']='abierta'
        if project_id:
            current.setdefault('project_ids',[])
            if project_id not in current['project_ids']:current['project_ids'].append(project_id)
        previous=str(current.get('hypothesis') or '')
        proposed=str(hypothesis or '')
        if proposed and proposed!=previous:
            # Registrar ambas formulaciones como creencias, nunca como
            # hallazgos. La hipótesis anterior no se borra del historial.
            history=current.setdefault('hypothesis_history',[])
            if previous and not history:
                history.append({'when':current.get('started'),
                                'hypothesis':previous,'kind':'belief'})
            history.append({'when':stamp,'hypothesis':proposed,'kind':'belief'})
            current['hypothesis']=proposed
        current['updated']=stamp
        if question!=current.get('question'):
            current.setdefault('related_questions',[])
            if question not in current['related_questions']:
                current['related_questions'].append(question)
                current['related_questions']=current['related_questions'][-15:]
        person['active_research']=current['question']
        return current,False
    created={'question':question,'hypothesis':hypothesis,'started':stamp,
             'state':'abierta','evidence':[],'id':create_id,
             'project_ids':[project_id] if project_id else []}
    research.append(created)
    person['active_research']=question
    return created,True
