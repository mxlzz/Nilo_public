"""Etapa 08: matriz por deliberación, huellas físicas y linaje textual exacto.

Pruebas con SQLite temporal y capturas sintéticas. Sin proveedores reales,
sin mutación de la partida y sin inferir causalidad de IDs/fechas cercanas.
"""
from __future__ import annotations

from contextlib import closing
import hashlib
import http.client
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile
import threading
import unittest

from laboratorio_motor import create_lab_server
from nilo_runtime.labs.cross_analysis import (
    analyze, _explicit_identifiers, _is_empty_json_literal, _signature,
)
from nilo_runtime.labs.hub import LabHub
from nilo_runtime.storage.llm_requests import RequestTraceStore

ROOT=Path(__file__).resolve().parents[1]
CALL_A="a"*32
CALL_B="b"*32
CALL_C="c"*32


class CrossAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="nilo-stage08-")
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.world=self.root/"world.sqlite3"
        with closing(sqlite3.connect(self.world)) as db:
            db.execute("""CREATE TABLE history (
                seq INTEGER PRIMARY KEY,category TEXT,
                simulated_at TEXT,payload TEXT)""")
            records=[
                (1,"experience",{"id":"exp-01","measurement_id":"med-01"}),
                (2,"experience",{"id":"exp-OTHER","measurement_id":"med-OTHER"}),
                (3,"diagnostic",{"id":"diag-1","op":"gather","target":"madera","success":False}),
                (4,"diagnostic",{"id":"diag-2","op":"gather","target":"madera","success":False}),
                (5,"diagnostic",{"id":"diag-3","op":"rest","success":True}),
                (6,"diagnostic",{"id":"diag-4","op":"gather","target":"madera","success":False}),
                (7,"diagnostic",{"id":"diag-5","op":"gather","target":"piedra","success":False}),
                (8,"diagnostic",{"id":"diag-6","op":"gather","target":"madera","success":True}),
            ]
            for seq,cat,record in records:
                db.execute("INSERT INTO history VALUES(?,?,?,?)",
                           (seq,cat,"Día 1",json.dumps(record)))
            db.commit()
        self.store=RequestTraceStore.for_world(self.world)

    def _attempt(self,call,values,status="accepted",ordinal=1):
        raw=json.dumps(values,ensure_ascii=False)
        wire=json.dumps({"model":"synthetic","messages":[
            {"role":"system","content":"Reglas fijas"},
            {"role":"user","content":raw}]},ensure_ascii=False).encode()
        attempt=self.store.begin(body=wire,call_id=call,session_id=1,
            purpose="deliberacion",source_id=None,
            simulated_at="Día 1",ordinal=ordinal,provider="groq",
            model="synthetic")
        self.store.finish(attempt,status)
        return attempt

    def _seed_requests(self):
        failed=self._attempt(CALL_A,{"necesidades":"ANTERIOR"},status="rejected")
        accepted=self._attempt(CALL_A,{
            "necesidades":{"fatiga":"bien"},
            "memorias_relevantes":[{"id":"exp-01","texto":"Experiencia medida"}],
            "objetos":[]},ordinal=2)
        second=self._attempt(CALL_B,{
            "necesidades":{"fatiga":"bien"},
            "memorias_relevantes":[{"id":"exp-OTHER-extras","texto":"sin igualdad"}],
            "objeto_vacio":None})
        third=self._attempt(CALL_C,{
            "necesidades":{"fatiga":"agotado"},
            "memorias_relevantes":[{"id":"exp-01","texto":"Recuerdo presente"}],
            "objetos":[]})
        return failed,accepted,second,third

    def test_matrix_retries_and_exact_field_presence(self):
        fail,a,b,c=self._seed_requests()
        world_before=self.world.read_bytes()
        sidecar_before=self.store.path.read_bytes()
        result=analyze(self.world,limit=3)
        self.assertEqual(self.world.read_bytes(),world_before)
        self.assertEqual(self.store.path.read_bytes(),sidecar_before)
        self.assertTrue(result["no_world_writes"])
        self.assertTrue(result["no_llm_calls"])
        self.assertEqual(result["window"]["visible_calls"],3)
        self.assertEqual([t["call_id"] for t in result["turns"]],
                         [CALL_A,CALL_B,CALL_C])
        self.assertEqual(result["turns"][0]["attempt_id"],a)
        self.assertEqual(result["turns"][0]["retry_count"],2)
        fields={x["field"]:x for x in result["matrix"]}
        self.assertIn("user:/necesidades",fields)
        self.assertIn("user:/memorias_relevantes",fields)
        self.assertTrue(fields["user:/necesidades"]["all_present"])
        self.assertFalse(fields["user:/necesidades"]["identical_when_present"])
        self.assertTrue(fields["system:@texto:/messages/0/content"]["identical_when_present"])
        self.assertEqual(fields["user:/objeto_vacio"]["empty_count"],1)
        self.assertIsNone(fields["user:/objeto_vacio"]["cells"][0])
        self.assertGreater(fields["user:/necesidades"]["total_bytes"],0)
        self.assertEqual(result["invalid_attempts"],[])

    def test_gemini_real_shaped_prompt_indexes_memory_after_operations_guide(self):
        # La solicitud real de Gemini antepone texto de operaciones y termina
        # con "SITUACIÓN REAL: {...}". No asumir JSON desde el primer carácter.
        context={"momento":"Día 1", "necesidades":{"fatiga":"bien"},
                 "memorias_relevantes":[{"id":"exp-01","evidence":"med-01"}],
                 "resultados_de_acciones":[]}
        prompt="Operaciones disponibles: explore, wait, gather.\\nSITUACIÓN REAL: "+json.dumps(
            context,ensure_ascii=False)
        raw=json.dumps({"model":"synthetic",
            "systemInstruction":{"parts":[{"text":"Instrucciones."}]},
            "contents":[{"role":"user","parts":[{"text":prompt}]}]},
            ensure_ascii=False).encode("utf-8")
        attempt=self.store.begin(body=raw,call_id=CALL_A,session_id=1,
            purpose="deliberacion",source_id=None,simulated_at="Día 1",
            ordinal=1,provider="gemini",model="synthetic")
        self.store.finish(attempt,"accepted")
        result=analyze(self.world)
        fields={x["field"] for x in result["matrix"]}
        self.assertIn("user:/memorias_relevantes",fields)
        self.assertIn("user:/necesidades",fields)
        self.assertEqual(result["memory"]["with_explicit_request_id"],1)
        self.assertEqual(result["memory"]["experiences"][0]["in_requests"][0]["attempt_id"],attempt)

    def test_operation_footprints_are_diagnostics_not_all_actions(self):
        self._seed_requests()
        data=analyze(self.world,limit=3)
        patterns=data["operations"]["patterns"]
        gather=next(p for p in patterns if p["op"]=="gather"
                    and p["target"]=="madera" and p["result"]=="fallo")
        self.assertEqual(gather["count"],3)
        self.assertEqual(gather["max_adjacent"],2)
        self.assertEqual(gather["sample_seq"],[3,4,6])
        self.assertEqual(data["operations"]["diagnostics_with_fingerprint"],6)
        self.assertEqual(data["operations"]["adjacent_scope"],
                         "consecutive_diagnostic_records_not_all_actions")

    def test_explicit_memory_id_not_textual_substring_or_mere_occurrence(self):
        self._seed_requests()
        data=analyze(self.world,limit=3)
        mem=data["memory"]
        self.assertEqual(mem["experience_count_in_window"],2)
        self.assertEqual(mem["with_explicit_request_id"],1)
        self.assertEqual([e["id"] for e in mem["experiences"]],["exp-01"])
        self.assertEqual([e["call_id"] for e in mem["experiences"][0]["in_requests"]],
                         [CALL_A,CALL_C])
        self.assertIn("not_proof_of_use",mem["experiences"][0]["in_requests"][0]["relation"])
        self.assertEqual(_explicit_identifiers({"texto":"ref exp-01; exp-OTHER"}),
                         set())
        self.assertEqual(_explicit_identifiers({"id":"exp-01"}),{"exp-01"})

    def test_corrupt_capture_fails_closed_without_erasing_other_turns(self):
        ids=self._seed_requests()
        with closing(sqlite3.connect(self.store.path)) as db:
            db.execute("UPDATE llm_requests SET body=? WHERE attempt_id=?",
                       (b"CORRUPTO",ids[2]))
            db.commit()
        result=analyze(self.world,limit=3)
        self.assertEqual(len(result["invalid_attempts"]),1)
        self.assertFalse(result["turns"][1]["indexed"])
        self.assertEqual(result["turns"][1]["field_count"] if
                         "field_count" in result["turns"][1] else None,None)
        self.assertEqual(result["memory"]["with_explicit_request_id"],1)
        self.assertTrue(any("corruptas" in l for l in result["limitations"]))

    def test_legacy_and_missing_sidecar_have_honest_absences(self):
        result=analyze(self.world,limit=3)
        self.assertEqual(result["turns"],[])
        self.assertEqual(result["matrix"],[])
        self.assertEqual(result["window"]["total_archived_calls"],0)
        self.assertTrue(result["operations"]["patterns"])
        self.assertTrue(any("No hay solicitudes" in x for x in result["limitations"]))
        another=self.root/"legacy.sqlite3"
        with closing(sqlite3.connect(another)) as db:
            db.execute("CREATE TABLE dummy(x TEXT)")
        old=analyze(another)
        self.assertEqual(old["operations"]["patterns"],[])
        self.assertTrue(any("anterior" in s for s in old["limitations"]))

    def test_no_fabricated_empty_when_unknown_format(self):
        self.assertIs(_is_empty_json_literal('"a": null'),True)
        self.assertIs(_is_empty_json_literal('"a": "x"'),False)
        self.assertIsNone(_is_empty_json_literal("a: None"))
        self.assertIsNone(_signature({"success":False,"target":"a"}))
        self.assertEqual(_signature({"op":"wait","success":False}),
                         ("wait",None,"fallo"))
        with self.assertRaises(ValueError): analyze(self.world,limit=0)
        with self.assertRaises(ValueError): analyze(self.world,limit=49)
        with self.assertRaises(ValueError): analyze(self.world,limit=True)

    def test_read_only_api_and_safe_local_html(self):
        self._seed_requests()
        hub=LabHub(self.root,self.world)
        server=create_lab_server(0,hub=hub)
        worker=threading.Thread(target=server.serve_forever,daemon=True)
        worker.start()
        def get(path):
            c=http.client.HTTPConnection("127.0.0.1",server.server_address[1],timeout=8)
            try:
                c.request("GET",path)
                r=c.getresponse()
                return r.status,r.read()
            finally:c.close()
        first=self.world.read_bytes()
        other=self.store.path.read_bytes()
        try:
            status,body=get("/api/lab/analysis?limit=12")
            self.assertEqual(status,200)
            data=json.loads(body)
            self.assertEqual(data["schema"],"nilo.lab.cross_analysis.v1")
            self.assertEqual(data["window"]["visible_calls"],3)
            status,html=get("/analisis")
            self.assertEqual(status,200)
            self.assertIn(b'id="matrixWrap"',html)
            self.assertIn(b'href="/analisis" aria-current="page"',html)
            for bad in (
                "/api/lab/analysis?file=secreto.sqlite3",
                "/api/lab/analysis?limit=12&limit=3",
                "/api/lab/analysis?limit=-1",
                "/api/lab/analysis?limit=1000",
                "/api/lab/analysis?limit=NaN",
            ):
                with self.subTest(path=bad):
                    self.assertEqual(get(bad)[0],400)
            self.assertEqual(first,self.world.read_bytes())
            self.assertEqual(other,self.store.path.read_bytes())
        finally:
            server.shutdown();server.server_close()
            server.RequestHandlerClass.lab.close()

    def test_navigation_and_syntax_and_manifest(self):
        manifest=json.loads((ROOT/"MANIFIESTO_SHA256.json").read_text("utf-8"))
        self.assertIn("laboratorio_analisis.html",manifest["files"])
        for name in ("laboratorio_motor.html","laboratorio_experimentos.html",
                     "laboratorio_escenarios.html","laboratorio_ajustes.html",
                     "laboratorio_historico.html","laboratorio_visor_llm.html"):
            html=(ROOT/name).read_text("utf-8")
            self.assertIn('href="/analisis"',html)
        html=(ROOT/"laboratorio_analisis.html").read_text("utf-8")
        self.assertIn('id="lab-theme-toggle"',html)
        self.assertIn('href="/assets/laboratorio.css"',html)
        self.assertIn('src="/assets/laboratorio_ui.js"',html)
        self.assertNotIn("innerHTML",html)
        self.assertIn("Una decisión inesperada",html)
        self.assertIn("Una acción infructuosa",html)
        self.assertIn("Un contexto demasiado extenso",html)
        node=shutil.which("node")
        if node:
            with tempfile.TemporaryDirectory() as folder:
                code=html.split("<script>",1)[1].split("</script>",1)[0]
                js=Path(folder)/"analisis.js";js.write_text(code,"utf-8")
                test=subprocess.run([node,"--check",str(js)],
                                    capture_output=True,text=True,timeout=15)
                self.assertEqual(test.returncode,0,test.stderr)


if __name__=="__main__":unittest.main()
