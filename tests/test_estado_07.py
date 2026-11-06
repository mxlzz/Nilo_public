"""Paso 02 de Nilo 0.7: esquema v5, vistas tipadas, carga y serialización."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from nilo import Simulation, initial_state
from nilo_runtime.application.bootstrap import initial_state as new_initial_state
from nilo_runtime.core.state import (
    SAVE_SCHEMA_VERSION,
    StateSchemaError,
    snapshot_state,
    validate_current_state,
    validate_loaded_envelope,
)
from island_views import map_snapshot


def saved_json(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


class DomainStateTests(unittest.TestCase):
    def test_bootstrap_is_unique_source_and_keeps_save_v5_shape(self):
        self.assertIs(initial_state, new_initial_state)
        with patch("nilo_runtime.application.bootstrap.time.time", return_value=1700000000):
            a = initial_state(7321)
            b = new_initial_state(7321)
        self.assertEqual(a, b)
        self.assertEqual(a["version"], SAVE_SCHEMA_VERSION)
        self.assertEqual(a["scenario_id"], "territorio_desconocido")
        self.assertEqual(a["person"]["pos"], [15, 10, 0])
        self.assertIn("0", a["world"]["levels"])
        self.assertNotIn("save_schema_version", a)  # no alterar fingerprint de 0.6.4
        self.assertNotIn("ui", a)

    def test_typing_preserves_unknown_fields_and_exact_json_roundtrip(self):
        state = initial_state()
        state["extension_legacy"] = {"variables": ["valor", {"cantidad": 2}]}
        state["person"]["observations"].append(
            {"text": "vi una roca", "id": "obs-1", "hipotesis": False}
        )
        state["person"]["research"].append(
            {"id": "hip-1", "question": "¿El material resiste?", "evidence": []}
        )
        state["person"]["measurements"] = [{"id": "med-1", "metric": 3.2}]
        state["person"]["knowledge"]["madera"] = {"base": "experiencia"}
        before = saved_json(state)
        view = snapshot_state(state)
        self.assertEqual(view.schema_version, 5)
        self.assertEqual(view.world.seed, 7321)
        self.assertEqual(view.actor.position, (15, 10, 0))
        self.assertEqual(view.actor.observations[0]["id"], "obs-1")
        self.assertEqual(view.actor.research[0]["id"], "hip-1")
        self.assertEqual(view.actor.measurements[0]["id"], "med-1")
        self.assertEqual(view.actor.knowledge["madera"]["base"], "experiencia")
        self.assertEqual(saved_json(view.to_legacy()), before)
        self.assertEqual(saved_json(state), before)

    def test_nested_view_is_immutable_and_detached_from_live_state(self):
        state = initial_state()
        view = snapshot_state(state)
        with self.assertRaises(TypeError):
            view.data["world"] = {}
        with self.assertRaises(TypeError):
            view.actor.inventory["madera"] = 100
        with self.assertRaises(TypeError):
            view.world.levels["0"][0] = "otro"
        state["person"]["inventory"]["madera"] = 25
        state["world"]["levels"]["0"][0] = "x" * 37
        self.assertEqual(view.actor.inventory["madera"], 1)
        self.assertNotEqual(view.world.levels["0"][0], "x" * 37)
        copy = view.to_legacy()
        copy["world"]["levels"]["0"][0] = "z" * 37
        self.assertNotEqual(view.world.levels["0"][0], "z" * 37)

    def test_current_validation_rejects_corrupt_values_without_repair(self):
        cases = [
            ("position_bool", lambda s: s["person"].update(pos=[True, 10, 0])),
            ("inventory_negative", lambda s: s["person"]["inventory"].update(madera=-2)),
            ("clock_nan", lambda s: s["person"].update(clock_minutes=float("nan"))),
            ("world_levels", lambda s: s["world"].update(levels=[])),
            ("version", lambda s: s.update(version=6)),
            ("paused", lambda s: s.update(paused="sí")),
        ]
        for name, make_invalid in cases:
            with self.subTest(name=name):
                state = initial_state()
                make_invalid(state)
                before = saved_json(state)
                with self.assertRaises(StateSchemaError):
                    validate_current_state(state, strict_physics=True)
                self.assertEqual(saved_json(state), before)

    def test_bad_inventory_is_visible_to_diagnostic_without_blocking_save(self):
        state = initial_state()
        state["person"]["inventory"]["piedra"] = -2
        validate_current_state(state)  # esquema legible; la física lo diagnostica
        with self.assertRaises(StateSchemaError):
            validate_current_state(state, strict_physics=True)
        self.assertEqual(snapshot_state(state).actor.inventory["piedra"], -2)

    def test_other_environments_need_not_use_island_levels(self):
        state = initial_state()
        state["world"] = {"seed": 14, "abi": "entorno-prueba"}
        validate_current_state(state)
        view = snapshot_state(state)
        self.assertEqual(view.world.seed, 14)
        self.assertEqual(view.world.levels, {})
        self.assertEqual(view.to_legacy()["world"], state["world"])

    def test_old_save_without_scenario_can_still_be_serialized(self):
        state = initial_state()
        state.pop("scenario_id")
        validate_current_state(state)
        view = snapshot_state(state)
        self.assertIsNone(view.scenario_id)
        self.assertNotIn("scenario_id", view.to_legacy())

    def test_future_save_rejected_without_downgrade(self):
        state = initial_state()
        state["version"] = 7
        saved = deepcopy(state)
        with self.assertRaises(StateSchemaError):
            validate_loaded_envelope(state)
        self.assertEqual(state, saved)
        for legacy in ({**state, "version": 0}, {k: v for k, v in state.items() if k != "version"}):
            validate_loaded_envelope(legacy)

    def test_map_rendering_no_longer_mutates_unenriched_structure(self):
        state = initial_state()
        w, p = state["world"], state["person"]
        w["structures"].append(
            {"id": "obra-prueba", "name": "cobertizo", "pos": [15, 10, 0],
             "purpose": "observación", "materials": ["madera"], "resistance": 2}
        )
        before = deepcopy(w)
        projection = map_snapshot(w, p)
        self.assertEqual(w, before)
        rendered = projection["structure_layers"]["0"]["15,10"]
        self.assertEqual(rendered["category"], "habitaculo")
        self.assertNotIn("category", w["structures"][0])
        rendered["materials"].append("piedra")
        self.assertEqual(w["structures"][0]["materials"], ["madera"])

    def test_public_state_read_does_not_enrich_live_structures(self):
        with tempfile.TemporaryDirectory(prefix="nilo-state-public-") as directory:
            sim = Simulation(db_path=Path(directory) / "sim.sqlite3")
            try:
                sim.s["world"]["structures"].append({
                    "id": "obra-sin-metadatos", "name": "cobertizo",
                    "pos": [15, 10, 0], "purpose": "ensayo",
                    "materials": ["madera"], "resistance": 2,
                })
                original = deepcopy(sim.s)
                response = sim.public_state()
                self.assertEqual(sim.s, original)
                self.assertIn("structure_layers", response)
                self.assertEqual(
                    response["structure_layers"]["0"]["15,10"]["category"],
                    "habitaculo",
                )
            finally:
                sim.conn.close()

    def test_corrupt_snapshot_does_not_reset_world(self):
        with tempfile.TemporaryDirectory(prefix="nilo-corrupt-save-") as directory:
            db = Path(directory) / "corrupt.sqlite3"
            sim = Simulation(db_path=db, world_seed=7321)
            sim.conn.close()
            corrupt = '{"version":5,"person":'
            with sqlite3.connect(db) as conn:
                conn.execute("UPDATE snapshot SET payload=? WHERE id=1", (corrupt,))
            with self.assertRaises(StateSchemaError):
                Simulation(db_path=db, world_seed=7321)
            with sqlite3.connect(db) as conn:
                persisted = conn.execute("SELECT payload FROM snapshot WHERE id=1").fetchone()[0]
            self.assertEqual(persisted, corrupt)

    def test_future_snapshot_rejected_before_schema_downgrade(self):
        with tempfile.TemporaryDirectory(prefix="nilo-future-save-") as directory:
            db = Path(directory) / "future.sqlite3"
            sim = Simulation(db_path=db, world_seed=7321)
            future = deepcopy(sim.s)
            sim.conn.close()
            future["version"] = SAVE_SCHEMA_VERSION + 1
            encoded = saved_json(future)
            with sqlite3.connect(db) as conn:
                conn.execute("UPDATE snapshot SET payload=? WHERE id=1", (encoded,))
            with self.assertRaisesRegex(StateSchemaError, "esquema 6"):
                Simulation(db_path=db, world_seed=7321)
            with sqlite3.connect(db) as conn:
                persisted = conn.execute("SELECT payload FROM snapshot WHERE id=1").fetchone()[0]
            self.assertEqual(persisted, encoded)

    def test_simulation_load_write_uses_schema_and_read_only_snapshot(self):
        with tempfile.TemporaryDirectory(prefix="nilo-state-07-") as directory:
            db = Path(directory) / "partida.sqlite3"
            sim = Simulation(db_path=db, world_seed=7321, rng_seed=9821)
            try:
                sim.s["person"]["observations"].append(
                    {"id": "obs-07", "result": "sólo percibí una piedra"}
                )
                before = deepcopy(sim.s)
                typed = sim.domain_snapshot()
                self.assertEqual(sim.s, before)
                self.assertEqual(typed.actor.observations[-1]["id"], "obs-07")
                sim.write()
                with sqlite3.connect(db) as conn:
                    payload = json.loads(conn.execute(
                        "SELECT payload FROM snapshot WHERE id=1").fetchone()[0])
                self.assertEqual(payload["person"]["observations"][-1]["id"], "obs-07")
                self.assertEqual(payload["version"], 5)
            finally:
                sim.conn.close()


if __name__ == "__main__":
    unittest.main()
