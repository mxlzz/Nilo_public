"""Etapa 02: texto original del LLM, fases y enlaces exactos de episodios.

No usa proveedor remoto ni escribe en la partida fuera de tests temporales.
"""
from __future__ import annotations

from contextlib import closing
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from brain import normalize_decision
from nilo import Simulation
from nilo_runtime.agent import gateway
from nilo_runtime.agent.trace_context import (
    capture_call, choose_candidate, transport_started, transport_finished,
    response_text_received, response_phase, candidate_finished,
)
from nilo_runtime.labs.episode_links import inspect_episode
from nilo_runtime.labs.llm_read import LocalLLMReadAPI, ReadError
from nilo_runtime.storage.llm_requests import RequestTraceStore, MAX_RESPONSE_BYTES
from nilo_runtime.storage.timeline import TimelineStore


CALL = "a" * 32
SECOND = "b" * 32


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="nilo-stage02-")
        self.addCleanup(self.temp.cleanup)
        self.world = Path(self.temp.name) / "world.sqlite3"
        self.store = RequestTraceStore.for_world(self.world)

    def _captured(self, text=' \n{"cuaderno":"á"} \t', phase="normalized"):
        with capture_call(self.store, purpose="deliberacion") as call:
            choose_candidate("gemini", "synthetic")
            transport_started(b'{"request":"NO-SECRET"}', "gemini")
            transport_finished("response_received")
            response_text_received(text)
            response_phase("json_parsed")
            if phase != "json_parsed":
                response_phase(phase)
            candidate_finished(phase=="normalized")
        row = self.store.recent()[0]
        return row["attempt_id"],call.call_id

    def test_original_text_bytes_sha_and_normalization_phase(self):
        txt = ' \n{"cuaderno":"á", "plan":[]} \t'
        ident,call = self._captured(txt)
        result = self.store.response_for(ident)
        self.assertEqual(result["text"],txt)
        self.assertEqual(result["body_sha256"],hashlib.sha256(txt.encode("utf-8")).hexdigest())
        self.assertEqual(result["body_bytes"],len(txt.encode("utf-8")))
        self.assertEqual(result["parse_phase"],"normalized")
        self.assertEqual(self.store.recent()[0]["status"],"accepted")
        with closing(sqlite3.connect(self.store.path)) as db:
            record=db.execute("SELECT body FROM llm_response_traces WHERE attempt_id=?",(ident,)).fetchone()[0]
            self.assertEqual(record,txt.encode("utf-8"))

    def test_invalid_contract_keeps_literal_and_rejection(self):
        ident,_=self._captured('{"plan":[]}',"invalid_contract")
        self.assertEqual(self.store.response_for(ident)["parse_phase"],"invalid_contract")
        self.assertEqual(self.store.recent()[0]["status"],"rejected")
        self.assertEqual(self.store.response_for(ident)["text"],'{"plan":[]}')

    def test_too_large_does_not_truncate_or_forge_original(self):
        txt = "a" * (MAX_RESPONSE_BYTES+1)
        ident,_=self._captured(txt)
        r=self.store.response_for(ident)
        self.assertEqual(r["capture_status"],"too_large")
        self.assertIsNone(r["text"])
        self.assertEqual(r["body_bytes"],len(txt))
        self.assertEqual(r["body_sha256"],hashlib.sha256(txt.encode()).hexdigest())

    def test_corrupted_response_is_rejected(self):
        ident,_=self._captured('{"plan":[]}')
        with closing(sqlite3.connect(self.store.path)) as db:
            db.execute("UPDATE llm_response_traces SET body=? WHERE attempt_id=?",(b"alterado",ident))
            db.commit()
        with self.assertRaisesRegex(ValueError,"integridad"):
            self.store.response_for(ident)

    def test_fallback_attempts_and_invalid_json_are_separate(self):
        with capture_call(self.store, purpose="deliberacion") as trace:
            choose_candidate("gemini","model-a")
            transport_started(b'{"provider":"a"}',"gemini")
            transport_finished("response_received")
            response_text_received("malformed {")
            response_phase("invalid_json")
            candidate_finished(False)
            choose_candidate("groq","model-b")
            transport_started(b'{"provider":"b"}',"groq")
            transport_finished("response_received")
            response_text_received("  {\"plan\":[]} ")
            response_phase("json_parsed")
            response_phase("normalized")
            candidate_finished(True)
        rows=sorted(self.store.recent(),key=lambda row:row["attempt_ordinal"])
        self.assertEqual([r["call_id"] for r in rows],[trace.call_id]*2)
        self.assertEqual([r["status"] for r in rows],["rejected","accepted"])
        self.assertEqual([self.store.response_for(r["attempt_id"])["parse_phase"] for r in rows],
                         ["invalid_json","normalized"])
        self.assertEqual([self.store.response_for(r["attempt_id"])["text"] for r in rows],
                         ["malformed {",'  {"plan":[]} '])

    def test_legacy_store_read_and_pruning_response_cleanup(self):
        self.assertIsNone(self.store.response_for(CALL))
        ident,_=self._captured("texto")
        self.assertIsNotNone(self.store.response_for(ident))
        # Límite FIFO artificial, asegura limpieza de tablas satélite.
        with patch("nilo_runtime.storage.llm_requests.MAX_RECORDS",1):
            self._captured("nueva respuesta")
        with closing(sqlite3.connect(self.store.path)) as db:
            count=db.execute("SELECT COUNT(*) FROM llm_response_traces").fetchone()[0]
        self.assertEqual(count,1)
        self.assertIsNone(self.store.response_for(ident))


class EpisodeLinkTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="nilo-episode-")
        self.addCleanup(self.temp.cleanup)
        self.world=Path(self.temp.name)/"world.sqlite3"

    def test_real_simulation_links_decision_and_direct_action_without_state_leak(self):
        sim=Simulation(db_path=self.world,world_seed=7321,rng_seed=9821)
        sim.think=lambda:None
        sim.s["paused"]=False
        sim.s["mode"]="demo"
        decision=normalize_decision({
            "cuaderno":"Voy a observar una acción",
            "accion_proyecto":"sin_proyecto",
            "plan":[{"op":"wait","minutes":30}],
            "revisar_en_minutos":90,
        })
        sim.archive.add("llm_decision",{
            "id":"llm-stage02","trace_call_id":CALL,
            "decision":decision,"clock_minutes":0,
        })
        sim.plan_ready(decision,"llm",{},lab_trace_call_id=CALL)
        for _ in range(5):
            sim.tick(3.0)
            if sim.s["person"].get("pending"):
                break
        sim.write()
        sim.conn.close()
        before=self.world.read_bytes()
        links=inspect_episode(self.world,CALL)
        self.assertEqual(before,self.world.read_bytes())
        self.assertTrue(links["world_available"])
        self.assertEqual(len(links["archived_decisions"]),1)
        self.assertEqual(len(links["decision_checkpoints"]),1)
        self.assertEqual(len(links["planned_actions"]),1)
        self.assertEqual(links["planned_actions"][0]["operation"],"wait")
        self.assertEqual(links["planned_actions"][0]["matched_by"],"journal_id")
        with closing(sqlite3.connect(self.world)) as db:
            row=db.execute("SELECT blob FROM timeline_checkpoints WHERE kind='decision'").fetchone()[0]
            import zlib
            self.assertNotIn(CALL,zlib.decompress(row).decode("utf-8"))
            manual=dict(simulated=False)
            # El vínculo técnico no se incorpora a persona, mundo ni plan.
            self.assertNotIn("trace_call_id",sim.s["person"])
            self.assertNotIn("trace_call_id",sim.s["world"])

    def test_automatic_action_is_never_linked_by_stale_journal_id(self):
        sim=Simulation(db_path=self.world,world_seed=7321,rng_seed=9821)
        sim.s["paused"]=False
        decision=normalize_decision({
            "cuaderno":"Voy a observar una acción",
            "accion_proyecto":"sin_proyecto",
            "plan":[{"op":"wait","minutes":30}],
        })
        sim.plan_ready(decision,"llm",{},lab_trace_call_id=CALL)
        journal_id=sim.s["person"]["plan"][0]["_journal_id"]
        sim.timeline.record("action",sim.s,sim.rng,action={
            "op":"wait","minutes":30,"_journal_id":journal_id,"_origin":"agenda",
        },source="agenda",engine_version=sim.timeline_version)
        sim.write()
        sim.conn.close()
        self.assertEqual(inspect_episode(self.world,CALL)["planned_actions"],[])

    def test_legacy_world_does_not_forge_missing_links(self):
        with closing(sqlite3.connect(self.world)) as db:
            db.execute("CREATE TABLE history (seq INTEGER PRIMARY KEY, category TEXT, simulated_at TEXT, payload TEXT)")
            db.execute("CREATE TABLE timeline_checkpoints (id INTEGER PRIMARY KEY,kind TEXT,history_seq INTEGER)")
            db.commit()
        original=self.world.read_bytes()
        item=inspect_episode(self.world,CALL)
        self.assertEqual(item["decision_checkpoints"],[])
        self.assertEqual(item["planned_actions"],[])
        self.assertIn("exact_decision_checkpoint_link_unavailable",item["limitations"])
        self.assertIn("archived_decision_not_found",item["limitations"])
        self.assertEqual(original,self.world.read_bytes())

    def test_timeline_additive_migration_accepts_old_schema(self):
        with closing(sqlite3.connect(self.world)) as db:
            db.execute("""CREATE TABLE timeline_checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT, clock_minutes REAL, day_label TEXT,engine_version TEXT,
                history_seq INTEGER,source TEXT,operation TEXT,decision_json TEXT,
                blob BLOB,blob_sha256 TEXT,created_real REAL)""")
            TimelineStore(db)
            fields={r[1] for r in db.execute("PRAGMA table_info(timeline_checkpoints)")}
            self.assertIn("trace_call_id",fields)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM lab_action_links").fetchone()[0],0)


