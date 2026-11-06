"""Etapa 05: API local del laboratorio, GET puro y lista de intentos segura."""
from __future__ import annotations

from contextlib import closing
import hashlib
import http.client
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest

from laboratorio_motor import create_lab_server
from nilo_runtime.labs.hub import LabHub
from nilo_runtime.labs.llm_read import LocalLLMReadAPI, ReadError
from nilo_runtime.storage.llm_requests import RequestTraceStore
from nilo_runtime.web.api import dispatch as observer_dispatch


def wire(payload):
    return json.dumps(payload,ensure_ascii=False).encode("utf-8")


GEMINI = wire({
    "systemInstruction":{"parts":[{"text":"Sos Nilo. No inventes resultados."}]},
    "contents":[{"role":"user","parts":[{
        "text":'Operaciones disponibles:\nSITUACIÓN REAL: {"momento":"Día 3",'
               '"necesidades":{"energia":"con energía"},"texto":"¿Dónde?"}'
    }]}],
    "generationConfig":{"temperature":0.85},
})
GROQ = wire({
    "model":"test-groq",
    "messages":[
        {"role":"system","content":"Sos Nilo."},
        {"role":"user","content":'{"momento":"Día 3", "proyecto_actual":{"title":"Agua"}}'},
    ],
})
CHAT = wire({
    "model":"test-chat",
    "messages":[
        {"role":"system","content":"Respondé como Nilo."},
        {"role":"user","content":'CONTEXTO COMPROBADO (no lo contradigas): '
         '{"momento":"Día 3"}\n\nHola'},
        {"role":"assistant","content":"Respondí antes."},
    ],
})


