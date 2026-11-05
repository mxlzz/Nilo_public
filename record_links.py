"""Vínculos de procedencia explícita entre registros; nunca inferir causalidad por fecha.

Cada relación se conserva como índice reversible del archivo. El campo en el
registro es la fuente de verdad: ni una coincidencia temporal ni un texto similar
crean un vínculo.
"""
import re

CATEGORY_BY_FIELD={
    'journal_id':'journal','research_id':'research','project_id':'project',
    'prediction_id':'prediction','measurement_id':'measurement',
    'design_id':'design','proposal_id':'proposal',
}
MEASUREMENT_ID=re.compile(r'^med-[a-z0-9-]{1,56}$',re.IGNORECASE)

def explicit_links(category, record):
    """Retorna (categoría, id, motivo) sin aceptar destinos inventados."""
    if not isinstance(record,dict):return []
    source_id=str(record.get('id') or '')
    found=set()
    def push(target,id_value,reason):
        if target not in ('journal','research','project','prediction','measurement',
                          'design','proposal','diagnostic','construction','tool'):return
        if not isinstance(id_value,str) or not (0<len(id_value)<=100):return
        if target==category and id_value==source_id:return
        found.add((target,id_value,reason))
    for field,target in CATEGORY_BY_FIELD.items():
        push(target,record.get(field),'origen' if field=='journal_id' else 'referencia')
    for field,target in (('journal_ids','journal'),('research_ids','research'),
                         ('project_ids','project'),('measurement_ids','measurement')):
        values=record.get(field,[])
        if isinstance(values,list):
            for value in values:push(target,value,'referencia')
    for field in ('evidence_ids','rest_evidence_ids','function_tests'):
        values=record.get(field,[])
        if isinstance(values,list):
            for value in values:
                if isinstance(value,str):
                    push('measurement' if MEASUREMENT_ID.fullmatch(value) else 'diagnostic',
                         value,'evidencia')
    # Las pruebas y los hitos guardan IDs físicos, no basta con que tengan
    # descripciones parecidas o hayan ocurrido el mismo día.
    for field in ('tests','verified_results','verified_milestones'):
        entries=record.get(field,[])
        if isinstance(entries,list):
            for item in entries:
                if isinstance(item,dict):
                    push('measurement',item.get('measurement_id'),'evidencia')
    # Instancias físicas verificadas en mediciones. Una variación de cantidad
    # no autoriza a inventar identidades de objetos.
    if category=='measurement':
        for link in record.get('entity_links',[]):
            if isinstance(link,dict) and link.get('category') in ('tool','construction'):
                push(link['category'],link.get('id'),link.get('relation','referencia'))
    physical=record.get('physical_result')
    if isinstance(physical,dict):push('measurement',physical.get('measurement_id'),'medición')
    evidence=record.get('evidence',[])
    if category=='proposal' and isinstance(evidence,list):
        for item in evidence:
            if isinstance(item,dict) and isinstance(item.get('id'),str):
                evidence_id=item['id']
                push('measurement' if MEASUREMENT_ID.fullmatch(evidence_id) else 'diagnostic',
                     evidence_id,'evidencia')
                physical_evidence=item.get('physical_result')
                if isinstance(physical_evidence,dict):
                    push('measurement',physical_evidence.get('measurement_id'),'evidencia')
    return sorted(found)

def record_title(category,record):
    if not isinstance(record,dict):return 'Registro archivado'
    fields={
      'journal':('text',),'research':('question',),'project':('title',),
      'prediction':('hypothesis',),'measurement':('label','target','op'),
      'conclusion':('text',),'proposal':('title','phenomenon'),
      'design':('name',),'construction':('name',),'tool':('name',),
      'diagnostic':('description','op'),'event':('text',)
    }.get(category,('title','name','text'))
    for field in fields:
        value=record.get(field)
        if isinstance(value,str) and value.strip():return value.strip()[:120]
    return category.capitalize()
