"""Etapa 20: CSS/JS reales y paridad de navegación del observatorio.

El fixture compatible NO es otro frontend; recompone los mismos assets
para los tests históricos que todavía verifican funciones inline.
"""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import hashlib
import http.client
import json
import re
import shutil
import subprocess
import tempfile
import threading
import unittest

from nilo_runtime.application.engine import Simulation
from nilo_runtime.web.assets import ASSETS, SCRIPT_ORDER
from nilo_runtime.web.api import GET_PATHS, POST_PATHS
from nilo_runtime.web.http import create_server
from ui_fixture import legacy_markup, legacy_html_path

ROOT=Path(__file__).resolve().parents[1]
STYLE=ROOT/"assets/nilo.css"
SCRIPTS=tuple(ROOT/"assets"/Path(p).name for p in SCRIPT_ORDER)
HTML=(ROOT/"interfaz.html").read_text("utf-8")
JS="".join(f.read_text("utf-8") for f in SCRIPTS)
CSS=STYLE.read_text("utf-8")


class Scanner(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids={}
        self.tabs=[]
        self.groups=[]
        self.resource_tabs=[]
        self.inline_attrs=[]
        self.script_src=[]
        self.stylesheets=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get("id"):
            if a["id"] in self.ids:raise ValueError("ID duplicado "+a["id"])
            self.ids[a["id"]]=(tag,a)
        if "data-tab" in a:self.tabs.append(a["data-tab"])
        if "data-group" in a:self.groups.append(a["data-group"])
        if "data-resource-tab" in a:self.resource_tabs.append(a["data-resource-tab"])
        self.inline_attrs += [(tag,k) for k,v in attrs if k.startswith("on")]
        if tag=="script":self.script_src.append(a.get("src"))
        if tag=="link" and a.get("rel")=="stylesheet":self.stylesheets.append(a.get("href"))


class StaticUI20(unittest.TestCase):
    def test_extracted_assets_reassemble_exact_historical_blob(self):
        # SHA1 formato de blob Git sobre interfaz.html anterior a etapa 20.
        reconstructed=legacy_markup(ROOT).encode("utf-8")
        digest=hashlib.sha1(
            f"blob {len(reconstructed)}\0".encode()+reconstructed).hexdigest()
        self.assertEqual(digest,"b2140f365ac0344189096cf615b5cf97d69fa8d2")
        self.assertGreater(len(reconstructed),170000)

    def test_browser_html_no_script_or_style_inline(self):
        self.assertNotIn("<style>",HTML)
        self.assertNotIn("<script>",HTML)
        self.assertNotIn("</style>",HTML)
        self.assertEqual(HTML.count("</script>"),4)
        self.assertLess(len(HTML.encode("utf-8")),16000)

    def test_css_and_classic_script_order_are_explicit(self):
        scanner=Scanner()
        scanner.feed(HTML)
        self.assertEqual(scanner.stylesheets,["/assets/nilo.css"])
        self.assertEqual(scanner.script_src,list(SCRIPT_ORDER))
        self.assertEqual(len(SCRIPTS),4)
        for path in SCRIPT_ORDER:
            self.assertIn('<script defer src="'+path+'"></script>',HTML)
            self.assertIn(path,ASSETS)

    def test_script_syntax_individually_and_concatenated(self):
        if not shutil.which("node"):
            self.skipTest("Node.js no instalado")
        with tempfile.TemporaryDirectory(prefix="nilo-ui-js-") as directory:
            for path in (*SCRIPTS,):
                r=subprocess.run(["node","--check",str(path)],
                                 capture_output=True,text=True,timeout=15)
                self.assertEqual(r.returncode,0,str(path)+" "+r.stderr)
            concat=Path(directory)/"legacy-concatenado.js"
            concat.write_text(JS,encoding="utf-8")
            r=subprocess.run(["node","--check",str(concat)],
                             capture_output=True,text=True,timeout=15)
            self.assertEqual(r.returncode,0,r.stderr)

    def test_all_constant_dom_references_have_real_ids(self):
        scanner=Scanner();scanner.feed(HTML)
        refs={m.group(2) for m in re.finditer(r"\bel\((['\"])([^'\"]+)\1\)",JS)}
        missing=refs-scanner.ids.keys()
        self.assertFalse(missing,sorted(missing))
        self.assertGreater(len(refs),70)

    def test_no_inline_event_attributes_and_no_duplicate_ids(self):
        scanner=Scanner();scanner.feed(HTML)
        self.assertEqual(scanner.inline_attrs,[])
        self.assertGreater(len(scanner.ids),80)

    def test_navigation_groups_and_resource_tabs_kept(self):
        scanner=Scanner();scanner.feed(HTML)
        self.assertEqual(scanner.groups,
                         ["diario","laboratorio","autonomia","vinculo"])
        self.assertEqual(scanner.resource_tabs,
                         ["materials","tools","buildings"])
        for name in ("notes","activity","research","measurements","projects",
                     "agenda","habits","chat","proposals"):
            self.assertIn(name,scanner.tabs)
        self.assertIn("function switchTab(t)",JS)
        self.assertIn("function recentTabEntry(t)",JS)
        self.assertIn("recentTabEntry(b.dataset.tab)",JS)
        self.assertIn("function setResourceTab(next)",JS)
        self.assertIn("['ArrowRight','ArrowLeft','Home','End']",JS)

    def test_ui_notifications_and_catchup_are_still_active(self):
        scanner=Scanner();scanner.feed(HTML)
        for uid in ("catchup-shortcut","catchup-dialog","catchup-more",
                    "catchup-history","catchup-back","notify-dialog",
                    "notify-activate","notify-mode","record-dialog"):
            self.assertIn(uid,scanner.ids)
        for function in ("processNotifications","renderNextObserverSummary",
                         "openPendingOverview","populateNotificationSettings",
                         "restoreRecordLocation","markLocalEntryRead"):
            self.assertIn("function "+function+"(",JS)

    def test_help_dialogs_and_filters_preserved(self):
        scanner=Scanner();scanner.feed(HTML)
        for name in ("research-filter","status-filter",
                     "indicator-inline"):
            self.assertIn(name,scanner.ids)
        self.assertIn("section-help-popover",JS)
        for func in ("closeSectionHelp","openSectionHelp","selectedStatusView",
                     "matchesResearchView","updateReadActions","drawFeed"):
            self.assertIn("function "+func+"(",JS)
        self.assertIn("event.key==='Escape'&&floatingHelp",JS)

    def test_themes_and_map_controls_preserved(self):
        scanner=Scanner();scanner.feed(HTML)
        for uid in ("theme-select","map-toggle","map-content",
                    "map-references","layerselect","zoomin","zoomout"):
            self.assertIn(uid,scanner.ids)
        self.assertIn(":root{",CSS)  # «bosque» es el tema por defecto.
        for theme in ("grafito","terracota",
                      "grises-oscuros","grises-claros"):
            self.assertIn('[data-theme="'+theme+'"]',CSS)
        self.assertIn("function setMapDisplay(mode)",JS)
        self.assertIn("function showMap()",JS)
        self.assertIn("function adjustZoom(delta)",JS)

    def test_api_routes_used_by_ui_are_available(self):
        paths={m.group(1).split("?")[0] for m in
               re.finditer(r"fetch\(['\"](/api/[a-z-]+)",JS)}
        self.assertTrue(paths)
        self.assertEqual(paths-(GET_PATHS|POST_PATHS),set())
        self.assertIn("/api/state",paths)
        self.assertIn("/api/chat",paths)
        self.assertIn("/api/review-mark",paths)

    def test_switching_tab_does_not_send_mutating_requests(self):
        source=JS.split("function switchTab(t){",1)[1].split(
            "async function refresh(){",1)[0]
        self.assertNotIn("fetch(",source)
        self.assertNotIn("settings(",source)
        self.assertNotIn("markRead(",source)
        self.assertNotIn("saveLocal(",source)
        self.assertIn("updateTabNotifications()",source)

    def test_deferred_renderers_and_refresh_have_same_runtime_symbols(self):
        self.assertIn("function show(data2)",SCRIPTS[0].read_text("utf-8"))
        self.assertIn("function renderNotes()",SCRIPTS[1].read_text("utf-8"))
        self.assertIn("function drawFeed()",SCRIPTS[2].read_text("utf-8"))
        self.assertIn("async function refresh()",SCRIPTS[3].read_text("utf-8"))
        self.assertIn("setInterval(refresh,2000)",SCRIPTS[3].read_text("utf-8"))
        self.assertIn("setInterval(animateWriting,130)",SCRIPTS[3].read_text("utf-8"))

    def test_legacy_node_tests_read_generated_source_not_duplicate_artifact(self):
        self.assertFalse((ROOT/"tests"/"interfaz_legacy.html").exists())
        self.assertTrue(legacy_html_path(ROOT).exists())
        self.assertEqual(legacy_html_path(ROOT).read_text("utf-8"),legacy_markup(ROOT))


class WebUI20(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix="nilo-web-ui-20-")
        cls.sim=Simulation(db_path=Path(cls.tmp.name)/"partida.sqlite3",
                           world_seed=7321,rng_seed=9821)
        cls.server=create_server(cls.sim,0)
        cls.port=cls.server.server_address[1]
        cls.thread=threading.Thread(target=cls.server.serve_forever,
                                    kwargs={"poll_interval":0.03},daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=4)
        cls.sim.conn.close()
        cls.tmp.cleanup()

    def get(self,path):
        conn=http.client.HTTPConnection("127.0.0.1",self.port,timeout=10)
        try:
            conn.request("GET",path)
            response=conn.getresponse()
            result=response.status,response.read(),dict(response.getheaders())
            return result
        finally:conn.close()

    def test_root_and_all_assets_are_http_accessible(self):
        status,body,headers=self.get("/")
        self.assertEqual(status,200)
        self.assertEqual(body,HTML.encode("utf-8"))
        self.assertIn("script-src 'self';",headers["Content-Security-Policy"])
        self.assertNotIn("script-src 'self' 'unsafe-inline'",
                         headers["Content-Security-Policy"])
        for route,(mime,path) in ASSETS.items():
            with self.subTest(asset=route):
                status,body,headers=self.get(route)
                self.assertEqual(status,200)
                self.assertEqual(body,path.read_bytes())
                self.assertEqual(headers["Content-Type"],mime)
                self.assertEqual(headers["Cache-Control"],"no-store")
                self.assertEqual(headers["X-Content-Type-Options"],"nosniff")

    def test_asset_requests_are_pure_reads_of_world_and_rng(self):
        world_before=json.dumps(self.sim.s,ensure_ascii=False,
                                sort_keys=True,default=str)
        rng_before=self.sim.entropy.to_record(agent_rng=self.sim.rng)
        writes=self.sim.conn.total_changes
        for route in ("/",*ASSETS):
            status,_,_=self.get(route)
            self.assertEqual(status,200)
        self.assertEqual(self.sim.conn.total_changes,writes)
        self.assertEqual(json.dumps(self.sim.s,ensure_ascii=False,
                                    sort_keys=True,default=str),world_before)
        self.assertEqual(self.sim.entropy.to_record(agent_rng=self.sim.rng),
                         rng_before)

    def test_unknown_files_and_path_traversal_are_404(self):
        for route in ("/assets/missing.js","/assets/../config.env",
                      "/assets/%2e%2e/config.env","/assets/private.sqlite3",
                      "/assets/nilo.css/../config.env",
                      "/nilo_runtime/application/session.py"):
            with self.subTest(route=route):
                status,body,_=self.get(route)
                self.assertEqual(status,404)
                self.assertIn(b"No encontrado",body)


if __name__=="__main__":
    unittest.main()
