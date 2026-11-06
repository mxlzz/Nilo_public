"""0.5.9.3.6 — memoria operativa, evidencia primaria y cierre prudente."""
import unittest
from brain import compact_context
from episodic_memory import recall_relevant
from experiment_log import observational_conclusion
from project_lifecycle import completion_evidence


def measurement(mid, op, fact, success=True):
    return {'id': mid, 'op': op, 'success': success, 'verified_facts': [fact]}


class EpisodicRecall(unittest.TestCase):
    def setUp(self):
        self.person = {
            'pos': [22, 8, 0],
            'project': {'title': 'Investigar acceso a la cueva', 'reason': 'Verificar entrada'},
            'active_research': None,
            'life_history': [
                {'id': 'old', 'when': 'Día 6 · 05:47', 'action': 'descend',
                 'successful': True,
                 'fact': 'Descendí a la cueva; identifiqué la salida hacia superficie.'},
                {'id': 'up', 'when': 'Día 6 · 23:22', 'action': 'ascend',
                 'successful': True, 'fact': 'Regresé a la superficie desde la cueva.'},
                *[{'id': f'repeat-{i}', 'when': 'Día 10', 'action': 'explore',
                   'successful': False,
                   'fact': 'No encuentro un sector accesible y desconocido desde aquí.'}
                  for i in range(20)],
            ],
        }
        # La entrada que Nilo ya recorrió figura en el terreno revelado;
        # el catálogo interno de sitios por sí solo no acredita conocimiento.
        self.world = {'sites': {'cueva': {'x': 23, 'y': 7, 'z': 0}},
                      'revealed': ['23,7,0']}

    def test_old_successful_descent_survives_recent_noise(self):
        recalled = recall_relevant(self.person, self.world)
        self.assertIn('old', [x['id'] for x in recalled])
        self.assertIn('up', [x['id'] for x in recalled])

    def test_location_triggers_recall_without_cave_in_title(self):
        self.person['project'] = {'title': 'Reconsiderar mi próximo objetivo'}
        recalled = recall_relevant(self.person, self.world)
        self.assertIn('old', [x['id'] for x in recalled])

    def test_no_recall_of_unrelated_distant_event(self):
        self.person['pos'] = [5, 5, 0]
        self.person['project'] = {'title': 'Investigar arcilla'}
        self.assertEqual(recall_relevant(self.person, self.world), [])

    def test_compact_provider_keeps_relevant_memory(self):
        context = {'momento': 'Día 10', 'posición': [22, 8, 0],
                   'memorias_relevantes': recall_relevant(self.person, self.world),
                   'conclusiones_verificadas': [],
                   'percepción_local': [{'texto': 'x'*200} for _ in range(50)]}
        compact = compact_context(context, char_budget=1050)
        self.assertTrue(any(x['id'] == 'old' for x in compact['memorias_relevantes']))
        self.assertLessEqual(len(compact['percepción_local']), 6)


class PrimaryEvidence(unittest.TestCase):
    def setUp(self):
        self.person = {'measurements': [
            measurement('m1', 'explore', 'No encuentro nuevas zonas', False),
            measurement('m2', 'inspect', 'Examiné entrada a una cueva'),
            measurement('m3', 'conclude', 'Concluí que otra conclusión fue correcta'),
            measurement('m4', 'compare', 'Comparé dos conclusiones'),
        ], 'conclusions': []}

    def test_conclude_measurement_is_not_physical_evidence(self):
        success, reason, entry = observational_conclusion(
            self.person, {'topic': 'cueva', 'evidence_ids': ['m3']}, 'Día 10')
        self.assertFalse(success)
        self.assertIsNone(entry)
        self.assertIn('conclusiones', reason.lower())

    def test_mixed_primary_and_derived_is_rejected(self):
        success, _, _ = observational_conclusion(
            self.person, {'topic': 'cueva', 'evidence_ids': ['m2', 'm3']}, 'Día 10')
        self.assertFalse(success)

    def test_primary_negative_and_positive_observations_work(self):
        success, _, entry = observational_conclusion(
            self.person, {'topic': 'frontera', 'evidence_ids': ['m1', 'm2']}, 'Día 10')
        self.assertTrue(success)
        self.assertEqual(entry['evidence_ids'], ['m1', 'm2'])
        self.assertEqual(entry['status'], 'observacion_comprobada')

    def test_reordering_same_evidence_does_not_create_another_conclusion(self):
        observational_conclusion(self.person,
            {'topic': 'frontera', 'evidence_ids': ['m1', 'm2']}, 'Día 10')
        success, _, entry = observational_conclusion(self.person,
            {'topic': 'frontera', 'evidence_ids': ['m2', 'm1']}, 'Día 10')
        self.assertFalse(success)
        self.assertIsNone(entry)


class ProjectClosure(unittest.TestCase):
    def test_conclude_result_cannot_close_a_project(self):
        project = {'title': 'Cerrar exploración', 'verified_results': [
            {'action': 'conclude', 'result': 'Conclusión basada en conclusión',
             'measurement_id': 'm3'}]}
        self.assertIsNone(completion_evidence(project, 'm3 prueba de cierre', {}))

    def test_unverified_potability_cannot_be_closed_by_drinking(self):
        project = {'title': 'Determinar potabilidad del agua', 'verified_results': [
            {'action': 'drink', 'result': 'Bebí de una fuente. Su potabilidad todavía no está comprobada.',
             'measurement_id': 'm1'}]}
        self.assertIsNone(completion_evidence(project, 'm1', {}))
        self.assertIsNone(completion_evidence(project,
            'Bebí de una fuente. Su potabilidad todavía no está comprobada.', {}))

    def test_genuine_water_location_can_be_closed(self):
        fact = 'Avancé hasta la orilla y encontré una fuente de agua.'
        project = {'title': 'Encontrar fuente de agua', 'verified_results': [
            {'action': 'go', 'result': fact, 'measurement_id': 'm1'}]}
        measured={'measurements':[{
            'id':'m1','op':'go','success':True,'evaluation_status':'verified_success',
            'verified_facts':[fact]}]}
        self.assertEqual(completion_evidence(project, fact,
            measured)['evidence_ids'],['m1'])

    def test_prototype_cannot_prove_shelter_function(self):
        fact = 'La estructura es un prototipo sin funcionamiento verificado.'
        project = {'title': 'Validar función del refugio', 'verified_results': [
            {'action': 'inspect', 'result': fact, 'measurement_id': 'm1'}]}
        self.assertIsNone(completion_evidence(project, fact, {}))


if __name__ == '__main__':
    unittest.main()