class LocalReadContracts(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix="nilo-llm-read-05-")
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.world=self.root/"partida.sqlite3"
        with closing(sqlite3.connect(self.world)) as db:
            db.execute("CREATE TABLE history (seq INTEGER PRIMARY KEY, "
                       "category TEXT, simulated_at TEXT, payload TEXT)")
            db.commit()
        self.store=RequestTraceStore.for_world(self.world)
        self.reader=LocalLLMReadAPI(self.world)
        self.rows=[]

    def add(self, body=GEMINI, *, provider="gemini",
            purpose="deliberacion", call="c1", source=None,
            session=5, status="accepted", provenance=None):
        if provenance is None:
            provenance={"schema_version":1,"field_count":1,
                        "payload_verification":"verificado_con_payload_http"}
        ident=self.store.begin(
            body=body,call_id=call,session_id=session,purpose=purpose,
            source_id=source,simulated_at="Día 3 · 12:00",
            ordinal=len(self.rows)+1,provider=provider,model="synthetic-model",
            provenance=provenance)
        if status!="transport_attempted":
            self.store.finish(ident,status)
        self.rows.append(ident)
        return ident

    def test_empty_missing_sidecar_does_not_create_files(self):
        self.assertFalse(self.store.path.exists())
        found=self.reader.list_attempts("limit=10")
        self.assertEqual(found,{"attempts":[],"next_before":None,
                                "available":False,"source":"local"})
        self.assertFalse(self.store.path.exists())
        with self.assertRaises(ReadError) as e:
            self.reader.get_attempt("id="+"a"*32)
        self.assertEqual(e.exception.status,404)
        self.assertFalse(self.store.path.exists())

    def test_list_metadata_filters_cursor_date_and_page(self):
        a=self.add(call="c1")
        b=self.add(body=GROQ,provider="groq",call="c2",status="http_error")
        c=self.add(body=CHAT,provider="groq",purpose="chat",
                   call="c3",source="chat-human-1",session=9)
        previous=self.store.path.read_bytes()
        first=self.reader.list_attempts("limit=1")
        self.assertTrue(first["available"])
        self.assertEqual([x["attempt_id"] for x in first["attempts"]],[c])
        self.assertIsInstance(first["next_before"],int)
        self.assertNotIn("body",first["attempts"][0])
        self.assertNotIn("metadata_json",first["attempts"][0])
        second=self.reader.list_attempts("limit=1&before="+str(first["next_before"]))
        self.assertEqual([x["attempt_id"] for x in second["attempts"]],[b])
        third=self.reader.list_attempts("limit=1&before="+str(second["next_before"]))
        self.assertEqual([x["attempt_id"] for x in third["attempts"]],[a])
        self.assertIsNone(third["next_before"])
        self.assertEqual([x["attempt_id"] for x in self.reader.list_attempts(
            "provider=gemini")["attempts"]],[a])
        self.assertEqual([x["attempt_id"] for x in self.reader.list_attempts(
            "provider=groq&status=http_error")["attempts"]],[b])
        self.assertEqual([x["attempt_id"] for x in self.reader.list_attempts(
            "purpose=chat&session=9")["attempts"]],[c])
        self.assertEqual([x["attempt_id"] for x in self.reader.list_attempts(
            "date="+self.store.recent()[0]["started_utc"][:10])["attempts"]],
            [c,b,a])
        self.assertEqual(self.reader.list_attempts("session=800")["attempts"],[])
        self.assertEqual(self.store.path.read_bytes(),previous)

    def test_raw_body_segments_and_provenance_are_verifiably_same_capture(self):
        ident=self.add()
        entry=self.reader.get_attempt("id="+ident)
        self.assertEqual(entry["attempt_id"],ident)
        self.assertEqual(entry["body_utf8"].encode("utf-8"),GEMINI)
        self.assertEqual(entry["body_sha256"],hashlib.sha256(GEMINI).hexdigest())
        self.assertEqual(entry["provenance_status"],"available")
        self.assertEqual(entry["provenance"]["field_count"],1)
        self.assertEqual([m["role"] for m in entry["messages"]],["system","user"])
        for message in entry["messages"]:
            self.assertEqual("".join(x["literal"] for x in message["segments"]),
                             message["text"])
        fields=[b for b in entry["messages"][1]["blocks"] if b["kind"]=="field"]
        self.assertEqual([f["title"] for f in fields],
                         ["momento","necesidades","texto"])
        self.assertEqual(fields[1]["subtitle"],
                         "Sensaciones corporales transmitidas al modelo.")
        self.assertIsNone(entry["linked_record"])

    def test_archive_link_uses_exact_call_id_no_interpretation(self):
        ident=self.add(call="real-correlated-call")
        with closing(sqlite3.connect(self.world)) as db:
            db.execute("INSERT INTO history(category,simulated_at,payload) "
                "VALUES(?,?,?)",
                ("llm_decision","Día 3 · 12:00",json.dumps({
                    "id":"llm-101","trace_call_id":"real-correlated-call",
                    "decision":{"cuaderno":"Texto privado de la decisión"}})))
            db.commit()
        entry=self.reader.get_attempt("id="+ident)
        self.assertEqual(entry["linked_record"]["category"],"llm_decision")
        self.assertEqual(entry["linked_record"]["record_id"],"llm-101")
        self.assertEqual(entry["linked_record"]["matched_by"],"trace_call_id")
        self.assertNotIn("decision",entry["linked_record"])

    def test_chat_link_requires_user_role_and_exact_source_id(self):
        ident=self.add(body=CHAT,provider="groq",purpose="chat",
                       source="chat-01")
        with closing(sqlite3.connect(self.world)) as db:
            for role in ("assistant","user"):
                db.execute("INSERT INTO history(category,simulated_at,payload) "
                    "VALUES(?,?,?)",("chat","Día 3",json.dumps({
                        "id":"chat-01","role":role,"text":"mensaje con datos"})))
            db.commit()
        detail=self.reader.get_attempt("id="+ident)
        self.assertEqual(detail["linked_record"]["category"],"chat")
        self.assertEqual(detail["linked_record"]["record_id"],"chat-01")
        self.assertNotIn("text",detail["linked_record"])

    def test_legacy_stage02_without_provenance_still_readable(self):
        ident=self.add(body=GROQ,provider="groq")
        with closing(sqlite3.connect(self.store.path)) as db:
            db.execute("DROP TABLE llm_request_provenance")
            db.commit()
        listed=self.reader.list_attempts()["attempts"]
        self.assertEqual(len(listed),1)
        self.assertFalse(listed[0]["has_provenance"])
        detail=self.reader.get_attempt("id="+ident)
        self.assertEqual(detail["body_utf8"].encode("utf-8"),GROQ)
        self.assertIsNone(detail["provenance"])
        self.assertEqual(detail["provenance_status"],"not_recorded")

    def test_wrong_partida_cannot_read_another_world_attempt(self):
        ident=self.add()
        other=self.root/"otra.sqlite3"
        self.assertEqual(LocalLLMReadAPI(other).list_attempts()["attempts"],[])
        with self.assertRaises(ReadError) as e:
            LocalLLMReadAPI(other).get_attempt("id="+ident)
        self.assertEqual(e.exception.status,404)

    def test_integrity_error_is_409_and_not_a_raw_traceback(self):
        ident=self.add()
        with closing(sqlite3.connect(self.store.path)) as db:
            db.execute("UPDATE llm_requests SET body=? WHERE attempt_id=?",
                       (sqlite3.Binary(b"cuerpo modificado"),ident))
            db.commit()
        with self.assertRaises(ReadError) as e:
            self.reader.get_attempt("id="+ident)
        self.assertEqual(e.exception.status,409)

    def test_invalid_parameters_rejected_before_access(self):
        for query in ("limit=0","limit=101","limit=-1",
                      "provider=desconocido","purpose=exploit","status=foo",
                      "before=abc","before=0","session=foo","date=2026-13-90",
                      "date=ayer","limit=1&limit=2",
                      "path=%2Ftmp%2Fuser.sqlite3","limit=1&unknown=x",
                      "date=2026-11-06&date=2026-11-07"):
            with self.subTest(query=query):
                with self.assertRaises(ReadError):
                    self.reader.list_attempts(query)
        for query in ("", "id=", "id=../config.env", "id="+"b"*65,
                      "id="+"a"*32+"&id="+"b"*32,
                      "id="+"a"*32+"&file=/etc/passwd"):
            with self.subTest(query=query):
                with self.assertRaises(ReadError):
                    self.reader.get_attempt(query)


