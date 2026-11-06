from ui_fixture import legacy_markup, legacy_html_path
"""Nilo 0.5.9.2.1: interfaz plegable, navegación y avisos discretos."""
from html.parser import HTMLParser
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
HTML = legacy_markup(Path(__file__).resolve().parents[1])


class Structure(HTMLParser):
    VOID = {"meta", "input", "link", "img", "br", "hr", "source", "area"}
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.nodes = {}
        self.ids = {}
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.setdefault(attrs["id"], []).append(tuple(self.stack))
        if "data-tab" in attrs:
            self.nodes[attrs["data-tab"]] = attrs
        if tag not in self.VOID:
            self.stack.append((tag, attrs.get("id")))
    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, -1, -1):
            if self.stack[i][0] == tag:
                self.stack = self.stack[:i]
                return


class DashboardUI(unittest.TestCase):
    def setUp(self):
        self.parser = Structure()
        self.parser.feed(HTML)

    def test_map_and_references_hide_without_hiding_resources(self):
        ids = self.parser.ids
        for key in ("world-scroll", "map-content", "map-references", "map", "legend",
                    "inventory", "tools", "buildings", "map-toggle", "resources-body"):
            self.assertEqual(len(ids[key]), 1, key)
        for key in ("map", "legend"):
            self.assertIn(("div", "map-content"), ids[key][0])
        for key in ("inventory", "tools", "buildings"):
            self.assertNotIn(("div", "map-content"), ids[key][0])
        self.assertIn("setMapDisplay(mapDisplay)", HTML)
        self.assertIn("nilo.mapDisplay.v2", HTML)
        self.assertIn('id="map-toggle"', HTML)
        self.assertIn('<details id="map-references"', HTML)
        self.assertNotIn('id="map-display"', HTML)
        for key in ("map", "legend", "inventory", "tools", "buildings"):
            self.assertIn(("div", "world-scroll"), ids[key][0])

    def test_model_and_queries_appear_only_in_configuration(self):
        for key in ("aiinfo", "retryllm", "retrymsg", "settings-alerts",
                    "settings-model", "notify-mode", "notify-test"):
            self.assertEqual(len(self.parser.ids[key]), 1, key)
        for key in ("aiinfo", "retryllm", "retrymsg"):
            self.assertIn(("div", "settings-model"), self.parser.ids[key][0])
        self.assertNotIn('<div class="section"><div class="heading">Modelo y consultas</div>', HTML)
        self.assertIn("showSettingsTab('alerts')", HTML)
        self.assertIn("showSettingsTab(button.dataset.settingTab)", HTML)
        self.assertIn("el('mode').textContent", HTML)  # El estado resumido sigue visible.

    def test_tab_dots_not_numeric_or_recolored(self):
        self.assertIn("dot.className=mode==='subtle'?'nav-dot nav-dot-muted':'nav-dot'", HTML)
        self.assertIn("updateTabNotifications()", HTML)
        self.assertIn("TAB_GROUPS[t]===group&&active[t]&&indicatorMode(t)==='normal'", HTML)
        self.assertNotIn("'Novedades ('+newsCount", HTML)
        self.assertNotIn("'Cuaderno ('+notesCount", HTML)
        self.assertIn("el('read-tab').onclick", HTML)
        self.assertNotIn('id="read-both"', HTML)
        self.assertIn("nilo.tabIndicators.v1", HTML)
        self.assertIn("localStorage", HTML)
        self.assertIn("if(t==='notes')return (s.unread?.journal||0)>0", HTML)
        self.assertIn("if(t==='activity'&&(s.unread?.news||0)>0", HTML)
        self.assertIn("if(t==='proposals')return signature(", HTML)
        for tab in ("notes", "activity", "identity", "research", "measurements", "findings", "creations", "projects", "agenda", "habits", "chat", "proposals"):
            self.assertIn(tab, self.parser.nodes)
        self.assertIn("--accent", HTML)

    def test_desktop_page_no_longer_scrolls_entire_document(self):
        self.assertIn("@media(min-width:1181px) and (min-height:680px)", HTML)
        self.assertIn("html,body{height:100%;overflow:hidden}", HTML)
        self.assertIn(".layout>.panel.world-panel>.world-scroll{flex:1;min-height:0;overflow-y:auto;overflow-x:hidden}", HTML)
        self.assertNotIn("#map-content{display:flex;flex-direction:column;min-height:0;max-height:55%}",HTML)
        self.assertIn("min-height:0;flex:1", HTML)

    def test_javascript_syntax(self):
        if not shutil.which("node"):
            self.skipTest("Node.js no disponible")
        js = HTML.split("<script>", 1)[1].split("</script>", 1)[0]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "nilo.js"
            path.write_text(js, encoding="utf-8")
            proc = subprocess.run(["node", "--check", str(path)], capture_output=True,
                                  text=True, check=False)
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_tab_indicators_real_javascript_smoke(self):
        if not shutil.which("node"):
            self.skipTest("Node.js no disponible")
        runner = r"""
const fs=require('fs');
const assert=require('assert');
const html=fs.readFileSync(process.argv[1],'utf8');
const source=html.slice(html.indexOf('const TAB_GROUPS='),html.indexOf('function refreshGroupNav(){'));
function btn(prop,id,label){
 return {
  dataset:{[prop]:id},textContent:label,children:[],
  replaceChildren(...xs){this.children=[...xs]},
  appendChild(child){this.children.push(child)},
  setAttribute(name,value){this[name]=value}
 };
}
const tabs=[
 btn('tab','notes','Cuaderno'),btn('tab','activity','Actividad'),
 btn('tab','research','Investigaciones'),btn('tab','proposals','Propuestas')
];
const groups=[
 btn('group','diario','Diario'),btn('group','laboratorio','Laboratorio'),
 btn('group','autonomia','Autonomía'),btn('group','vinculo','Vínculo')
];
const document={
 querySelectorAll(query){return query==='[data-tab]'?tabs:query==='[data-group]'?groups:[]},
 createTextNode(text){return {textContent:text}},
 createElement(tag){return {tag,className:'',setAttribute(){}}}
};
const readActions={hidden:true},readCount={textContent:''},readTab={disabled:false},indicatorInline={value:''};
const el=id=>({'read-actions':readActions,'unread-count':readCount,'read-tab':readTab,'indicator-inline':indicatorInline}[id]||(()=>{throw Error(id)})());
const saved={};
const stored=(key,fallback)=>saved[key]||fallback;
const saveLocal=(key,value)=>{saved[key]=JSON.parse(JSON.stringify(value))};
let data={unread:{journal:2,news:1},proposals:[{id:'p1',status:'pendiente'}],research:[{id:'r1',state:'abierta'}]};
let tab='research',focusedMeasurement=null;
function marked(button){return button.children.some(x=>x.className==='nav-dot')}
function subtle(button){return button.children.some(x=>x.className==='nav-dot nav-dot-muted')}
const checks = [
 "updateTabNotifications();",
 "assert(marked(tabs[0]));",
 "assert(marked(tabs[1]));",
 "assert(marked(tabs[3]));",
 "assert(marked(groups[0]));",
 "assert(marked(groups[3]));",
 "assert(!marked(tabs[2]));",
 "data.research.push({id:'r2',state:'abierta'});",
 "updateTabNotifications();",
 "assert(marked(tabs[2]));",
 "assert(marked(groups[1]));",
 "updateReadActions();",
 "assert(readActions.hidden===false);",
 "assert(readTab.disabled===false);",
 "indicatorModes.research='subtle';",
 "updateTabNotifications();",
 "assert(subtle(tabs[2]));",
 "assert(!marked(groups[1]));",
 "indicatorModes.research='off';",
 "updateTabNotifications();",
 "assert(!subtle(tabs[2])&&!marked(tabs[2]));",
 "assert(!marked(groups[1]));",
 "indicatorModes.research='normal';",
 "updateTabNotifications();",
 "assert(marked(groups[1]));",
 "updateTabNotifications();", // Entrar sin confirmar no borra la novedad.
 "assert(marked(tabs[2]));",
 "locallyReviewed.research=tabEntries('research',data);",
 "updateTabNotifications();",
 "assert(!marked(tabs[2]));",
 "assert(!marked(groups[1]));",
 "updateReadActions();",
 "assert(readTab.disabled===true);",
 "data.unread={journal:0,news:0};",
 "data.proposals=[{id:'p1',status:'aceptada'}];",
 "updateTabNotifications();",
 "assert(!marked(groups[0]));",
 "assert(!marked(groups[3]));",
 "console.log('UI indicators OK');"
].join('\n');
eval(source+'\n'+checks);
"""
        proc = subprocess.run(
            ["node", "-e", runner, str(legacy_html_path(ROOT))],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("UI indicators OK", proc.stdout)

    def test_historical_engine_and_cognition_not_modified(self):
        version=(ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.assertGreaterEqual(tuple(map(int,version.split("."))), (0,5,9,2,1))
        self.assertTrue((ROOT / "research_cycle.py").exists())
        self.assertTrue((ROOT / "run_history.py").exists())


if __name__ == "__main__":
    unittest.main()
