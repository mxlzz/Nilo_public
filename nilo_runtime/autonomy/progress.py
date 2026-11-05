"""Evidencia de progreso por operación, sin interpretar la intención del agente.

La navegación revela casillas ANTES de finalizar la acción. El recuento debe
partir de su instantánea inicial y no del estado ya modificado al concluir.
"""
from __future__ import annotations


def discovered_during_action(world, pending, revealed_before_finish, *, legacy=False):
    """Cantidad no negativa de casillas nuevas desde que comenzó la acción.

    Para replays anteriores se conserva el cálculo histórico. Partidas
    importadas sin marcador no reciben descubrimientos inventados.
    """
    current=len(world.get('revealed',[]))
    baseline=revealed_before_finish
    if not legacy:
        recorded=pending.get('behavior_revealed_at_start') if isinstance(pending,dict) else None
        if isinstance(recorded,int) and not isinstance(recorded,bool) and 0<=recorded<=current:
            baseline=recorded
    return max(0,current-baseline)


def advance_evidence(*, new_knowledge=False,new_tiles=0,terrain_change=False,
                     new_structure=False,new_material=False,novel_tool=False,
                     useful_revision=False):
    """No otorgar avance por desplazamiento conocido, ensayo vacío o nombre."""
    reasons=[]
    for key,ok in (('conocimiento',new_knowledge),('territorio',new_tiles>0),
                   ('terreno_modificado',terrain_change),('obra',new_structure),
                   ('material_nuevo',new_material),('herramienta_nueva',novel_tool),
                   ('revision_fisica',useful_revision)):
        if ok:reasons.append(key)
    return {'progress':bool(reasons),'reasons':reasons,'new_tiles':max(0,int(new_tiles))}


def repeated_methods(attempts,project_id,*,min_count=3):
    """Descripción informativa, no veto de operaciones ni declaración de inutilidad.

    El algoritmo anterior imponía un bloqueo a cualquier instancia de una
    operación tras acumular 3 fallos. No confundimos varios destinos de explore.
    """
    recent=[x for x in attempts[-12:] if isinstance(x,dict)
            and x.get('project_id')==project_id and not x.get('progress')]
    counts={}
    for a in recent:
        op=a.get('op')
        if op in ('inspect','excavate','explore','use','experiment','go'):
            counts[op]=counts.get(op,0)+1
    # Mantener el orden del detector legado para replays que almacenan la lista.
    order=('inspect','excavate','explore','use','experiment','go')
    return [op for op in order if counts.get(op,0)>=min_count]
