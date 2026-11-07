"""Etapa 06: selección humana y exportación local, SIN aplicar cambios.

Verificación del contrato del artefacto en Node, y rutas/HTML mediante Python.
No requiere red ni credenciales LLM.
"""
from __future__ import annotations

import http.client
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import unittest

from laboratorio_motor import create_lab_server, HistorySource
from nilo_runtime.labs.hub import LabHub, _request
from nilo_runtime.labs.profiles import baseline
from auditar_contexto_llm import scenario_context

ROOT=Path(__file__).resolve().parents[1]
ASSET=ROOT/"assets"/"laboratorio_ui.js"


class ReviewArtifactTests(unittest.TestCase):
    def test_review_json_requires_exact_http_and_keeps_unicode_codepoint_offsets(self):
        node=shutil.which("node")
        if not node:self.skipTest("Node no disponible")
        script=r"""
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
globalThis.crypto=crypto.webcrypto;
const api=require(process.argv[1]);
const hash=x=>crypto.createHash('sha256').update(x,'utf8').digest('hex');
const cp=x=>Array.from(x).length;
(async()=>{
 const prefix='💚 {',field='"antecedentes_relacionados":"día"',suffix='}';
 const txt=prefix+field+suffix;
 const p=cp(prefix),end=p+cp(field);
 const body=JSON.stringify({model:'demo',messages:[{role:'user',content:txt}]});
 const seg=(kind,a,b,literal)=>({
   kind,start:a,end:b,literal,literal_sha256:hash(literal),
   display_group:kind==='field'?'memoria':'texto'
 });
 const block={...seg('field',p,end,field),
   title:'antecedentes_relacionados',subtitle:'Antecedente',
   json_pointer:'/antecedentes_relacionados'};
 const message={
   path:'/messages/0/content',role:'user',text:txt,text_sha256:hash(txt),
   segments:[seg('text',0,p,prefix),block,seg('syntax',end,cp(txt),suffix)],
   blocks:[block]
 };
 const model={kind:'captured_http',sent_to_llm:true,body_utf8:body,
   body_sha256:hash(body),body_bytes:Buffer.byteLength(body,'utf8'),
   provider:'groq',model:'demo',purpose:'deliberacion',attempt_id:'a'.repeat(32),
   call_id:'b'.repeat(32),simulated_at:'Día 12',messages:[message]};
 const selection=new Map([[api.key(message.path,block),{note:'Se repite sin aportar evidencia'}]]);
 const policy={engine_version:'0.7',commit:null,optional_context:['antecedentes_relacionados']};
 const original=JSON.stringify(model);
 const review=await api.buildReview(model,selection,'revisión contextual',policy);
 assert.equal(review.schema,'nilo.lab.context_review.v1');
 assert.equal(review.review_status,'human_proposal_not_applied');
 assert.equal(review.source.sent_to_llm,true);
 assert.equal(review.source.installed_engine_version,'0.7');
 assert.equal(review.original.body_utf8,body);
 assert.equal(review.original.body_sha256,hash(body));
 assert.equal(review.integrity.offsets_checked_as_unicode_codepoints,true);
 assert.equal(review.proposals.length,1);
 assert.equal(review.proposals[0].start_codepoint,cp(prefix));
 assert.equal(review.proposals[0].original_literal,field);
 assert.equal(review.proposals[0].original_literal_sha256,hash(field));
 assert.equal(review.proposals[0].existing_profile_optional_field,true);
 assert.equal(review.proposals[0].requires_manual_review,true);
 assert.equal(review.proposals[0].applied_to_engine,false);
 assert.equal(JSON.stringify(model),original);
 assert.ok(!review.modified_prompt);
 // Una nota sola también permite documentar hallazgos, sin exclusiones.
 const empty=await api.buildReview(model,new Map(),'Sin cambios aún',policy);
 assert.equal(empty.proposals.length,0);
 assert.equal(empty.general_observation,'Sin cambios aún');
 const wrong={...model,body_utf8:body+' MODIFICADO'};
 await assert.rejects(()=>api.buildReview(wrong,selection,'',policy),/SHA-256/);
 const forged=new Map([['otra/ruta|0:1|hash',{note:''}]]);
 await assert.rejects(()=>api.buildReview(model,forged,'',policy),/Selección ajena/);
 const incorrect={...model,messages:[{...message,
   blocks:[{...block,literal:'Texto cambiado'}]}]};
 await assert.rejects(()=>api.buildReview(incorrect,selection,'',policy),/Bloque ajeno|Un bloque cambió/);
 const fakeSimulation={...model,kind:'calculated_preview',sent_to_llm:false};
 const preview=await api.buildReview(fakeSimulation,selection,'',policy);
 assert.equal(preview.source.sent_to_llm,false);
 assert.equal(preview.source.kind,'calculated_preview');
 await assert.rejects(()=>api.buildReview({...model,kind:'calculated_preview'},
   selection,'',policy),/previsualización/);
 const systemBlock={...block,json_pointer:null};
 const system={...message,path:'/systemInstruction/parts/0/text',role:'system',
   blocks:[systemBlock]};
 const systemBody=JSON.stringify({systemInstruction:{parts:[{text:txt}]}});
 const extra={...model,messages:[system],body_utf8:systemBody,
   body_sha256:hash(systemBody),body_bytes:Buffer.byteLength(systemBody,'utf8')};
 const marked=new Map([[api.key(system.path,systemBlock),{note:'Revisar instrucciones'}]]);
 const uncertain=await api.buildReview(extra,marked,'',policy);
 assert.equal(uncertain.proposals[0].existing_profile_optional_field,false);
 assert.equal(uncertain.proposals[0].requires_manual_review,true);
 console.log(JSON.stringify({passed:true,sha:review.original.body_sha256,
   proposal_count:review.proposals.length,scenario:preview.source.kind}));
})().catch(e=>{console.error(e.stack);process.exit(1)});
"""
        out=subprocess.run([node,"-e",script,str(ASSET)],capture_output=True,
                           text=True,timeout=30)
        self.assertEqual(out.returncode,0,out.stdout+"\n"+out.stderr)
        self.assertTrue(json.loads(out.stdout)["passed"])

    def test_selected_text_cannot_exceed_limit_or_be_nonexistent(self):
        node=shutil.which("node")
        if not node:self.skipTest("Node no disponible")
        js=r"""
const assert=require('node:assert/strict');
const a=require(process.argv[1]);
const crypto=require('node:crypto');
globalThis.crypto=crypto.webcrypto;
const text='a',h=crypto.createHash('sha256').update(text).digest('hex');
const m={path:'/messages/0/content',role:'user',text,
 text_sha256:h,segments:[{kind:'text',start:0,end:1,literal:text,
 literal_sha256:h}],blocks:[{kind:'text',start:0,end:1,literal:text,literal_sha256:h}]};
const body=JSON.stringify({messages:[{role:'user',content:text}]});
const bodyHash=crypto.createHash('sha256').update(body).digest('hex');
const src={kind:'captured_http',sent_to_llm:true,body_utf8:body,body_sha256:bodyHash,
 body_bytes:Buffer.byteLength(body),messages:[m]};
const id=a.key(m.path,m.blocks[0]);
(async()=>{
  await assert.rejects(()=>a.buildReview(src,new Map([[id,{note:'x'.repeat(1601)}]]),'',{}),/observación/);
  await assert.rejects(()=>a.buildReview(src,new Map(),'x'.repeat(5001),{}),/observación/);
  console.log('ok');
})().catch(e=>{console.error(e.stack);process.exit(1)});
"""
        p=subprocess.run([node,"-e",js,str(ASSET)],capture_output=True,text=True,timeout=20)
        self.assertEqual(p.returncode,0,p.stderr)

    def test_profile_preview_preserves_literal_bytes_for_export(self):
        for provider in ("gemini","groq"):
            with self.subTest(provider=provider):
                p=_request(baseline(),scenario_context("pausa"),provider)
                self.assertIs(p["enviado_a_llm"],False)
                self.assertEqual(p["solicitud_serializada"],
                                 json.dumps(p["solicitud_json"],ensure_ascii=False))
                self.assertIsInstance(p["mensaje_literal_por_rol"],list)
                self.assertGreater(len(p["mensaje_literal_por_rol"]),0)

    def test_viewer_profile_scenario_have_checks_and_safe_local_export(self):
        script=ASSET.read_text(encoding="utf-8")
        self.assertIn('nilo.lab.context_review.v1',script)
        self.assertIn('Proponer excluir',script)
        self.assertIn('global.URL.createObjectURL',script)
        self.assertIn('propose_exclusion_only',script)
        self.assertIn('getBlocks(source)',script)
        self.assertIn('no_motor_or_world_changes:true',script)
        self.assertNotIn('/api/lab/profile/apply',script)
        for path in ("laboratorio_visor_llm.html",
                     "laboratorio_escenarios.html",
                     "laboratorio_ajustes.html"):
            with self.subTest(path=path):
                html=(ROOT/path).read_text(encoding="utf-8")
                self.assertIn('/assets/laboratorio_ui.js',html)
                self.assertIn('/assets/laboratorio.css',html)
                self.assertNotIn('/assets/laboratorio_revision.',html)
                self.assertIn('NiloReview.controller(',html)
                self.assertIn('.addHeader(',html)
                self.assertIn('.addBlock(',html)
                self.assertIn('.addGroup(',html)

    def test_review_assets_and_policy_served_locally_without_arbitrary_paths(self):
        with tempfile.TemporaryDirectory(prefix="nilo-review06-") as folder:
            root=Path(folder)
            source=HistorySource()
            hub=LabHub(root,root/"nilo.sqlite3")
            server=create_lab_server(0,history=source,hub=hub)
            worker=threading.Thread(target=server.serve_forever,daemon=True)
            worker.start()
            def get(path):
                c=http.client.HTTPConnection("127.0.0.1",server.server_address[1],timeout=8)
                try:
                    c.request("GET",path);r=c.getresponse();return r.status,r.read()
                finally:c.close()
            try:
                status,body=get('/api/lab/audit/info')
                self.assertEqual(status,200)
                info=json.loads(body)
                self.assertEqual(info["schema"],"nilo.lab.context_review.v1")
                self.assertTrue(info["engine_version"])
                self.assertIsNone(info["commit"]) # no inventar commit
                self.assertFalse(info["writes_to_world"])
                self.assertIn("antecedentes_relacionados",info["optional_context"])
                self.assertEqual(get('/api/lab/audit/info?file=/etc/passwd')[0],400)
                for path in ('/assets/laboratorio_ui.js',
                             '/assets/laboratorio.css'):
                    self.assertEqual(get(path)[0],200)
                self.assertNotEqual(get('/assets/laboratorio_revision.js')[0],200)
                self.assertNotEqual(get('/assets/../../etc/passwd')[0],200)
            finally:
                server.shutdown();server.server_close()
                source.temp_directory.cleanup()
                server.RequestHandlerClass.lab.close()

    def test_frontend_js_syntax(self):
        node=shutil.which("node")
        if not node:self.skipTest("Node no disponible")
        with tempfile.TemporaryDirectory() as folder:
            paths=[ASSET]+[ROOT/p for p in (
                "laboratorio_visor_llm.html",
                "laboratorio_escenarios.html",
                "laboratorio_ajustes.html")]
            for p in paths:
                with self.subTest(name=p.name):
                    if p.suffix==".js":code=p.read_text("utf-8")
                    else:code=p.read_text("utf-8").split("<script>",1)[1].split("</script>",1)[0]
                    script=Path(folder)/(p.stem+".js")
                    script.write_text(code,"utf-8")
                    out=subprocess.run([node,"--check",str(script)],capture_output=True,
                                       text=True,timeout=15)
                    self.assertEqual(out.returncode,0,out.stderr)


if __name__=="__main__":
    unittest.main()
