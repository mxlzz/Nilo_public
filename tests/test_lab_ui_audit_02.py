"""Etapa 02 · Contrato transversal de información y navegación del laboratorio."""
from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGES = {
    "laboratorio_visor_llm.html": "Solicitudes LLM",
    "laboratorio_historico.html": "Historial",
    "laboratorio_escenarios.html": "Pruebas",
    "laboratorio_motor.html": "Pruebas",
    "laboratorio_experimentos.html": "Experimentos A/B",
    "laboratorio_ajustes.html": "Ajustes",
}
PRIMARY = [
    ("/visor-llm", "Solicitudes LLM"),
    ("/historico", "Historial"),
    ("/", "Pruebas"),
    ("/experimentos", "Experimentos A/B"),
    ("/ajustes", "Ajustes"),
]


def page(name):
    return (ROOT / name).read_text("utf-8")


def inline_script(name):
    script = re.search(r"<script(?:\s[^>]*)?>([\s\S]*?)</script>", page(name))
    if not script:
        raise AssertionError("Script inexistente: " + name)
    return script.group(1)


class NavParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.groups = []
        self.current = None
        self.capture = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "nav":
            self.current = {"attrs": attrs, "items": []}
            self.groups.append(self.current)
        elif self.current is not None and tag in {"a", "button"}:
            self.capture = {"tag": tag, "attrs": attrs, "text": ""}
            self.current["items"].append(self.capture)

    def handle_endtag(self, tag):
        if self.capture is not None and tag == self.capture["tag"]:
            self.capture = None
        if tag == "nav":
            self.current = None

    def handle_data(self, data):
        if self.capture is not None:
            self.capture["text"] += data


class Stage02NavigationContract(unittest.TestCase):
    def setUp(self):
        self.pages = {name: page(name) for name in PAGES}

    def test_six_pages_use_exact_same_primary_navigation(self):
        for filename, selected in PAGES.items():
            with self.subTest(page=filename):
                p = NavParser()
                p.feed(self.pages[filename])
                primary = [g for g in p.groups if g["attrs"].get("data-lab-nav") == "primary"]
                self.assertEqual(len(primary), 1)
                nav = primary[0]
                self.assertEqual(nav["attrs"].get("aria-label"), "Secciones del laboratorio")
                links = [(x["attrs"].get("href"), x["text"].strip()) for x in nav["items"]]
                self.assertEqual(links, PRIMARY)
                active = [x for x in nav["items"] if x["attrs"].get("aria-current") == "page"]
                self.assertEqual(len(active), 1)
                self.assertEqual(active[0]["text"].strip(), selected)

    def test_trial_modes_are_accessible_and_have_stable_urls(self):
        scenarios = self.pages["laboratorio_escenarios.html"]
        sandbox = self.pages["laboratorio_motor.html"]
        self.assertIn('aria-label="Modalidades de prueba"', scenarios)
        self.assertIn('aria-label="Modalidades de prueba"', sandbox)
        self.assertIn('id="tabCases"', scenarios)
        self.assertIn('id="tabSandbox"', scenarios)
        self.assertIn('href="/sandbox">Mundo interactivo</a>', scenarios)
        self.assertIn('href="/?modo=plan">Plan de acciones</a>', sandbox)
        self.assertIn('href="/"', sandbox)
        self.assertIn('aria-current="page">Mundo interactivo</a>', sandbox)
        self.assertNotIn("Sandbox de acciones</button>", scenarios)
        self.assertNotIn("Partidas históricas</a>", scenarios)

    def test_query_mode_and_browser_history_have_explicit_contract(self):
        js = inline_script("laboratorio_escenarios.html")
        for marker in (
            "function modeFromAddress()",
            'new URLSearchParams(window.location.search).get("modo")==="plan"',
            'window.history.pushState(',
            'window.addEventListener("popstate"',
            "activateSandbox(modeFromAddress(),false)",
            'setAttribute("aria-pressed",String(on))',
        ):
            self.assertIn(marker, js)

    def test_kind_of_information_is_not_confused_with_real_llm_requests(self):
        self.assertIn("Solicitudes calculadas, no enviadas al LLM",
                      self.pages["laboratorio_escenarios.html"])
        self.assertIn("Pruebas aisladas con el motor real",
                      self.pages["laboratorio_motor.html"])
        self.assertIn("Registros originales de solo lectura",
                      self.pages["laboratorio_historico.html"])
        self.assertIn("Solicitudes reales archivadas",
                      self.pages["laboratorio_visor_llm.html"])
        self.assertIn("Solicitudes calculadas para comparar",
                      self.pages["laboratorio_ajustes.html"])
        self.assertIn("Comparar dos condiciones desde la misma referencia",
                      self.pages["laboratorio_experimentos.html"])

    def test_experiment_mode_works_with_back_forward_navigation(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js no instalado")
        source = inline_script("laboratorio_escenarios.html")
        harness = r"""
const assert=require("node:assert/strict");
const vm=require("node:vm");
const listeners={};
const nodes={};
function element(id){
 if(!nodes[id]){
  const attr={};
  const classes=new Set(id==="tabCases"?["active"]:[]);
  nodes[id]={
   id,attrs:attr,
   classList:{
    toggle(k,on){if(on)classes.add(k);else classes.delete(k);},
    contains(k){return classes.has(k);}
   },
   setAttribute(k,v){attr[k]=v;},
   removeAttribute(k){delete attr[k];}
  };
 }
 return nodes[id];
}
const location={pathname:"/",search:""};
const window={
 location,
 history:{pushState(state,title,address){
  const url=new URL(address,"http://localhost");
  location.pathname=url.pathname;location.search=url.search;
 }},
 addEventListener(type,fn){listeners[type]=fn}
};
const document={
 getElementById:element,
 querySelector(selector){
  assert.equal(selector,".shell");
  return element("shell");
 },
 addEventListener(){}
};
vm.runInNewContext(SOURCE,{
 document,window,URLSearchParams,fetch:()=>new Promise(()=>{}),
 navigator:{clipboard:{writeText:async()=>{}}},console,
},{timeout:2500});
assert.equal(element("tabCases").classList.contains("active"),true);
assert.equal(element("tabSandbox").attrs["aria-pressed"],"false");
element("tabSandbox").onclick();
assert.equal(location.search,"?modo=plan");
assert.equal(element("tabSandbox").classList.contains("active"),true);
assert.equal(element("tabCases").attrs["aria-current"],undefined);
location.search="";
listeners.popstate();
assert.equal(element("tabCases").classList.contains("active"),true);
assert.equal(element("tabCases").attrs["aria-current"],"page");
location.search="?modo=plan";
listeners.popstate();
assert.equal(element("tabSandbox").classList.contains("active"),true);
element("tabCases").onclick();
assert.equal(location.search,"");
assert.equal(element("tabCases").attrs["aria-pressed"],"true");
"""
        completed = subprocess.run(
            [node, "-e", harness.replace("SOURCE", json.dumps(source, ensure_ascii=False))],
            capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