class ReadAPIStage02Tests(unittest.TestCase):
    def test_explicit_detail_includes_model_text_and_absence_is_explicit(self):
        with tempfile.TemporaryDirectory(prefix="nilo-api02-") as root:
            world=Path(root)/"world.sqlite3"
            with closing(sqlite3.connect(world)) as db:
                db.execute("CREATE TABLE history(seq INTEGER PRIMARY KEY, category TEXT, simulated_at TEXT, payload TEXT)")
            store=RequestTraceStore.for_world(world)
            body=json.dumps({"systemInstruction":{"parts":[{"text":"SYS"}]},
                             "contents":[{"role":"user","parts":[{"text":"SITUACIÓN REAL: {}"}]}]}).encode("utf-8")
            ident=store.begin(body=body,call_id=CALL,session_id=None,purpose="deliberacion",
                              source_id=None,simulated_at=None,ordinal=1,provider="gemini",
                              model="synthetic")
            store.finish(ident,"response_received")
            store.record_response(ident,'  {"plan":[]} ')
            store.mark_response_phase(ident,"json_parsed")
            store.finish(ident,"accepted")
            item=LocalLLMReadAPI(world).get_attempt("id="+ident)
            self.assertEqual(item["response"]["text"],'  {"plan":[]} ')
            self.assertEqual(item["episode"]["archived_decisions"],[])
            self.assertIn("archived_decision_not_found",item["episode"]["limitations"])
            with closing(sqlite3.connect(store.path)) as db:
                db.execute("UPDATE llm_response_traces SET body=? WHERE attempt_id=?",
                           (b"wrong",ident))
                db.commit()
            with self.assertRaises(ReadError) as exc:
                LocalLLMReadAPI(world).get_attempt("id="+ident)
            self.assertEqual(exc.exception.status,409)


if __name__=="__main__":
    unittest.main()
