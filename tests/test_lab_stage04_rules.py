"""Etapa 04: reglas documentadas vs comprobaciones físicas realmente registradas.

Sin llamadas a LLM ni mutación de partidas reales. No inferir condiciones
booleanas a partir de líneas ejecutadas o de una descripción del contrato.
"""
from __future__ import annotations

from contextlib import closing
import http.client
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile
import threading
import unittest

from laboratorio_motor import (
    MotorLab, HistorySource, create_lab_server,
    HISTORY_HTML_FILE, HTML_FILE, SCENARIO_HTML_FILE,
)
from nilo_runtime.labs.hub import LabHub
from nilo_runtime.labs.rules_inspector import operation_reference, inspect_rule
from nilo_runtime.core.operations import registered_operations


class RuleReferenceTests(unittest.TestCase):
    def test_all_registered_operations_have_reference(self):
        catalog=registered_operations()
        self.assertGreaterEqual(len(catalog),26)
        for op in catalog:
            with self.subTest(op=op):
                ref=operation_reference(op)
                self.assertEqual(ref["operation"],op)
                self.assertEqual(ref["evidence_level"],"documented_rule_not_executed")
                self.assertEqual(ref["description"],catalog[op].description)
                self.assertIsInstance(ref["required_fields"],list)
                self.assertIsInstance(ref["planned_minutes"],int)

    def test_unknown_operation_is_never_documented_as_real(self):
        for invalid in ("fire", "go/../../etc", "", None, 14):
            with self.subTest(op=invalid),self.assertRaises(ValueError):
                operation_reference(invalid)

    def test_static_contract_never_claims_real_execution(self):
        report=inspect_rule("gather",step={"op":"gather","target":"piedra"},
                            source="reference")
        self.assertIsNone(report["actual"])
        self.assertEqual(report["instrumented_functions"],[])
        self.assertEqual(report["shape_check"]["evidence_level"],
                         "rechecked_now_not_original_validation")
        self.assertEqual(report["source"],"reference")
        self.assertTrue(report["limitations"])

    def test_historical_checkpoint_does_not_claim_verifier_was_run(self):
        diagnostic={"op":"gather","contract_status":"conforme",
                    "action_result":{"op":"gather","status":"success","success":True}}
        report=inspect_rule("gather",step={"op":"gather","target":"piedra"},
                            diagnostic=diagnostic,source="historical")
        self.assertIsNone(report["actual"])
        self.assertEqual(report["instrumented_functions"],[])
        self.assertTrue(any("checkpoint" in value for value in report["limitations"]))

    def test_actual_sandbox_exposes_only_recorded_conditions(self):
        sample={"op":"interact","contract_status":"conforme",
                "contract_code":"intercambio_verificado",
                "contract_expected":"Intercambio de materia",
                "contract_observed":{"cantidad":2},
                "physical_result":{"inventory_delta":{"piedra":-2}},
                "action_result":{"op":"interact","status":"success",
                                 "success":True,"facts":["Transferí piedra"],
                                 "physical":{"kind":"capability",
                                             "conditions":{"method":"transferir","quantity":2}}}}
        trace=[{"file":"world.py","function":"execute_action",
                "text":"Ejecuta físico","count":1,"first":45,
                "last":55,"line_count":7}]
        report=inspect_rule("interact",step={"op":"interact","method":"transferir"},
                            diagnostic=sample,trace=trace,source="simulation")
        self.assertEqual(report["actual"]["physical_conditions"]["quantity"],2)
        self.assertEqual(report["actual"]["contract_verifier"]["status"],"conforme")
        self.assertEqual(report["instrumented_functions"][0]["function"],"execute_action")
        self.assertTrue(any("condición booleana" in t for t in report["limitations"]))

    def test_result_from_wrong_operation_is_not_attributed(self):
        wrong={"op":"use","contract_status":"conforme",
               "action_result":{"op":"use","success":True}}
        r=inspect_rule("gather",step={"op":"gather","target":"madera"},
                       diagnostic=wrong,result={"op":"gather","success":True},
                       source="simulation")
        self.assertIsNone(r["actual"])
        self.assertTrue(any("otra operación" in t for t in r["limitations"]))

    def test_missing_physical_details_are_explicit(self):
        r=inspect_rule("wait",step={"op":"wait","minutes":20},
                       result={"op":"wait","status":"completed","success":True},
                       source="simulation",trace=[])
        self.assertIsNone(r["actual"]["physical_conditions"])
        self.assertEqual(r["instrumented_functions"],[])
        self.assertTrue(any("desglose" in t for t in r["limitations"]))

    def test_invalid_step_or_source_fails(self):
        for kwargs in (
            {"step":{"op":"rest"}},
            {"source":"invented"},
        ):
            with self.assertRaises(ValueError):
                inspect_rule("wait",**kwargs)


