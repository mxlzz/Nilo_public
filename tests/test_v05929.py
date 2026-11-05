"""0.5.9.2.9 — organización del archivo y resumen veraz de pendientes."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
HTML=(ROOT/'interfaz.html').read_text(encoding='utf-8')
JS=HTML.split('<script>',1)[1].split('</script>',1)[0]


class OrganizedArchiveTests(unittest.TestCase):
    def test_exactly_twelve_visible_tabs_and_four_groups(self):
        import re
        tabs=re.findall(r'<button data-tab="([^"]+)"',HTML)
        self.assertEqual(tabs,['notes','activity','identity','research','measurements',
                               'findings','creations','projects','agenda','habits','chat','proposals'])
        self.assertIn('data-setting-tab="versions"',HTML)
        self.assertIn('id="settings-versions"',HTML)
        self.assertIn('id="catchup-dialog"',HTML)
        self.assertNotIn('data-tab="versions"',HTML)
        for old in ('news','events','predictions','designs','plans'):
            self.assertNotIn('data-tab="'+old+'"',HTML)

    def test_new_sections_keep_old_data_and_concrete_links(self):
        for fragment in ("function renderActivity(){","function renderFindings(){",
                         "function renderCreations(){","function renderResearch(){",
                         "renderPredictions();","renderDesigns()","renderPlans()",
                         "function pendingOverview(source,s){",
                         "data-measurement-id","function openMeasurement(id){",
                         "function openPlanForBuilding(id){"):
            self.assertIn(fragment,JS)
        self.assertIn("creationView='objects';switchTab('creations')",JS)
        self.assertIn("switchTab(item.type==='journal'?'notes':'activity')",JS)
        self.assertIn("essayView='all';switchTab('measurements')",JS)
        self.assertIn("if(source==='activity')",JS)
        self.assertIn("if(source==='proposals')",JS)
        self.assertNotIn('Resumime lo más importante de las novedades de',JS)
        self.assertIn('últimos resultados conservados',HTML)
        self.assertIn('Tendencias de acción calculadas',HTML)
        self.assertIn('Etapas de vida (30 días simulados)',HTML)

    def test_unread_archive_http_does_not_change_read_markers(self):
        import json
        import threading
        import urllib.request
        import urllib.error
        import nilo
        from http.server import ThreadingHTTPServer
        with tempfile.TemporaryDirectory() as tmp:
            old=nilo.DB
            nilo.DB=Path(tmp)/'world.sqlite3'
            sim=None
            server=None
            try:
                sim=nilo.Simulation()
                sim.archive.add('journal',{'id':'old-note','when':'Día 1','text':'Una entrada histórica','origin':'llm'})
                sim.archive.add('news',{'id':'old-news','when':'Día 2','title':'Una novedad histórica'})
                sim.conn.commit()
                nilo.Handler.sim=sim
                server=ThreadingHTTPServer(('127.0.0.1',0),nilo.Handler)
                thread=threading.Thread(target=server.serve_forever,daemon=True)
                thread.start()
                base=f'http://127.0.0.1:{server.server_port}'
                with urllib.request.urlopen(base+'/api/unread?category=journal',timeout=3) as resp:
                    result=json.loads(resp.read())
                self.assertGreaterEqual(result['total'],1)
                self.assertTrue(any(e['id']=='old-note' for e in result['entries']))
                self.assertGreaterEqual(sim.archive.count_unread('journal'),1)
                with urllib.request.urlopen(base+'/api/unread?category=news',timeout=3) as resp:
                    result=json.loads(resp.read())
                self.assertTrue(any(e['id']=='old-news' for e in result['entries']))
                with self.assertRaises(urllib.error.HTTPError) as invalid:
                    urllib.request.urlopen(base+'/api/unread?category=private',timeout=3)
                self.assertEqual(invalid.exception.code,400)
            finally:
                if server:server.shutdown();server.server_close()
                if sim:sim.conn.close()
                nilo.DB=old

    def test_node_renders_unified_sections_and_pending_subset(self):
        if not shutil.which('node'):self.skipTest('Node.js no disponible')
        runner=r"""
