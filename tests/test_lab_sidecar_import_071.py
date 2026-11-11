"""Importación temporal de sidecar LLM: pareamiento exacto y sin tocar originales."""
from __future__ import annotations

import hashlib
import http.client
import json
import pathlib
import sqlite3
import tempfile
import threading
import unittest

from laboratorio_motor import HistorySource, create_lab_server
from nilo_runtime.labs.hub import LabHub
from nilo_runtime.storage.llm_requests import RequestTraceStore

CALL = "a" * 32
UNRELATED = "b" * 32


def make_world(path, call_id=CALL):
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE history(seq INTEGER PRIMARY KEY, category TEXT, simulated_at TEXT,payload TEXT)")
        db.execute("INSERT INTO history VALUES(1,'llm_decision','Día 1',?)",(
            json.dumps({"id":"decision-1", "trace_call_id":call_id,
                        "decision":{"cuaderno":"Prueba","plan":[]}}),))
        db.commit()


def make_sidecar(world, call_id):
    store=RequestTraceStore.for_world(world)
    payload=json.dumps({
        "systemInstruction":{"parts":[{"text":"INSTRUCCIONES"}]},
        "contents":[{"role":"user","parts":[{"text":"CONTEXTO"}]}],
    }).encode("utf-8")
    attempt=store.begin(
        body=payload,call_id=call_id,session_id=1,purpose="deliberacion",
        source_id=None,simulated_at="Día 1",ordinal=1,
        provider="gemini",model="modelo-falso",
    )
    store.finish(attempt,"accepted")
    return store.path,attempt


class ImportedSidecarTests(unittest.TestCase):
    def test_import_pair_proves_ids_and_keeps_original_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root=pathlib.Path(folder)
            original=root/"nilo_mundo.sqlite3"
            make_world(original)
            sidecar,attempt=make_sidecar(original,CALL)
            source=HistorySource()
            before_world=original.read_bytes()
            before_trace=sidecar.read_bytes()
            source.load_bytes(before_world,name=original.name)
            imported=source.require()
            self.assertNotEqual(imported,original)
            self.assertFalse(RequestTraceStore.for_world(imported).path.exists())
            with self.assertRaisesRegex(ValueError,"SQLite válida"):
                source.import_sidecar_bytes(b"no es una sqlite")
            with tempfile.TemporaryDirectory() as other:
                foreign=pathlib.Path(other)/"other.sqlite3"
                make_world(foreign,UNRELATED)
                foreign_sidecar,_=make_sidecar(foreign,UNRELATED)
                with self.assertRaisesRegex(ValueError,"no comparten ningún ID"):
                    source.import_sidecar_bytes(foreign_sidecar.read_bytes())
            report=source.import_sidecar_bytes(before_trace)
            self.assertEqual(report["attempts"],1)
            self.assertEqual(report["matched_calls"],1)
            self.assertTrue(report["imported"])
            self.assertEqual(original.read_bytes(),before_world)
            self.assertEqual(sidecar.read_bytes(),before_trace)
            self.assertEqual(imported.read_bytes(),before_world)
            self.assertTrue(RequestTraceStore.for_world(imported).path.is_file())
            with self.assertRaisesRegex(ValueError,"ya tiene capturas"):
                source.import_sidecar_bytes(before_trace)
            source.temp_directory.cleanup()

    def test_original_world_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            root=pathlib.Path(folder)
            original=root/"nilo_mundo.sqlite3"
            make_world(original)
            sidecar,_=make_sidecar(original,CALL)
            source=HistorySource()
            source.path=original
            source.origin="carpeta"
            with self.assertRaisesRegex(ValueError,"Primero importá"):
                source.import_sidecar_bytes(sidecar.read_bytes())
            source.temp_directory.cleanup()

    def test_http_visors_and_episode_links_use_imported_pair(self):
        with tempfile.TemporaryDirectory() as folder:
            root=pathlib.Path(folder)
            original=root/"source.sqlite3"
            make_world(original)
            trace,attempt=make_sidecar(original,CALL)
            src=HistorySource()
            src.load_bytes(original.read_bytes(),name=original.name)
            hub=LabHub(root,original)
            server=create_lab_server(0,history=src,hub=hub)
            worker=threading.Thread(target=server.serve_forever,daemon=True)
            worker.start()
            def get(path):
                con=http.client.HTTPConnection("127.0.0.1",server.server_address[1],timeout=8)
                try:
                    con.request("GET",path)
                    response=con.getresponse()
                    return response.status,json.loads(response.read().decode("utf-8"))
                finally:
                    con.close()
            def upload(body):
                con=http.client.HTTPConnection("127.0.0.1",server.server_address[1],timeout=8)
                try:
                    con.request("POST","/api/history/upload-sidecar",body=body,
                                headers={"Content-Type":"application/octet-stream"})
                    response=con.getresponse()
                    return response.status,json.loads(response.read().decode("utf-8"))
                finally:
                    con.close()
            try:
                self.assertEqual(get("/api/lab/llm/attempts")[1]["attempts"],[])
                status,result=upload(trace.read_bytes())
                self.assertEqual(status,200,result)
                self.assertEqual(result["matched_calls"],1)
                status,list_result=get("/api/lab/llm/attempts")
                self.assertEqual(status,200)
                self.assertEqual(list_result["attempts"][0]["attempt_id"],attempt)
                status,detail=get("/api/lab/llm/attempt?id="+attempt)
                self.assertEqual(status,200)
                self.assertIn("CONTEXTO",detail["body_utf8"])
                status,episode=get("/api/history/episode?id=hist%3A1")
                self.assertEqual(status,200,episode)
                self.assertTrue(episode["open_in_llm_viewer"])
            finally:
                server.shutdown();server.server_close()
                src.temp_directory.cleanup()


if __name__ == "__main__":
    unittest.main()
