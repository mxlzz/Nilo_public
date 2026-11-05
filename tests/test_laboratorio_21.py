"""Etapa 21: laboratorio unificado, perfiles y recuperación reversible."""
from __future__ import annotations

import hashlib
import http.client
import json
from pathlib import Path
import sqlite3
import subprocess
import shutil
import tempfile
import threading
import unittest
from unittest.mock import patch

from nilo import Simulation
from laboratorio_motor import MotorLab, create_lab_server
from nilo_runtime.core.lab_settings import (
    validate, baseline, config_overlay, OPTIONAL_CONTEXT,
)
from nilo_runtime.labs.profiles import ProfileStore
from nilo_runtime.labs.hub import LabHub

ROOT=Path(__file__).resolve().parents[1]


def variant(name="variante-uno"):
    value=baseline()
    value["name"]=name
    value["limits"]["MAX_LLM_CALLS_PER_DAY"]=230
    value["omit_context"]=[OPTIONAL_CONTEXT[0]]
    value["prompt_note"]="Considerar las mediciones antes de cualquier afirmación."
    return value


class ProfileContracts21(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="nilo-lab-profile-21-")
        self.root=Path(self.temp.name)
        self.store=ProfileStore(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_validate_and_reject_limits_and_unknown_keys(self):
        p=variant()
        self.assertEqual(validate(p),p)
        for key in p["limits"]:
            for v in (True,-1,99999,0.5,float("nan"),"100"):
                with self.subTest(key=key,value=v):
                    bad=variant()
                    bad["limits"][key]=v
                    with self.assertRaises(ValueError):validate(bad)
        for field,value in (
            ("name","../../config.env"),("name","Nombre inválido"),
            ("omit_context",["necesidades"]),
            ("omit_context",["posición"]),
            ("omit_context",[OPTIONAL_CONTEXT[0],OPTIONAL_CONTEXT[0]]),
            ("prompt_note","x"*701),
        ):
            bad=variant();bad[field]=value
            with self.subTest(field=field):
                with self.assertRaises(ValueError):validate(bad)
        bad=variant();bad["GEMINI_API_KEY"]="secreto"
        with self.assertRaises(ValueError):validate(bad)

    def test_save_load_diff_and_apply_restorable(self):
        p=variant()
        stored=self.store.save(p)
        self.assertEqual(self.store.load(p["name"]),p)
        self.assertEqual(stored["profile"],p)
        self.assertIn("limits",self.store.diff(p))
        before=config_overlay(self.root)
        self.assertEqual(before,{})
        result=self.store.apply(p)
        self.assertTrue(result["applied"])
        self.assertTrue(result["restart_required"])
        self.assertEqual(self.store.current(),p)
        self.assertEqual(config_overlay(self.root)["MAX_LLM_CALLS_PER_DAY"],"230")
        self.assertEqual(config_overlay(self.root)["_LAB_OMIT_CONTEXT"],
                         tuple(p["omit_context"]))
        self.assertIn(result["checkpoint"],self.store.entries()["backups"])
        self.assertFalse(self.store.apply(p)["applied"])
        recovered=self.store.restore(result["checkpoint"])
        self.assertTrue(recovered["restored"])
        self.assertEqual(self.store.current(),baseline())
        self.assertEqual(config_overlay(self.root),{})
        self.assertNotIn("config.env",str(self.store.active))
        self.assertEqual(len((self.store.dir/"changes.jsonl").read_text().splitlines()),2)

    def test_restore_has_undo_checkpoint(self):
        first=variant("uno")
        second=variant("dos")
        self.store.apply(first)
        result=self.store.apply(second)
        undo=self.store.restore(result["checkpoint"])["checkpoint_undo"]
        self.assertEqual(self.store.current(),first)
        self.store.restore(undo)
        self.assertEqual(self.store.current(),second)

    def test_failed_apply_keeps_previous_file_and_profile(self):
        self.store.apply(variant("base-ajustada"))
        original=self.store.active.read_bytes()
        with patch("nilo_runtime.labs.profiles._atomic",
                   side_effect=OSError("simulación de falla de disco")):
            with self.assertRaises(OSError):
                self.store.apply(variant("fallo"))
        self.assertEqual(self.store.active.read_bytes(),original)
        self.assertEqual(self.store.current()["name"],"base-ajustada")

    def test_tampered_checkpoint_cannot_restore(self):
        first=self.store.apply(variant())
        checkpoint=first["checkpoint"]
        file=self.store.dir/"backups"/(checkpoint+".json")
        record=json.loads(file.read_text("utf-8"))
        record["profile_sha256"]="0"*64
        file.write_text(json.dumps(record),encoding="utf-8")
        before=self.store.active.read_bytes()
        with self.assertRaises(ValueError):
            self.store.restore(checkpoint)
        self.assertEqual(before,self.store.active.read_bytes())

    def test_no_path_traversal_via_name_or_checkpoint(self):
        for name in ("../secrets","/tmp/evil","../../hello","a/b",".env"):
            with self.assertRaises(ValueError):self.store.load(name)
        with self.assertRaises(ValueError):self.store.restore("../active.json")

    def test_lab_root_does_not_contain_credentials_after_apply(self):
        p=variant()
        self.store.save(p)
        self.store.apply(p)
        text="".join(f.read_text("utf-8") for f in self.store.dir.rglob("*.json"))
        self.assertNotIn("GEMINI_API_KEY",text)
        self.assertNotIn("GROQ_API_KEY",text)
        self.assertFalse((self.root/"config.env").exists())


class Hub21(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="nilo-hub21-")
        self.root=Path(self.tmp.name)
        self.db=self.root/"world.sqlite3"
        self.sim=Simulation(db_path=self.db,world_seed=7321,rng_seed=9821)
        self.hub=LabHub(self.root,self.db)

    def tearDown(self):
        self.sim.conn.close()
        self.tmp.cleanup()

    def test_preview_uses_real_request_builder_without_network(self):
        p=variant()
        with patch("urllib.request.urlopen",side_effect=AssertionError("network")):
            base=self.hub.preview(baseline(),provider="gemini",seed=7321)
            candidate=self.hub.preview(p,provider="gemini",seed=7321)
        self.assertFalse(candidate["enviado_a_llm"])
        self.assertIn(p["prompt_note"],candidate["mensaje_sistema"])
        self.assertNotIn("NOTA ADICIONAL",base["mensaje_sistema"])
        self.assertIn("systemInstruction",candidate["solicitud_json"])
        self.assertNotIn("vista-previa-sin-red",
                         json.dumps(candidate["solicitud_json"],ensure_ascii=False))

    def test_groq_prompt_preview_and_diff(self):
        p=variant()
        response=self.hub.compare(p,provider="groq",seed=7321)
        self.assertIn("messages",response["after"]["solicitud_json"])
        self.assertNotEqual(response["baseline_bytes"],response["variant_bytes"])
        self.assertIn("prompt_note",response["diff"])
        self.assertFalse(response["physical_params_modified"])
        self.assertIn("considerar",response["after"]["mensaje_sistema"].lower())

    def test_scenario_compare_uses_two_real_simulations(self):
        report=self.hub.compare(variant(),provider="gemini",seed=7321,
                                scenario="rest")
        self.assertEqual(report["scenario"]["id"],"rest")
        self.assertTrue(report["scenario"]["same_physical_effects"])
        self.assertEqual(report["scenario"]["baseline"],
                         report["scenario"]["variant"])
        self.assertTrue(report["scenario"]["expected_baseline"])

    def test_world_backup_and_restore_copy_never_overwrite_main(self):
        before=self.sim.conn.execute(
            "SELECT payload FROM snapshot WHERE id=1").fetchone()[0]
        with self.assertRaises(ValueError):
            self.hub.backup_world()
        copied=self.hub.backup_world(confirm=True)
        self.assertTrue(copied["created"])
        name=copied["name"]
        self.assertIn(name,self.hub.list()["world_backups"])
        restored=self.hub.restore_world_copy(name,confirm=True)
        self.assertTrue(restored["restored_as_copy"])
        self.assertNotEqual(restored["location"],str(self.db))
        self.assertEqual(self.sim.conn.execute(
            "SELECT payload FROM snapshot WHERE id=1").fetchone()[0],before)
        with self.assertRaises(ValueError):
            self.hub.restore_world_copy("../../secret.sqlite3",confirm=True)

    def test_invalid_names_and_seeds_are_rejected(self):
        with self.assertRaises(ValueError):self.hub.preview(variant(),seed=True)
        with self.assertRaises(ValueError):self.hub.compare(variant(),scenario="../config.env")
        with self.assertRaises(ValueError):self.hub.preview(variant(),provider="otro")


class Sandbox21(unittest.TestCase):
    def test_motor_lab_runs_real_simulation_and_not_duplicate_execute(self):
        lab=MotorLab()
        try:
            self.assertIsInstance(lab.sim,Simulation)
            self.assertFalse(hasattr(lab,"_execute"))
            before=lab.person["clock_minutes"]
            state=lab.act({"op":"rest","minutes":30})
            self.assertEqual(state["last"]["engine"],
                             "Simulation.plan_ready / Simulation.tick")
            self.assertGreater(lab.person["clock_minutes"],before)
            self.assertIsNotNone(state["last"]["diagnostic"])
            self.assertEqual(state["last"]["result"],
                             state["last"]["diagnostic"]["action_result"])
        finally:lab.close()

    def test_sandbox_reset_and_context_preserve_isolation(self):
        lab=MotorLab()
        try:
            state=lab.state()
            self.assertEqual(state["history"],[])
            state=lab.act({"op":"wait","minutes":20})
            self.assertIsInstance(state["last"]["trace"],list)
            before=json.dumps(lab.sim.s,sort_keys=True,default=str)
            lab.payload("gemini")
            self.assertEqual(json.dumps(lab.sim.s,sort_keys=True,default=str),before)
            after=lab.reset("nuevo",7321,False)
            self.assertEqual(after["history"],[])
            self.assertIsNone(after["last"])
        finally:lab.close()


class LabHttp21(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix="nilo-lab-http21-")
        cls.root=Path(cls.tmp.name)
        cls.sim=Simulation(db_path=cls.root/"world.sqlite3",rng_seed=9821)
        cls.lab=MotorLab()
        cls.server=create_lab_server(0,lab=cls.lab,
            hub=LabHub(cls.root,cls.root/"world.sqlite3"))
        cls.port=cls.server.server_address[1]
        cls.thread=threading.Thread(target=cls.server.serve_forever,
                                    kwargs={"poll_interval":0.02},daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close()
        cls.thread.join(timeout=4)
        cls.lab.close();cls.sim.conn.close();cls.tmp.cleanup()

    def request(self,method,path,data=None,headers=None):
        conn=http.client.HTTPConnection("127.0.0.1",self.port,timeout=30)
        try:
            h=dict(headers or {})
            body=None
            if data is not None:
                body=json.dumps(data).encode("utf-8")
                h.setdefault("Content-Type","application/json")
            conn.request(method,path,body=body,headers=h)
            resp=conn.getresponse()
            raw=resp.read()
            return resp.status,(json.loads(raw) if resp.getheader(
                "Content-Type","").startswith("application/json") else raw)
        finally:conn.close()

    def test_hub_page_and_readonly_listing(self):
        code,html=self.request("GET","/ajustes")
        self.assertEqual(code,200)
        self.assertIn(b"Centro de ajustes",html)
        for url in ("/api/lab/profile/list","/api/catalog","/api/state"):
            code,payload=self.request("GET",url)
            self.assertEqual(code,200)
        code,invalid=self.request("GET","/api/lab/profile/load?name=../../env")
        self.assertEqual(code,400)

    def test_save_load_apply_and_restore_http(self):
        p=variant("http-test")
        code,saved=self.request("POST","/api/lab/profile/save",{"profile":p})
        self.assertEqual(code,200,saved)
        code,loaded=self.request("GET","/api/lab/profile/load?name=http-test")
        self.assertEqual(code,200)
        self.assertEqual(loaded,p)
        code,denied=self.request("POST","/api/lab/profile/apply",{"profile":p})
        self.assertEqual(code,400)
        code,applied=self.request("POST","/api/lab/profile/apply",
                                  {"profile":p,"confirm":True})
        self.assertEqual(code,200,applied)
        self.assertTrue(applied["applied"])
        code,restored=self.request("POST","/api/lab/profile/restore",
            {"checkpoint":applied["checkpoint"],"confirm":True})
        self.assertEqual(code,200,restored)
        self.assertTrue(restored["restored"])
        self.assertEqual(restored["current"],baseline())

    def test_cross_origin_rejected_for_writes(self):
        p=variant()
        code,msg=self.request("POST","/api/lab/profile/apply",
            {"profile":p,"confirm":True},
            {"Origin":"https://example.org"})
        self.assertEqual(code,403)
        self.assertFalse((self.root/"lab_profiles"/"active.json").exists())

    def test_old_lab_scenarios_routes_still_available(self):
        for endpoint in ("/","/sandbox","/historico","/api/catalog"):
            code,_=self.request("GET",endpoint)
            self.assertEqual(code,200)

    def test_new_http_mutation_rejects_wrong_content_type(self):
        code,result=self.request("POST","/api/lab/profile/save",
             {"profile":variant()},headers={"Content-Type":"text/plain"})
        self.assertEqual(code,415)

    def test_ui_javascript_parses_when_node_available(self):
        node=shutil.which("node")
        if not node:self.skipTest("Node.js no instalado")
        page=(ROOT/"laboratorio_ajustes.html").read_text("utf-8")
        self.assertIn("Centro de ajustes",page)
        script=page.split("<script>",1)[1].split("</script>",1)[0]
        with tempfile.TemporaryDirectory(prefix="nilo-lab-js21-") as td:
            js=Path(td)/"lab.js";js.write_text(script,encoding="utf-8")
            r=subprocess.run([node,"--check",str(js)],capture_output=True,
                             text=True,timeout=20)
            self.assertEqual(r.returncode,0,r.stderr)


if __name__=="__main__":
    unittest.main()
