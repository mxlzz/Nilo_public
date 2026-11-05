"""Frontera espacial de Nilo 0.5.8.1: isla_v1 sin dependencia en Simulation."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from environments import IslandEnvironment
from island_views import map_snapshot, survival_conditions
from nilo import Simulation
from world import new_world, set_tile, tile_key


class SpatialBoundary(unittest.TestCase):
    def test_survival_conditions_match_shelter_and_water_rules(self):
        world = new_world(7321)
        person = {"pos": [15, 10, 0]}
        self.assertEqual(survival_conditions(world, person), (True, False))
        person["pos"] = [15, 11, 0]
        set_tile(world, 16, 11, 0, "~")
        self.assertEqual(survival_conditions(world, person), (False, True))
        world["structures"].append({
            "pos": [15, 11, 0],
            "category": "habitaculo",
            "shelter_condition": "insuficiente",
        })
        self.assertEqual(survival_conditions(world, person), (False, True))
        world["structures"][0]["shelter_condition"] = "apto"
        self.assertEqual(survival_conditions(world, person), (True, True))
        person["pos"] = [15, 11, -1]
        self.assertFalse(survival_conditions(world, person)[1])

    def test_map_is_multilayer_with_unseen_tiles_hidden(self):
        world = new_world(7321)
        person = {"pos": [15, 10, 0]}
        old_reveal = list(world["revealed"])
        projection = map_snapshot(world, person)
        self.assertEqual((projection["w"], projection["h"]), (37, 21))
        self.assertEqual(projection["map"][10][15], "@")
        self.assertEqual(projection["maps"]["0"][10][15], "@")
        self.assertEqual(projection["maps"]["-1"][10][15], " ")
        self.assertEqual(projection["maps"]["0"][0][0], " ")
        self.assertEqual(world["revealed"], old_reveal)
        self.assertEqual(projection["level"], "Superficie")

    def test_all_structures_at_a_location_are_preserved(self):
        world = new_world(7321)
        first = {"name": "refugio 1", "pos": [16, 10, 0],
                 "materials": ["madera"], "resistance": 4,
                 "purpose": "ensayo", "category": "estructura"}
        second = {"name": "refugio 2", "pos": [16, 10, 0],
                  "materials": ["piedra"], "resistance": 4,
                  "purpose": "ensayo", "category": "estructura"}
        world["structures"].extend([first, second])
        projection = map_snapshot(world, {"pos": [15, 10, 0]})
        self.assertEqual(len(projection["structure_cell_lists"]["0"]["16,10"]), 2)
        self.assertEqual(projection["structure_cells"]["16,10"]["name"], "refugio 1")
        self.assertNotEqual(projection["maps"]["0"][10][16], " ")

    def test_environment_delegates_to_island_specific_view(self):
        environment = IslandEnvironment()
        world = new_world(7321)
        person = {"pos": [15, 10, 0]}
        self.assertEqual(environment.surroundings(world, person),
                         survival_conditions(world, person))
        self.assertEqual(environment.render_map(world, person),
                         map_snapshot(world, person))

    def test_public_state_uses_environment_projection(self):
        with tempfile.TemporaryDirectory() as directory:
            sim = Simulation(db_path=Path(directory) / "test.sqlite")
            try:
                original = sim.public_state()
                fields = (
                    "map", "maps", "w", "h", "level", "legend", "trail",
                    "trail_layers", "structure_cells", "structure_layers",
                    "structure_cell_lists",
                )
                projected = sim.environment.render_map(
                    sim.s["world"], sim.s["person"]
                )
                for field in fields:
                    self.assertEqual(original[field], projected[field])
                with patch.object(IslandEnvironment, "render_map",
                                  return_value={**projected, "level": "Prueba"}):
                    self.assertEqual(sim.public_state()["level"], "Prueba")
            finally:
                sim.conn.close()

    def test_tick_observes_conditions_through_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            sim = Simulation(db_path=Path(directory) / "test.sqlite")
            try:
                sim.s["planning"] = True  # No deliberación externa
                with patch.object(IslandEnvironment, "surroundings",
                                  return_value=(True, False)) as observe:
                    sim.tick(1)
                    observe.assert_called()
                    self.assertEqual(observe.call_args.args[0], sim.s["world"])
            finally:
                sim.conn.close()


if __name__ == "__main__":
    unittest.main()
