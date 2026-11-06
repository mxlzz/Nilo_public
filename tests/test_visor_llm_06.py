"""Etapa 06: visor UI sobre API de solo lectura, integridad y texto no ejecutable."""
from __future__ import annotations

import http.client
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading
import unittest

from laboratorio_motor import create_lab_server
from nilo_runtime.labs.hub import LabHub
from nilo_runtime.storage.llm_requests import RequestTraceStore
from nilo_runtime.web.api import dispatch

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "laboratorio_visor_llm.html"
IDS = ("attempt-list", "list-status", "detail", "refresh", "filters",
       "provider", "purpose", "state", "date", "model", "call", "session",
       "limit", "more", "count", "simple-mode", "pro-mode", "notice", "clear")


class BrowserContract(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.hrefs = set()
        self.scripts = []
        self.in_script = False
        self.nav_labels = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            assert a["id"] not in self.ids, "id duplicado: " + a["id"]
            self.ids.add(a["id"])
        if tag == "script":
            self.in_script = True
            assert "src" not in a, "La vista inicial utiliza JS autocontenido"
        if tag == "a":
            self.hrefs.add(a.get("href"))
        for name,_ in attrs:
            assert not name.lower().startswith("on"), "No eventos HTML inline"

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_script = False

    def handle_data(self, data):
        if self.in_script:
            self.scripts.append(data)


def fixture():
    return json.dumps({
        "model":"llm-demo",
        "messages":[
            {"role":"system","content":"Respondé sin inventar."},
            {"role":"user","content":'{"necesidades":{"energia":"con energía"},'
             '"texto":"<img src=x onerror=alert(1)>"}'}
        ]
    },ensure_ascii=False).encode("utf-8")


class BrowserMarkup06(unittest.TestCase):
    def setUp(self):
        self.text = PAGE.read_text("utf-8")
        self.doc = BrowserContract()
        self.doc.feed(self.text)

    def test_page_has_two_views_filters_buttons_and_labeled_block_sections(self):
        self.assertTrue(set(IDS) <= self.doc.ids)
        self.assertTrue({"/","/visor-llm","/historico","/ajustes"} <= self.doc.hrefs)
        self.assertIn('aria-current="page"', self.text)
        for marker in ("Simplificada","Profesional",
                       "Contexto que recibe el LLM","Copiar bloque",
                       "Procedencia del campo","body_utf8","json_pointer",
                       "renderMessages","renderProfessional","block.literal"):
            self.assertIn(marker,self.text)
        self.assertIn('type="date" id="date"',self.text)
        self.assertIn("aria-pressed",self.text)

    def test_literally_rendered_text_is_not_parsed_as_dynamic_html(self):
        script="\n".join(self.doc.scripts)
        self.assertNotIn(".innerHTML",script)
        self.assertNotIn(".outerHTML",script)
        self.assertNotIn(".insertAdjacentHTML",script)
        self.assertNotIn("document.write",script)
        self.assertIn("node.textContent=String(text)",script)
        self.assertIn("pre",self.text)
        self.assertIn("message.blocks",self.text)
        self.assertIn("block.literal",script)
        self.assertNotIn("markdown",script.lower())

    def test_javascript_parses_with_node_when_installed(self):
        node=shutil.which("node")
        if not node:
            self.skipTest("Node.js no instalado")
        with tempfile.TemporaryDirectory(prefix="nilo-visor-js-") as folder:
            js=Path(folder)/"visor.js"
            js.write_text("\n".join(self.doc.scripts),encoding="utf-8")
            proc=subprocess.run([node,"--check",str(js)],capture_output=True,
                                text=True,timeout=18)
            self.assertEqual(proc.returncode,0,proc.stderr)

    def test_page_and_assets_are_in_portable_manifest(self):
        manifest=json.loads((ROOT/"MANIFIESTO_SHA256.json").read_text("utf-8"))
        self.assertIn("laboratorio_visor_llm.html",manifest["files"])
        self.assertTrue(PAGE.is_file())
        self.assertIn("laboratorio_motor.py",manifest["files"])


class BrowserHttp06(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix="nilo-visor-http06-")
        cls.root=Path(cls.temp.name)
        cls.world=cls.root/"world.sqlite3"
        cls.store=RequestTraceStore.for_world(cls.world)
        cls.server=create_lab_server(0,lab=object(),hub=LabHub(cls.root,cls.world))
        cls.port=cls.server.server_address[1]
        cls.thread=threading.Thread(target=cls.server.serve_forever,
            kwargs={"poll_interval":0.02},daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=4)
        cls.temp.cleanup()

    def request(self,path,method="GET",headers=None):
        conn=http.client.HTTPConnection("127.0.0.1",self.port,timeout=6)
        try:
            conn.request(method,path,headers=headers or {})
            response=conn.getresponse()
            return response.status,dict(response.getheaders()),response.read()
        finally:
            conn.close()

    def test_viewer_is_served_only_at_lab_path_without_creating_sidecar(self):
        # Otras pruebas de esta clase pueden haber escrito una captura
        # sintética: comprobar ausencia de cambios, no ausencia de datos.
        before=(self.store.path.read_bytes() if self.store.path.exists() else None)
        status,headers,body=self.request("/visor-llm")
        self.assertEqual(status,200)
        self.assertEqual(headers["Content-Type"],"text/html; charset=utf-8")
        self.assertEqual(headers["Cache-Control"],"no-store")
        self.assertIn(b"id=\"simple-mode\"",body)
        self.assertIn(b"id=\"pro-mode\"",body)
        after=(self.store.path.read_bytes() if self.store.path.exists() else None)
        self.assertEqual(before,after)
        self.assertEqual(dispatch(object(),"GET","/visor-llm").status,404)
        self.assertEqual(dispatch(object(),"GET",
                "/api/lab/llm/attempts").status,404)

    def test_old_lab_navigation_stays_reachable(self):
        for path in ("/","/sandbox","/historico","/ajustes"):
            status,_,body=self.request(path)
            self.assertEqual(status,200,path)
            self.assertIn(b'href="/visor-llm"',body,path)
        for path in ("/visor-llm","/sandbox"):
            status,_,body=self.request(path)
            self.assertEqual(status,200)
            self.assertNotEqual(body,b"")

    def test_page_loopback_host_origin_and_methods(self):
        self.assertEqual(self.request("/visor-llm",headers={
            "Origin":"https://malicioso.example"})[0],403)
        self.assertEqual(self.request("/visor-llm",headers={
            "Host":"malicioso.example"})[0],403)
        self.assertEqual(self.request("/visor-llm",method="POST")[0],404)
        self.assertEqual(self.request("/api/lab/llm/attempts",method="POST")[0],404)

    def test_fixture_can_be_requested_by_detail_without_html_execution(self):
        ident=self.store.begin(body=fixture(),call_id="a"*32,
             session_id=10,purpose="deliberacion",source_id=None,
             simulated_at="Día 4 · 12:00",ordinal=1,provider="groq",
             model="llm-demo",
             provenance={"schema_version":1,"payload_verification":
                         "verificado_con_payload_http"})
        status,headers,raw=self.request("/api/lab/llm/attempt?id="+ident)
        self.assertEqual(status,200)
        response=json.loads(raw)
        self.assertEqual(response["body_utf8"].encode("utf-8"),fixture())
        self.assertIn("<img src=x onerror=alert(1)>",response["body_utf8"])
        self.assertEqual(headers["X-Content-Type-Options"],"nosniff")
        self.assertEqual(headers["Cache-Control"],"no-store")


if __name__ == "__main__":
    unittest.main()
