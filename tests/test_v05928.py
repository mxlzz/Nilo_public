"""0.5.9.2.8: navegación contextual, referencias legibles y mapa atenuado."""
import sqlite3
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from archive import History

ROOT=Path(__file__).resolve().parent.parent
HTML=(ROOT/'interfaz.html').read_text(encoding='utf-8')
JS=HTML.split('<script>',1)[1].split('</script>',1)[0]
CSS=HTML.split('<style>',1)[1].split('</style>',1)[0]


class ContextualNavigation(unittest.TestCase):
    def test_plan_link_selects_and_expands_exact_structure(self):
        self.assertIn('function openPlanForBuilding(id){',JS)
        self.assertIn("node.dataset.planId===id",JS)
        self.assertIn("target.querySelectorAll('details.physical-details').forEach(item=>item.open=true)",JS)
        self.assertIn('data-plan-id=',HTML)
        self.assertIn("if(building)openPlanForBuilding(building.id||building.name)",JS)
        self.assertNotIn('Identificadores técnicos',HTML)

    def test_toolbar_is_compact_and_group_highlights_are_independent(self):
        self.assertNotIn('Mundo conocido</span>',HTML)
        self.assertNotIn('id="unread-count"',HTML)
        self.assertIn("el('indicator-inline').value=indicatorMode(tab)",JS)
        self.assertIn('id="catchup-shortcut"',HTML)
        self.assertIn('.feedentry.new-record',CSS)
        self.assertIn('[data-agenda-history-index].new-record',CSS)
        self.assertIn("indicatorMode(t)==='normal'",JS)

    def test_transparency_applies_only_to_terrain_glyph(self):
        self.assertIn('.terrain-glyph{opacity:.5}',CSS)
        self.assertIn("['t-plain','t-grass','t-sand','t-road','t-gallery'].includes(cl)",JS)
        self.assertNotIn('.tile.t-plain{opacity:',CSS)
        self.assertIn('trail-5',CSS)

    def test_technical_agenda_section_removed(self):
        start=HTML.index('function renderAgenda(){')
        end=HTML.index('function renderIdentity(){',start)
        self.assertNotIn('technical-details',HTML[start:end])
        self.assertNotIn('JSON.stringify',HTML[start:end])
        self.assertIn('agendaCondition(t.cuando)',HTML[start:end])

    def test_archive_exact_lookup_and_nonexistent_record(self):
        db=sqlite3.connect(':memory:')
        history=History(db)
        history.add('measurement',{'id':'med-a1b2','op':'use','when':'Día 2',
                                   'verified_facts':['Avancé 2 unidades.']})
        self.assertEqual(history.get('measurement','med-a1b2')['op'],'use')
        self.assertIsNone(history.get('measurement','med-nada'))
        self.assertIsNone(history.get('journal','med-a1b2'))
        # Etapa 19: la ruta pertenece al contrato API, no al transporte HTTP.
        from nilo_runtime.web.api import GET_PATHS
        self.assertIn('/api/measurement', GET_PATHS)
        db.close()

    def test_rendered_reference_and_archive_navigation(self):
        if not shutil.which('node'):self.skipTest('Node.js no disponible')
        runner=r"""
const fs=require('fs'),assert=require('assert'),vm=require('vm');
const js=fs.readFileSync(process.argv[2],'utf8').split('<script>')[1].split('</script>')[0];
const extract=(a,b)=>{const i=js.indexOf(a),j=js.indexOf(b,i);assert(i>=0&&j>i);return js.slice(i,j)};
const src=extract('function measurementLink(', 'function renderMeasurements(){');
let selected=null,opened=false,scrolled=false,lookups=0;
const ctx={
 data:{measurements:[]},focusedMeasurement:null,
 esc:v=>String(v??'').replace(/&/g,'&amp;').replace(/</g,'&lt;'),
 actionName:({op})=>({use:'Usar',build:'Construir'})[op]||op,
 measurementActionTitle:m=>m.op,
 fetch:async path=>{lookups++;assert(path.includes('/api/measurement?id=med-b3b051dd68ab'));return {ok:true,json:async()=>({id:'med-b3b051dd68ab',op:'use',success:true,when:'Día 2',verified_facts:['2 unidades']})}},
 switchTab:t=>{selected=t},
 el:id=>({querySelectorAll:()=>[{dataset:{measurementRecord:'med-b3b051dd68ab'},classList:{add:()=>{opened=true}},scrollIntoView:()=>{scrolled=true},set open(v){opened=v}}]}),
 alert:msg=>{throw Error(msg)}
};
vm.createContext(ctx);vm.runInContext(src,ctx);
const result=ctx.renderEvidenceText("Registré: use (med-b3b051dd68ab; éxito): avancé 2 unidades.");
assert(result.includes('data-measurement-id="med-b3b051dd68ab"'));
assert(result.includes('Ver ensayo · Usar'));
assert(!result.includes('>med-b3b051dd68ab<'));
ctx.openMeasurement('med-b3b051dd68ab').then(()=>{
 assert.equal(lookups,1);assert.equal(selected,'measurements');
 assert(opened&&scrolled);console.log('referencias y navegación archivada OK');
}).catch(e=>{console.error(e);process.exitCode=1});
""";
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'test.js';p.write_text(runner,encoding='utf-8')
            result=subprocess.run(['node',str(p),str(ROOT/'interfaz.html')],
                                  capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('referencias y navegación archivada OK',result.stdout)


if __name__=='__main__':
    unittest.main()
