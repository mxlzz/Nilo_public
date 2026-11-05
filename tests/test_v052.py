"""Regresiones de la historia permanente, marcadores y continuidad de partidas."""
import unittest,tempfile,sqlite3,json,random,time
from pathlib import Path
from unittest.mock import patch
import nilo
from archive import History

class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.db=sqlite3.connect(Path(self.temp.name)/'historico.sqlite3')
        self.h=History(self.db)
    def tearDown(self):
        self.db.close();self.temp.cleanup()
    def test_add_is_idempotent_and_read_markers_independent(self):
        a=self.h.add('journal',{'id':'a','when':'Día 1','text':'A'});self.h.add('journal',{'id':'a','when':'Día 1','text':'A'})
        b=self.h.add('news',{'id':'b','when':'Día 1','title':'B'})
        self.assertEqual(self.h.counts(),{'journal':1,'news':1})
        self.assertEqual((self.h.count_unread('journal'),self.h.count_unread('news')),(1,1))
        self.h.mark_read('journal',a)
        self.assertEqual((self.h.count_unread('journal'),self.h.count_unread('news')),(0,1))
        self.h.mark_read('journal',a)
        self.assertEqual(self.h.position('journal'),a)
        self.assertEqual(self.h.pending_page()[0],1)
        self.assertEqual(self.h.pending_page()[1][0]['id'],'b')
    def test_historic_revisions_preserve_edits(self):
        v={'id':'pr','question':'¿Hay presión?','hypothesis':'Primera idea'}
        self.h.add('research',v);v['hypothesis']='Nueva hipótesis';self.h.add('research',v)
        self.h.add('research',v)
        self.assertEqual(self.h.counts()['research'],1)
        items=self.db.execute("SELECT payload FROM history_revisions WHERE category='research' ORDER BY revision").fetchall()
        self.assertEqual(len(items),2)
        self.assertEqual(json.loads(items[0][0])['hypothesis'],'Primera idea')
    def test_large_page_without_loading_all(self):
        for i in range(300):self.h.add('journal',{'id':f'n{i}','when':f'Día {i}','text':f'Texto {i}'})
        total,page=self.h.pending_page(200,80)
        self.assertEqual(total,300);self.assertEqual(len(page),80)
        self.assertEqual(page[0]['id'],'n200')
        self.h.mark_read('journal')
        self.assertEqual(self.h.count_unread('journal'),0)
        self.assertEqual(self.h.counts()['journal'],300)

class SimulationArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.previous=nilo.DB
        nilo.DB=Path(self.temp.name)/'mundo.sqlite3'
        self.sim=nilo.Simulation()
    def tearDown(self):
        self.sim.conn.close();nilo.DB=self.previous;self.temp.cleanup()
    def test_retains_notes_beyond_snapshot_window_and_newscounts(self):
        sim=self.sim
        for i in range(170):
            sim.journal(f'Nota {i}')
            sim.s['person']['pending']=None
        self.assertEqual(len(sim.s['journal']),160)
        self.assertEqual(sim.archive.counts()['journal'],170)
        self.assertEqual(sim.archive.count_unread('journal'),170)
        self.assertEqual(sim.catchup()['total'],170)
        self.assertEqual(sim.catchup()['restantes'],90)
        sim.mark_all_read(['journal'])
        self.assertEqual(sim.catchup()['total'],0)
        self.assertEqual(sim.archive.counts()['journal'],170)
    def test_event_archive_survives_memory_trim_and_restart(self):
        for i in range(260):self.sim.event([f'Evento {i}'],'resultado',False)
        self.assertEqual(len(self.sim.s['events']),250)
        self.sim.write()
        count=self.sim.archive.counts()['event'];self.assertGreaterEqual(count,260)
        self.sim.conn.close()
        self.sim=nilo.Simulation()
        self.assertEqual(self.sim.archive.counts()['event'],count)
        self.assertEqual(self.sim.archive.recent('event',1)[0]['text'],'Evento 259')
    def test_mark_only_summarized_messages(self):
        self.sim.journal('Primero');self.sim.s['person']['pending']=None
        first=self.sim.archive.seq_for('journal',self.sim.s['journal'][-1]['id'])
        self.sim.journal('Segundo');self.sim.s['person']['pending']=None
        self.sim.s['last_catchup_covered']={'journal':first}
        self.sim.write()
        self.sim.mark_summarized_read()
        self.assertEqual(self.sim.archive.count_unread('journal'),1)
        self.assertEqual(self.sim.archive.counts()['journal'],2)

    def test_legacy_news_marker_imports(self):
        self.sim.conn.close()
        source=nilo.initial_state()
        source['news']=[{'id':'h1','when':'Día 1','title':'Uno','detail':'Uno'},
                        {'id':'h2','when':'Día 1','title':'Dos','detail':'Dos'}]
        source['read_marker']='h1'
        source['journal']=[{'id':'j1','when':'Día 1','text':'Original'}]
        conn=sqlite3.connect(nilo.DB)
        conn.execute('DELETE FROM snapshot')
        conn.execute('INSERT INTO snapshot (id,payload) VALUES(1,?)',(json.dumps(source),))
        conn.execute('DELETE FROM history');conn.execute('DELETE FROM history_revisions')
        conn.execute('UPDATE reading_positions SET through_seq=0')
        conn.commit();conn.close()
        self.sim=nilo.Simulation()
        self.assertEqual(self.sim.archive.count_unread('news'),1)
        self.assertEqual(self.sim.archive.count_unread('journal'),0)
        self.assertEqual(self.sim.archive.counts()['journal'],1)
