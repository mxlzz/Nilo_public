"""Regresiones: refugio, trazabilidad entre proyectos y pausas de investigación."""
import unittest

from brain import context_for, compact_context
from goal_evidence import check_goal, select_closure_evidence
from project_lifecycle import closure_diagnostic
from nilo import initial_state


def measurement(identity, op, building, relation):
    return {
        'id': identity, 'op': op, 'success': True,
        'evaluation_status': 'verified_success',
        'entity_links': [{'category': 'construction', 'id': building,
                          'relation': relation}],
        'verified_facts': [f'Acción {op} verificada para {building}.'],
    }


class ShelterEvidence(unittest.TestCase):
    def setUp(self):
        self.build = measurement('med-construccion-01', 'build', 'obra-a', 'creada')
        self.modify = measurement('med-ampliacion-02', 'modify', 'obra-a', 'modificada')
        self.inspect = measurement('med-inspeccion-03', 'inspect', 'obra-a', 'consultada')
        self.person = {'measurements': [self.build, self.modify, self.inspect]}
        self.project = {
            'id': 'proyecto-actual',
            'title': 'Construir y modificar la estructura de refugio elemental',
            'verified_results': [
                {'action': 'modify', 'measurement_id': self.modify['id']},
                {'action': 'inspect', 'measurement_id': self.inspect['id']},
            ],
        }

    def test_prior_build_same_entity_supports_continued_modification(self):
        valid, ids, why = check_goal(self.project, self.person)
        self.assertTrue(valid, why)
        self.assertEqual(set(ids), {self.build['id'], self.modify['id']})
        closure = select_closure_evidence(self.project, self.person,
                                         self.modify['id'])
        self.assertIsNotNone(closure)
        self.assertIn(self.modify['id'], closure['evidence_ids'])

    def test_other_construction_does_not_prove_this_one(self):
        self.build['entity_links'][0]['id'] = 'obra-distinta'
        valid, ids, why = check_goal(self.project, self.person)
        self.assertFalse(valid)
        self.assertIn('fabricación o construcción', why)

    def test_build_by_name_without_physical_id_cannot_be_reused(self):
        self.build['entity_links'] = []
        valid, _, why = check_goal(self.project, self.person)
        self.assertFalse(valid)
        self.assertIn('construcción', why)

    def test_simple_build_with_shelter_as_purpose_still_completes(self):
        project = {
            'id': 'obra-simple',
            'title': 'Construir un refugio para abrigo',
            'verified_results': [
                {'action': 'build', 'measurement_id': self.build['id']}],
        }
        valid, ids, reason = check_goal(project, self.person)
        self.assertTrue(valid, reason)
        self.assertEqual(ids, [self.build['id']])

    def test_modification_does_not_prove_functional_improvement(self):
        self.project['title'] = (
            'Construir y mejorar la estructura de refugio elemental '
            'y registrar su estado con una prueba válida.')
        diag = closure_diagnostic(self.project, self.person,
                                  self.modify['id'])
        self.assertFalse(diag['comprobado'])
        self.assertEqual(diag['estado'], 'criterio_no_instrumentado')
        self.assertIn('modificar', diag['motivo'].lower())

    def test_inspection_does_not_prove_climate_protection(self):
        self.project['title'] = 'Comprobar que el refugio protege contra el clima'
        valid, _, why = check_goal(self.project, self.person)
        self.assertFalse(valid)
        self.assertIn('no se simula protección', why)


class ShelterContext(unittest.TestCase):
    def test_related_pauses_and_questions_survive_context_compaction(self):
        s = initial_state()
        p, w = s['person'], s['world']
        p['project'] = {
            'id': 'nuevo', 'title': 'Investigar refugio de madera',
            'reason': 'Determinar estado del refugio', 'status': 'activo'}
        p['projects'] = [{
            'id': 'previo', 'title': 'Estudiar refugio de madera',
            'reason': 'Inspeccionar el refugio', 'state': 'Sin pruebas funcionales',
            'status': 'pausado', 'closure_reason': 'Repetí ensayos sin información nueva',
            'no_progress_steps': 8}]
        p['research'] = [{
            'id': 'pregunta-anterior',
            'question': 'Cómo verificar refugio de madera',
            'hypothesis': 'El refugio de madera protege del clima',
            'state': 'pausada', 'evidence': [],
            'project_retirement': {
                'project_id': 'previo', 'status': 'pausado',
                'conclusion_not_verified': True}}]
        context = context_for(w, p, [], 'Día 1')
        self.assertEqual(context['antecedentes_relacionados'][0]['id'], 'previo')
        self.assertEqual(
            context['investigaciones_pausadas_relacionadas'][0]['id'],
            'pregunta-anterior')
        reduced = compact_context(context, 5400)
        self.assertEqual(reduced['antecedentes_relacionados'][0]['id'], 'previo')
        self.assertEqual(
            reduced['investigaciones_pausadas_relacionadas'][0]['id'],
            'pregunta-anterior')
        # Justo después de pausar, project=None: la memoria no debe
        # desaparecer antes de la próxima deliberación.
        p['project'] = None
        after_pause = compact_context(context_for(w, p, [], 'Día 1'), 5400)
        self.assertEqual(after_pause['antecedentes_relacionados'][0]['id'], 'previo')
        self.assertEqual(
            after_pause['investigaciones_pausadas_relacionadas'][0]['id'],
            'pregunta-anterior')


if __name__ == '__main__':
    unittest.main()
