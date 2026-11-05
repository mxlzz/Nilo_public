"""Trazabilidad: enlaces explícitos, inversos, persistentes y no especulativos."""
import json
import sqlite3
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from archive import History
from record_links import explicit_links

ROOT=Path(__file__).resolve().parent.parent

class RelationTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        self.history=History(self.db)
        self.history.add('journal',{'id':'j1','text':'Probar piedra','when':'Día 1',
                                    'research_id':'r1','project_id':'pr1'})
        self.history.add('research',{'id':'r1','question':'¿Resiste la piedra?','when':'Día 1'})
        self.history.add('project',{'id':'pr1','title':'Construir una herramienta'})
        self.history.add('measurement',{'id':'med-001','op':'experiment','when':'Día 2',
                                        'journal_id':'j1','project_id':'pr1'})
        self.history.add('prediction',{'id':'pred-1','hypothesis':'Resiste','when':'Día 2',
                                      'journal_id':'j1','measurement_id':'med-001'})
        self.history.add('proposal',{'id':'sol-1','phenomenon':'Resistencia','when':'Día 3',
                                    'journal_id':'j1','evidence_ids':['med-001']})
        self.history.add('conclusion',{'id':'c1','text':'Una muestra resistió',
                                      'evidence_ids':['med-001']})
        self.history.add('measurement',{'id':'med-002','op':'experiment','when':'Día 2',
                                        'verified_facts':['Resistió parecido']})
        self.db.commit()

    def tearDown(self):self.db.close()

    def test_journal_links_to_verified_records_in_both_directions(self):
        linked={(r['category'],r['id']) for r in self.history.relations_for('journal','j1')}
        self.assertTrue({('research','r1'),('project','pr1'),('measurement','med-001'),
                         ('prediction','pred-1'),('proposal','sol-1')}<=linked)
        self.assertNotIn(('measurement','med-002'),linked)
        reverse={(r['category'],r['id']) for r in self.history.relations_for('measurement','med-001')}
        self.assertIn(('journal','j1'),reverse)
        self.assertIn(('proposal','sol-1'),reverse)
        self.assertIn(('conclusion','c1'),reverse)
        self.assertIn(('prediction','pred-1'),reverse)

    def test_time_and_similarity_do_not_create_links(self):
        self.assertEqual(self.history.relations_for('measurement','med-002'),[])
        self.assertEqual(explicit_links('journal',{'id':'j2','text':'med-001 en mi diario',
                                                  'when':'Día 2'}),[])
        self.history.add('journal',{'id':'j2','text':'Pienso en med-001','when':'Día 2'})
        self.assertEqual(self.history.relations_for('journal','j2'),[])

    def test_no_ghost_target_or_self_reference(self):
        self.history.add('journal',{'id':'j3','text':'Sin prueba','research_id':'desconocida',
                                    'journal_id':'j3'})
        self.assertEqual(self.history.relations_for('journal','j3'),[])
        self.assertEqual(self.history.get('journal','j1')['text'],'Probar piedra')

    def test_relations_persist_and_index_updates(self):
        reopened=History(self.db)
        self.assertTrue(reopened.relations_for('journal','j1'))
        reopened.add('project',{'id':'pr1','title':'Nuevo título',
                                'verified_results':[{'measurement_id':'med-002'}]})
        by_measurement={(r['category'],r['id']) for r in reopened.relations_for('measurement','med-002')}
        self.assertIn(('project','pr1'),by_measurement)
        self.assertEqual(reopened.relations_for('journal','j1'),
                         self.history.relations_for('journal','j1'))

    def test_archived_mutable_records_use_latest_revision(self):
        self.history.add('prediction',{'id':'pred-old','hypothesis':'Flota','status':'pendiente'})
        self.history.add('prediction',{'id':'pred-old','hypothesis':'Flota','status':'prediccion_coincide',
                                        'measurement_id':'med-001'})
        self.assertEqual(self.history.get('prediction','pred-old')['status'],'pendiente')
        self.assertEqual(self.history.latest_record('prediction','pred-old')['status'],'prediccion_coincide')
        related={(r['category'],r['id']) for r in self.history.relations_for('measurement','med-001')}
        self.assertIn(('prediction','pred-old'),related)

    def test_batch_includes_only_existing_associations(self):
        records=self.history.relations_batch([('journal','j1'),('journal','j2'),
                                               ('measurement','med-001')])
        self.assertIn('journal:j1',records)
        self.assertIn('measurement:med-001',records)
        self.assertNotIn('journal:j2',records)

