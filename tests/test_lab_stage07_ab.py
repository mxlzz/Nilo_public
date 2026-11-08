"""Etapa 07: A/B con misma referencia física, sin red por defecto.

Las salidas de proveedor son sintéticas para tests. Ninguna prueba tiene
licencia para usar claves reales ni escribir la partida original.
"""
from __future__ import annotations

from contextlib import closing
import copy
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
from unittest.mock import patch

from laboratorio_motor import create_lab_server
from nilo_runtime.labs.hub import LabHub
from nilo_runtime.labs.sandbox import SimulationSandbox
from nilo_runtime.labs.ab_experiment import (
    _SilentTrace,context_pair,physical_pair,live_pair,
)
from nilo_runtime.core.lab_settings import baseline
from nilo_runtime.application.engine import Simulation

ROOT=Path(__file__).resolve().parents[1]


def candidate():
    p=baseline()
    p["name"]="variante"
    p["omit_context"]=["antecedentes_relacionados"]
    p["prompt_note"]="Revisar hipótesis antes de experimentar."
    return p


def fake_decision():
    return {
        "objetivo":"Observar entorno",
        "cuaderno":"Decidí esperar para observar.",
        "motivo":"La situación es estable.",
        "accion_proyecto":"sin_proyecto",
        "revisar_en_minutos":90,
        "plan":[{"op":"wait","minutes":20}],
    }


class OfflineABTests(unittest.TestCase):
    def test_same_frozen_context_provider_and_exact_wire_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            hub=LabHub(Path(tmp))
            with patch("nilo_runtime.labs.ab_experiment.gateway._post",
                       side_effect=AssertionError("NO se puede llamar a API")):
                r=context_pair(hub,candidate(),provider="gemini",seed=7321)
            self.assertEqual(r["llm_calls"],0)
            self.assertTrue(r["comparison"]["comparable_same_reference"])
            self.assertTrue(r["comparison"]["changed_request"])
            self.assertTrue(r["comparison"]["actual_model_response"] is False)
            self.assertEqual(r["baseline"]["seed"],7321)
            self.assertEqual(r["variant"]["seed"],7321)
            for k in ("baseline","variant"):
                p=r[k]
                self.assertIs(p["enviado_a_llm"],False)
                self.assertEqual(hashlib.sha256(p["solicitud_serializada"].encode()).hexdigest(),
                                 p["huella_solicitud_calculada"])
            self.assertFalse(r["modified_original_world"])

    def test_same_seed_runs_are_reproducible_for_scripted_motor(self):
        script=[{"op":"wait","minutes":20}]
        with patch("nilo_runtime.labs.ab_experiment.gateway._post",
                   side_effect=AssertionError("Prohibida red")):
            r=physical_pair(seed=7321,baseline_steps=script,variant_steps=script)
            again=physical_pair(seed=7321,baseline_steps=script,variant_steps=script)
        self.assertEqual(r["llm_calls"],0)
        self.assertTrue(r["comparison"]["same_initial_state"])
        self.assertTrue(r["comparison"]["same_script"])
        self.assertTrue(r["comparison"]["same_final_state"])
        self.assertEqual(r["reference_sha256"],again["reference_sha256"])
        self.assertEqual(r["baseline"]["final_sha256"],again["baseline"]["final_sha256"])
        self.assertEqual(r["variant"]["steps"][0]["action"],script[0])
        self.assertFalse(r["modified_original_world"])

    def test_different_scripts_give_two_independent_worlds(self):
        r=physical_pair(seed=315,baseline_steps=[{"op":"wait","minutes":20}],
                        variant_steps=[{"op":"rest","minutes":30}],kit=True)
        self.assertEqual(r["baseline"]["initial_sha256"],r["variant"]["initial_sha256"])
        self.assertNotEqual(r["baseline"]["steps"][0]["action"],
                            r["variant"]["steps"][0]["action"])
        self.assertFalse(r["comparison"]["different_llm_context_tested"])

    def test_script_limits_and_unknown_operations(self):
        for script in ([{"op":"hijack"}],
                       [{"op":"wait","minutes":30}]*7,
                       [{"op":"wait","minutes":float("nan")}]):
            with self.subTest(script=str(script)[:45]),self.assertRaises(ValueError):
                physical_pair(seed=21,baseline_steps=script,variant_steps=[])

    def test_saved_world_backups_are_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=Path(tmp)/"original.sqlite3"
            sim=Simulation(db_path=db,world_seed=7321,rng_seed=9821)
            try:sim.write()
            finally:sim.conn.close()
            before=hashlib.sha256(db.read_bytes()).hexdigest()
            result=physical_pair(seed=7321,source="saved",world_path=db,
                         baseline_steps=[{"op":"wait","minutes":20}],
                         variant_steps=[{"op":"wait","minutes":20}])
            self.assertEqual(result["source"],"readonly_copy_of_saved_world")
            self.assertEqual(hashlib.sha256(db.read_bytes()).hexdigest(),before)
            with tempfile.TemporaryDirectory() as td:
                hub=LabHub(Path(td),db)
                context=context_pair(hub,candidate(),seed=7321,source="saved",world_path=db)
            self.assertEqual(context["source"],"readonly_copy_of_saved_world")
            self.assertEqual(hashlib.sha256(db.read_bytes()).hexdigest(),before)