const assert=require('assert'),fs=require('fs'),vm=require('vm');
const js=fs.readFileSync(process.argv[2],'utf8').split('<script>')[1].split('</script>')[0];
function extract(a,b){let i=js.indexOf(a),j=js.indexOf(b,i);assert(i>=0&&j>i,a);return js.slice(i,j)}
const src=extract('function renderActivity(){','function renderNotes(){')+
          extract('function pendingOverview(source,s){','let pendingOverviewItems=');
const state={
 news:[{id:'n1',read:false,when:'Día 2',title:'Construí una mesa',detail:''}],
 events:[{id:'e1',when:'Día 2',text:'Construí una mesa'},
         {id:'e2',when:'Día 3',text:'Encontré mineral'}],
 conclusions:[{id:'c1',when:'Día 3',text:'Probé el material',evidence_ids:['m1'],scope:'Solo esta muestra'}],
 knowledge:[['k1','La piedra resistió la prueba']],
 research:[{id:'r1',started:'Día 3',question:'¿Cómo excavar?',hypothesis:'Una punta ayudará',state:'abierta'}],
 prediction_log:[{id:'p1',status:'pendiente',hypothesis:'La herramienta avanza más',expected_effect:'Más avance'}],
 designs:[{id:'d1',name:'Punta',status:'hipotesis',versions:[{version:1}]}],
 structures:[{id:'s1',name:'Refugio',revision:1}],retired_structures:[],items:[],
 measurements:[{id:'m1',op:'go',verified_facts:['Avancé un tramo']}],projects:[],agenda:[],
 proposals:[{id:'p2',status:'pendiente',phenomenon:'Flotación',rationale:'Falta física'}],
 experience_summary:[],waiting_history:[],skills:[],conclusions:[],journal:[]
};
state.conclusions=[{id:'c1',text:'Medí el resultado',scope:'Una muestra',evidence_ids:['m1']}];
const ctx={
 data:state,activityView:'featured',creationView:'all',essayView:'tests',
 locallyReviewed:{activity:['e1'],research:[],creations:[],findings:[],proposals:[]},
 tabHasUpdates:()=>true,
 esc:v=>String(v??'').replace(/&/g,'&amp;').replace(/</g,'&lt;'),
 renderNews:()=>'<div>Destacados reales</div>',
 renderEvidenceText:v=>String(v??''),measurementLink:id=>'<button>'+id+'</button>',
 renderDesigns:()=>'<div>Invento real</div>',renderPlans:()=>'<div>Objeto real</div>',
 measurementActionTitle:m=>m.op,agendaCondition:()=>'',newsExtra:()=>''
};
vm.createContext(ctx);vm.runInContext(src,ctx);
assert(ctx.renderActivity().includes('Destacados reales'));
ctx.activityView='all';
assert(ctx.renderActivity().includes('Encontré mineral'));
assert(ctx.renderFindings().includes('Medí el resultado'));
assert(ctx.renderFindings().includes('La piedra resistió la prueba'));
assert(ctx.renderCreations().includes('Invento real')&&ctx.renderCreations().includes('Objeto real'));
const activity=ctx.pendingOverview('activity',state);
assert(activity.some(x=>x.kind==='news'&&x.id==='n1'));
assert(activity.some(x=>x.kind==='event'&&x.id==='e2'));
assert(!activity.some(x=>x.kind==='event'&&x.id==='e1'));
const research=ctx.pendingOverview('research',state);
assert(research.some(x=>x.kind==='research')&&research.some(x=>x.kind==='prediction'));
const proposals=ctx.pendingOverview('proposals',state);
assert.equal(proposals.length,1);
console.log('secciones y pendientes reales OK');
""";
        with tempfile.TemporaryDirectory() as tmp:
            test=Path(tmp)/'test.js'
            test.write_text(runner,encoding='utf-8')
            result=subprocess.run(['node',str(test),str(ROOT/'interfaz.html')],
                                  capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('secciones y pendientes reales OK',result.stdout)

if __name__=='__main__':unittest.main()
