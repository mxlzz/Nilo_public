"""Etapa 03: sistema visual compartido, temas y assets seguros.

Las pruebas son locales/sintéticas. No ejecutan proveedores LLM.
"""
from __future__ import annotations

import http.client
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import unittest

from laboratorio_motor import create_lab_server
from nilo_runtime.labs.hub import LabHub

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "assets/laboratorio.css"
JS = ROOT / "assets/laboratorio_ui.js"
PAGES = (
    "laboratorio_motor.html",
    "laboratorio_escenarios.html",
    "laboratorio_historico.html",
    "laboratorio_ajustes.html",
    "laboratorio_visor_llm.html",
    "laboratorio_analisis.html",
)


class AssetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.body = []
        self.stylesheets = []
        self.scripts = []
        self.toggle_count = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "body":
            self.body.append(a.get("data-lab"))
        if tag == "link" and a.get("rel") == "stylesheet":
            self.stylesheets.append(a.get("href"))
        if tag == "script" and "src" in a:
            self.scripts.append(a["src"])
        if a.get("id") == "lab-theme-toggle":
            self.toggle_count += 1
            assert tag == "button" and a.get("type") == "button"


class Stage03Design(unittest.TestCase):
    def test_all_pages_use_single_allowlisted_asset_and_toggle(self):
        for file in PAGES:
            with self.subTest(file=file):
                source = (ROOT / file).read_text("utf-8")
                parsed = AssetParser()
                parsed.feed(source)
                self.assertEqual(len(parsed.body), 1)
                self.assertTrue(parsed.body[0])
                self.assertEqual(parsed.stylesheets, ["/assets/laboratorio.css"])
                self.assertEqual(parsed.scripts, ["/assets/laboratorio_ui.js"])
                self.assertEqual(parsed.toggle_count, 1)
                self.assertLess(source.index("</style>"), source.index("/assets/laboratorio.css"))
                self.assertIn('id="lab-theme-toggle"', source)

    def test_theme_tokens_and_accessibility_contract(self):
        css = CSS.read_text("utf-8")
        for marker in (
            "--lab-bg", "--lab-surface", "--lab-border", "--lab-text",
            "--lab-accent", "--lab-focus", "--lab-font", "--lab-mono",
            'data-lab-theme="dark"', 'data-lab-theme="light"',
            "prefers-color-scheme:dark", "prefers-reduced-motion:reduce",
            "focus-visible", "max-width:720px", "max-width:430px",
            'nav[data-lab-nav="primary"]',
            "body[data-lab] .panel",
        ):
            self.assertIn(marker, css)
        self.assertNotIn("@import", css)
        js = JS.read_text("utf-8")
        for marker in ('"system"', '"light"', '"dark"', "localStorage",
                       "data-lab-theme", "DOMContentLoaded"):
            self.assertIn(marker, js)
        self.assertNotIn("fetch(", js)
        self.assertNotIn("innerHTML", js)
        self.assertNotIn("document.write", js)

    def test_theme_cycles_and_remembers_preference_without_network(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js no instalado")
        source = JS.read_text("utf-8")
        harness = r"""
const vm=require("node:vm");
const assert=require("node:assert/strict");
const attrs={},saved={};
const events={};
const button={textContent:"",attrs:{},
 setAttribute(k,v){this.attrs[k]=v},addEventListener(type,fn){events[type]=fn}};
const html={
 setAttribute(k,v){attrs[k]=v},
 removeAttribute(k){delete attrs[k]}
};
const document={readyState:"complete",documentElement:html,
 getElementById(id){return id==="lab-theme-toggle"?button:null}};
const window={localStorage:{
 getItem(key){return saved[key]||null},
 setItem(key,value){saved[key]=value},
}};
const source=SOURCE;
vm.runInNewContext(source,{document,window,console},{timeout:3000});
assert.equal(button.textContent,"Tema: sistema");
assert.equal(attrs["data-lab-theme"],undefined);
events.click();
assert.equal(attrs["data-lab-theme"],"light");
assert.equal(button.textContent,"Tema: claro");
events.click();
assert.equal(attrs["data-lab-theme"],"dark");
assert.equal(button.textContent,"Tema: oscuro");
events.click();
assert.equal(attrs["data-lab-theme"],undefined);
assert.equal(saved["nilo.lab.theme.v1"],"system");
"""
        proc = subprocess.run(
            [node, "-e", harness.replace("SOURCE", json.dumps(source, ensure_ascii=False))],
            capture_output=True, text=True, timeout=12,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)


class Stage03LocalServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="nilo-lab-ui03-")
        root = Path(cls.temp.name)
        cls.server = create_lab_server(0, lab=object(),
                                       hub=LabHub(root, root / "world.sqlite3"))
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever,
             kwargs={"poll_interval":0.02}, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=4)
        cls.temp.cleanup()

    def request(self, path, headers=None):
        con = http.client.HTTPConnection("127.0.0.1", self.port, timeout=6)
        try:
            con.request("GET", path, headers=headers or {})
            response = con.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            con.close()

    def test_serve_only_allowlisted_assets_with_correct_mime(self):
        for path, mime, fixture in (
            ("/assets/laboratorio.css", "text/css; charset=utf-8", CSS),
            ("/assets/laboratorio_ui.js", "text/javascript; charset=utf-8", JS),
        ):
            with self.subTest(path=path):
                status, headers, data = self.request(path)
                self.assertEqual(status, 200)
                self.assertEqual(headers.get("Content-Type"), mime)
                self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")
                self.assertEqual(headers.get("Cache-Control"), "no-store")
                self.assertEqual(data, fixture.read_bytes())
        self.assertEqual(self.request("/assets/unlisted.js")[0], 404)
        self.assertEqual(self.request("/assets/../../config.env")[0], 404)

    def test_all_lab_html_pages_reference_available_assets(self):
        for path in ("/", "/sandbox", "/historico", "/ajustes", "/visor-llm"):
            with self.subTest(path=path):
                status, headers, body = self.request(path)
                self.assertEqual(status, 200)
                self.assertIn("text/html", headers.get("Content-Type", ""))
                self.assertIn(b"/assets/laboratorio.css", body)
                self.assertIn(b"/assets/laboratorio_ui.js", body)

    def test_foreign_host_cannot_read_assets(self):
        status, _, _ = self.request(
            "/assets/laboratorio_ui.js", headers={"Host":"evil.example"}
        )
        self.assertNotEqual(status, 200)


class Stage03Package(unittest.TestCase):
    def test_both_assets_are_in_portable_manifest(self):
        manifest=json.loads((ROOT/"MANIFIESTO_SHA256.json").read_text("utf-8"))
        for file in ("assets/laboratorio.css","assets/laboratorio_ui.js"):
            self.assertIn(file, manifest["files"])
            self.assertTrue((ROOT/file).is_file())


if __name__ == "__main__":
    unittest.main()
