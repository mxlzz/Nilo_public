"""Regresiones de métricas descriptivas y contexto reducido: Nilo 0.5.7.1."""
import unittest
from behavior import record_behavior, behavior_summary
from brain import compact_context


def add(p, op, origin, duration, before, after, project, tiles=0,
        knowledge=0, materials=(), progress=False):
    return record_behavior(
        p, op=op, origin=origin, duration_minutes=duration,
        position_before=before, position_after=after, project_id=project,
        new_tiles=tiles, new_knowledge=knowledge,
        new_materials=materials, progress=progress)


class BehaviorMetrics(unittest.TestCase):
    def test_empty_history_is_not_fabricated(self):
        p = {'clock_minutes': 10000, 'action_outcomes': [{'op': 'go'}]}
        self.assertEqual(behavior_summary(p)['estado'], 'sin_datos')
        self.assertNotIn('behavior_metrics', p)

    def test_verified_novelty_origins_and_revisits(self):
        p = {'clock_minutes': 10}
        add(p, 'go', 'llm', 19, [0, 0, 0], [1, 0, 0], 'proy-a',
            tiles=2, materials=('madera',), progress=True)
        p['clock_minutes'] = 30
        add(p, 'inspect', 'motor', 9, [1, 0, 0], [1, 0, 0], 'proy-a',
            materials=('madera',))
        p['clock_minutes'] = 60
        add(p, 'go', 'llm', None, [2, 0, 0], [1, 0, 0], 'proy-b',
            knowledge=1, progress=True)
        s = behavior_summary(p)
        self.assertEqual(s['acciones_registradas'], 3)
        self.assertEqual(s['acciones_por_clase']['exploracion'], 3)
        self.assertEqual(s['acciones_por_origen'], {'llm': 2, 'motor': 1})
        self.assertEqual(s['acciones_con_duracion_medida'], 2)
        self.assertEqual(s['minutos_medidos_por_clase']['exploracion'], 28)
        self.assertEqual(s['acciones_con_progreso_segun_motor'], 2)
        self.assertEqual(s['acciones_con_novedad_observable'], 2)
        self.assertAlmostEqual(s['proporcion_con_novedad_observable'], 2/3, places=3)
        self.assertEqual(s['casillas_nuevas_reveladas'], 2)
        self.assertEqual(s['registros_de_conocimiento_nuevos'], 1)
        self.assertEqual(s['materiales_distintos_obtenidos'], 1)
        self.assertEqual(s['destinos_distintos_al_moverse'], 1)
        self.assertEqual(s['regresos_a_destinos_ya_visitados'], 1)
        self.assertEqual(s['cambios_entre_proyectos_activos'], 1)
        self.assertEqual(s['desde_minuto_simulado'], 10)

    def test_old_data_remains_untouched_and_time_not_guessed(self):
        p = {'clock_minutes': 1, 'action_outcomes': [{'id': 'original'}]}
        add(p, 'design', 'llm', None, [0,0,0], [0,0,0], None)
        s = behavior_summary(p)
        self.assertEqual(s['acciones_con_duracion_medida'], 0)
        self.assertEqual(s['minutos_medidos_por_clase'], {})
        self.assertEqual(p['action_outcomes'], [{'id': 'original'}])

    def test_optional_metrics_can_be_dropped_on_small_provider_budget(self):
        base = {'momento': 'Día 2', 'posición': [1,2,0],
                'proyecto_actual': {'id':'p','title':'Proyecto importante'},
                'conclusiones_verificadas':[{'id':'con-1','text':'Dato real'}],
                'comportamiento_medido':{'acciones_registradas':10,'factual':'x'*1000}}
        large = compact_context(base, 6000)
        self.assertIn('comportamiento_medido', large)
        small = compact_context(base, 150)
        self.assertNotIn('comportamiento_medido', small)
        self.assertEqual(small['conclusiones_verificadas'][0]['id'], 'con-1')
        self.assertEqual(small['proyecto_actual']['id'], 'p')


if __name__ == '__main__':
    unittest.main()
