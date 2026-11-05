"""0.5.9.3.5 — síntesis priorizada, continuación y lecturas exactas."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import nilo
from observer import importance, pending_sources, MIN_IMPORTANCE
from archive import History
from review_store import ReviewStore
import sqlite3

class PrioritizationTests(unittest.TestCase):
    def setUp(self):
        self.conn=sqlite3.connect(':memory:')
        self.archive=History(self.conn)
        self.review=ReviewStore(self.conn)
        self.review.bootstrap({})
        self.state={'person':{'pending':None},'world':{}}
    def tearDown(self):self.conn.close()

    def test_important_record_number_130_wins_over_first_100(self):
        for i in range(150):
            title='Construí un dispositivo nuevo y lo comprobé' if i==129 else 'Rutina: descansé sin cambios'
            self.archive.add('news',{'id':f'n-{i}','title':title,'when':f'Día {i+1}'})
        selected,refs,remaining=pending_sources(self.state,self.archive,self.review,[],limit=7)
        self.assertEqual([r['id'] for r in selected],['n-129'])
        self.assertEqual(len(refs),1)
        self.assertEqual(remaining,0)
        self.assertEqual(self.archive.count_unread('news'),150)

    def test_more_is_decreasing_priority_and_does_not_repeat(self):
        for i in range(12):
            self.archive.add('news',{'id':f'n-{i}','title':f'Construí una estructura {i}'})
        first,refs,remaining=pending_sources(self.state,self.archive,self.review,[],limit=7)
        self.assertEqual(len(first),7)
        self.assertEqual(remaining,5)
        first_ids={r['id'] for r in first}
        for ref in refs:self.archive.mark_one_read('news',self.archive.seq_for('news',ref['id']))
        second,_,rest=pending_sources(self.state,self.archive,self.review,[],limit=7,
                                     max_seq=self.archive.max_seq('news'),
                                     score_ceiling=first[-1]['priority'])
        self.assertEqual(len(second),5)
        self.assertFalse(first_ids & {r['id'] for r in second})
        self.assertEqual(rest,0)

    def test_snapshot_excludes_new_events(self):
        self.archive.add('news',{'id':'old','title':'Construí una máquina'})
        seq=self.archive.max_seq('news')
        self.archive.add('news',{'id':'new','title':'Descubrí un mecanismo'})
        found,_,_=pending_sources(self.state,self.archive,self.review,[],
                                 max_seq=seq,limit=7)
        self.assertEqual([r['id'] for r in found],['old'])

    def test_no_interest_does_not_erase_routines(self):
        for i in range(20):
            self.archive.add('news',{'id':f'n-{i}','title':'Rutina: descansé sin cambios'})
        records,refs,remaining=pending_sources(self.state,self.archive,self.review,[])
        self.assertEqual(records,[])
        self.assertEqual(refs,[])
        self.assertEqual(remaining,0)
        self.assertEqual(self.archive.count_unread('news'),20)

    def test_same_conclusion_in_findings_and_measurements_is_one_source(self):
        record={'id':'con-1','text':'Concluí que el recipiente retiene agua'}
        self.archive.add('conclusion',record)
        self.state['person']['conclusions']=[record]
        sources=[
            {'tab':'findings','key':'con-1','kind':'finding','id':'con-1'},
            {'tab':'measurements','key':'con-1','kind':'conclusion','id':'con-1'}]
        records,refs,_=pending_sources(self.state,self.archive,self.review,sources)
        self.assertEqual([r['id'] for r in records],['con-1'])
        self.assertEqual({(r['tab'],r['key']) for r in refs},
                         {('findings','con-1'),('measurements','con-1')})

    def test_importance_is_deterministic_and_ignores_routine_noise(self):
        high={'kind':'news','text':'Se comprobó un nuevo dispositivo'}
        low={'kind':'news','text':'Rutina: descansé sin cambios'}
        self.assertGreater(importance(high),importance(low))
        self.assertGreaterEqual(importance(high),MIN_IMPORTANCE)

class SummaryIntegration(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.sim=nilo.Simulation(db_path=Path(self.temp.name)/'nilo.sqlite3')
        self.sim.bootstrap_reviews({})
        self.cfg={'PROVIDER':'gemini','MODEL':'test','GEMINI_API_KEY':'fake',
                  'MAX_CHAT_CALLS_PER_DAY':'100'}
        self.mock_config=patch.object(nilo,'config',return_value=self.cfg)
        self.mock_available=patch.object(nilo,'available',return_value=True)
        self.mock_route=patch.object(nilo,'route',
                       return_value=(('Síntesis de hechos respaldados.',{}),'gemini','test'))
        for p in (self.mock_config,self.mock_available,self.mock_route):p.start()
    def tearDown(self):
        for p in (self.mock_route,self.mock_available,self.mock_config):p.stop()
        self.sim.conn.close()
        self.temp.cleanup()

    def test_pages_mark_only_sources_displayed_not_others(self):
        for i in range(22):
            self.sim.archive.add('news',{'id':f'n-{i}','title':f'Construí un refugio {i}',
                                         'when':f'Día {i}'})
        first=self.sim.observer_summary([])
        self.assertEqual(first['count'],12)
        self.assertEqual(first['remaining'],10)
        self.assertEqual(len(first['links']),12)
        self.assertEqual(self.sim.archive.count_unread('news'),22)
        self.sim.acknowledge_observer_summary(first['id'])
        self.assertEqual(self.sim.archive.count_unread('news'),10)
        second=self.sim.observer_summary([],first['continuation'])
        self.assertEqual(second['count'],10)
        self.assertEqual(second['remaining'],0)
        self.assertIsNone(second['continuation'])
        self.sim.acknowledge_observer_summary(second['id'])
        self.assertEqual(self.sim.archive.count_unread('news'),0)
        self.assertEqual(len(self.sim.observer_summary_history()),2)

    def test_new_high_priority_event_after_first_page_is_not_swallowed(self):
        for i in range(15):
            self.sim.archive.add('news',{'id':f'n-{i}','title':f'Construí aparato {i}'})
        first=self.sim.observer_summary([])
        self.sim.archive.add('news',{'id':'new','title':'Descubrí algo crucial'})
        self.sim.acknowledge_observer_summary(first['id'])
        second=self.sim.observer_summary([],first['continuation'])
        self.assertNotIn('new',{r['id'] for r in second['links']})
        self.sim.acknowledge_observer_summary(second['id'])
        self.assertFalse(self.sim.archive.is_read('news',self.sim.archive.seq_for('news','new')))
        next_first=self.sim.observer_summary([])
        self.assertIn('new',{r['id'] for r in next_first['links']})

    def test_no_relevance_no_call_and_no_false_read(self):
        self.sim.archive.add('news',{'id':'routine','title':'Rutina: descansé sin cambios'})
        with patch.object(nilo,'route',side_effect=AssertionError('No hay hechos relevantes')):
            empty=self.sim.observer_summary([])
        self.assertTrue(empty['empty'])
        self.assertEqual(self.sim.archive.count_unread('news'),1)

class InterfaceStructure(unittest.TestCase):
    def test_more_button_is_linked_to_continuation(self):
        html=(Path(__file__).resolve().parent.parent/'interfaz.html').read_text('utf8')
        self.assertIn('id="catchup-more"',html)
        self.assertIn('id="catchup-history"',html)
        self.assertGreater(html.index('id="catchup-more"'),html.index('id="catchup-content"'))
        self.assertIn('renderNextObserverSummary(summaryContinuation,summaryGeneration)',html)
        self.assertIn('Registros destacados (',html)
        self.assertIn('summaryContinuation=packet.continuation||null',html)
        self.assertIn("'news','journal'",(Path(__file__).resolve().parent.parent/'nilo.py').read_text('utf8'))
if __name__=='__main__':unittest.main()