class RuleSandboxTests(unittest.TestCase):
    def test_real_sandbox_action_includes_read_only_rule_report(self):
        lab=MotorLab()
        try:
            before=lab.state()
            output=lab.act({"op":"wait","minutes":30})
            report=output["last"]["rule_inspection"]
            self.assertEqual(report["source"],"simulation")
            self.assertEqual(report["reference"]["operation"],"wait")
            self.assertEqual(report["recorded_step"]["op"],"wait")
            self.assertIn("shape_check",report)
            self.assertEqual(report["shape_check"]["evidence_level"],
                             "rechecked_now_not_original_validation")
            self.assertEqual(before["origin"],output["origin"])
            self.assertEqual(report["instrumented_functions"],
                             output["last"]["rule_inspection"]["instrumented_functions"])
        finally:
            lab.close()


class RuleHttpTests(unittest.TestCase):
    def test_rules_endpoints_validate_action_and_archive_without_path_access(self):
        with tempfile.TemporaryDirectory(prefix="nilo-stage04-") as dirname:
            root=Path(dirname)
            world=root/"world.sqlite3"
            with closing(sqlite3.connect(world)) as db:
                db.execute("""CREATE TABLE history (
                    seq INTEGER PRIMARY KEY, category TEXT,
                    simulated_at TEXT, payload TEXT)""")
                db.execute("""CREATE TABLE timeline_checkpoints (
                    id INTEGER PRIMARY KEY, kind TEXT,clock_minutes REAL,
                    day_label TEXT,source TEXT,operation TEXT, engine_version TEXT,
                    history_seq INTEGER,decision_json TEXT,blob BLOB,blob_sha256 TEXT)""")
                db.execute("""INSERT INTO timeline_checkpoints VALUES
                    (1,'action',480,'Día 1 · 08:00','agenda','wait',
                    '0.7.0',1,?,X'00','hash')""",
                    (json.dumps({"op":"wait","minutes":30,"_origin":"agenda"}),))
                db.commit()
            source=HistorySource()
            source.path=world
            hub=LabHub(root,world)
            server=create_lab_server(0,history=source,hub=hub)
            worker=threading.Thread(target=server.serve_forever,daemon=True)
            worker.start()
            def get(target):
                connection=http.client.HTTPConnection(
                    "127.0.0.1",server.server_address[1],timeout=8)
                try:
                    connection.request("GET",target)
                    response=connection.getresponse()
                    return response.status,json.loads(response.read().decode())
                finally:
                    connection.close()
            initial=world.read_bytes()
            try:
                status,ref=get("/api/lab/rule?op=gather")
                self.assertEqual(status,200)
                self.assertEqual(ref["operation"],"gather")
                status,historical=get("/api/history/rule?event=cp%3A1")
                self.assertEqual(status,200)
                self.assertEqual(historical["source"],"historical")
                self.assertIsNone(historical["actual"])
                self.assertEqual(historical["recorded_step"]["_origin"],"agenda")
                for route in ("/api/lab/rule?op=fire",
                              "/api/lab/rule?op=wait&op=gather",
                              "/api/lab/rule?path=%2Fetc",
                              "/api/history/rule?event=cp%3A1&file=%2Fetc",
                              "/api/history/rule?event=../../etc",
                              "/api/history/rule?event=cp%3A99"):
                    with self.subTest(route=route):
                        status,_=get(route)
                        self.assertEqual(status,400)
                self.assertEqual(world.read_bytes(),initial)
            finally:
                server.shutdown();server.server_close()
                source.temp_directory.cleanup()
                server.RequestHandlerClass.lab.close()


class RulesUiTests(unittest.TestCase):
    def test_lookups_present_in_all_three_relevant_lenses(self):
        sandbox=HTML_FILE.read_text(encoding="utf-8")
        history=HISTORY_HTML_FILE.read_text(encoding="utf-8")
        scenarios=SCENARIO_HTML_FILE.read_text(encoding="utf-8")
        self.assertIn('id="operationRules"',sandbox)
        self.assertIn('last.rule_inspection',sandbox)
        self.assertIn('/api/lab/rule?op=',sandbox)
        self.assertIn('data-rule-event',history)
        self.assertIn('/api/history/rule?event=',history)
        self.assertIn('data-rule-op',scenarios)
        self.assertIn("Regla documentada:",scenarios)

    def test_frontend_scripts_are_syntactically_valid(self):
        node=shutil.which("node")
        if not node:
            self.skipTest("Node no está disponible")
        with tempfile.TemporaryDirectory() as dirname:
            for name,path in (
                ("sandbox",HTML_FILE),("history",HISTORY_HTML_FILE),
                ("scenarios",SCENARIO_HTML_FILE)):
                markup=path.read_text(encoding="utf-8")
                js=markup.split("<script>",1)[1].split("</script>",1)[0]
                file=Path(dirname)/(name+".js")
                file.write_text(js,encoding="utf-8")
                proc=subprocess.run([node,"--check",str(file)],capture_output=True,
                                    text=True,timeout=12)
                self.assertEqual(proc.returncode,0,name+": "+proc.stderr)


if __name__=="__main__":
    unittest.main()
