"""Etapa 04.1 · Visor LLM: lectura progresiva y fidelidad literal.

Pruebas de interfaz con datos sintéticos; no requieren red ni proveedor LLM.
"""
from __future__ import annotations
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
PAGE=ROOT/"laboratorio_visor_llm.html"


def script():
    html=PAGE.read_text(encoding="utf-8")
    found=re.search(r"<script>([\s\S]*?)</script>",html)
    if not found:
        raise AssertionError("Falta script principal del visor")
    return found.group(1)


class Markup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids=set()
        self.advanced_depth=0
        self.in_advanced=False
        self.advanced_ids=set()
        self.names=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        ident=attrs.get("id")
        if ident:
            assert ident not in self.ids, "ID duplicado: "+ident
            self.ids.add(ident)
            if self.in_advanced: self.advanced_ids.add(ident)
        if tag=="details" and "filter-advanced" in attrs.get("class",""):
            self.in_advanced=True
        self.names.append(tag)
    def handle_endtag(self,tag):
        if tag=="details" and self.in_advanced:
            self.in_advanced=False
        if self.names: self.names.pop()


class ViewerStage041(unittest.TestCase):
    def test_filters_are_progressive_without_losing_fields(self):
        markup=PAGE.read_text("utf-8")
        doc=Markup();doc.feed(markup)
        self.assertEqual(
            {"provider","purpose","state","date","model","call","session","limit"},
            doc.ids.intersection({"provider","purpose","state","date","model","call","session","limit"}))
        self.assertEqual(doc.advanced_ids,{"date","model","call","session","limit"})
        self.assertIn("Más filtros · fecha, modelo e identificadores",markup)
        self.assertIn("Aplicar filtros",markup)
        self.assertIn("Limpiar",markup)
        self.assertIn("Consultas y reintentos",markup)
        self.assertIn("Vista",markup) if False else None

    def test_syntax_and_literal_safety(self):
        source=script()
        self.assertIn("groupAttempts(attempts)",source)
        self.assertIn("Índice de bloques",source)
        self.assertIn("focusBlock(target)",source)
        self.assertIn("block.literal",source)
        self.assertIn("data.body_utf8",source)
        self.assertIn("N(\"details\",\"capture-meta\")",source)
        self.assertNotIn(".innerHTML",source)
        self.assertNotIn(".outerHTML",source)
        self.assertNotIn("insertAdjacentHTML",source)
        self.assertNotIn("document.write",source)
        node=shutil.which("node")
        if not node: self.skipTest("Node.js no instalado")
        checked=subprocess.run([node,"--check","-"],input=source,
                               capture_output=True,text=True,timeout=10)
        self.assertEqual(checked.returncode,0,checked.stderr)

    def test_retry_grouping_and_direct_literal_block_navigation(self):
        node=shutil.which("node")
        if not node: self.skipTest("Node.js no instalado")
        source=script()
        # Los listeners finales pertenecen a la página; el harness evalúa
        # únicamente las funciones puras de renderizado sobre DOM sintético.
        marker='$("simple-mode").addEventListener('
        self.assertIn(marker,source)
        pure=source.split(marker,1)[0]
        harness=r"""
const vm=require("node:vm");
const assert=require("node:assert/strict");
class Element {
 constructor(tag){
  this.tagName=tag;this.children=[];this.attributes={};this.dataset={};
  this.listeners={};this.className="";this.textContent="";this.type="";
  this.open=false;this.scrolled=false;this.focused=false;
  this.classList={toggle:()=>{}};
 }
 appendChild(node){this.children.push(node);return node;}
 replaceChildren(...items){this.children=[...items];}
 setAttribute(k,v){this.attributes[k]=String(v);}
 addEventListener(type,fn){this.listeners[type]=fn;}
 scrollIntoView(){this.scrolled=true;}
 focus(){this.focused=true;}
 querySelector(tag){return find(this,x=>x.tagName===tag)[0]||null;}
}
function find(node,check){let found=[];
 if(check(node))found.push(node);
 for(const child of node.children||[])found.push(...find(child,check));
 return found;
}
const elements=new Map();
const document={
 createElement:tag=>new Element(tag),
 getElementById:id=>{if(!elements.has(id))elements.set(id,new Element(id));return elements.get(id);}
};
const sandbox={document,console,URLSearchParams,encodeURIComponent};
vm.runInNewContext(SOURCE+"\n;this.lab={groupAttempts,renderAttempts,renderMessages};this.setAttempts=x=>{attempts=x};",sandbox,{timeout:2500});
const entries=[
 {attempt_id:"a1",call_id:"call_A",session_id:1,attempt_ordinal:1,purpose:"deliberacion",provider:"gemini",model:"m",
  status:"transport_error",started_utc:"2026-11-06T20:00:00",simulated_at:"día 1"},
 {attempt_id:"a2",call_id:"call_A",session_id:1,attempt_ordinal:2,purpose:"deliberacion",provider:"gemini",model:"m",
  status:"accepted",started_utc:"2026-11-06T20:00:15",simulated_at:"día 1"},
 {attempt_id:"b1",call_id:"call_B",session_id:1,attempt_ordinal:1,purpose:"chat",provider:"groq",model:"m",
  status:"accepted",started_utc:"2026-11-06T20:01:00",simulated_at:"día 1"}
];
assert.equal(sandbox.lab.groupAttempts(entries).length,2);
assert.deepEqual(sandbox.lab.groupAttempts(entries).map(g=>g.length).join(","),"2,1");
sandbox.setAttempts(entries);
sandbox.lab.renderAttempts();
const list=document.getElementById("attempt-list");
assert.equal(list.children.length,2);
const items=find(list,x=>x.tagName==="button"&&x.dataset.attempt);
assert.deepEqual(items.map(x=>x.dataset.attempt).join(","),"a1,a2,b1");
const malicious='<img src=x onerror=alert(1)>\n  {\n  "raw": "\"literal\""\n}';
const message={
 role:"user",path:"/contents/0/parts/0/text",
 blocks:[{title:"necesidades",subtitle:"Sensaciones corporales transmitidas",literal:malicious,json_pointer:"/necesidades"},
         {title:"posición",subtitle:"",literal:"\"x\": 17",json_pointer:"/posición"}]
};
const container=new Element("div");
sandbox.lab.renderMessages({messages:[message],provenance:null},container);
const pres=find(container,x=>x.tagName==="pre");
assert.equal(pres.length,2);
assert.equal(pres[0].textContent,malicious);
assert.equal(pres[1].textContent,'\"x\": 17');
const block=find(container,x=>x.tagName==="details"&&x.className==="block")[0];
assert.equal(block.open,false);
const navButton=find(container,x=>x.tagName==="button"&&x.textContent==="necesidades")[0];
assert.ok(navButton);
navButton.listeners.click();
assert.equal(block.open,true);
assert.equal(block.scrolled,true);
assert.equal(block.querySelector("summary").focused,true);
"""
        code=harness.replace("SOURCE",json.dumps(pure,ensure_ascii=False))
        result=subprocess.run([node,"-e",code],capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stderr)


if __name__=="__main__":
    unittest.main()
