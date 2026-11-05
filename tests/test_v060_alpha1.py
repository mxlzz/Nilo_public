"""0.6 alpha 1: ciclo físico de construcción, carga, ensayo y reforma."""
from __future__ import annotations

import random
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from action_contracts import before, classify
from brain import context_for
from capabilities import manifest
from cognitive_projection import project_context
from construction import apply_intervention
from environments import get_environment
from nilo import Simulation, initial_state
from structural_loads import load_limit
from world import execute_action


class StructuralLoadsTests(unittest.TestCase):
    def setUp(self):
        state = initial_state(7321)
        self.w, self.p = state["world"], state["person"]
        self.p["pos"] = [15, 10, 0]
        self.p["inventory"]["madera"] = 14
        self.p["inventory"]["piedra"] = 22
        self.rng = random.Random(17)

    def build(self, name="superficie sin función presupuesta"):
        step = {"op": "build", "name": name, "purpose": "observar efectos",
                "materials": ["madera", "madera"],
                "geometry": {"shape": "plataforma", "size": 2}}
        result = execute_action(self.w, self.p, step, self.rng)
        self.assertTrue(result[2], result[1])
        obj = self.w["structures"][-1]
        self.assertEqual(obj["geometry"]["shape"], "plataforma")
        return obj

    def interact(self, method, **details):
        step = {"op": "interact", "method": method, **details}
        return get_environment("isla_v1").perform_result(self.w, self.p, step, self.rng)

    def test_second_module_installed_without_new_operation(self):
        ids = {c["id"]: c for c in manifest()}
        self.assertEqual(set(ids), {"contenidos", "cargas_estructurales"})
        self.assertEqual(ids["cargas_estructurales"]["methods"],
                         ["depositar_carga", "recuperar_carga", "probar_carga"])

    def test_build_trial_deposit_recover_conserves_real_inventory(self):
        obj = self.build("mesa de prueba")
        start_inventory = self.p["inventory"]["piedra"]
        sample = self.interact("probar_carga", item=obj["id"],
                               material="piedra", quantity=2)
        self.assertEqual(sample.status, "verified_success", sample.facts)
        self.assertTrue(sample.physical["conditions"]["supported"])
        self.assertEqual(sample.physical["kind"], "capability")
        self.assertEqual(sample.physical["conditions"]["revision"], 1)
        self.assertEqual(self.p["inventory"]["piedra"], start_inventory)
        self.assertFalse(obj.get("cargas_almacenadas"))
        self.assertEqual(len(obj["ensayos_de_carga"]), 1)

        deposit = self.interact("depositar_carga", item=obj["id"],
                                material="piedra", quantity=2)
        self.assertEqual(deposit.status, "verified_success")
        self.assertEqual(obj["cargas_almacenadas"], {"piedra": 2})
        self.assertEqual(self.p["inventory"]["piedra"], start_inventory - 2)
        self.assertEqual(deposit.physical["conditions"]["before"]["source"], start_inventory)
        self.assertEqual(deposit.physical["conditions"]["after"]["destination"], 2)

        retrieve = self.interact("recuperar_carga", item=obj["id"],
                                 material="piedra", quantity=2)
        self.assertEqual(retrieve.status, "verified_success")
        self.assertEqual(obj["cargas_almacenadas"], {})
        self.assertEqual(self.p["inventory"]["piedra"], start_inventory)

    def test_negative_trial_is_real_evidence_not_an_error(self):
        obj = self.build()
        before_inventory = deepcopy(self.p["inventory"])
        trial = self.interact("probar_carga", item=obj["id"],
                              material="piedra", quantity=8)
        self.assertEqual(trial.status, "verified_success")
        self.assertFalse(trial.physical["conditions"]["supported"])
        self.assertEqual(before_inventory, self.p["inventory"])
        self.assertEqual(obj.get("cargas_almacenadas"), None)
        report = classify(self.w, self.p, {"op": "interact", "method": "probar_carga"},
                          before(self.w, self.p, {}), trial)
        self.assertEqual(report["code"], "carga_estatica_ensayada")

    def test_rename_does_not_modify_material_capacity(self):
        obj = self.build("puente futurista")
        renamed = deepcopy(obj)
        renamed["name"] = "cabaña de piedra imaginaria"
        renamed["purpose"] = "volar"
        renamed["category"] = "habitaculo"
        self.assertEqual(load_limit(obj, self.p), load_limit(renamed, self.p))
        weaker = deepcopy(obj)
        weaker["geometry"]["shape"] = "hueco"
        self.assertLess(load_limit(weaker, self.p), load_limit(obj, self.p))
        longer = deepcopy(obj)
        longer["geometry"]["size"] = 4
        self.assertLess(load_limit(longer, self.p), load_limit(obj, self.p))

    def test_invalid_deposit_never_mutates_inventory_or_structure(self):
        obj = self.build()
        initial = deepcopy(self.p["inventory"])
        for qty in (0, -1, 1.1, True, 100, float("nan"), "abc"):
            report = self.interact("depositar_carga", item=obj["id"],
                                   material="piedra", quantity=qty)
            self.assertEqual(report.status, "precondition_failed", (qty,report.facts))
            self.assertEqual(self.p["inventory"], initial)
            self.assertFalse(obj.get("cargas_almacenadas"))
        # Excede el limite físico, aun cuando hay material disponible.
        over = self.interact("depositar_carga", item=obj["id"],
                             material="piedra", quantity=5)
        self.assertEqual(over.status, "precondition_failed")
        self.assertEqual(self.p["inventory"], initial)

    def test_modify_changes_limit_and_prevents_destroying_stored_load(self):
        obj = self.build()
        self.assertEqual(load_limit(obj, self.p), 10.0)
        self.assertEqual(self.interact("depositar_carga", item=obj["id"],
                                       material="piedra", quantity=3).status, "verified_success")
        inv = deepcopy(self.p["inventory"])
        original_revision = obj["revision"]
        part = obj["components"][0]["id"]
        rejected = apply_intervention(self.w, self.p,
                    {"op": "modify", "item": obj["id"], "mode": "remove", "component": part})
        self.assertFalse(rejected[2])
        self.assertIn("capacidad", rejected[1][0])
        self.assertEqual(inv, self.p["inventory"])
        self.assertEqual(obj["revision"], original_revision)
        self.assertEqual(len(obj["components"]), 2)
        self.assertFalse(apply_intervention(self.w, self.p,
                         {"op": "dismantle", "item": obj["id"]})[2])

        changed = apply_intervention(self.w, self.p,
                    {"op": "modify", "item": obj["id"], "mode": "add",
                     "materials": ["madera", "madera"]})
        self.assertTrue(changed[2], changed[1])
        self.assertEqual(obj["revision"], original_revision+1)
        self.assertEqual(load_limit(obj, self.p), 20.0)
        self.assertEqual(obj["cargas_almacenadas"]["piedra"], 3)
        new_trial = self.interact("probar_carga", item=obj["id"],
                                  material="piedra", quantity=4)
        self.assertTrue(new_trial.physical["conditions"]["supported"])
        self.assertEqual(obj["ensayos_de_carga"][-1]["revision"], 2)

    def test_rejects_unknown_remote_and_incompatible_capability(self):
        obj = self.build()
        inv = deepcopy(self.p["inventory"])
        self.assertEqual(self.interact("depositar_carga", item="no-existe",
                                      material="piedra").status, "precondition_failed")
        self.p["pos"] = [5, 5, 0]
        self.assertEqual(self.interact("depositar_carga", item=obj["id"],
                                      material="piedra").status, "precondition_failed")
        self.p["pos"] = [15, 10, 0]
        self.w["capability_versions"]["cargas_estructurales"] = "0.0.9"
        result = self.interact("depositar_carga", item=obj["id"], material="piedra")
        self.assertEqual(result.status, "verified_failure")
        self.assertEqual(inv, self.p["inventory"])
        self.assertFalse(obj.get("cargas_almacenadas"))

    def test_visible_context_does_not_reveal_unmeasured_limit(self):
        obj = self.build()
        raw = context_for(self.w, self.p, [], "Día 1")
        view = project_context(raw)
        row = next(row for row in view["construcciones_fijas"] if row["id"]==obj["id"])
        self.assertEqual(row["materiales_almacenados"], {})
        self.assertEqual(row["ensayos_de_carga"], [])
        self.assertNotIn("load_limit", str(row))
        self.interact("probar_carga", item=obj["id"], material="piedra", quantity=2)
        view = project_context(context_for(self.w, self.p, [], "Día 1"))
        row = next(row for row in view["construcciones_fijas"] if row["id"]==obj["id"])
        self.assertTrue(row["ensayos_de_carga"][-1]["supported"])
        self.assertEqual(row["ensayos_de_carga"][-1]["limit"], 10.0)


