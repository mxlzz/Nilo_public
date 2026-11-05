"""Cierre de un objetivo explícito cuando existen hechos suficientes.

No califica intereses ni inventa resultados: solo reconoce un caso estrecho con
pruebas de agua conocida, bebida y recorrido material. Los demás quedan a Nilo.
"""
from __future__ import annotations
from world import tile


def verified_simple_goal(world, person, stamp):
    pr=person.get('project')
    if not isinstance(pr,dict) or pr.get('status')!='activo':return None
    title=str(pr.get('title','')).casefold()
    # No confundir con una investigación de filtración, condensación o potabilidad.
    if not (('explorar el entorno' in title or 'explorar una zona' in title)
            and 'localizar' in title and 'fuente de agua' in title):return None
    drink=person.get('skills',{}).get('drink',{}).get('verified')
    if not drink:return None
    visited=world.get('visited',{})
    if len(visited)<25:return None
    source=next((k for k in world.get('revealed',[])
                 if k.endswith(',0') and tile(world,*map(int,k.split(',')))=='~'),None)
    if not source:return None
    evidence={'fuente_observada':source,'accion_verificada':'drink','casillas_visitadas':len(visited)}
    pr['status']='terminado'
    pr['progress']=100
    pr['ended']=stamp
    pr['closure_evidence']=evidence
    pr['state']='Objetivo inicial cumplido con hechos del motor; otras investigaciones pueden continuar.'
    person.setdefault('projects',[])
    if pr not in person['projects']:person['projects'].append(pr)
    person['project']=None
    return {'title':pr['title'],'evidence':evidence}
