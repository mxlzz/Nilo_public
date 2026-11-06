"""Etapa 02: cada intento conserva Request.data literal, con red simulada."""
from __future__ import annotations
from contextlib import closing
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from auditar_contexto_llm import PROVIDERS, scenario_context
from nilo import Simulation
from nilo_runtime.agent import gateway
from nilo_runtime.agent.trace_context import (
    capture_call, choose_candidate, candidate_finished,
)
from nilo_runtime.storage.llm_requests import RequestTraceStore
from providers import route


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, kind, value, trace):
        self.close()


def response(provider, content='{"cuaderno":"Respuesta válida"}'):
    if provider == "gemini":
        obj = {"candidates":[{"content":{"parts":[{"text":content}]}}],
               "usageMetadata":{"promptTokenCount":2,"candidatesTokenCount":3}}
    else:
        obj = {"choices":[{"message":{"content":content}}],
               "usage":{"prompt_tokens":2,"completion_tokens":3}}
    return FakeResponse(json.dumps(obj, ensure_ascii=False).encode("utf-8"))


class TraceCaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="nilo-llm-stage02-")
        self.addCleanup(self.temp.cleanup)
        self.world=Path(self.temp.name)/"original.sqlite3"
        self.store=RequestTraceStore.for_world(self.world)
        self.context=scenario_context("proyecto_refugio")

    def test_real_http_body_is_identical_and_headers_are_excluded(self):
        for provider in ("gemini","groq","openai_compatible"):
            with self.subTest(provider=provider):
                cfg=dict(PROVIDERS[provider])
                seen=[]
                def send(request, timeout=40):
                    seen.append((request.data, dict(request.header_items())))
                    return response(provider)
                with patch.object(gateway.urllib.request,"urlopen",side_effect=send):
                    with capture_call(self.store,purpose="deliberacion",
                                      session_id=12,simulated_at="Día 2 · 12:00") as call:
                        choose_candidate(provider,cfg["MODEL"])
                        decision,_=gateway.request_llm(cfg,self.context)
                        candidate_finished(True)
                self.assertEqual(decision["cuaderno"],"Respuesta válida")
                row=next(x for x in self.store.recent() if x["call_id"]==call.call_id)
                self.assertEqual(row["body"],seen[0][0])
                self.assertEqual(row["body_sha256"],hashlib.sha256(seen[0][0]).hexdigest())
                self.assertEqual(row["body_bytes"],len(seen[0][0]))
                self.assertEqual(row["status"],"accepted")
                self.assertEqual(row["model"],cfg["MODEL"])
                self.assertEqual(row["purpose"],"deliberacion")
                self.assertEqual(row["session_id"],12)
                self.assertEqual(row["simulated_at"],"Día 2 · 12:00")
                self.assertNotIn("headers",row)
                self.assertNotIn(cfg.get("GEMINI_API_KEY","not-a-key"),row["body"].decode("utf-8"))
                if provider=="gemini":
                    self.assertIn("X-goog-api-key",seen[0][1])
                else:
                    self.assertIn("Authorization",seen[0][1])

    def test_fallback_preserves_two_different_attempts_one_call(self):
        cfg=dict(PROVIDERS["gemini"],BACKUP_PROVIDER="groq",
                 GROQ_API_KEY="very-private-key",
                 GROQ_MODEL="openai/gpt-oss-20b",GEMINI_FALLBACK_MODELS="")
        seen=[]
        def send(request,timeout=40):
            seen.append(request.data)
            if "generativelanguage.googleapis.com" in request.full_url:
                raise HTTPError(request.full_url,429,"synthetic",{},io.BytesIO(b"{}"))
            return response("groq")
        with patch.object(gateway.urllib.request,"urlopen",side_effect=send):
            with capture_call(self.store,purpose="deliberacion",session_id=44) as call:
                (decision,tokens),provider,model=route(
                    cfg,{},threading.RLock(),
                    lambda current: gateway.request_llm(current,self.context),
                    sleep=lambda _:None)
        self.assertEqual(provider,"groq")
        self.assertEqual(decision["cuaderno"],"Respuesta válida")
        rows=sorted((r for r in self.store.recent() if r["call_id"]==call.call_id),
                    key=lambda r:r["attempt_ordinal"])
        self.assertEqual(len(rows),2)
        self.assertEqual([r["provider"] for r in rows],["gemini","groq"])
        self.assertEqual([r["status"] for r in rows],["http_error","accepted"])
        self.assertEqual(rows[0]["error_http_code"],429)
        self.assertEqual([r["body"] for r in rows],seen)
        self.assertNotEqual(rows[0]["body_sha256"],rows[1]["body_sha256"])
        self.assertNotIn(b"very-private-key",rows[1]["body"])

    def test_retry_creates_two_attempts_even_on_same_model(self):
        cfg=dict(PROVIDERS["groq"],BACKUP_PROVIDER="none")
        calls=[0]
        def send(request,timeout=40):
            calls[0]+=1
            if calls[0]==1:
                raise URLError("no-network")
            return response("groq")
        with patch.object(gateway.urllib.request,"urlopen",side_effect=send):
            with capture_call(self.store,purpose="deliberacion") as call:
                (decision,_),provider,_=route(
                    cfg,{},threading.RLock(),
                    lambda current:gateway.request_llm(current,self.context),
                    sleep=lambda _:None)
        self.assertEqual(provider,"groq")
        rows=sorted((r for r in self.store.recent() if r["call_id"]==call.call_id),
                    key=lambda x:x["attempt_ordinal"])
        self.assertEqual([r["status"] for r in rows],["transport_error","accepted"])
        self.assertEqual([r["attempt_ordinal"] for r in rows],[1,2])
        self.assertEqual(rows[0]["body"],rows[1]["body"])

    def test_rejected_model_response_is_not_claimed_accepted(self):
        cfg=dict(PROVIDERS["gemini"],GEMINI_FALLBACK_MODELS="",
                 BACKUP_PROVIDER="groq",GROQ_API_KEY="secret",
                 GROQ_MODEL="openai/gpt-oss-20b")
        def send(request,timeout=40):
            if "generativelanguage.googleapis.com" in request.full_url:
                return response("gemini",content="{broken json")
            return response("groq")
        with patch.object(gateway.urllib.request,"urlopen",side_effect=send):
            with capture_call(self.store,purpose="deliberacion") as call:
                (_, _),provider,_=route(
                    cfg,{},threading.RLock(),
                    lambda current:gateway.request_llm(current,self.context),
                    sleep=lambda _:None)
        self.assertEqual(provider,"groq")
        rows=sorted((r for r in self.store.recent() if r["call_id"]==call.call_id),
                    key=lambda x:x["attempt_ordinal"])
        self.assertEqual([r["status"] for r in rows],["rejected","accepted"])

    def test_chat_is_a_separate_purpose_and_tracks_source_message(self):
        cfg=dict(PROVIDERS["gemini"])
        with patch.object(gateway.urllib.request,"urlopen",
                          return_value=response("gemini",content="Te respondo.")):
            with capture_call(self.store,purpose="chat",session_id=5,
                              source_id="human-chat-04") as call:
                (reply,_),provider,_=route(
                    cfg,{},threading.RLock(),
                    lambda pcfg:gateway.request_chat(
                        pcfg,self.context,[{"role":"user","text":"Hola"}]),
                    purpose="chat",sleep=lambda _:None)
        self.assertEqual(reply,"Te respondo.")
        row=next(r for r in self.store.recent() if r["call_id"]==call.call_id)
        self.assertEqual(row["source_id"],"human-chat-04")
        self.assertEqual(row["purpose"],"chat")
        self.assertEqual(row["status"],"accepted")
        self.assertIn(b"contents",row["body"])

    def test_capture_failure_does_not_abort_model_request(self):
        class Broken:
            def begin(self,**kwargs):
                raise PermissionError("sin espacio")
            def finish(self,*args,**kwargs):
                raise PermissionError()
        cfg=dict(PROVIDERS["gemini"])
        with patch.object(gateway.urllib.request,"urlopen",
                          return_value=response("gemini")):
            with capture_call(Broken(),purpose="deliberacion"):
                result,_=gateway.request_llm(cfg,self.context)
        self.assertEqual(result["cuaderno"],"Respuesta válida")

    def test_simulation_is_lazy_and_sidecar_is_not_part_of_world(self):
        sim=Simulation(db_path=self.world,world_seed=7321,rng_seed=9821)
        try:
            self.assertEqual(sim.llm_request_store.path,self.store.path)
            self.assertFalse(self.store.path.exists())
            sim.write()
            self.assertFalse(self.store.path.exists())
            with closing(sqlite3.connect(self.world)) as db:
                names={x[0] for x in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertNotIn("llm_requests",names)
        finally:
            sim.conn.close()

    def test_read_validates_checksum_and_does_not_recreate_missing_db(self):
        self.assertEqual(self.store.recent(),[])
        self.assertFalse(self.store.path.exists())
        item=self.store.begin(
            body='{"texto":"ñ"}'.encode("utf-8"),call_id="call-1",session_id=1,
            purpose="deliberacion",source_id=None,simulated_at=None,
            ordinal=1,provider="gemini",model="gemini-model")
        self.assertEqual(len(self.store.recent()),1)
        with closing(sqlite3.connect(self.store.path)) as db:
            db.execute("UPDATE llm_requests SET body=? WHERE attempt_id=?",
                       (sqlite3.Binary(b"corrupto"),item))
            db.commit()
        with self.assertRaises(ValueError):
            self.store.recent()


if __name__=="__main__":
    unittest.main()
