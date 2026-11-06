"""Regresión de frontera de planificación y representación configurable (0.5.8.2)."""
from __future__ import annotations
from ui_fixture import legacy_markup, legacy_html_path

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from html.parser import HTMLParser

from environments import IslandEnvironment
from nilo import Simulation


class PlanningBoundary(unittest.TestCase):
    def make_sim(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        sim = Simulation(db_path=Path(self.tmp.name) / "test.sqlite")
        self.addCleanup(sim.conn.close)
        return sim

    def test_validation_goes_through_environment(self):
        sim = self.make_sim()
        step = {"op": "go", "x": 15, "y": 11}
        with patch.object(IslandEnvironment, "validate_plan",
                          return_value=[step]) as validate:
            self.assertEqual(sim.validate_plan([step]), [step])
        self.assertEqual(validate.call_args.args[0], sim.s["world"])
        self.assertEqual(validate.call_args.args[1], sim.s["person"])
        self.assertEqual(validate.call_args.args[2], [step])

    def test_refuses_hidden_destination_without_terrain_oracle(self):
        sim = self.make_sim()
        before = sim.s["world"]["revealed"][:]
        rejected = sim.validate_plan([{"op": "go", "x": 0, "y": 2}])
        self.assertEqual(rejected, [])
        self.assertEqual(sim.s["world"]["revealed"], before)
        self.assertTrue(sim.s["person"].get("strategy_feedback"))

    def test_can_prevalidate_gather_then_craft_sequence(self):
        sim = self.make_sim()
        steps = [
            {"op": "gather", "target": "madera"},
            {"op": "craft", "name": "mazo", "materials": ["madera"]},
        ]
        self.assertEqual(sim.validate_plan(steps), steps)

    def test_redundant_proven_experiment_filtered(self):
        sim = self.make_sim()
        sim.s["person"]["knowledge"]["madera|golpear"] = "observación comprobada"
        steps = [{"op": "experiment", "target": "madera", "method": "golpear"},
                 {"op": "inspect", "target": "madera"}]
        with patch.object(IslandEnvironment, "improve_plan",
                          wraps=sim.environment.improve_plan) as prune:
            accepted = sim.improve_plan(steps)
        self.assertEqual(accepted, [steps[1]])
        prune.assert_called_once()
        self.assertTrue(sim.s["person"].get("strategy_feedback"))

    def test_validation_does_not_mutate_input_steps(self):
        sim = self.make_sim()
        raw = [{"op": "inspect", "target": "piedra"}]
        result = sim.validate_plan(raw)
        self.assertEqual(result, raw)
        self.assertIsNot(result[0], raw[0])


class ThemeSelectParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_theme = False
        self.theme_options = []
        self.found_select = False

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "select" and attributes.get("id") == "theme-select":
            self.in_theme = True
            self.found_select = True
        elif tag == "option" and self.in_theme:
            self.theme_options.append(attributes.get("value"))

    def handle_endtag(self, tag):
        if tag == "select":
            self.in_theme = False


class ThemeBoundary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.markup = legacy_markup(Path(__file__).resolve().parents[1])

    def test_five_persistent_local_themes(self):
        parsed = ThemeSelectParser()
        parsed.feed(self.markup)
        self.assertTrue(parsed.found_select)
        self.assertEqual(parsed.theme_options, ["bosque", "grafito", "terracota", "grises-oscuros", "grises-claros"])
        self.assertIn("localStorage", self.markup)
        self.assertIn("nilo.theme.v1", self.markup)
        self.assertIn('document.documentElement.dataset.theme=theme', self.markup)

    def test_solid_tiles_contrast_separately_from_ground(self):
        css = self.markup.split("</style>", 1)[0]
        for token in ("--rock-bg:", "--wall-bg:", "--floor-color:",
                      "--grass-color:", "--sand-color:", "--map-grid:"):
            self.assertIn(token, css)
        self.assertIn(".tile.t-rock{color:var(--rock-color);background:var(--rock-bg)", css)
        self.assertIn(".tile.t-wall{color:var(--wall-color);background:var(--wall-bg)", css)
        self.assertIn(".tile.t-grass{color:var(--grass-color);font-weight:400}", css)

    def test_theme_is_local_visual_preference_only(self):
        self.assertIn("saveLocal('nilo.theme.v1',theme)", self.markup)
        self.assertIn('document.documentElement.dataset.theme=theme', self.markup)
        self.assertNotIn("settings({theme:", self.markup)


if __name__ == "__main__":
    unittest.main()