class BrowserAndServerTests(unittest.TestCase):
    def test_html_writes_no_links_into_nilo_journal_text(self):
        html=(ROOT/'interfaz.html').read_text(encoding='utf-8')
        self.assertIn("data-note=\"${esc(e.id)}\"",html)
        self.assertIn("${recordLinks('journal',e.id)}</article>",html)
        for label in ("recordLinks('research',q.id)","recordLinks('prediction',p.id)",
                      "recordLinks('measurement',m.id)","recordLinks('proposal',p.id)",
                      "recordLinks('conclusion',c.id)"):
            self.assertIn(label,html)
        self.assertIn("function openRelatedRecord(category,id){",html)
        self.assertIn('/api/record?category=',html)

    def test_new_deliberation_links_note_research_project_and_plan(self):
        import nilo
        with tempfile.TemporaryDirectory() as tmp:
            old=nilo.DB;nilo.DB=Path(tmp)/'world.sqlite3'
            sim=None
            try:
                sim=nilo.Simulation()
                raw={'cuaderno':'Voy a medir las condiciones de mi descanso.',
                     'objetivo':'Medir descanso','motivo':'Entender mis necesidades',
                     'pregunta':'¿Cuánto recupero al dormir?',
                     'hipotesis':'Recupero energía después del descanso',
                     'plan':[{'op':'rest'}],
                     'accion_proyecto':'nuevo','revisar_en_minutos':90}
                sim.plan_ready(nilo.normalize_decision(raw),'demo')
                note=sim.s['journal'][-1]
                self.assertEqual(note['project_id'],sim.s['person']['project']['id'])
                research=sim.s['person']['research'][-1]
                self.assertEqual(note['research_id'],research['id'])
                self.assertTrue(sim.s['person']['plan'])
                self.assertEqual(sim.s['person']['plan'][0]['_journal_id'],note['id'])
                related={(r['category'],r['id']) for r in sim.archive.relations_for('journal',note['id'])}
                self.assertIn(('research',research['id']),related)
                self.assertIn(('project',note['project_id']),related)
            finally:
                if sim:sim.conn.close()
                nilo.DB=old

    def test_fetch_historical_record_has_inverse_links(self):
        import nilo
        import threading, urllib.request, urllib.error
        from http.server import ThreadingHTTPServer
        with tempfile.TemporaryDirectory() as tmp:
            old=nilo.DB;nilo.DB=Path(tmp)/'world.sqlite3'
            sim=server=None
            try:
                sim=nilo.Simulation()
                sim.archive.add('journal',{'id':'hist-note','text':'Hice una prueba','when':'Día 1'})
                sim.archive.add('measurement',{'id':'med-hist','journal_id':'hist-note',
                                               'when':'Día 2','op':'experiment'})
                sim.conn.commit()
                nilo.Handler.sim=sim
                server=ThreadingHTTPServer(('127.0.0.1',0),nilo.Handler)
                thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
                base='http://127.0.0.1:'+str(server.server_port)
                with urllib.request.urlopen(base+'/api/record?category=journal&id=hist-note',timeout=4) as response:
                    packet=json.loads(response.read())
                self.assertEqual(packet['record']['text'],'Hice una prueba')
                self.assertTrue(any(r['id']=='med-hist' for r in packet['relations']))
                with self.assertRaises(urllib.error.HTTPError) as forbidden:
                    urllib.request.urlopen(base+'/api/record?category=chat&id=unknown',timeout=4)
                self.assertEqual(forbidden.exception.code,404)
                self.assertEqual(sim.archive.count_unread('journal'),1)
            finally:
                if server:server.shutdown();server.server_close()
                if sim:sim.conn.close()
                nilo.DB=old

if __name__=='__main__':unittest.main()
