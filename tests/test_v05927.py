from ui_fixture import legacy_markup, legacy_html_path
"""0.5.9.2.7 — lectura directa, indicador contextual, mapa y resultados vinculados."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = legacy_markup(Path(__file__).resolve().parents[1])
JS = HTML.split("<script>", 1)[1].split("</script>", 1)[0]
CSS = HTML.split("<style>", 1)[1].split("</style>", 1)[0]


class VisualRegression(unittest.TestCase):
    def test_clicking_cards_replaces_all_checks(self):
        self.assertNotIn('type="checkbox"', HTML)
        self.assertNotIn("record-mark", HTML)
        self.assertIn("card.dataset.reviewEntryKey", JS)
        self.assertIn("if(!id||!item||item.read||item.writing", JS)
        self.assertIn("markRead(tab==='notes'?'journal':'news',id,true)", JS)
        self.assertIn("node.classList.remove('new-record')", JS)
        self.assertIn("   drawFeed();", JS)
        self.assertIn("if(!res.ok||result.ok!==true)", JS)

    def test_indicator_is_contextual_and_portable(self):
        self.assertIn('id="indicator-inline"', HTML)
        self.assertIn("indicatorModes[tab]=ev.target.value", JS)
        self.assertIn("saveLocal('nilo.tabIndicators.v1',indicatorModes)", JS)
        self.assertIn("el('indicator-inline').value=indicatorMode(tab)", JS)
        self.assertIn("indicatorMode(t)==='normal'", JS)

    def test_rock_terrain_and_trail_have_separate_colors(self):
        self.assertIn('--rock-bg:#293c4c', CSS)
        self.assertIn('--floor-color:#3b5143', CSS)
        self.assertIn('--grass-color:#486650', CSS)
        self.assertIn('.tile.trail-5{background:rgba(215,182,119,.59)}', CSS)
        self.assertIn('.tile.t-rock{color:var(--rock-color);background:var(--rock-bg)', CSS)

    def test_research_names_real_results(self):
        self.assertIn('Ver los ${linked.length} registros asociados', JS)
        self.assertIn('(e.facts||[]).map(f=>', JS)
        self.assertIn('No todos acreditan la hipótesis.', JS)
        self.assertIn('Mediciones citadas:', JS)

    def test_node_runs_research_and_local_read(self):
        if not shutil.which('node'):
            self.skipTest('Node.js no disponible')
        runner = r"""
const fs=require('fs'),assert=require('assert'),vm=require('vm');
const js=fs.readFileSync(process.argv[2],'utf8').split('<script>')[1].split('</script>')[0];
function extract(a,b){const i=js.indexOf(a),j=js.indexOf(b,i);assert(i>=0&&j>i,a);return js.slice(i,j)}
const src=extract('function renderResearch(){','function renderPredictions(){')+
          extract('function relatedReadKeys(', "el('feed').addEventListener('click',async ev=>");
let removed=0,update=0;
const ctx={
 tab:'research',data:{conclusions:[],research:[{question:'¿Resiste?',hypothesis:'Tal vez',started:'Día 2',state:'abierta',evidence:[{when:'Día 2 · 03:00',facts:['Probé piedra y falló.']},{when:'Día 2 · 04:00',facts:['Construí un muro.']}]}],measurements:[]},
 esc:v=>String(v??'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])),
 locallyReviewed:{research:[]},saveLocal:()=>{},updateTabNotifications:()=>update++,
 tabEntries:()=>[],fetch:async()=>({ok:true}),
 updateReadActions:()=>{},drawFeed:()=>{},measurementActionTitle:m=>m.op,lastFeedSig:'prior',
 renderEvidenceText:v=>v,measurementLink:id=>'Ver ensayo '+id,renderPredictions:()=>' ',recordLinks:()=>'',
 el:()=>({querySelectorAll:()=>[{dataset:{reviewEntryKey:'r1'},classList:{remove:()=>removed++}}]})
};
vm.createContext(ctx);vm.runInContext(src,ctx);
const card=ctx.renderResearch();
assert(card.includes('Probé piedra y falló.'));
assert(card.includes('Construí un muro.'));
assert(card.includes('2 registros de acciones asociados'));
ctx.markLocalEntryRead('r1');
assert.equal(ctx.lastFeedSig,'prior');assert.equal(removed,1);assert.equal(update,1);
assert(ctx.locallyReviewed.research.includes('r1'));
console.log('investigación y lectura directa OK');
""";
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'check.js'
            path.write_text(runner,encoding='utf-8')
            proc=subprocess.run(['node',str(path),str(legacy_html_path(ROOT))],capture_output=True,text=True,timeout=15)
        self.assertEqual(proc.returncode,0,proc.stderr)
        self.assertIn('investigación y lectura directa OK',proc.stdout)


if __name__=='__main__':
    unittest.main()
