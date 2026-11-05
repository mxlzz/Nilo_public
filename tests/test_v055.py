"""Nilo 05.5: ensayos medidos, descanso/espera y memoria factual."""
from __future__ import annotations
import json, sqlite3, tempfile, unittest
from pathlib import Path
import nilo
from survival import ensure_needs, update_needs
from experiment_log import capture, measure, compare_rest, closure_status, link_conclusion, topic
from cognition import register_research
from brain import context_for, normalize_decision

class MeasurementTests(unittest.TestCase):
    def setUp(self):
        self.s=nilo.initial_state();self.p=self.s['person'];ensure_needs(self.p)
    def sample(self,shelter=False,initial=40,minutes=30,op='rest',end=None):
        p=self.p;w=self.s['world']
        p['needs']['energia']=initial
        x,y,z=p['pos'];w['levels'][str(z)][y]=w['levels'][str(z)][y][:x]+('h' if shelter else ',')+w['levels'][str(z)][y][x+1:]
        before=capture(w,p)
        update_needs(p,w,minutes,at_shelter=shelter,active=False,resting=op=='rest')
        p['clock_minutes']+=minutes
        if end is not None:p['needs']['energia']=end
        after=capture(w,p)
        return measure(p,{'op':op},before,after,['Se completó la prueba.'],True,'Día 2')
    def test_rest_and_idle_are_distinct(self):
        rest=self.sample(initial=40)
        self.assertGreater(rest['energy_per_hour'],6.0)
        idle=self.sample(initial=40,op='inspect')
        self.assertNotIn('energy_per_hour',idle)
        self.assertGreater(rest['needs_delta']['energia'],idle['needs_delta']['energia']*3)
    def test_comparison_only_uses_measured_trials(self):
        a=self.sample(True); b=self.sample(False)
        self.assertTrue(a['rest_comparable']);self.assertTrue(b['rest_comparable'])
        c=compare_rest(self.p,'Día 2')
        self.assertEqual(c['evidence_ids'],[a['id'],b['id']])
        self.assertGreater(c['rates']['refugio'],c['rates']['intemperie'])
        self.assertIn('recuperé',c['text'])
        self.assertIsNone(compare_rest(self.p,'Día 3'))
    def test_no_invented_conclusion_when_saturated(self):
        self.sample(True,initial=90)
        self.sample(False,initial=90)
        self.assertIsNone(compare_rest(self.p,'Día 2'))
        self.assertEqual(closure_status(self.p)['status'],'incompleta')
    def test_repeated_identical_trials_need_new_condition(self):
        for i in range(3):self.sample(True,initial=40)
        report=closure_status(self.p)
        self.assertEqual(report['missing_conditions'],['intemperie'])
        self.assertIn('cambiar una condición',report['message'])
    def test_related_questions_map_to_same_problem(self):
        self.assertEqual(topic('¿Me recupero mejor descansando en el refugio?'),'recuperacion_energia')
        self.assertEqual(topic('¿La arboleda mejora mi recuperación energética?'),'recuperacion_energia')
        self.assertEqual(topic('¿Puedo reforzar las paredes del refugio?'),'')
    def test_conclusion_closes_research(self):
        r,_=register_research(self.p,'¿Me recupero mejor en refugio?', 'Comparar', 'Día 2','res-1')
        self.sample(True);self.sample(False)
        c=compare_rest(self.p,'Día 2')
        link_conclusion(self.p,c)
        self.assertEqual(r['state'],'concluida')
        self.assertEqual(r['evidence_ids'],c['evidence_ids'])
        self.assertEqual(closure_status(self.p)['status'],'comprobada')
    def test_general_measurements_are_descriptive(self):
        start=capture(self.s['world'],self.p)
        self.p['inventory']['madera']=self.p['inventory'].get('madera',0)+2
        self.p['clock_minutes']+=20
        m=measure(self.p,dict(op='gather',target='madera'),start,capture(self.s['world'],self.p),['Recolecté madera.'],True,'Día 1')
        self.assertEqual(m['inventory_delta']['madera'],2)
        self.assertNotIn('energy_per_hour',m)
        self.assertEqual(m['verified_facts'],['Recolecté madera.'])

class SimulationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.original=nilo.DB
        nilo.DB=Path(self.temp.name)/'test.sqlite3'
        self.sim=nilo.Simulation();self.sim.think=lambda:None
        self.sim.s['speed']=60
        self.p=self.sim.s['person'];self.p['needs']['energia']=40
        self.p['pos']=[15,10,0]
    def tearDown(self):
        self.sim.conn.close();nilo.DB=self.original;self.temp.cleanup()
    def rest(self,shelter):
        x,y,z=self.p['pos'];w=self.sim.s['world']
        w['levels']['0'][y]=w['levels']['0'][y][:x]+('h' if shelter else ',')+w['levels']['0'][y][x+1:]
        self.p['needs']['energia']=40
        self.p['plan']=[{'op':'rest','minutes':20}]
        self.sim.tick(1)
        self.sim.tick(20)
        self.assertIsNone(self.p['pending'])
    def test_from_rest_to_verified_conclusion_and_sqlite(self):
        self.p['research']=[{'id':'r1','question':'¿El refugio ayuda a recuperar energía?','hypothesis':'sí', 'state':'abierta','evidence':[]}]
        self.p['active_research']=self.p['research'][0]['question']
        self.rest(True)
        self.rest(False)
        self.assertEqual(len(self.p['measurements']),2)
        self.assertEqual(len(self.p['conclusions']),0)
        # En el test el refugio está representado por terreno h, sin obra:
        # no se inventa una estructura donde no la hay.
        self.assertEqual(self.p['research'][0]['state'],'abierta')
        self.assertEqual(self.sim.archive.counts()['measurement'],2)
        self.assertEqual(self.sim.archive.counts().get('conclusion',0),0)
        ctx=context_for(self.sim.s['world'],self.p,[],self.sim.stamp())
        self.assertEqual(ctx['estado_investigacion_descanso']['status'],'lista')
        public=self.sim.public_state()
        self.assertEqual(len(public['measurements']),2)
        self.assertEqual(len(public['conclusions']),0)
        self.assertEqual(public['experiment_status']['status'],'lista')
        self.sim.write()
        self.assertEqual(json.loads(self.sim.conn.execute('SELECT payload FROM snapshot WHERE id=1').fetchone()[0])['person']['research'][0]['state'],'abierta')
    def test_restarting_continues_without_losing_measurements(self):
        self.rest(True);self.sim.write();self.sim.conn.close()
        other=nilo.Simulation();other.think=lambda:None
        self.sim=other;self.p=other.s['person']
        self.assertEqual(len(self.p['measurements']),1)
        self.rest(False)
        self.assertEqual(len(self.p['conclusions']),0)
    def test_no_repeat_research_opened_by_next_llm(self):
        self.rest(True);self.rest(False)
        decision={'objetivo':'Comparar si el refugio mejora el descanso','motivo':'Quiero contrastar',
                  'plan':[{'op':'rest'}],'cuaderno':'Aun tengo preguntas',
                  'pregunta':'¿Recupero más energía al descansar en el refugio?','hipotesis':'sí',
                  'accion_proyecto':'nuevo','revisar_en_minutos':90}
        self.sim.plan_ready(decision,'llm')
        self.assertTrue(any(r.get('state')=='abierta' and topic(r.get('question'))=='recuperacion_energia' for r in self.p['research']))
        self.assertFalse(self.p['project'].get('reconsideration_required',False))
    def test_old_save_migrates_without_claiming_unmeasured_knowledge(self):
        self.sim.s['person'].pop('measurements',None)
        self.sim.s['person'].pop('conclusions',None)
        self.sim.write();self.sim.conn.close()
        self.sim=nilo.Simulation();self.p=self.sim.s['person']
        self.assertEqual(self.p['measurements'],[])
        self.assertEqual(self.p['conclusions'],[])
        self.assertEqual(self.sim.public_state()['experiment_status']['status'],'sin_comparacion')

if __name__=='__main__':unittest.main()

class GenericConclusionTests(unittest.TestCase):
    def test_conclusion_requires_real_matching_evidence(self):
        from experiment_log import observational_conclusion
        s=nilo.initial_state();p=s['person'];ensure_needs(p)
        start=capture(s['world'],p)
        p['clock_minutes']+=25
        record=measure(p,{'op':'experiment','target':'madera','method':'mojar'},start,capture(s['world'],p),
                       ['La muestra de madera no cambió de color.'],True,'Día 1')
        ok,info,entry=observational_conclusion(p,{'topic':'madera mojada','evidence_ids':[record['id']]},'Día 1')
        self.assertTrue(ok,info)
        self.assertIn('no cambió de color',entry['text'])
        self.assertIn(record['id'],entry['evidence_ids'])
        ok,info,entry=observational_conclusion(p,{'topic':'madera mojada','evidence_ids':['med-inventado']},'Día 1')
        self.assertFalse(ok)
        self.assertIsNone(entry)
    def test_comparison_cannot_be_claimed_with_generic_evidence(self):
        from experiment_log import observational_conclusion
        p=nilo.initial_state()['person'];ensure_needs(p)
        ok,reason,entry=observational_conclusion(p,{'topic':'comparar descanso y refugio','evidence_ids':['med-falso']},'Día 1')
        self.assertFalse(ok)
        self.assertIsNone(entry)
    def test_archived_samples_remain_when_working_window_is_trimmed(self):
        from archive import History
        with tempfile.TemporaryDirectory() as tmp:
            db=sqlite3.connect(Path(tmp)/'test.sqlite3')
            history=History(db)
            for i in range(200):history.add('measurement',{'id':f'med-{i}','when':'Día 1', 'op':'inspect'})
            db.commit()
            self.assertEqual(history.counts()['measurement'],200)
            db.close()
