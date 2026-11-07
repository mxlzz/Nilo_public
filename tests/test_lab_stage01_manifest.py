"""Pruebas del inventario de Etapa 01 (sin importar la simulación ni ejecutar red)."""
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from tools.lab_stage01_manifest import make_manifest


class LabStage01InventoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.world = Path(self.tmp.name) / "world.sqlite3"
        self.req = Path(self.tmp.name) / "requests.sqlite3"
        with sqlite3.connect(self.world) as db:
            db.execute("CREATE TABLE history(seq INTEGER, category TEXT, payload TEXT)")
            db.execute("CREATE TABLE timeline_checkpoints(kind TEXT, operation TEXT, blob BLOB, blob_sha256 TEXT)")
            db.execute("CREATE TABLE engine_sessions(engine_version TEXT)")
            db.execute("INSERT INTO engine_sessions VALUES ('0.7.0')")
            call = "secret-call-id"
            db.execute("INSERT INTO history VALUES(1,'llm_decision',?)",
                       (json.dumps({"trace_call_id":call,
                                    "decision":{"cuaderno":"SECRETO"}}),))
            blob = b"checkpoint privado"
            db.execute("INSERT INTO timeline_checkpoints VALUES('action','gather',?,?)",
                       (blob,hashlib.sha256(blob).hexdigest()))
        with sqlite3.connect(self.req) as db:
            db.execute("CREATE TABLE llm_requests(call_id TEXT,attempt_ordinal INTEGER,status TEXT,body BLOB,body_bytes INTEGER,body_sha256 TEXT)")
            db.execute("CREATE TABLE llm_request_provenance(metadata_json TEXT)")
            body = b'{"contents":"PROMPT-SECRETO"}'
            h = hashlib.sha256(body).hexdigest()
            db.execute("INSERT INTO llm_requests VALUES(?,?,?,?,?,?)",
                       (call,1,"transport_error",body,len(body),h))
            db.execute("INSERT INTO llm_requests VALUES(?,?,?,?,?,?)",
                       (call,2,"accepted",body,len(body),h))
            db.execute("INSERT INTO llm_request_provenance VALUES(?)",
                       (json.dumps({"schema_version":1,
                                    "payload_verification":"verificado_con_payload_http",
                                    "trace_status":"complete"}),))

    def test_retry_and_links_and_privacy(self):
        out = make_manifest(self.world,self.req)
        self.assertEqual(out["requests"]["attempts_total"],2)
        self.assertEqual(out["requests"]["unique_calls"],1)
        self.assertEqual(out["requests"]["duplicate_body_hashes"],1)
        self.assertEqual(out["links"]["decisions_with_matching_request"],1)
        self.assertEqual(out["links"]["accepted_attempts_without_archived_decision"],0)
        self.assertEqual(out["world"]["checkpoint_hash_valid"],1)
        dumped = json.dumps(out)
        for secret in ("PROMPT-SECRETO","SECRETO","secret-call-id","checkpoint privado"):
            self.assertNotIn(secret,dumped)

    def test_missing_link_and_bad_checksum(self):
        with sqlite3.connect(self.req) as db:
            raw = b'{"input":"PRIVATE"}'
            db.execute("INSERT INTO llm_requests VALUES(?,?,?,?,?,?)",
                       ("another-call",1,"accepted",raw,len(raw),"0"*64))
        with sqlite3.connect(self.world) as db:
            db.execute("UPDATE timeline_checkpoints SET blob_sha256=?",("0"*64,))
        out = make_manifest(self.world,self.req)
        self.assertEqual(out["requests"]["body_sha256_invalid"],1)
        self.assertEqual(out["world"]["checkpoint_hash_invalid"],1)
        self.assertEqual(out["links"]["accepted_attempts_without_archived_decision"],1)

    def test_read_only_and_determinism(self):
        before = (self.world.read_bytes(),self.req.read_bytes())
        first = make_manifest(self.world,self.req)
        second = make_manifest(self.world,self.req)
        self.assertEqual(first,second)
        self.assertEqual(before,(self.world.read_bytes(),self.req.read_bytes()))


if __name__=="__main__":
    unittest.main()