class LiveLocalLabHttp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix="nilo-lab-http05-")
        cls.root=Path(cls.temp.name)
        cls.world=cls.root/"partida.sqlite3"
        cls.store=RequestTraceStore.for_world(cls.world)
        cls.server=create_lab_server(0,lab=object(),
             hub=LabHub(cls.root,cls.world))
        cls.port=cls.server.server_address[1]
        cls.worker=threading.Thread(target=cls.server.serve_forever,
            kwargs={"poll_interval":0.02},daemon=True)
        cls.worker.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.worker.join(timeout=3)
        cls.temp.cleanup()

    def request(self, method, path, headers=None):
        conn=http.client.HTTPConnection("127.0.0.1",self.port,timeout=5)
        try:
            conn.request(method,path,headers=headers or {})
            reply=conn.getresponse()
            raw=reply.read()
            return reply.status,json.loads(raw.decode("utf-8")),dict(reply.getheaders())
        finally:
            conn.close()

    def test_list_detail_and_unrelated_main_interface_rejection(self):
        self.assertEqual(self.request("GET","/api/lab/llm/attempts")[0],200)
        aid=self.store.begin(
            body=GEMINI,call_id="http-a",session_id=8,
            purpose="deliberacion",source_id=None,simulated_at="Día 3",
            ordinal=1,provider="gemini",model="x",
            provenance={"schema_version":1,"field_count":1})
        status,payload,headers=self.request("GET","/api/lab/llm/attempts?limit=5")
        self.assertEqual(status,200)
        self.assertEqual(headers["Cache-Control"],"no-store")
        self.assertEqual(payload["attempts"][0]["attempt_id"],aid)
        self.assertNotIn("body_utf8",str(payload))
        detail=self.request("GET","/api/lab/llm/attempt?id="+aid)
        self.assertEqual(detail[0],200)
        self.assertEqual(detail[1]["body_utf8"].encode("utf-8"),GEMINI)
        self.assertEqual(detail[2]["X-Content-Type-Options"],"nosniff")
        self.assertEqual(observer_dispatch(object(),"GET",
             "/api/lab/llm/attempt?id="+aid).status,404)

    def test_http_validation_cross_origin_host_and_non_get(self):
        self.assertEqual(self.request("GET","/api/lab/llm/attempt?id=bad")[0],400)
        self.assertEqual(self.request("GET","/api/lab/llm/attempt?id="+"f"*32)[0],404)
        self.assertEqual(self.request("GET","/api/lab/llm/attempts?limit=999")[0],400)
        self.assertEqual(self.request("POST","/api/lab/llm/attempts")[0],404)
        self.assertEqual(self.request("GET","/api/lab/llm/attempts",
                        {"Origin":"https://example.org"})[0],403)
        self.assertEqual(self.request("GET","/api/lab/llm/attempts",
                        {"Host":"evil.example"})[0],403)
        self.assertEqual(self.request("GET","/api/lab/llm/attempts",
                        {"Sec-Fetch-Site":"cross-site"})[0],403)

    def test_unbound_hub_has_no_arbitrary_file_lookup(self):
        self.assertFalse(hasattr(LocalLLMReadAPI(None),"path"))
        self.assertEqual(LocalLLMReadAPI(None).list_attempts()["available"],False)


if __name__ == "__main__":
    unittest.main()
