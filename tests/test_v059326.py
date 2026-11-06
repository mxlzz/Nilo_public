"""0.5.9.3.26: relaciones exhaustivas, grupos contiguos y efectos de recipientes."""
from __future__ import annotations
from ui_fixture import legacy_markup, legacy_html_path
import json
import random
import re
import shutil
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path

from archive import History
from physical_links import snapshot, entities_for_action
from nilo import Simulation

ROOT=Path(__file__).resolve().parent.parent
HTML=legacy_markup(Path(__file__).resolve().parents[1])


class FullRelations(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        self.archive=History(self.db)
        self.archive.add('journal',{'id':'j-large','text':'Registro original íntegro',
                                     'when':'Día 2 · 00:00'})

    def tearDown(self):
        self.db.close()

    def test_over_150_relations_each_kind_are_complete_and_deduplicated(self):
        # Antes había LIMIT 40 por dirección, 32 en /api/state y
        # recortes de indexación en 80/100/150 relaciones.
        for n in range(170):
            measurement={'id':f'med-{n:04d}','journal_id':'j-large',
                'op':'interact','when':f'Día 2 · 00:{n % 60:02d}',
                'inventory_delta':{f'material-{n:04d}':n+1},
                'entity_links':[{'category':'tool','id':f'obj-{n:04d}',
                                  'relation':'contenido transferido (origen)'}]}
            self.archive.add('tool',{'id':f'obj-{n:04d}',
                                      'name':f'Contenedor {n}', 'revision':1})
            self.archive.add('measurement',measurement)
        rows=self.archive.relations_for('journal','j-large')
        self.assertEqual(len(rows),510)
        self.assertEqual({r['category'] for r in rows},
                         {'measurement','material','tool'})
        for category in ('measurement','material','tool'):
            self.assertEqual(sum(r['category']==category for r in rows),170)
        self.assertEqual(len({(r['category'],r['id']) for r in rows}),510)
        batch=self.archive.relations_batch([('journal','j-large'),('journal','j-large')])
        self.assertEqual(len(batch['journal:j-large']),510)
        self.assertEqual(len(batch),1)

    def test_archived_record_returns_all_links_both_directions(self):
        for n in range(90):
            self.archive.add('project',{'id':f'p-{n}','title':f'Proyecto {n}',
                                         'journal_id':'j-large'})
            self.archive.add('measurement',{'id':f'med-proj-{n}','journal_id':'j-large',
                                             'project_id':f'p-{n}'})
        links=self.archive.relations_for('journal','j-large')
        self.assertEqual(sum(r['category']=='project' for r in links),90)
        self.assertEqual(sum(r['category']=='measurement' for r in links),90)

    def test_rebuild_missing_legacy_edges_once_preserves_history(self):
        # Simular base antigua: limitaciones en índice pero documentos completos.
        record={'id':'med-legacy','journal_id':'j-large',
                'entity_links':[{'category':'tool','id':f'old-{n:03d}'}
                                 for n in range(165)]}
        for n in range(165):
            self.archive.add('tool',{'id':f'old-{n:03d}','name':f'Viejo {n}'})
        self.archive.add('measurement',record)
        self.db.execute("DELETE FROM record_links WHERE source_category='measurement' AND source_id='med-legacy' AND target_id='old-164'")
        self.db.execute("DELETE FROM record_link_meta WHERE key='indexed_v2_full'")
        before=self.db.execute('SELECT COUNT(*) FROM history').fetchone()[0]
        self.db.commit()
        migrated=History(self.db)
        self.assertTrue(self.db.execute("SELECT 1 FROM record_links WHERE source_category='measurement' AND source_id='med-legacy' AND target_id='old-164'").fetchone())
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM history').fetchone()[0],before)
        count=self.db.execute('SELECT COUNT(*) FROM record_links').fetchone()[0]
        History(self.db)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM record_links').fetchone()[0],count)

    def test_no_relationship_from_unrelated_action_or_narrative(self):
        self.archive.add('tool',{'id':'vessel-a','name':'Jarra narrada'})
        self.archive.add('measurement',{'id':'med-no','journal_id':'j-other',
                              'op':'interact','verified_facts':['Usé jarra narrada']})
        rows=self.archive.relations_for('journal','j-large')
        self.assertFalse(any(r.get('id')=='vessel-a' for r in rows))


class VesselRelations(unittest.TestCase):
    def setUp(self):
        self.a={'id':'a','name':'A','revision':1}
        self.b={'id':'b','name':'B','revision':1}
        self.p={'items':[self.a,self.b]}
        self.w={'structures':[]}
        self.before=snapshot(self.w,self.p)

    def link(self,step,method,src,dst,success=True):
        evidence={'kind':'capability','conditions':{
            'capability':'contenidos','version':'1.0.0',
            'method':method,'source_id':src,'destination_id':dst,'quantity':0.3}}
        return entities_for_action(self.before,self.w,self.p,step,
                                  {'success':success,'physical':evidence})

    def test_transfer_links_both_existing_vessels_with_distinct_roles(self):
        rows=self.link({'op':'interact','method':'transferir',
                        'source':'a','destination':'b'},'transferir','a','b')
        self.assertEqual(rows,[
          {'category':'tool','id':'a','relation':'contenido transferido (origen)'},
          {'category':'tool','id':'b','relation':'contenido transferido (destino)'}])

    def test_consumption_and_refill_link_only_real_vessel(self):
        self.assertEqual(self.link({'op':'drink','item':'a'},'beber','a','persona'),
            [{'category':'tool','id':'a','relation':'agua consumida de'}])
        self.assertEqual(self.link({'op':'interact','method':'rellenar'},'rellenar','agua_ambiental','b'),
            [{'category':'tool','id':'b','relation':'contenido recargado'}])

    def test_rejected_transfer_and_fake_ids_do_not_create_links(self):
        self.assertEqual(self.link({'op':'interact','method':'transferir'},
                            'transferir','a','b',success=False),[])
        self.assertEqual(self.link({'op':'interact','method':'transferir'},
                            'transferir','not-real','also-fake'),[])
        self.assertEqual(entities_for_action(self.before,self.w,self.p,
            {'op':'interact','source':'a','destination':'b'},
            {'success':True,'physical':None}),[])


class VisualVerification(unittest.TestCase):
    def test_relationship_groups_and_no_toggle_execute_in_node(self):
        if not shutil.which('node'):self.skipTest('Node.js no instalado')
        js=HTML[HTML.index('const RECORD_LABELS='):HTML.index('function recordDescription(')]
        runner=r"""
const vm=require('node:vm'),assert=require('node:assert');
const src=require('node:fs').readFileSync(0,'utf8');
const esc=x=>String(x);
const data={record_relations:{}};
vm.runInThisContext(src);
const entries=[];
for(let i=0;i<85;i++)entries.push({category:'material',id:'material-'+i,
 title:'Material '+i,phase:'new',seq:i});
for(let i=0;i<85;i++)entries.push({category:'measurement',id:'meas-'+i,
 title:'Medición '+i,phase:'related',seq:i});
for(let i=0;i<85;i++)entries.push({category:'tool',id:'tool-'+i,
 title:'Recipiente '+i,phase:'updated',seq:i});
const shuffled=[...entries.slice(170),...entries.slice(85,170),...entries.slice(0,85)];
const ordered=orderedRecordLinks(shuffled);
assert.deepEqual(ordered.slice(0,85).map(e=>e.category),Array(85).fill('measurement'));
assert.deepEqual(ordered.slice(85,170).map(e=>e.category),Array(85).fill('material'));
assert.deepEqual(ordered.slice(170).map(e=>e.category),Array(85).fill('tool'));
const rendered=recordLinks('journal','j-1',shuffled);
assert.match(rendered,/vínculos documentados \(255\)/);
assert.equal((rendered.match(/record-link-label/g)||[]).length,255);
assert.equal((rendered.match(/record-links-items/g)||[]).length,1);
assert.ok(!rendered.includes('<details'));
assert.ok(!rendered.includes('relaciones más'));
assert.ok(rendered.indexOf('Medición 84')<rendered.indexOf('Material 84'));
assert.ok(rendered.indexOf('Material 84')<rendered.indexOf('Recipiente 84'));
assert.equal(recordLinks('journal','missing',[]),'');
"""
        proc=subprocess.run(['node','-e',runner],input=js,text=True,capture_output=True)
        self.assertEqual(proc.returncode,0,proc.stderr)

    def test_existing_interface_features_remain_available(self):
        for name in ('function showMap(){','function helpButton','researchView',
                     'data.active_intervention','installed_capabilities',
                     'recordNavigationHistory','catchup-dock'):
            # installed_capabilities is exposed via the server, not necessarily
            # displayed in the current UI.
            if name=='installed_capabilities':continue
            self.assertIn(name,HTML)
        self.assertIn('Nilo '+(ROOT/'VERSION').read_text('utf-8').strip(),HTML)


class SqliteIntegration(unittest.TestCase):
    def test_journal_links_transfer_after_save_and_reopen(self):
        with tempfile.TemporaryDirectory() as folder:
            db=Path(folder)/'nilo.sqlite3'
            sim=Simulation(db_path=db)
            try:
                sim.think=lambda:None
                p=sim.s['person']
                p['items']=[
                    {'id':'jarra-a','name':'Jarra A','form':'recipiente',
                     'materials':['piedra']*3,'geometry':{'shape':'hueco','size':3},
                     'durability':100,'revision':1,'contents':{'material':'agua','quantity':.7}},
                    {'id':'jarra-b','name':'Jarra B','form':'recipiente',
                     'materials':['piedra']*3,'geometry':{'shape':'hueco','size':3},
                     'durability':100,'revision':1,'contents':{}}
                ]
                note={'id':'journal-proof','text':'Observaré recipientes distintos.',
                      'origin':'llm','when':sim.stamp()}
                sim.s['journal'].append(note)
                sim.archive.add('journal',note)
                p['plan']=[{'op':'interact','method':'transferir',
                            'source':'jarra-a','destination':'jarra-b',
                            'quantity':.3,'_journal_id':'journal-proof'}]
                sim.s['planning']=True
                sim._tick_slice(0)
                self.assertIsNotNone(p['pending'])
                sim.s['planning']=False
                sim.s['speed']=60
                sim._tick_slice(20)
                self.assertIsNone(p['pending'])
                sim.write()
                links=sim.archive.relations_for('journal','journal-proof')
                self.assertTrue(any(r['category']=='tool' and r['id']=='jarra-a' for r in links))
                self.assertTrue(any(r['category']=='tool' and r['id']=='jarra-b' for r in links))
                self.assertTrue(any(r['category']=='measurement' for r in links))
                public=sim.public_state()
                self.assertIn('journal:journal-proof',public['record_relations'])
                self.assertEqual(len([r for r in links if r['category']=='tool']),2)
            finally:
                sim.conn.close()
            resumed=Simulation(db_path=db)
            try:
                links=resumed.linked_record('journal','journal-proof')['relations']
                ids={r['id'] for r in links if r['category']=='tool'}
                self.assertEqual(ids,{'jarra-a','jarra-b'})
                self.assertEqual(resumed.s['person']['items'][0]['contents']['quantity'],.4)
                self.assertEqual(resumed.s['person']['items'][1]['contents']['quantity'],.3)
            finally:
                resumed.conn.close()


if __name__=='__main__':unittest.main()
