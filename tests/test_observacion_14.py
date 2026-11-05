"""Etapa 14: las observaciones no mutan estado ni anticipan información."""
from __future__ import annotations

from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
import tempfile
from pathlib import Path
import unittest

import brain
import world
from cognitive_projection import project_context
from island_views import map_snapshot, survival_conditions
from nilo import Simulation, initial_state
from nilo_runtime.perception.island import adjacent_terrain, visible_structures, world_view
from nilo_runtime.perception.objects import desgaste_observable
from nilo_runtime.worlds.island import set_tile, tile_key


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                        ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


class Observacion14(unittest.TestCase):
    def setUp(self):
        state = initial_state(7321)
        self.w, self.p = state["world"], state["person"]
        # Una estructura a la vista y otra real pero todavía desconocida.
        self.seen = [15, 10, 0]
        self.hidden = [30, 18, 0]
        self.w["structures"] = [
            {"id": "obra-conocida", "name": "taller", "pos": self.seen,
             "materials": ["madera"], "category": "habitaculo"},
            {"id": "SECRETO-14", "name": "OBRA-OCULTA-14", "pos": self.hidden,
             "materials": ["mineral oscuro"], "category": "laboratorio"},
        ]
        self.assertIn(tile_key(*self.seen), self.w["revealed"])
        self.assertNotIn(tile_key(*self.hidden), self.w["revealed"])

    def test_only_visible_structures_and_detached_copies(self):
        structures = visible_structures(self.w)
        self.assertEqual([v["id"] for v in structures], ["obra-conocida"])
        structures[0]["name"] = "mutación de copia"
        self.assertEqual(self.w["structures"][0]["name"], "taller")

    def test_map_all_layers_and_metadata_hide_unknown_structures(self):
        before = digest(self.w)
        m = map_snapshot(self.w, self.p)
        self.assertEqual(digest(self.w), before)
        self.assertIn("15,10", m["structure_cells"])
        self.assertNotIn("30,18", m["structure_layers"]["0"])
        self.assertNotIn("30,18", m["structure_cell_lists"]["0"])
        self.assertNotIn("SECRETO-14", json.dumps(m))
        self.assertEqual(m["maps"]["0"][18][30], " ")
        self.assertEqual(m["maps"]["-1"][18][30], " ")
        m["structure_cells"]["15,10"]["name"] = "mutación UI"
        self.assertEqual(self.w["structures"][0]["name"], "taller")

    def test_perception_has_no_hidden_buildings_or_terrain(self):
        before = digest({"world": self.w, "person": self.p})
        c = brain.context_for(self.w, self.p, [], "Día 1")
        payload = project_context(c)
        data = json.dumps(payload, ensure_ascii=False)
        self.assertNotIn("SECRETO-14", data)
        self.assertNotIn("OBRA-OCULTA-14", data)
        self.assertIn("obra-conocida", data)
        self.assertEqual(before, digest({"world": self.w, "person": self.p}))

    def test_unknown_neighbour_not_reported_from_internal_grid(self):
        x, y, z = self.p["pos"]
        target = tile_key(x + 1, y, z)
        self.w["revealed"] = [k for k in self.w["revealed"] if k != target]
        set_tile(self.w, x + 1, y, z, "v")
        view = adjacent_terrain(self.w, self.p)
        entry = next(v for v in view if (v["x"],v["y"])==(x+1,y))
        self.assertEqual(entry["tipo"], " ")
        c = brain.context_for(self.w, self.p, [], "Día 1")
        entry = next(v for v in c["adyacentes"] if (v["x"],v["y"])==(x+1,y))
        self.assertEqual(entry["tipo"], " ")
        self.assertFalse(any(v["pos"] == [x+1,y] for v in world_view(self.w, self.p)))

    def test_reveal_only_changes_projection_not_physics(self):
        before = deepcopy(self.w)
        first = map_snapshot(self.w, self.p)
        self.w["revealed"].append(tile_key(*self.hidden))
        second = map_snapshot(self.w, self.p)
        self.assertNotIn("30,18", first["structure_cells"])
        self.assertIn("30,18", second["structure_cells"])
        self.assertEqual(self.w["structures"], before["structures"])

    def test_inspection_of_hidden_building_does_not_leak_id_or_name(self):
        ok, facts = world.inspect_target(self.w, self.p,
                                         {"op": "inspect", "target": "OBRA-OCULTA-14"})
        self.assertFalse(ok)
        self.assertNotIn("SECRETO-14", " ".join(facts))
        self.assertNotIn("(30,18", " ".join(facts))

    def test_inspection_wear_uses_sensation_not_engine_score(self):
        self.p["items"] = [{"id":"pieza-14","name":"herramienta",
                             "form":"punta","durability":48,"materials":["madera"]}]
        ok, facts = world.inspect_target(self.w, self.p,
                                         {"op":"inspect","target":"pieza-14"})
        self.assertTrue(ok)
        self.assertIn("desgaste apreciable", " ".join(facts))
        self.assertNotIn("48%", " ".join(facts))
        self.assertEqual(desgaste_observable(float("nan")), "estado de desgaste desconocido")
        self.assertEqual(desgaste_observable(float("inf")), "estado de desgaste desconocido")

    def test_no_render_migration_of_history_or_shelter_claims(self):
        before = digest({"world": self.w, "person": self.p})
        for _ in range(3):
            map_snapshot(self.w,self.p)
            survival_conditions(self.w,self.p)
            brain.context_for(self.w,self.p,[],"Día 1")
        self.assertEqual(before,digest({"world": self.w,"person": self.p}))

    def test_parallel_and_repeated_reading_leaves_exact_state(self):
        before = digest({"world": self.w, "person": self.p})
        def read(_):
            m = map_snapshot(self.w, self.p)
            nearby = adjacent_terrain(self.w, self.p)
            return digest({"map":m, "adjacent":nearby,
                           "survival":survival_conditions(self.w, self.p)})
        with ThreadPoolExecutor(max_workers=6) as pool:
            hashes = list(pool.map(read, range(40)))
        self.assertEqual(len(set(hashes)), 1)
        self.assertEqual(before, digest({"world": self.w, "person": self.p}))

    def test_public_endpoint_does_not_emit_hidden_structures(self):
        with tempfile.TemporaryDirectory() as directory:
            sim = Simulation(db_path=Path(directory)/"nilo.sqlite3")
            try:
                sim.s["world"]["structures"] = deepcopy(self.w["structures"])
                snap = digest(sim.s)
                result = sim.public_state()
                self.assertEqual(snap, digest(sim.s))
                self.assertEqual([r["id"] for r in result["structures"]],["obra-conocida"])
                self.assertNotIn("SECRETO-14",json.dumps(result,ensure_ascii=False))
            finally:
                sim.conn.close()


if __name__ == "__main__":
    unittest.main()
