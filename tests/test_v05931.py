from ui_fixture import legacy_markup, legacy_html_path
"""0.5.9.3.1 — lectura compartida, síntesis de pendientes y accesos rápidos."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import nilo
from archive import History
from review_store import ReviewStore
from observer import pending_sources

ROOT=Path(__file__).resolve().parent.parent

class ReviewStoreTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        self.archive=History(self.db)
        self.reviews=ReviewStore(self.db)
    def tearDown(self):self.db.close()

    def test_bootstrap_and_persistent_tab_reads(self):
        self.assertFalse(self.reviews.initialized())
        self.reviews.bootstrap({'research':['r1:abierta'], 'findings':['c1']})
        self.assertTrue(self.reviews.initialized())
        self.assertTrue(self.reviews.is_seen('research','r1:abierta'))
        self.assertTrue(self.reviews.is_seen('findings','c1'))
        self.assertFalse(self.reviews.bootstrap({'research':['r2:cerrada']}))
        self.assertFalse(self.reviews.is_seen('research','r2:cerrada'))
        self.assertIn('r1:abierta',ReviewStore(self.db).seen()['research'])

    def test_summary_ack_marks_exact_snapshot(self):
        self.archive.add('journal',{'id':'note1','text':'Primera nota'})
        self.archive.add('news',{'id':'news1','title':'Primer hallazgo'})
        self.reviews.bootstrap({})
        self.reviews.mark([('measurements','med1')])
        sid=self.reviews.new_summary('Lo más importante',['ignored'] if False else [
           {'category':'journal','id':'note1'},{'category':'news','id':'news1'},
           {'tab':'measurements','key':'med1','id':'med1','category':'measurement'}], 'test')
        self.archive.add('news',{'id':'news2','title':'Apareció después'})
        self.assertFalse(self.archive.is_read('journal',self.archive.seq_for('journal','note1')))
        self.reviews.acknowledge(sid,self.archive)
        self.assertTrue(self.archive.is_read('journal',self.archive.seq_for('journal','note1')))
        self.assertTrue(self.archive.is_read('news',self.archive.seq_for('news','news1')))
        self.assertFalse(self.archive.is_read('news',self.archive.seq_for('news','news2')))
        self.assertEqual(len(self.reviews.recent_summaries()),1)
        self.assertTrue(self.reviews.summary(sid)['acknowledged'])

    def test_source_selection_excludes_seen_and_deduplicates(self):
        self.reviews.bootstrap({'measurements':['med-1']})
        self.archive.add('measurement',{'id':'med-1','op':'rest','verified_facts':['Recuperé energía']})
        self.archive.add('conclusion',{'id':'con-1','text':'Esta muestra funcionó'})
        self.archive.add('journal',{'id':'note1','text':'Anotación pendiente','origin':'llm'})
        state={'person':{'pending':None,'conclusions':[{'id':'con-1','text':'Esta muestra funcionó'}],
                         'research':[],'projects':[],'project':None,'prediction_log':[],
                         'measurements':[],'designs':[],'proposals':[],'agenda':[],
                         'experience_summary':[],'waiting_history':[],'skills':{},'knowledge':{}},
               'world':{'structures':[],'retired_structures':[]},'events':[]}
        candidates=[
          {'tab':'measurements','key':'med-1','kind':'measurement','id':'med-1'},
          {'tab':'measurements','key':'con-1','kind':'conclusion','id':'con-1'},
          {'tab':'findings','key':'con-1','kind':'finding','id':'con-1'}]
        selected,refs,remaining=pending_sources(state,self.archive,self.reviews,candidates)
        names=[x['id'] for x in selected]
        self.assertNotIn('med-1',names)
        self.assertEqual(names.count('con-1'),1)
        self.assertEqual(len([r for r in refs if r['id']=='con-1']),2)
        self.assertIn('note1',names)
        self.assertEqual(remaining,0)

class SimulationSummaryTests(unittest.TestCase):
    def test_does_not_mark_read_until_ack_and_preserves_new_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=Path(tmp)/'world.sqlite3'
            sim=nilo.Simulation(db_path=db)
            try:
                sim.bootstrap_reviews({})
                sim.archive.add('journal',{'id':'old-note','text':'Probé piedra','origin':'llm'})
                sim.conn.commit()
                cfg={'PROVIDER':'gemini','MODEL':'fake','GEMINI_API_KEY':'fake',
                     'MAX_CHAT_CALLS_PER_DAY':'40'}
                with patch.object(nilo,'config',return_value=cfg),patch.object(nilo,'available',return_value=True),patch.object(nilo,'route',return_value=(('Nilo intentó probar piedra.',{}),'gemini','fake')):
                    summary=sim.observer_summary([])
                self.assertIn('id',summary)
                self.assertGreater(summary['count'],0)
                self.assertGreater(sim.archive.count_unread('journal'),0)
                sim.archive.add('journal',{'id':'new-note','text':'Pasó algo nuevo','origin':'llm'})
                sim.acknowledge_observer_summary(summary['id'])
                self.assertTrue(sim.archive.is_read('journal',sim.archive.seq_for('journal','old-note')))
                self.assertFalse(sim.archive.is_read('journal',sim.archive.seq_for('journal','new-note')))
                self.assertEqual(sim.observer_summary_history()[0]['text'],'Nilo intentó probar piedra.')
            finally:
                sim.conn.close()

class InterfaceSummaryTests(unittest.TestCase):
    def test_shortcuts_and_history_and_navigation(self):
        html=legacy_markup(Path(__file__).resolve().parents[1])
        self.assertNotIn('Archivo y pensamiento</span>',html)
        self.assertIn('Conocimientos registrados',html)
        self.assertIn('data-tool-jump=',html)
        self.assertIn('data-knowledge-jump=',html)
        self.assertIn("openRelatedRecord('tool',tool.dataset.toolJump)",html)
        self.assertIn("function openObserverHistory()",html)
        self.assertIn("fetch('/api/summary-generate'",html)
        self.assertIn("fetch('/api/summary-ack'",html)
        self.assertIn("await persistTabRead(t,group)",html)
        self.assertIn('data-review-entry-key',html)
if __name__=='__main__':unittest.main()
