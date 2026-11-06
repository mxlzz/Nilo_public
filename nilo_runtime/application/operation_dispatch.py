"""Despacho único de acciones documentales, dirigido por el registro del núcleo.

Las operaciones que no modifican materia conservan sus límites: design solo
documenta, compare/conclude usan IDs de evidencia y propose/report_issue
solicitan revisión. El motor físico permanece en Environment.perform_result.
"""
from __future__ import annotations

from types import MappingProxyType

from nilo_runtime.core.operations import DOCUMENT_EXECUTORS, get_spec


def _design(sim, person, step):
    from inventions import register_design
    success, message = register_design(person, step, sim.stamp())
    return [message], success, success


def _propose(sim, person, step):
    from inventions import submit_proposal
    success, message = submit_proposal(
        person, step, sim.stamp(),
        ('flotacion', 'contencion', 'excavacion', 'impacto')
    )
    return [message], success, success


def _report_issue(sim, person, step):
    from inventions import submit_debug_report
    success, message = submit_debug_report(person, step, sim.stamp())
    return [message], success, success


def _compare(sim, person, step):
    from laboratory import compare as compare_physical
    from cognition import same_research
    success, description, entry = compare_physical(person, step, sim.stamp())
    if entry:
        subject = str(step.get('topic') or '').strip()[:150]
        if subject:
            entry['label'] = subject
            for investigation in person.get('research', []):
                if (investigation.get('state') == 'abierta'
                        and same_research(investigation.get('question', ''), subject)):
                    investigation['state'] = 'documentada'
                    investigation['conclusion'] = entry['text']
                    investigation['evidence_ids'] = entry['evidence_ids']
                    investigation['closed'] = entry['when']
                    if person.get('active_research') == investigation.get('question'):
                        person['active_research'] = None
        sim.archive.add('conclusion', entry)
        sim.event(['Comparación de ensayos medidos: ' + description], 'evaluación', True)
    return [description], success, bool(success)


def _conclude(sim, person, step):
    from experiment_log import observational_conclusion
    from cognition import same_research
    success, description, entry = observational_conclusion(person, step, sim.stamp())
    if entry:
        sim.archive.add('conclusion', entry)
        for research in person.get('research', []):
            if (research.get('state') == 'abierta'
                    and same_research(research.get('question', ''), entry['label'])):
                research['state'] = 'documentada'
                research['conclusion'] = entry['text']
                research['evidence_ids'] = entry['evidence_ids']
                research['closed'] = entry['when']
                if person.get('active_research') == research.get('question'):
                    person['active_research'] = None
    return [description], success, False


_HANDLERS = MappingProxyType({
    'design': _design,
    'propose': _propose,
    'report_issue': _report_issue,
    'compare': _compare,
    'conclude': _conclude,
})
if set(_HANDLERS) != set(DOCUMENT_EXECUTORS.values()):
    raise RuntimeError("El registro y los handlers documentales no coinciden")


def execute_document(sim, person, step):
    """Ejecuta un único handler DOCUMENTAL registrado; no simula física."""
    spec = get_spec(step.get('op'))
    if spec.executor == 'physical':
        raise ValueError(f"La operación física {spec.name} pertenece al entorno")
    return _HANDLERS[spec.executor](sim, person, step)
