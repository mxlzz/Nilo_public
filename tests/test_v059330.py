"""0.5.9.3.30 · Revisión semántica observacional, sin bloqueo de acciones."""
import unittest

from strategy_review import semantic_signature, evidence_snapshot, detect_repetition


class SemanticStrategy(unittest.TestCase):
    def setUp(self):
        self.p={'pos':[10,10,0],'project':{'id':'pr-rest',
                 'title':'Comparar recuperación energética en refugio'},
                'measurements':[{'op':'rest','rest_comparable':False}]}
        self.w={'revealed':['10,10,0'],'excavation':{},'structures':[]}

    def test_nearby_go_rest_variants_share_signature_without_rewriting_plan(self):
        a=[{'op':'go','x':11,'y':10},{'op':'rest','minutes':20}]
        b=[{'op':'go','x':10,'y':12},{'op':'rest','minutes':25}]
        c=[{'op':'go','x':12,'y':10},{'op':'rest','minutes':40}]
        signatures=[semantic_signature(self.p,s) for s in (a,b,c)]
        self.assertEqual(len(set(signatures)),1)
        self.assertEqual(a[0]['x'],11)
        self.assertNotEqual(signatures[0],semantic_signature(
            self.p,[{'op':'go','x':30,'y':10},{'op':'rest','minutes':20}]))

    def test_review_requires_three_same_project_deliberations_and_no_new_evidence(self):
        sig=semantic_signature(self.p,[{'op':'go','x':11,'y':10},{'op':'rest'}])
        snap=evidence_snapshot(self.p,self.w)
        h=[{'semantic_signature':sig,'evidence_snapshot':snap,'project_id':'pr-rest'}]
        self.assertIsNone(detect_repetition(h,sig,snap,'pr-rest'))
        h.append(dict(h[0]))
        warning=detect_repetition(h,sig,snap,'pr-rest',rest_energy=95)
        self.assertEqual(warning['coincidencias_consecutivas'],3)
        self.assertIn('60',warning['fundamentos'][-1])
        self.assertIn('no prueba',warning['alcance'])
        self.assertIsNone(detect_repetition(h,sig,snap,'other'))
        self.assertIsNone(detect_repetition(h,sig,snap+[1],'pr-rest'))
        self.assertIsNone(detect_repetition([{'signature':sig},{'signature':sig}],
                                             sig,snap,'pr-rest'))

    def test_distinct_explore_regions_and_methods_not_confused(self):
        self.assertNotEqual(semantic_signature(self.p,[{'op':'explore','direction':'east'}]),
                            semantic_signature(self.p,[{'op':'explore','direction':'west'}]))
        self.assertNotEqual(semantic_signature(self.p,[{'op':'explore','region':{'x':20,'y':9}}]),
                            semantic_signature(self.p,[{'op':'explore','region':{'x':5,'y':9}}]))
        self.assertNotEqual(semantic_signature(self.p,[{'op':'use','method':'golpear','item':'obj-1'}]),
                            semantic_signature(self.p,[{'op':'use','method':'cortar','item':'obj-1'}]))

    def test_progress_invalidates_repetition_even_if_text_unchanged(self):
        sig=semantic_signature(self.p,[{'op':'rest'}])
        original=evidence_snapshot(self.p,self.w)
        prior=[{'semantic_signature':sig,'evidence_snapshot':original,'project_id':'pr-rest'}]*2
        self.p['measurements'].append({'op':'rest','rest_comparable':True})
        self.assertNotEqual(original,evidence_snapshot(self.p,self.w))
        self.assertIsNone(detect_repetition(prior,sig,evidence_snapshot(self.p,self.w),'pr-rest'))



class EpisodicProvenance(unittest.TestCase):
    def test_new_experience_has_grounded_object_action_measurement_and_location(self):
        from inventions import record_personal_experience
        p={'pos':[10,10,0],'clock_minutes':150,
           'project':{'id':'project-2'},'life_history':[],
           'experience_summary':[]}
        step={'op':'craft','name':'punta de ensayo','_built_object_id':'obj-55'}
        record_personal_experience(
            p,step,True,True,['Fabriqué la pieza'],'Día 1',
            position=[10,10,0],measurement_id='med-5',action_id='act-5')
        episode=p['life_history'][-1]
        self.assertEqual(episode['id'],'exp-1')
        self.assertEqual(episode['object_id'],'obj-55')
        self.assertEqual(episode['project_id'],'project-2')
        self.assertEqual(episode['position_at_end'],[10,10,0])
        self.assertEqual(episode['measurement_id'],'med-5')
        self.assertEqual(episode['action_id'],'act-5')

    def test_legacy_replay_episode_is_byte_structure_compatible(self):
        from inventions import record_personal_experience
        p={'clock_minutes':100,'project':{'id':'p-old'},
           'life_history':[],'experience_summary':[]}
        record_personal_experience(p,{'op':'inspect','target':'roca'},True,True,
                                   ['Inspeccioné la roca'],'Día 1',
                                   position=[5,5,0],measurement_id='med-new',
                                   action_id='act-new',legacy=True)
        self.assertEqual(p['life_history'][0],
                         {'when':'Día 1','action':'inspect',
                          'successful':True,'fact':'Inspeccioné la roca'})

    def test_recall_picks_old_relevant_object_over_recent_unrelated_entries(self):
        from episodic_memory import recall_relevant
        episode={'id':'exp-23','when':'Día 2','action':'use','successful':False,
                 'fact':'El ensayo de excavación no produjo avance.',
                 'target':'obj-55','object_id':'obj-55','project_id':'project-2',
                 'position_at_end':[10,10,0],'measurement_id':'med-23',
                 'action_id':'act-23'}
        others=[{'when':'Día 9','action':'inspect','successful':True,
                 'fact':f'Observé otra región del bosque {i}.'} for i in range(140)]
        p={'project':{'id':'project-2','title':'Investigar herramienta'},
           'pos':[10,10,0],'action_outcomes':[{'target':'obj-55'}],
           'life_history':[episode,*others]}
        memory=recall_relevant(p,{'sites':{},'revealed':[]},limit=3)
        self.assertEqual(memory[0]['id'],'exp-23')
        self.assertEqual(memory[0]['accion_id'],'act-23')
        self.assertEqual(memory[0]['medicion_id'],'med-23')
        self.assertEqual(memory[0]['posicion_tras_accion'],[10,10,0])
        legacy={'action':'use','successful':True,'fact':'Probé otra herramienta.'}
        p['life_history']=[legacy]
        p['project']['title']='Probar herramienta'
        recalled=recall_relevant(p,{'sites':{},'revealed':[]})
        if recalled:
            self.assertNotIn('posicion_tras_accion',recalled[0])
            self.assertNotIn('accion_id',recalled[0])

    def test_compact_context_preserves_review_informative_signal(self):
        from brain import compact_context
        context={'momento':'Día 3','revision_de_estrategia':{
            'codigo':'repeticion_semantica_sin_evidencia_nueva',
            'fundamentos':['misma secuencia'], 'alcance':'No impone acciones'},
            'memorias_relevantes':[{'id':'exp-3','hecho':'Ensayo anterior','accion_id':'act-3'}],
            'regla':'Motor determinista'}
        compact=compact_context(context,4300)
        self.assertEqual(compact['revision_de_estrategia']['codigo'],
                         'repeticion_semantica_sin_evidencia_nueva')
        self.assertEqual(compact['memorias_relevantes'][0]['accion_id'],'act-3')


if __name__=='__main__':
    unittest.main()
