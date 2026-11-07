"""Etapa 03: recorrido/ficha de episodios y conservación de la reproducción.

Pruebas sintéticas; ninguna consulta a Gemini, Groq ni a internet.
"""
from __future__ import annotations

from contextlib import closing
import hashlib
import json
import pathlib
import shutil
import sqlite3
import subprocess
import tempfile
import threading
import unittest
import http.client

from nilo_runtime.labs.episode_view import list_episodes, get_episode
from nilo_runtime.storage.llm_requests import RequestTraceStore
from laboratorio_motor import (
    create_lab_server, HistorySource, HISTORY_HTML_FILE, LLM_VIEWER_HTML_FILE,
)
from nilo_runtime.labs.hub import LabHub

CALL = "a" * 32
LEGACY = "b" * 32
ORPHAN = "c" * 32


def fake_world(path: pathlib.Path):
    with closing(sqlite3.connect(path)) as db:
        db.execute("""CREATE TABLE history (
            seq INTEGER PRIMARY KEY, category TEXT,
            simulated_at TEXT, payload TEXT)""")
        db.execute("""CREATE TABLE timeline_checkpoints (
            id INTEGER PRIMARY KEY, kind TEXT,clock_minutes REAL,
            day_label TEXT,engine_version TEXT,history_seq INTEGER,
            source TEXT,operation TEXT, decision_json TEXT,
            trace_call_id TEXT, blob BLOB, blob_sha256 TEXT,
            created_real REAL)""")
        db.execute("""CREATE TABLE lab_action_links (
            action_checkpoint_id INTEGER PRIMARY KEY,
            journal_id TEXT,trace_call_id TEXT)""")
        db.execute("""CREATE TABLE lab_journal_trace (
            journal_id TEXT PRIMARY KEY,
            trace_call_id TEXT,decision_checkpoint_id INTEGER)""")
        def hist(seq,cat,payload):
            db.execute("INSERT INTO history VALUES(?,?,?,?)",
                       (seq,cat,"Día 1 · 08:00",json.dumps(payload,ensure_ascii=False)))
        hist(1,"llm_decision",{"id":"llm-legacy","trace_call_id":LEGACY,
                                  "decision":{"cuaderno":"Anterior","plan":[]}})
        hist(3,"diagnostic",{"op":"gather","success":False,"id":"old-diagnostic"})
        hist(11,"llm_decision",{"id":"llm-a","trace_call_id":CALL,
                                   "decision":{"cuaderno":"Observaré","plan":[{"op":"wait","minutes":30}]}})
        hist(12,"journal",{"id":"journal-a","text":"Registro privado del cuaderno"})
        hist(13,"measurement",{"id":"med-a","journal_id":"journal-a","op":"wait"})
        hist(14,"diagnostic",{"id":"out-a","op":"wait","success":True,
                                   "physical_result":{"measurement_id":"med-a"}})
        hist(15,"experience",{"id":"exp-a","measurement_id":"med-a","text":"Esperé"})
        for ident,kind,seq,source,op,trace,command in [
            (1,"decision",10,"llm",None,CALL,
             {"cuaderno":"Observaré","plan":[{"op":"wait","minutes":30}]}),
            (2,"action",11,"llm","wait",None,
             {"op":"wait","minutes":30,"_journal_id":"journal-a"}),
            (3,"action",18,"agenda","gather",None,
             {"op":"gather","target":"madera","_origin":"agenda"}),
        ]:
            body=b"synthetic-checkpoint-"+str(ident).encode()
            db.execute("""INSERT INTO timeline_checkpoints VALUES
                (?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                ident,kind,480+ident,"Día 1 · 08:00","0.7.0",seq,source,op,
                json.dumps(command),trace,body,hashlib.sha256(body).hexdigest(),0.0))
        db.execute("INSERT INTO lab_journal_trace VALUES(?,?,?)",("journal-a",CALL,1))
        db.execute("INSERT INTO lab_action_links VALUES(?,?,?)",(2,"journal-a",CALL))
        db.commit()
    store=RequestTraceStore.for_world(path)
    body=json.dumps({"systemInstruction":{"parts":[{"text":"INSTRUCCIONES"}]},
                      "contents":[{"role":"user","parts":[{"text":"SITUACIÓN REAL: {}"}]}]
                    },ensure_ascii=False).encode()
    def attempt(call,ordinal,status,text=None):
        ident=store.begin(
            body=body,call_id=call,session_id=1,purpose="deliberacion",
            source_id=None,simulated_at="Día 1 · 08:00",
            ordinal=ordinal,provider="gemini",model="synthetic")
        if text is not None:
            store.finish(ident,"response_received")
            store.record_response(ident,text)
            store.mark_response_phase(ident,"json_parsed")
            store.mark_response_phase(ident,"normalized")
        store.finish(ident,status)
        return ident
    id1=attempt(CALL,1,"accepted",'  {"cuaderno":"Observé"} \n')
    id2=attempt(ORPHAN,1,"transport_error")
    id3=attempt(ORPHAN,2,"accepted",'{"cuaderno":"Sin archivo"}')
    return store,(id1,id2,id3)


class EpisodeStage03Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="nilo-episode03-")
        self.addCleanup(self.temp.cleanup)
        self.root=pathlib.Path(self.temp.name)
        self.world=self.root/"nilo_mundo.sqlite3"
        self.store,self.attempts=fake_world(self.world)

    def test_catalog_has_decision_independent_action_old_and_orphan(self):
        original=self.world.read_bytes()
        result=list_episodes(self.world)
        self.assertEqual(original,self.world.read_bytes())
        ids={e["id"]:e for e in result["entries"]}
        self.assertIn("cp:1",ids)
        self.assertNotIn("cp:2",ids)  # Acción agrupada por vínculo exacto
        self.assertIn("cp:3",ids)   # Acción de agenda independiente
        self.assertIn("hist:1",ids) # Deliberación antigua sin checkpoint
        self.assertIn("call:"+ORPHAN,ids)  # HTTP sin decisión archivada
        self.assertEqual(ids["cp:3"]["episode_kind"],"independent")
        self.assertEqual(ids["call:"+ORPHAN]["timeline_position"],"not_verified")
        self.assertEqual(ids["call:"+ORPHAN]["attempt_count"],2)

    def test_episode_four_stages_exact_and_literal(self):
        result=get_episode(self.world,"cp:1",viewer_world=self.world)
        self.assertEqual(result["decision"]["cuaderno"],"Observaré")
        self.assertEqual(result["attempts"][0]["response"]["text"],
                         '  {"cuaderno":"Observé"} \n')
        self.assertEqual(len(result["linked"]["planned_actions"]),1)
        self.assertEqual(result["linked"]["planned_actions"][0]["operation"],"wait")
        self.assertEqual([x["record"]["id"] for x in
                          result["related"]["measurements"]],["med-a"])
        self.assertEqual([x["record"]["id"] for x in
                          result["related"]["diagnostics"]],["out-a"])
        self.assertEqual([x["record"]["id"] for x in
                          result["related"]["experiences"]],["exp-a"])
        self.assertTrue(result["open_in_llm_viewer"])
        self.assertIn("next_turn",result["fidelity"])

    def test_automatic_action_does_not_claim_llm_origin(self):
        result=get_episode(self.world,"cp:3",viewer_world=self.world)
        self.assertEqual(result["kind"],"action")
        self.assertIsNone(result["trace_call_id"])
        self.assertEqual(result["recorded_event"]["command"]["_origin"],"agenda")
        self.assertEqual(result["attempts"],[])
        self.assertIsNone(result["decision"])
        self.assertIn("El origen de la acción no está vinculado",result["limitations"][-1])

    def test_orphan_attempts_maintain_retry_and_no_fake_decision(self):
        result=get_episode(self.world,"call:"+ORPHAN,viewer_world=self.world)
        self.assertEqual(result["attempts"][0]["status"],"transport_error")
        self.assertEqual(result["attempts"][1]["status"],"accepted")
        self.assertEqual(result["attempts"][1]["response"]["text"],
                         '{"cuaderno":"Sin archivo"}')
        self.assertIsNone(result["decision"])
        self.assertIn("archived_decision_not_found",result["limitations"])

    def test_legacy_and_uploaded_world_do_not_forge_http_links(self):
        leg=get_episode(self.world,"hist:1",viewer_world=self.world)
        self.assertEqual(leg["decision"]["cuaderno"],"Anterior")
        self.assertEqual(leg["attempts"],[])
        uploaded=self.root/"copiada.sqlite3"
        shutil.copyfile(self.world,uploaded)
        result=get_episode(uploaded,"cp:1",viewer_world=self.world)
        self.assertFalse(result["open_in_llm_viewer"])
        self.assertEqual(result["attempts"],[])
        self.assertIn("El cuerpo HTTP original no está disponible",result["limitations"][-1])

    def test_legacy_world_missing_all_modern_tables(self):
        file=self.root/"legacy.sqlite3"
        with closing(sqlite3.connect(file)) as db:
            db.execute("CREATE TABLE history(seq INTEGER PRIMARY KEY, category TEXT, simulated_at TEXT,payload TEXT)")
            db.execute("INSERT INTO history VALUES(1,'diagnostic','Día 1',?)",
                       (json.dumps({"op":"use","success":False}),))
            db.commit()
        result=list_episodes(file)
        self.assertEqual(len(result["entries"]),1)
        self.assertEqual(result["entries"][0]["episode_kind"],"legacy")
        detail=get_episode(file,"hist:1")
        self.assertIsNone(detail["decision"])
        self.assertFalse(detail["open_in_llm_viewer"])

    def test_invalid_and_cross_partida_identifiers_fail(self):
        for bad in ("../file","call:"+ORPHAN+"/../../","cp:-1","hist:99/abc",
                    "call:invalid","id="+CALL):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                get_episode(self.world,bad)
        with self.assertRaises(ValueError):
            get_episode(self.world,"call:"+"d"*32)
        with self.assertRaises(ValueError):
            list_episodes(self.world,limit=100000)

    def test_corrupt_http_capture_fails_not_misreported(self):
        with closing(sqlite3.connect(self.store.path)) as db:
            db.execute("UPDATE llm_requests SET body=? WHERE attempt_id=?",
                       (b"tampered",self.attempts[0]))
            db.commit()
        with self.assertRaisesRegex(ValueError,"integridad"):
            get_episode(self.world,"cp:1")

    def test_unlinked_action_with_no_surviving_decision_stays_visible(self):
        with closing(sqlite3.connect(self.world)) as db:
            db.execute("INSERT INTO lab_action_links VALUES(?,?,?)",
                       (3,"journal-orphan","d"*32))
            db.commit()
        ids={e["id"] for e in list_episodes(self.world)["entries"]}
        self.assertIn("cp:3",ids)


class Stage03BrowserTests(unittest.TestCase):
    def test_markup_modes_safe_originals_and_javascript_syntax(self):
        html=HISTORY_HTML_FILE.read_text("utf-8")
        visor=LLM_VIEWER_HTML_FILE.read_text("utf-8")
        self.assertIn('id="episodesMode"',html)
        self.assertIn('id="momentsMode"',html)
        self.assertIn("/api/history/episode?id=",html)
        self.assertIn("renderEpisode(data)",html)
        self.assertIn("safe(response.text)",html)
        self.assertIn('href="/visor-llm?id=',html)
        self.assertIn("requestedAttempt",visor)
        node=shutil.which("node")
        if node:
            for name,markup in (("historical",html),("viewer",visor)):
                js=markup.split("<script>",1)[1].split("</script>",1)[0]
                with tempfile.TemporaryDirectory() as td:
                    file=pathlib.Path(td)/(name+".js")
                    file.write_text(js,encoding="utf-8")
                    completed=subprocess.run([node,"--check",str(file)],
                                           capture_output=True,text=True,timeout=12)
                    self.assertEqual(completed.returncode,0,completed.stderr)

    def test_http_endpoints_respect_selected_world_and_method(self):
        with tempfile.TemporaryDirectory(prefix="nilo-lab03-http-") as td:
            folder=pathlib.Path(td)
            world=folder/"partida.sqlite3"
            fake_world(world)
            source=HistorySource()
            source.path=world
            hub=LabHub(folder,world)
            server=create_lab_server(0,history=source,hub=hub)
            th=threading.Thread(target=server.serve_forever,daemon=True)
            th.start()
            port=server.server_address[1]
            def get(path):
                conn=http.client.HTTPConnection("127.0.0.1",port,timeout=6)
                try:
                    conn.request("GET",path)
                    reply=conn.getresponse()
                    return reply.status,json.loads(reply.read().decode("utf-8"))
                finally:
                    conn.close()
            try:
                status,items=get("/api/history/episodes")
                self.assertEqual(status,200)
                self.assertTrue(any(e["id"]=="cp:1" for e in items["entries"]))
                status,card=get("/api/history/episode?id=cp%3A1")
                self.assertEqual(status,200)
                self.assertEqual(card["linked"]["planned_actions"][0]["operation"],"wait")
                self.assertEqual(get("/api/history/episode?id=call%3A..")[0],400)
                self.assertEqual(get("/api/history/episode?id=cp%3A1&path=%2Fetc")[0],400)
                self.assertEqual(get("/api/history/episodes?file=%2Fetc")[0],400)
            finally:
                server.shutdown();server.server_close()
                source.temp_directory.cleanup()


if __name__=="__main__":
    unittest.main()
