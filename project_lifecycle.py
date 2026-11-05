"""Reglas verificables para continuidad de proyectos.

El motor no decide objetivos ni declara trabajos completos por porcentaje.
Sí impide reciclar un ID si Nilo pidió expresamente iniciar un proyecto nuevo.
"""
from __future__ import annotations

_DERIVED={'conclude','compare','manual','design','propose','report_issue','write'}
_UNVERIFIED=('no esta comprobada', 'no esta demostrado', 'no comprobada',
             'no se ha comprobado', 'sin funcionamiento verificado',
             'no evaluable', 'no demuestra', 'sin verificar',
             'todavia no', 'aun no')


def _plain(value):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFKD',str(value).casefold())
                   if not unicodedata.combining(c))


def completion_evidence(project,proof,person):
    """No confundir una medición válida con la prueba del objetivo."""
    from goal_evidence import select_closure_evidence
    return select_closure_evidence(project,person,proof)



def closure_diagnostic(project,person,proof=""):
    """Explica por qué un cierre no es válido sin atribuir evidencia ausente.

    'Sin criterio' solo cuando la validación llega efectivamente a esa rama;
    sin mediciones no puede saberse si se cumpliría el objetivo.
    """
    from goal_evidence import check_goal
    if not isinstance(project,dict):
        return {'estado':'sin_proyecto','comprobado':False,
                'motivo':'No hay proyecto activo identificado.','ids_evidencia':[]}
    valid,ids,reason=check_goal(project,person,proof)
    if valid:
        from goal_evidence import select_closure_evidence
        cited=select_closure_evidence(project,person,proof)
        return {'estado':'verificado' if cited else 'evidencia_sin_cita',
                'comprobado':bool(cited),'ids_evidencia':ids,
                'motivo':'' if cited else 'El objetivo admite prueba, pero falta citar un resultado pertinente del proyecto.'}
    if (reason=='El objetivo no tiene un criterio físico verificable instrumentado.'
            or reason.startswith('Criterio no instrumentado:')):
        state='criterio_no_instrumentado'
    elif reason.startswith('No hay mediciones físicas'):
        state='sin_mediciones_del_proyecto'
    else:
        state='condicion_fisica_no_demostrada'
    return {'estado':state,'comprobado':False,'ids_evidencia':ids,
            'motivo':reason}

def project_needs_review(project):
    if not isinstance(project,dict):return False
    # Es una sugerencia de revisión, no cierre automático.
    return (project.get('deliberations',0)>=16
            and project.get('deliberations_since_progress',0)>=7)


def retire_project(person, project, status, stamp, reason="", evidence=None):
    """Cerrar o pausar un proyecto sin fabricar éxitos físicos.

    El historial persiste. Se cancelan solo tareas diferidas del proyecto,
    para que no revivan una investigación abandonada.
    """
    if not isinstance(project, dict) or status not in ('terminado','abandonado','pausado'):
        raise ValueError('Proyecto o estado inválido.')
    project['status']=status
    project['updated']=stamp
    project['ended']=stamp if status!='pausado' else None
    project['closure_kind']=status
    if status=='terminado':
        if not evidence:
            raise ValueError('Completar exige evidencia física pertinente.')
        project['progress']=100
        project['closure_evidence']=evidence
    elif status=='abandonado':
        project['closure_reason']=str(reason or 'Decidí no continuar investigándolo.')[:260]
        # No convertir una renuncia en progreso físico ficticio.
        project['progress']=min(95, max(0,int(project.get('progress',0))))
    else:
        project['closure_reason']=str(reason or 'Pendiente de retomar.')[:260]
    person.setdefault('projects',[])
    if project not in person['projects']:
        person['projects'].append(project)
    if (person.get('project') or {}).get('id')==project.get('id'):
        person['project']=None
    # Solo investigaciones con una relación de proyecto REALMENTE registrada.
    # No inferir que una pregunta histórica quedó respondida porque el
    # proyecto tenga un porcentaje o una prueba sobre otro tema.
    next_state={'pausado':'pausada','abandonado':'archivada_sin_resolver',
                'terminado':'archivada_con_proyecto'}[status]
    for investigation in person.get('research',[]):
        if (investigation.get('state')=='abierta' and
                project.get('id') in investigation.get('project_ids',[])):
            other_projects=[
                x for x in person.get('projects',[])
                if x.get('id')!=project.get('id')
                and x.get('id') in investigation.get('project_ids',[])
                and x.get('status')=='activo']
            if other_projects:continue
            investigation['state']=next_state
            investigation['project_retirement']={
                'project_id':project['id'],'status':status,'when':stamp,
                'conclusion_not_verified':True}
            investigation['updated']=stamp
            if person.get('active_research')==investigation.get('question'):
                person['active_research']=None
    for task in person.get('agenda',[]):
        if task.get('modo')=='recordatorio' and status=='pausado':
            continue  # El aviso de reanudacion puede cumplirse durante la pausa.
        if task.get('proyecto_id')==project.get('id') and task.get('estado') in ('pendiente','en_curso','pospuesta','lista_para_revisar'):
            task['estado']='cancelada' if status!='pausado' else 'pospuesta'
            task['ultimo_motivo']='Proyecto '+status
            # Las tareas pausadas no se ejecutan mientras el proyecto no esté activo.
            if status=='pausado':task['reanudar_minuto']=1e15
    return project
