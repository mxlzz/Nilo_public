from ui_fixture import legacy_markup, legacy_html_path
"""Regresiones .32: progreso espacial, autonomía y contexto de proyectos."""
import tempfile
import unittest
from pathlib import Path
from project_progress import discovered_during_action,advance_evidence,repeated_methods
from nilo import Simulation
from brain import context_for,compact_context
from project_lifecycle import closure_diagnostic


class NavigationEvidence(unittest.TestCase):
    def test_tiles_revealed_mid_navigation_count_as_progress(self):
        world={'revealed':['1,1,0','2,1,0','3,1,0','4,1,0']}
        pending={'behavior_revealed_at_start':1}
        discovered=discovered_during_action(world,pending,4)
        self.assertEqual(discovered,3)
        result=advance_evidence(new_tiles=discovered)
        self.assertTrue(result['progress'])
        self.assertEqual(result['reasons'],['territorio'])

    def test_revisited_route_does_not_count_as_discovery(self):
        world={'revealed':['1,1,0','2,1,0']}
        self.assertEqual(discovered_during_action(world,{'behavior_revealed_at_start':2},2),0)
        self.assertFalse(advance_evidence(new_tiles=0)['progress'])

    def test_partial_blocked_navigation_still_reports_real_discovery(self):
        world={'revealed':['1,1,0','2,1,0']}
        self.assertTrue(advance_evidence(new_tiles=discovered_during_action(
            world,{'behavior_revealed_at_start':1,'navigation':{'blocked':True}},2))['progress'])

    def test_legacy_replay_uses_old_baseline_and_missing_marker_is_conservative(self):
        world={'revealed':['1,1,0','2,1,0','3,1,0']}
        self.assertEqual(discovered_during_action(world,{'behavior_revealed_at_start':1},3,legacy=True),0)
        self.assertEqual(discovered_during_action(world,{},3),0)

    def test_repeated_methods_are_observational_only(self):
        attempts=[{'project_id':'P','op':'explore','progress':False,'pos':[x,8,0]} for x in (3,4,5)]
        self.assertEqual(repeated_methods(attempts,'P'),['explore'])
        self.assertEqual(repeated_methods(attempts,'other'),[])


class Continuity(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.sim=Simulation(db_path=Path(self.temp.name)/'nilo.sqlite')
        self.p=self.sim.s['person']

    def tearDown(self):
        self.sim.conn.close()
        self.temp.cleanup()

    def test_close_rejection_classifies_missing_criterion_without_fake_success(self):
        target={'id':'P','title':'Transportar agua con recipiente','status':'activo',
                'verified_results':[{'measurement_id':'med-1','action':'use','result':'Contuvo agua.'}]}
        self.p['project']=target
        self.p.setdefault('measurements',[]).append({
            'id':'med-1','op':'use','success':True,'evaluation_status':'verified_success',
            'method':'contener','target':'agua','verified_facts':['Contuvo agua.']})
        result=closure_diagnostic(target,self.p,'med-1')
        self.assertEqual(result['estado'],'criterio_no_instrumentado')
        self.assertFalse(result['comprobado'])

    def test_ready_reminder_exposes_only_own_paused_project(self):
        self.p['projects']=[{'id':'pause-a','title':'Estudiar mineral','status':'pausado',
                 'closure_reason':'Falta muestra','verified_results':[]},
                 {'id':'pause-b','title':'Estudiar agua','status':'pausado',
                 'closure_reason':'Interés suspendido'}]
        self.p['agenda']=[{'id':'tar-1','modo':'recordatorio','estado':'lista_para_revisar',
            'proyecto_id':'pause-a','titulo':'Retomar mineral',
            'motivo':'Obtuve muestra','condicion_cumplida':'Día 4','cuando':{}}]
        self.assertIsNone(self.p.get('project'))
        context=context_for(self.sim.s['world'],self.p,[],'Día 4',self.sim.scenario)
        ready=context['proyectos_reanudables']
        self.assertEqual(len(ready),1)
        self.assertEqual(ready[0]['id'],'pause-a')
        self.assertEqual(ready[0]['motivo_pausa'],'Falta muestra')
        compact=compact_context(context,7000)
        self.assertEqual(compact['proyectos_reanudables'][0]['id'],'pause-a')
        self.assertIsNone(self.p['project'])

    def test_queued_work_finishes_without_claiming_goal(self):
        from agenda import record_agenda_result
        task={'id':'task-1','titulo':'Verificar refugio','estado':'en_curso',
              'indice':0,'pasos':[{'op':'rest'}],'resultados':[]}
        person={'agenda':[task],'agenda_history':[]}
        record_agenda_result(person,{'op':'rest','_agenda_id':'task-1'},
                             True,['Descansé 30 minutos'],'Día 2')
        self.assertEqual(task['estado'],'completada')
        self.assertEqual(task['cumplimiento_objetivo']['estado'],'no_verificado_por_ejecucion')

    def test_legacy_agenda_replay_keeps_original_record_structure(self):
        from agenda import record_agenda_result
        task={'id':'task-1','titulo':'Verificar refugio','estado':'en_curso',
              'indice':0,'pasos':[{'op':'rest'}],'resultados':[]}
        person={'agenda':[task],'agenda_history':[]}
        record_agenda_result(person,{'op':'rest','_agenda_id':'task-1'},
                             True,['Descansé 30 minutos'],'Día 2',legacy=True)
        self.assertNotIn('cumplimiento_objetivo',task)
        self.assertEqual(task['ultimo_motivo'],'Secuencia terminada')

    def test_agenda_interface_shows_explicit_nonverification(self):
        from pathlib import Path
        ui=legacy_markup(Path(__file__).resolve().parents[1])
        self.assertIn("t.cumplimiento_objetivo?.estado==='no_verificado_por_ejecucion'",ui)
        self.assertIn('Los pasos se ejecutaron; el cumplimiento del objetivo declarado',ui)

    def test_exact_duplicate_keeps_authorized_plan_current_rules(self):
        from brain import normalize_decision
        self.p['project']={'id':'pr-repeat','title':'Examinar piedra',
            'status':'activo','verified_results':[],'deliberations':2,
            'deliberations_since_progress':2,'no_progress_steps':0}
        decision=normalize_decision({
            'cuaderno':'Voy a revisar la piedra cercana.',
            'objetivo':'Examinar piedra','motivo':'Aún no resolví este ensayo.',
            'accion_proyecto':'continuar','proyecto_id':'pr-repeat',
            'estado_actual':'Ensayo pendiente','plan':[{'op':'inspect','target':'roca'}]})
        self.sim.plan_ready(decision,'llm')
        self.sim.plan_ready(decision,'llm')
        self.assertEqual(self.p['plan'][0]['op'],'inspect')
        self.assertTrue(self.p['project']['reconsideration_required'])


if __name__=='__main__':
    unittest.main()
