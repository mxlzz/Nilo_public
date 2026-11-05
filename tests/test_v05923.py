"""0.5.9.2.3 — regresiones visuales y de navegación del dashboard."""
from html.parser import HTMLParser
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parent.parent
HTML=(ROOT/"interfaz.html").read_text(encoding="utf-8")
JS=HTML.split("<script>",1)[1].split("</script>",1)[0]
CSS=HTML.split("<style>",1)[1].split("</style>",1)[0]


class Tree(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack=[]
        self.ids={}
        self.options={}
        self.inside=None

    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if attrs.get("id"):self.ids[attrs["id"]]=list(self.stack)
        if tag=="select":
            self.inside=attrs.get("id")
            self.options[self.inside]=[]
        if tag=="option" and self.inside:self.options[self.inside].append(attrs.get("value"))
        if tag not in ("meta","input","link","br","hr"):
            self.stack.append((tag,attrs.get("id")))

    def handle_endtag(self,tag):
        if tag=="select":self.inside=None
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i][0]==tag:
                self.stack=self.stack[:i]
                break


class UI023(unittest.TestCase):
    def setUp(self):
        self.dom=Tree()
        self.dom.feed(HTML)

    def test_one_vertical_scroller_for_world_column(self):
        for id_ in ("map-content","map-references","map","legend","resources-body",
                    "inventory","tools","buildings"):
            self.assertIn(("div","world-scroll"),self.dom.ids[id_],id_)
        self.assertNotIn(("div","map-content"),self.dom.ids["inventory"])
        self.assertIn("overflow-y:auto;overflow-x:hidden",CSS)
        self.assertNotIn("max-height:55%",CSS)
        self.assertNotIn(".layout>.panel>#world-body{flex:1;overflow-y:auto",CSS)

    def test_map_options_are_persisted_and_do_not_hide_resources(self):
        self.assertIn("map-toggle",self.dom.ids)
        self.assertNotIn("map-display",self.dom.options)
        self.assertIn("nilo.mapDisplay.v2",JS)
        self.assertIn("nilo.mapVisible.v1",JS)
        self.assertIn("el('map-content').hidden=!visible",JS)
        self.assertIn("if(mode==='map')mode='both'",JS)
        self.assertNotIn("el('resources-body').hidden",JS)

    def test_toolbar_matches_speed_controls(self):
        self.assertIn(".headertime button{font-size:11px;padding:5px 7px}",CSS)
        self.assertIn(".maptoolbar button{font:11px/1.35 var(--mono);padding:5px 7px}",CSS)
        self.assertIn(".world-panel .panelhead select,.maptoolbar select{font:11px",CSS)

    def test_indicators_can_be_muted_or_disabled_individually(self):
        self.assertNotIn('data-setting-tab="indicators"',HTML)
        self.assertNotIn('id="indicator-grid"',HTML)
        self.assertIn('id="indicator-inline"',HTML)
        self.assertIn("subtle:'Discreto",JS)
        self.assertIn("off:'Oculto",JS)
        self.assertIn("indicatorMode(t)==='normal'",JS)
        self.assertIn("saveLocal('nilo.tabIndicators.v1',indicatorModes)",JS)
        self.assertIn("nav-dot-muted",CSS)

    def test_read_button_is_per_tab_and_chat_prompt_has_context(self):
        self.assertEqual(HTML.count('id="read-tab"'),1)
        self.assertNotIn('id="read-both"',HTML)
        self.assertNotIn('id="review-tab"',HTML)
        self.assertIn("body:JSON.stringify({categories:[category]})",JS)
        self.assertNotIn("categories:['journal','news']",JS)
        self.assertIn("const keys=tabEntries(selected,data)",JS)
        self.assertIn("await persistTabRead(t,group)",JS)
        self.assertIn("function pendingOverview(source,s)",JS)
        self.assertIn("el('catchup-shortcut').onclick=openPendingOverview;",JS)

    def test_scrollbar_colors_follow_themes(self):
        for theme in ("grafito","terracota"):
            self.assertIn(':root[data-theme="'+theme+'"]{--scroll-track:',CSS)
        self.assertIn("scrollbar-color:var(--scroll-thumb) var(--scroll-track)",CSS)
        self.assertIn("::-webkit-scrollbar-thumb",CSS)

    def test_binary_map_toggle_and_legacy_migration_in_javascript(self):
        if not shutil.which("node"):
            self.skipTest("Node.js no disponible")
        runner=r"""
const fs=require('fs'),assert=require('assert');
const html=fs.readFileSync(process.argv[1],'utf8');
const source=html.slice(html.indexOf('const savedMapDisplay='),html.indexOf('let mapZoom='));
const nodes={'map-toggle':{textContent:'',attrs:{},
                 setAttribute(k,v){this.attrs[k]=v}},
             'map-content':{hidden:false},'resources-body':{hidden:false}};
const memory={'nilo.mapVisible.v1':false};
const stored=(k,fallback)=>Object.hasOwn(memory,k)?memory[k]:fallback;
const saveLocal=(k,v)=>memory[k]=v;
const el=id=>nodes[id];
let shown=0;function showMap(){shown++}
const checks=[
 "assert.equal(mapDisplay,'none');",
 "setMapDisplay('both');",
 "assert.equal(nodes['map-content'].hidden,false);",
 "assert.equal(nodes['map-toggle'].attrs['aria-pressed'],'true');",
 "setMapDisplay('map');",
 "assert.equal(nodes['map-content'].hidden,false);",
 "assert.equal(nodes['map-toggle'].textContent,'Ocultar mapa');",
 "setMapDisplay('none');",
 "assert.equal(nodes['map-content'].hidden,true);",
 "assert.equal(nodes['map-toggle'].attrs['aria-pressed'],'false');",
 "assert.equal(nodes['resources-body'].hidden,false);",
 "assert.equal(memory['nilo.mapDisplay.v2'],'none');",
 "assert.equal(shown,2);",
 "console.log('map toggle OK');"
].join('\n');
eval(source+'\n'+checks);
"""
        result=subprocess.run(["node","-e",runner,str(ROOT/"interfaz.html")],
                              capture_output=True,text=True,check=False)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn("map toggle OK",result.stdout)


if __name__=="__main__":
    unittest.main()