class PersistenceTests(unittest.TestCase):
    def test_load_and_module_version_survive_sqlite_reopen(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "nilo.sqlite3"
            sim = Simulation(db_path=path)
            try:
                p, w = sim.s["person"], sim.s["world"]
                p["inventory"]["madera"] = 4
                p["inventory"]["piedra"] = 3
                built = execute_action(w, p, {"op": "build", "name": "apoyo persistente",
                    "materials": ["madera", "madera"],
                    "geometry": {"shape": "plataforma", "size": 2}}, random.Random(1))
                self.assertTrue(built[2])
                ident = w["structures"][-1]["id"]
                stored = get_environment("isla_v1").perform_result(w, p,
                    {"op": "interact", "method": "depositar_carga",
                     "item": ident, "material": "piedra", "quantity": 2}, random.Random(1))
                self.assertEqual(stored.status, "verified_success", stored.facts)
                sim.write()
            finally:
                sim.conn.close()
            resumed = Simulation(db_path=path)
            try:
                obj = next(o for o in resumed.s["world"]["structures"] if o["id"] == ident)
                self.assertEqual(obj["cargas_almacenadas"], {"piedra": 2})
                self.assertEqual(resumed.s["person"]["inventory"]["piedra"], 1)
                self.assertEqual(resumed.s["world"]["capability_versions"]["cargas_estructurales"], "1.0.0")
            finally:
                resumed.conn.close()


if __name__ == "__main__":
    unittest.main()
