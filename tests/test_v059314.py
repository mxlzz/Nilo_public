"""0.5.9.3.14: integración de recolección, evidencia y rutas conocidas."""
import random
import unittest

from action_results import evidence_before, result_from_execution
from goal_evidence import check_goal, select_closure_evidence
from habits import choose_wait_action, record_skill, set_wait_preferences
from laboratory import measured_physics
from nilo import initial_state, is_newsworthy
from world import execute_action, move, new_world, set_tile, tile_key


class RecoleccionSinParseoDeTexto(unittest.TestCase):
    def scenario(self, qty):
        state = initial_state()
        person, world = state['person'], state['world']
        person['pos'] = [15, 10, 0]
        set_tile(world, 15, 10, 0, 'T')
        world['deposits'][tile_key(15, 10, 0)] = qty
        return world, person

    def test_una_y_dos_unidades_habilitan_recoleccion_sin_llm(self):
        for qty in (1, 2):
            with self.subTest(qty=qty):
                world, person = self.scenario(qty)
                step = {'op': 'gather', 'target': 'arboleda'}
                before = dict(person['inventory'])
                physical_before = evidence_before(person)
                legacy = execute_action(world, person, step, random.Random(13))
                duration, facts, success, notable = legacy
                self.assertTrue(success, facts)
                self.assertEqual(person['inventory']['madera'] - before.get('madera', 0), qty)
                result = result_from_execution(step, legacy, person, physical_before)
                self.assertEqual(result.status, 'verified_success')
                self.assertIsNone(measured_physics(person, step, success, facts))
                self.assertFalse(is_newsworthy(facts[-1], 'resultado'))
                skill = record_skill(person, step, success, facts, 'Día 1', before)
                self.assertIsNotNone(skill)
                self.assertEqual(person['skills']['gather:madera']['count'], 1)
                self.assertTrue(skill['verified'])
                # Nueva reserva tangible y stock bajo: la rutina se puede elegir
                # sin nueva deliberación, usando el aprendizaje registrado.
                person['inventory']['madera'] = 0
                world['deposits'][tile_key(15, 10, 0)] = 2
                # La habilidad solo se automatiza si Nilo la delegó expresamente.
                self.assertIsNone(choose_wait_action(world, person))
                set_wait_preferences(person,[{'op':'gather','target':'madera','hasta':3,'radio':2}], 'Día 1')
                waiting = choose_wait_action(world, person)
                self.assertIsNotNone(waiting)
                self.assertEqual(waiting[0], {'op': 'gather', 'target': 'madera'})

    def test_el_resultado_no_depende_de_la_redaccion(self):
        world, person = self.scenario(2)
        old = dict(person['inventory'])
        person['inventory']['madera'] = old.get('madera', 0) + 2
        skill = record_skill(person, {'op': 'gather', 'target': 'madera'}, True,
                             ['Resultado físico confirmado'], 'Día 1', old)
        self.assertIsNotNone(skill)
        self.assertEqual(skill['target'], 'madera')

    def test_no_registra_habilidad_sin_incremento_o_exito(self):
        for success, delta, target in ((False, 2, 'madera'),
                                       (True, 0, 'madera'),
                                       (True, 1, 'material inexistente')):
            with self.subTest(success=success, delta=delta, target=target):
                _, person = self.scenario(2)
                old = dict(person['inventory'])
                person['inventory']['madera'] = old.get('madera', 0) + delta
                self.assertIsNone(record_skill(
                    person, {'op': 'gather', 'target': target},
                    success, ['Recogí material.'], 'Día 1', old))
                self.assertFalse(person['skills'])


class CierresSinEvidenciaTematicaFalsa(unittest.TestCase):
    def case(self, title, fact, op, target='', method=''):
        mid = 'med-prueba'
        project = {'id': 'pr-prueba', 'title': title,
                   'verified_results': [{'measurement_id': mid,
                                         'action': op, 'result': fact}]}
        person = {'measurements': [{'id': mid, 'op': op, 'target': target,
                                   'method': method, 'success': True,
                                   'evaluation_status': 'verified_success',
                                   'verified_facts': [fact]}]}
        return project, person

    def test_la_dureza_de_piedra_no_demuestra_flotacion(self):
        title = 'Demostrar que la piedra flota sobre el agua'
        fact = 'Al golpear piedra, su dureza estimada es 7/10.'
        project, person = self.case(title, fact, 'experiment', 'piedra', 'golpear')
        self.assertFalse(check_goal(project, person)[0])
        self.assertIsNone(select_closure_evidence(project, person, fact))

    def test_la_dureza_no_demuestra_capacidad_para_cortar_madera(self):
        project, person = self.case(
            'Determinar si la piedra permite cortar madera de forma eficiente',
            'Al golpear piedra, su dureza estimada es 7/10.', 'experiment',
            'piedra', 'golpear')
        self.assertFalse(check_goal(project, person)[0])

    def test_comer_no_prueba_conservacion_prolongada(self):
        project, person = self.case(
            'Descubrir cómo conservar alimento durante semanas',
            'Comí una porción de alimento vegetal.', 'eat', 'alimento')
        self.assertFalse(check_goal(project, person)[0])


class MovimientoSinMapaOculto(unittest.TestCase):
    def test_no_usa_atajo_por_casilla_no_revelada(self):
        world = new_world(7321)
        person = {'pos': [10, 10, 0]}
        known = [(10, 10), (10, 11), (11, 11), (12, 11), (12, 10)]
        for x, y in known + [(11, 10)]:
            set_tile(world, x, y, 0, '.')
        world['revealed'] = [tile_key(x, y, 0) for x, y in known]
        world['trail'] = []
        steps, _ = move(world, person, (12, 10), 9)
        self.assertEqual(steps, 4)
        self.assertEqual(person['pos'], [12, 10, 0])
        self.assertNotIn(tile_key(11, 10, 0), world['trail'])


if __name__ == '__main__':
    unittest.main()
