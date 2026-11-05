"""Nilo 0.5.9.3.16: catálogo modular, velocidad HTTP y cadencia LLM.

Sin APIs externas, sin cambiar reglas de la partida y sin exponer física
del catálogo al conocimiento de Nilo.
"""
from __future__ import annotations
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import catalogo
import nilo
from brain import config
from physics import MATERIAL_PHYSICS, properties
from construction import RECOVERABILITY
from mechanics import JOINTS, SHAPES
from timing import SUPPORTED_SPEEDS, deliberation_interval_seconds
from world import (MATERIALS, TERRAINS, YIELDS, FORMS, PORTABLE_WORDS,
                   GATHER_SOURCES, PASSABLE, new_world, gather_material)

ROOT = Path(__file__).resolve().parent.parent


class CatalogContract(unittest.TestCase):
    def test_material_constants_preserve_original_physics(self):
        self.assertEqual(len(MATERIALS), 7)
        self.assertEqual(MATERIALS["madera"],
                         {"dureza":3,"resistencia":5,"peso":2,"combustible":8,"brillo":0})
        self.assertEqual(MATERIALS["mineral oscuro"]["dureza"],9)
        self.assertEqual(MATERIAL_PHYSICS["madera"],{"density":.62,"permeability":.25})
        self.assertEqual(properties("arcilla")["permeability"],.35)
        self.assertEqual(RECOVERABILITY["piedra"],.90)
        self.assertEqual(set(MATERIAL_PHYSICS),set(MATERIALS))
        self.assertEqual(set(RECOVERABILITY),set(MATERIALS))

    def test_materials_in_independent_new_games(self):
        a=nilo.initial_state(7321)
        b=nilo.initial_state(7321)
        self.assertEqual(a["person"]["materials"],b["person"]["materials"])
        self.assertIsNot(a["person"]["materials"]["madera"],MATERIALS["madera"])
        a["person"]["materials"]["madera"]["dureza"]=999
        self.assertEqual(MATERIALS["madera"]["dureza"],3)
        self.assertEqual(b["person"]["materials"]["madera"]["dureza"],3)

    def test_terrain_and_aliases_preserved(self):
        self.assertEqual(TERRAINS["~"],"agua")
        self.assertEqual(YIELDS["v"],("cristal",1))
        self.assertEqual(GATHER_SOURCES["piedra"],"^r")
        self.assertEqual(gather_material(" afloramiento mineral "),"mineral oscuro")
        self.assertNotIn("~",PASSABLE)
        self.assertIn("T",PASSABLE)

    def test_legacy_forms_are_vocabulary_not_a_closed_recipe_list(self):
        self.assertIn("cuenco",FORMS["recipiente"])
        self.assertIn("martillo",PORTABLE_WORDS)
        self.assertIn("articulada",JOINTS)
        self.assertIn("rueda",SHAPES)

    def test_unknown_catalogue_filename_is_rejected(self):
        with self.assertRaises(ValueError):
            catalogo._read("../config.env")

    def test_invalid_physics_and_terrain_references_fail_closed(self):
        bad={"materials":{"x":{"world":{"dureza":1,"resistencia":1,
             "peso":1,"combustible":0,"brillo":0},
             "physics":{"density":float("nan"),"permeability":.2},
             "recoverability":.5}}}
        with self.assertRaises(ValueError):
            catalogo._validated_materials(bad)
        raw={"labels":{".":"suelo"},"yields":{".":["fantasma",1]},
             "gather_sources":{},"gather_aliases":{},"inspect_aliases":{},
             "passable":"."}
        with self.assertRaises(ValueError):
            catalogo._validated_terrain(raw,MATERIALS)

    def test_catalogue_is_packaged_explicitly(self):
        manifest=json.loads((ROOT/"MANIFIESTO_SHA256.json").read_text("utf8"))
        for name in ("catalogo.py","catalog/materiales.json","catalog/terrenos.json",
                     "catalog/objetos.json","tests/test_v059316.py"):
            self.assertIn(name,manifest["files"],name)

    def test_same_seed_preserves_world_generation(self):
        a=nilo.initial_state(7321)["world"]
        b=nilo.initial_state(7321)["world"]
        self.assertEqual(a,b)


class SpeedApi(unittest.TestCase):
    def test_the_same_modes_drive_api_and_engine(self):
        self.assertEqual(SUPPORTED_SPEEDS,(1,10,60,80))
        with tempfile.TemporaryDirectory() as tmp:
            sim=nilo.Simulation(db_path=Path(tmp)/"test.sqlite3")
            old=nilo.Handler.sim
            nilo.Handler.sim=sim
            server=ThreadingHTTPServer(("127.0.0.1",0),nilo.Handler)
            runner=threading.Thread(target=server.serve_forever,daemon=True)
            runner.start()
            base=f"http://127.0.0.1:{server.server_port}"
            def send(value):
                req=urllib.request.Request(base+"/api/settings",
                    json.dumps({"speed":value}).encode("utf-8"),
                    {"Content-Type":"application/json"}, method="POST")
                try:
                    with urllib.request.urlopen(req,timeout=3) as resp:
                        return resp.status,json.load(resp)
                except urllib.error.HTTPError as err:
                    return err.code,json.loads(err.read())
            try:
                self.assertEqual(send(80)[0],200)
                with urllib.request.urlopen(base+"/api/state",timeout=3) as resp:
                    state=json.load(resp)
                self.assertEqual(state["speed"],80)
                for invalid in (300,600,0,80.0,True,"80"):
                    status, _=send(invalid)
                    self.assertEqual(status,400,invalid)
                self.assertEqual(sim.s["speed"],80)
            finally:
                server.shutdown()
                server.server_close()
                runner.join(timeout=3)
                nilo.Handler.sim=old
                sim.conn.close()


class LlMTiming(unittest.TestCase):
    def test_new_installation_uses_15_second_minimum(self):
        with patch("brain.config",return_value=None):
            self.assertEqual(deliberation_interval_seconds({"MIN_REAL_SECONDS_BETWEEN_CALLS":"15"}),15)
        self.assertIn("MIN_REAL_SECONDS_BETWEEN_CALLS=15",
                      (ROOT/"config.env.example").read_text("utf8"))

    def test_invalid_or_excessive_intervals_do_not_disable_limit(self):
        for value, expected in [("5",10),("10",10),("23",23),
                                ("900",300),("nan",15),("no",15)]:
            self.assertEqual(deliberation_interval_seconds(
                {"MIN_REAL_SECONDS_BETWEEN_CALLS":value}),expected)

    def test_old_config_is_not_migrated_or_replaced(self):
        self.assertEqual(deliberation_interval_seconds(
            {"MIN_REAL_SECONDS_BETWEEN_CALLS":"60"}),60)
        self.assertIn("provider_health",nilo.initial_state())


if __name__ == "__main__":
    unittest.main()
