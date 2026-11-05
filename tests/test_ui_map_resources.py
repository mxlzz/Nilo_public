from ui_fixture import legacy_markup, legacy_html_path
"""Regresiones de la interfaz compacta y preferencias visuales."""
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

from interface_prefs import validate, load, save

ROOT = Path(__file__).resolve().parent.parent


class NodeScanner(HTMLParser):
    def __init__(self):
        super().__init__()
        self.nodes = {}
    def handle_starttag(self, tag, attrs):
        node = dict(attrs)
        if node.get("id"):
            self.nodes[node["id"]] = (tag, node)


class InterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = legacy_markup(Path(__file__).resolve().parents[1])
        cls.scan = NodeScanner()
        cls.scan.feed(cls.html)

    def test_toggle_map_replaces_three_choice_select(self):
        self.assertNotIn('id="map-display"', self.html)
        self.assertEqual(self.scan.nodes["map-toggle"][0], "button")
        self.assertEqual(self.scan.nodes["map-toggle"][1]["aria-controls"], "map-content")
        self.assertIn("el('map-toggle').onclick=", self.html)
        self.assertIn("if(mode==='map')mode='both'", self.html)
        self.assertIn("el('map-content').hidden=!visible", self.html)

    def test_map_references_are_collapsible_and_inside_map(self):
        self.assertEqual(self.scan.nodes["map-references"][0], "details")
        self.assertEqual(self.scan.nodes["legend"][0], "div")
        self.assertLess(self.html.index('id="map-content"'),
                        self.html.index('id="map-references"'))
        self.assertLess(self.html.index('id="map-references"'),
                        self.html.index('id="resources-body"'))

    def test_three_resource_tabs_reuse_all_existing_containers(self):
        for section, container in (("materials", "inventory"),
                                   ("tools", "tools"),
                                   ("buildings", "buildings")):
            tag, attr = self.scan.nodes["resource-tab-" + section]
            self.assertEqual(tag, "button")
            self.assertEqual(attr["role"], "tab")
            self.assertEqual(attr["aria-controls"], "resource-panel-" + section)
            self.assertEqual(self.scan.nodes["resource-panel-" + section][0], "section")
            self.assertIn(container, self.scan.nodes)
        self.assertIn("setResourceTab(resourceTab)", self.html)
        self.assertIn("el('resource-panel-'+button.dataset.resourceTab).hidden=!selected", self.html)

    def test_visual_themes_and_no_obsolete_navigation(self):
        for name in ("grises-oscuros", "grises-claros"):
            self.assertIn('<option value="' + name + '">', self.html)
            self.assertIn(':root[data-theme="' + name + '"]', self.html)
        self.assertIn("color-scheme:light", self.html)
        self.assertNotIn("record-navigation-back", self.html)
        self.assertIn('id="record-dialog-back"', self.html)


class PreferenceTests(unittest.TestCase):
    def test_legacy_map_only_migrates_to_visible_map(self):
        self.assertEqual(validate({"mapDisplay": "map"})["mapDisplay"], "both")

    def test_accepts_two_neutral_themes_and_resource_tab(self):
        self.assertEqual(validate({"theme": "grises-oscuros",
                                   "resources": "tools", "mapDisplay": "none"}),
                         {"theme": "grises-oscuros", "mapDisplay": "none",
                          "resources": "tools"})
        self.assertEqual(validate({"theme": "grises-claros"})["theme"],
                         "grises-claros")

    def test_invalid_tabs_are_ignored_without_changing_old_preferences(self):
        self.assertEqual(validate({"resources": "false", "theme": "bosque",
                                   "mapDisplay": "both"}),
                         {"theme": "bosque", "mapDisplay": "both"})

    def test_persist_settings_without_touching_world_state(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            given = {"theme": "grises-claros", "resources": "buildings",
                     "mapDisplay": "none"}
            self.assertEqual(save(root, given), given)
            self.assertEqual(load(root), given)
            self.assertFalse((root / "nilo_mundo.sqlite3").exists())


if __name__ == "__main__":
    unittest.main()