class ProviderOptinTests(unittest.TestCase):
    @staticmethod
    def stub(url,payload,headers,provider):
        if provider!="groq":raise AssertionError("Solo groq sintético")
        if not url.startswith("https://api.groq.com/"):
            raise AssertionError("Endpoint inesperado")
        if not headers.get("Authorization","").startswith("Bearer "):
            raise AssertionError("No se pasó clave privada al cliente")
        assert "messages" in payload
        return {"choices":[{"message":{"content":json.dumps(fake_decision())}}],
                "usage":{"prompt_tokens":400,"completion_tokens":70}}

    def test_live_does_not_call_network_without_explicit_confirmation(self):
        with tempfile.TemporaryDirectory() as td:
            hub=LabHub(Path(td))
            with patch("nilo_runtime.labs.ab_experiment.config",
                       return_value={"GROQ_API_KEY":"sintetica","MIN_REAL_SECONDS_BETWEEN_CALLS":"15"}):
                with self.assertRaisesRegex(ValueError,"confirmación"):
                    live_pair(hub,candidate(),provider="groq",turns=1,
                              seed=7321,confirm=False,poster=self.stub,sleep_fn=lambda _:None)
            with self.assertRaisesRegex(ValueError,"dos"):
                live_pair(hub,candidate(),provider="groq",turns=3,confirm=True)

    def test_two_decisions_are_frozen_one_turn_and_never_executed(self):
        with tempfile.TemporaryDirectory() as td:
            hub=LabHub(Path(td))
            calls=[]
            def fake_post(url,payload,headers,provider):
                calls.append(json.dumps(payload,ensure_ascii=False))
                return self.stub(url,payload,headers,provider)
            with patch("nilo_runtime.labs.ab_experiment.config",
                       return_value={"GROQ_API_KEY":"prueba-secreta","MIN_REAL_SECONDS_BETWEEN_CALLS":"15"}):
                result=live_pair(hub,candidate(),provider="groq",seed=7321,confirm=True,
                                 turns=1,poster=fake_post,sleep_fn=lambda _:None)
            self.assertEqual(len(calls),2)
            self.assertEqual(result["llm_calls"],2)
            self.assertEqual(result["baseline"]["turns"][0]["response"]["normalized"]["plan"][0]["op"],"wait")
            self.assertIsNone(result["variant"]["turns"][0]["world_effect"])
            self.assertNotIn("prueba-secreta",json.dumps(result))
            self.assertEqual(result["baseline"]["turns"][0]["pre_context_sha256"],
                             result["variant"]["turns"][0]["pre_context_sha256"])

    def test_multi_turn_uses_real_plan_on_each_temporary_world(self):
        with tempfile.TemporaryDirectory() as td:
            hub=LabHub(Path(td))
            with patch("nilo_runtime.labs.ab_experiment.config",
                       return_value={"GROQ_API_KEY":"sintetica","MIN_REAL_SECONDS_BETWEEN_CALLS":"15"}):
                result=live_pair(hub,candidate(),provider="groq",seed=7321,confirm=True,
                                 turns=2,poster=self.stub,sleep_fn=lambda _:None)
            self.assertEqual(result["llm_calls"],4)
            for name in ("baseline","variant"):
                turns=result[name]["turns"]
                self.assertEqual(len(turns),2)
                self.assertTrue(turns[0]["world_effect"]["applied"])
                self.assertTrue(turns[1]["world_effect"]["applied"])
            self.assertFalse(result["original_world_modified"])

    def test_missing_provider_key_fails_without_network(self):
        with tempfile.TemporaryDirectory() as td:
            hub=LabHub(Path(td))
            with patch("nilo_runtime.labs.ab_experiment.config",return_value={}):
                with self.assertRaisesRegex(ValueError,"clave"):
                    live_pair(hub,candidate(),provider="groq",seed=7321,
                              confirm=True,turns=1,poster=self.stub,sleep_fn=lambda _:None)


class ExperimentHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix="nilo-ab-http-")
        cls.root=Path(cls.tmp.name)
        cls.hub=LabHub(cls.root,cls.root/"missing.sqlite3")
        cls.server=create_lab_server(0,hub=cls.hub)
        cls.thread=threading.Thread(target=cls.server.serve_forever,
                                    kwargs={"poll_interval":0.02},daemon=True)
        cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=3)
        cls.server.RequestHandlerClass.lab.close();cls.tmp.cleanup()

    @classmethod
    def request(cls,method,path,body=None,headers=None):
        conn=http.client.HTTPConnection("127.0.0.1",
                 cls.server.server_address[1],timeout=25)
        try:
            data=json.dumps(body).encode() if body is not None else None
            h=headers or ({"Content-Type":"application/json"} if body is not None else {})
            conn.request(method,path,body=data,headers=h)
            response=conn.getresponse()
            blob=response.read()
            try:return response.status,json.loads(blob)
            except ValueError:return response.status,blob
        finally:conn.close()

    def test_view_and_context_route_are_local_only(self):
        status,html=self.request("GET","/experimentos")
        self.assertEqual(status,200)
        self.assertIn(b"Experimentos A/B",html)
        status,data=self.request("POST","/api/lab/experiment",
                 {"mode":"context","seed":21,"profile":candidate(),"provider":"groq"})
        self.assertEqual(status,200,str(data)[:320])
        self.assertEqual(data["llm_calls"],0)
        self.assertTrue(data["comparison"]["comparable_same_reference"])
        self.assertEqual(self.request("GET","/api/lab/experiment")[0],404)
        self.assertEqual(self.request("POST","/api/lab/experiment",
                  {"mode":"live","seed":21,"profile":candidate(),
                   "provider":"groq","confirm_live":False})[0],400)
        self.assertEqual(self.request("POST","/api/lab/experiment",
                  {"mode":"context","seed":21,"profile":candidate(),
                   "path":"/etc/passwd"})[0],400)

    def test_saved_source_never_accepts_client_supplied_filename(self):
        status,data=self.request("POST","/api/lab/experiment",
                   {"mode":"physical","seed":1,"source":"saved",
                    "path":"/tmp/my-world.sqlite3",
                    "baseline_steps":[],"variant_steps":[]})
        self.assertEqual(status,400)
        self.assertIn("No hay una partida",data["error"])

    def test_browser_syntax_and_new_page_bundle(self):
        node=shutil.which("node")
        html=(ROOT/"laboratorio_experimentos.html").read_text("utf-8")
        self.assertIn("confirm(",html)
        self.assertIn('"mode"',html)
        self.assertIn('value="context"',html)
        self.assertIn('href="/visor-llm"',html)
        self.assertIn('href="/experimentos"',html)
        self.assertIn('/assets/laboratorio_ui.js',html)
        self.assertNotIn("eval(",html)
        manifest=json.loads((ROOT/"MANIFIESTO_SHA256.json").read_text("utf-8"))
        self.assertIn("laboratorio_experimentos.html",manifest["files"])
        if node:
            with tempfile.TemporaryDirectory() as tmp:
                js=html.split("<script>",1)[1].split("</script>",1)[0]
                f=Path(tmp)/"ab.js";f.write_text(js,"utf-8")
                proc=subprocess.run([node,"--check",str(f)],capture_output=True,text=True)
                self.assertEqual(proc.returncode,0,proc.stderr)


if __name__=="__main__":
    unittest.main()
