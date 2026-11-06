from ui_fixture import legacy_markup, legacy_html_path
"""Regresiones 0.5.9.3.11: vínculos, jerarquía y lectura del resumen."""
import tempfile
import unittest
import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch

import nilo
from archive import History
from review_store import ReviewStore


class RelatedRecordPhases(unittest.TestCase):
    def setUp(self):
        import sqlite3
        self.db=sqlite3.connect(':memory:')
        self.history=History(self.db)

    def tearDown(self):
        self.db.close()

    def test_new_project_is_not_confused_with_ongoing_project(self):
        self.history.add('journal',{'id':'j1','text':'Comienzo una investigación','when':'Día 2 · 10:10',
                                    'project_id':'p1'})
        self.history.add('project',{'id':'p1','title':'Investigar una propiedad',
                                    'started':'Día 2 · 10:10','status':'activo',
                                    'updated':'Día 2 · 10:10'})
        links=self.history.relations_for('journal','j1')
        self.assertEqual(len(links),1)
        self.assertEqual(links[0]['phase'],'new')

        self.history.add('journal',{'id':'j2','text':'Sigo con el ensayo','when':'Día 4 · 11:20',
                                    'project_id':'p1'})
        links=self.history.relations_for('journal','j2')
        self.assertEqual(links[0]['phase'],'related')

    def test_new_measurement_in_existing_project(self):
        self.history.add('journal',{'id':'j3','text':'Nueva medición','when':'Día 4 · 13:30'})
        self.history.add('measurement',{'id':'med-111','op':'rest','when':'Día 4 · 13:30',
                                        'journal_id':'j3'})
        links=self.history.relations_for('journal','j3')
        self.assertEqual([(x['category'],x['phase']) for x in links],
                         [('measurement','new')])

    def test_old_record_without_provenance_is_not_labelled_new(self):
        self.history.add('journal',{'id':'j4','when':'Día 8 · 11:10','project_id':'p2'})
        self.history.add('project',{'id':'p2','title':'Proyecto anterior',
                                    'started':'Día 1 · 05:00'})
        self.assertEqual(self.history.relations_for('journal','j4')[0]['phase'],'related')


class SummaryLinkedAcknowledgments(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.sim=nilo.Simulation(db_path=Path(self.temp.name)/'world.sqlite')
        self.sim.bootstrap_reviews({})
        self.cfg={'PROVIDER':'gemini','MODEL':'test','GEMINI_API_KEY':'fake',
                  'MAX_CHAT_CALLS_PER_DAY':'100'}
        self.p1=patch.object(nilo,'config',return_value=self.cfg)
        self.p2=patch.object(nilo,'available',return_value=True)
        self.p3=patch.object(nilo,'route',return_value=(('Informe verificado.',{}),'gemini','test'))
        for p in (self.p1,self.p2,self.p3):p.start()

    def tearDown(self):
        for p in (self.p3,self.p2,self.p1):p.stop()
        self.sim.conn.close()
        self.temp.cleanup()

    def test_summary_ack_marks_directly_linked_unread_journal_but_not_later_one(self):
        self.sim.archive.add('journal',{'id':'old-j','when':'Día 1 · 12:30',
                                         'text':'Prueba del proyecto'})
        self.sim.archive.add('project',{'id':'p-a','title':'Investigar materiales',
                                         'started':'Día 1 · 12:30','journal_id':'old-j'})
        candidates=[{'tab':'projects','key':'p-a:activo','kind':'project','id':'p-a'}]
        for i in range(11):
            rid=f'p-other-{i}'
            self.sim.archive.add('project',{'id':rid,'title':f'Construí e investigué un material {i}',
                                            'started':'Día 1 · 10:00'})
            candidates.append({'tab':'projects','key':rid+':activo','kind':'project','id':rid})
        packet=self.sim.observer_summary(candidates)
        reviewed_ids={r['id'] for r in packet['links']} | {
            r['id'] for r in packet['related_links']}
        self.assertIn('old-j',reviewed_ids)
        self.assertIn('p-a',reviewed_ids)
        self.assertEqual(self.sim.archive.count_unread('journal'),1)
        self.sim.archive.add('journal',{'id':'future-j','when':'Día 2 · 05:00',
                                         'text':'Una noticia posterior'})
        self.sim.acknowledge_observer_summary(packet['id'])
        self.assertTrue(self.sim.review.is_seen('projects','p-a:activo'))
        self.assertTrue(self.sim.archive.is_read('journal',self.sim.archive.seq_for('journal','old-j')))
        self.assertFalse(self.sim.archive.is_read('journal',self.sim.archive.seq_for('journal','future-j')))

    def test_unrelated_important_entry_stays_pending_for_what_more(self):
        for i in range(15):
            self.sim.archive.add('news',{'id':f'n-{i}','title':f'Construí una máquina {i}'})
        first=self.sim.observer_summary([])
        self.assertEqual(first['remaining'],3)
        self.assertEqual(first.get('related_links'),[])
        self.sim.acknowledge_observer_summary(first['id'])
        self.assertEqual(self.sim.archive.count_unread('news'),3)


class InterfacePlacement(unittest.TestCase):
    def test_embedded_javascript_syntax_when_node_is_available(self):
        node=shutil.which('node')
        if node is None:self.skipTest('Node.js no disponible')
        html=legacy_markup(Path(__file__).resolve().parents[1])
        js=html.split('<script>',1)[1].rsplit('</script>',1)[0]
        with tempfile.TemporaryDirectory() as folder:
            filename=Path(folder)/'nilo_interface.js'
            filename.write_text(js,encoding='utf-8')
            result=subprocess.run([node,'--check',str(filename)],
                                  capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr)

    def test_summary_actions_below_report_without_extra_phrase(self):
        html=legacy_markup(Path(__file__).resolve().parents[1])
        self.assertLess(html.index('id="catchup-content" class="catchup-content"'),
                        html.index('id="catchup-actions"'))
        self.assertNotIn('narrada por un observador externo.',html)
        self.assertIn('Registros vinculados revisados',html)
        self.assertIn('recordLinkMarkup',html)
        self.assertIn('data-link-phase=',html)
        self.assertNotIn('Volver al Cuaderno',html)


if __name__=='__main__':
    unittest.main()
