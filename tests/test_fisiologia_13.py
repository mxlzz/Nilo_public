"""Etapa 13 · Necesidades corporales y descanso: física e invariantes."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import math
import random
import tempfile
import unittest
from unittest.mock import patch

import bodily_policy
import survival
import world
from experiment_log import capture, sheltered as measured_shelter
from island_views import survival_conditions
from nilo import initial_state, Simulation
from nilo_runtime.physiology import needs as physiological_needs
from nilo_runtime.physiology import policy
from nilo_runtime.worlds.island import set_tile
from nilo_runtime.worlds.shelter import sheltered, shelter_properties


def actor(energy=50, thirst=70, hunger=70):
    return {
        "pos":[15,10,0],"clock_minutes":0,
        "needs":{"energia":energy,"hidratacion":thirst,"nutricion":hunger,
                 "abrigo":80,"seguridad":68},
        "inventory":{"alimento":2},"items":[],
    }


class ShelterWithoutLabels13(unittest.TestCase):
    def setUp(self):
        self.w=world.new_world(7321)
        self.p=actor()

    def test_original_map_shelter_is_a_terrain_fact(self):
        evidence=shelter_properties(self.w,self.p["pos"])
        self.assertEqual(evidence["status"],"verified")
        self.assertTrue(evidence["sheltered"])
        self.assertEqual(evidence["source"],"terrain")
        self.assertTrue(measured_shelter(self.w,self.p))
        self.assertEqual(survival_conditions(self.w,self.p)[0],True)

    def test_text_label_category_and_purpose_do_not_enable_cover(self):
        self.p["pos"]=[14,10,0]
        set_tile(self.w,14,10,0,".")
        base={"id":"obra-identica","pos":[14,10,0],"materials":["madera"]*8,
              "resistance":9,"category":"habitaculo",
              "shelter_condition":"cubierto_parcialmente",
              "geometry":{"shape":"hueco","size":8},
              "components":[{"id":f"c{i}","material":"madera","condition":1}
                            for i in range(8)]}
        snapshots=[]
        for name,purpose,category in (
            ("refugio bien equipado","dormir seguro","habitaculo"),
            ("laboratorio experimental","trabajar","prototipo"),
            ("objeto sin significado","cualquier cosa","deposito"),
        ):
            structure=dict(base,name=name,purpose=purpose,category=category)
            self.w["structures"]=[structure]
            conditions=survival_conditions(self.w,self.p)
            snapshots.append((conditions,measured_shelter(self.w,self.p),
                              shelter_properties(self.w,self.p["pos"])))
        self.assertEqual(snapshots[0],snapshots[1])
        self.assertEqual(snapshots[0],snapshots[2])
        self.assertFalse(snapshots[0][0][0])
        self.assertEqual(snapshots[0][2]["status"],"no_evaluable")

    def test_self_declared_verified_shelter_property_is_not_accepted(self):
        self.p["pos"]=[14,10,0]
        set_tile(self.w,14,10,0,".")
        self.w["structures"]=[{"id":"fake","name":"cabaña","pos":[14,10,0],
                                 "shelter_properties":{"status":"verified",
                                                       "sheltered":True}}]
        outcome=shelter_properties(self.w,self.p["pos"])
        self.assertFalse(outcome["sheltered"])
        self.assertEqual(outcome["status"],"no_evaluable")

    def test_name_change_does_not_remove_terrain_shelter(self):
        self.w["structures"]=[{"id":"fake","name":"refugio","pos":[15,10,0],
                                  "category":"prototipo","shelter_condition":"insuficiente"}]
        before=survival_conditions(self.w,self.p)
        self.w["structures"][0]["name"]="objeto abstracto"
        self.w["structures"][0]["category"]="laboratorio"
        self.assertEqual(survival_conditions(self.w,self.p),before)
        self.assertTrue(before[0])

    def test_legacy_visual_condition_no_longer_counts_as_physical(self):
        self.p["pos"]=[14,10,0]
        set_tile(self.w,14,10,0,".")
        self.w["structures"]=[{"id":"legacy","name":"refugio heredado",
                                "pos":[14,10,0],"category":"habitaculo",
                                "shelter_condition":"cubierto_parcialmente"}]
        self.assertFalse(sheltered(self.w,self.p["pos"]))
        self.assertEqual(shelter_properties(self.w,self.p["pos"])["status"],"no_evaluable")

    def test_reading_shelter_and_capture_does_not_mutate_world(self):
        source=deepcopy(self.w)
        before=deepcopy(self.p)
        shelter_properties(self.w,self.p["pos"])
        survival_conditions(self.w,self.p)
        measured_shelter(self.w,self.p)
        capture(self.w,self.p)
        self.assertEqual(self.w,source)
        # capture() historically ensures missing needs metadata; the physical
        # shelter and survival_conditions checks themselves must be pure.
        self.assertEqual(self.p["needs"],before["needs"])

    def test_unseen_location_out_of_bounds_fails_closed(self):
        sample=shelter_properties(self.w,[-1,999,0])
        self.assertFalse(sample["sheltered"])
        self.assertEqual(sample["status"],"no_evaluable")

    def test_shelter_status_stable_across_repeated_consultations(self):
        first=shelter_properties(self.w,[15,10,0])
        for _ in range(10):
            self.assertEqual(shelter_properties(self.w,[15,10,0]),first)

    def test_building_named_refugio_cannot_create_shelter_effect(self):
        st=initial_state(7321)
        w,p=st["world"],st["person"]
        p["pos"]=[14,10,0]
        set_tile(w,14,10,0,".")
        p["inventory"]["madera"]=8
        out=world.execute_action(w,p,{"op":"build","name":"refugio",
                      "purpose":"cubierta para dormir",
                      "materials":["madera"]*4},random.Random(45))
        self.assertTrue(out[2],out)
        built=w["structures"][-1]
        self.assertEqual(built["category"],"habitaculo")
        self.assertFalse(sheltered(w,p["pos"]))
        self.assertNotIn("shelter_condition",built)
        self.assertEqual(shelter_properties(w,p["pos"])["status"],"no_evaluable")

    def test_old_structure_shelter_flags_preserved_as_history(self):
        from construction import ensure_object
        obj={"id":"historical","name":"antiguo",
             "pos":[14,10,0],"category":"habitaculo",
             "materials":["madera"]*4,"resistance":6,
             "shelter_condition":"cubierto_parcialmente"}
        ensure_object(obj,structure=True)
        self.assertEqual(obj["shelter_condition"],"cubierto_parcialmente")
        missing={"id":"missing","name":"otro","category":"habitaculo",
                 "materials":["madera"]*4,"resistance":6}
        ensure_object(missing,structure=True)
        self.assertNotIn("shelter_condition",missing)


class BodyAndRest13(unittest.TestCase):
    def test_survival_facade_keeps_public_contract(self):
        self.assertIs(survival.ensure_needs,physiological_needs.ensure_needs)
        self.assertIs(survival.needs_summary,physiological_needs.needs_summary)
        self.assertIs(survival.perceived_needs,physiological_needs.perceived_needs)
        self.assertIs(bodily_policy.rest_minutes,policy.rest_minutes)
        self.assertIs(bodily_policy.wait_minutes,policy.wait_minutes)
        self.assertIs(bodily_policy.fatigue_multiplier,policy.fatigue_multiplier)

    def test_rest_improves_energy_wait_does_not(self):
        rest=actor()
        wait=actor()
        survival.update_needs(rest,{},60,resting=True,at_shelter=False)
        survival.update_needs(wait,{},60,waiting=True,resting=False,at_shelter=False)
        self.assertGreater(rest["needs"]["energia"],50)
        self.assertLess(wait["needs"]["energia"],50)
        self.assertEqual(rest["needs"]["energia"],56.6)
        self.assertEqual(wait["needs"]["energia"],49.6)

    def test_shelter_bonus_only_during_real_rest(self):
        outdoors=actor()
        inside=actor()
        survival.update_needs(outdoors,{},60,resting=True,at_shelter=False)
        survival.update_needs(inside,{},60,resting=True,at_shelter=True)
        self.assertEqual(inside["needs"]["energia"]-outdoors["needs"]["energia"],4.0)
        self.assertEqual(inside["needs"]["energia"],60.6)

    def test_idle_and_wait_are_distinct(self):
        idle=actor()
        waiting=actor()
        survival.update_needs(idle,{},60)
        survival.update_needs(waiting,{},60,waiting=True)
        self.assertEqual(idle["needs"]["energia"],50.8)
        self.assertEqual(waiting["needs"]["energia"],49.6)

    def test_wait_ignores_named_refuge_but_rest_uses_real_site(self):
        w=world.new_world(7321)
        p=actor()
        self.assertTrue(survival_conditions(w,p)[0])
        survival.update_needs(p,w,60,at_shelter=True,waiting=True)
        self.assertEqual(p["needs"]["energia"],49.6)

    def test_corporeal_time_has_no_automatic_food_water(self):
        p=actor(energy=20,thirst=14,hunger=14)
        original=deepcopy(p["inventory"])
        for _ in range(24):
            survival.update_needs(p,{},60,at_shelter=True,near_water=True,
                                  active=False)
        self.assertEqual(p["inventory"],original)
        self.assertLess(p["needs"]["hidratacion"],14)
        self.assertLess(p["needs"]["nutricion"],14)
        self.assertEqual(p["needs"]["abrigo"],80)
        self.assertEqual(p["needs"]["seguridad"],68)

    def test_active_consumes_more_energy_than_waiting(self):
        active=actor()
        waiting=actor()
        survival.update_needs(active,{},60,active=True)
        survival.update_needs(waiting,{},60,waiting=True)
        self.assertEqual(active["needs"]["energia"],48.85)
        self.assertEqual(waiting["needs"]["energia"],49.6)

    def test_unconscious_recovery_requires_explicit_resting_physics(self):
        p=actor(energy=4)
        p["unconscious"]=True
        survival.update_needs(p,{},60,resting=True,at_shelter=False)
        self.assertGreater(p["needs"]["energia"],4)
        self.assertFalse(policy.can_wake(p["needs"]["energia"]))
        self.assertTrue(policy.should_collapse(5))
        self.assertFalse(policy.should_collapse(5.01))
        self.assertFalse(policy.can_wake(39.99))
        self.assertTrue(policy.can_wake(40))

    def test_strain_thresholds_conserve_modern_rules(self):
        p=actor(energy=11.99,thirst=50,hunger=50)
        self.assertTrue(policy.body_strained(p["needs"]))
        p["needs"]["energia"]=20
        self.assertFalse(policy.body_strained(p["needs"]))
        p["needs"]["nutricion"]=11.99
        self.assertTrue(policy.body_strained(p["needs"]))
        p["needs"]["nutricion"]=15
        p["needs"]["hidratacion"]=14.99
        self.assertTrue(policy.body_strained(p["needs"]))

    def test_rest_wait_durations_reject_nan_inf_bool(self):
        for value in (float("nan"),float("inf"),True,-5,0,1441,"foo"):
            with self.subTest(value=value):
                self.assertIsNone(bodily_policy.rest_minutes({"minutes":value}))
                self.assertIsNone(bodily_policy.wait_minutes({"minutes":value}))
        self.assertEqual(bodily_policy.rest_minutes({}),30)
        self.assertEqual(bodily_policy.wait_minutes({"minutes":45}),45)

    def test_elapsed_time_and_reserves_fail_without_partial_update(self):
        for duration in (float("nan"),float("inf"),-float("inf"),True):
            p=actor()
            before=deepcopy(p)
            with self.subTest(duration=duration):
                with self.assertRaises(ValueError):
                    survival.update_needs(p,{},duration)
                self.assertEqual(p,before)
        p=actor()
        p["needs"]["energia"]=float("nan")
        values=deepcopy(p["needs"])
        with self.assertRaises(ValueError):
            survival.update_needs(p,{},60)
        self.assertEqual(p["needs"],values)

    def test_needs_summary_is_pure_and_qualitative_to_agent(self):
        p=actor()
        baseline=deepcopy(p)
        observer=survival.needs_summary(p)
        perceived=survival.perceived_needs(p)
        self.assertIn("valores",observer)
        self.assertEqual(observer["valores"]["energia"],50)
        self.assertNotIn("valores",perceived)
        self.assertTrue(all(not isinstance(v,(int,float)) for v in perceived.values()))
        self.assertEqual(p,baseline)

    def test_empty_person_summary_does_not_create_needs(self):
        p={}
        result=survival.needs_summary(p)
        self.assertIn("energia",result["valores"])
        self.assertEqual(p,{})

    def test_legacy_autocare_still_explicitly_compatible(self):
        p=actor(energy=70,thirst=44,hunger=70)
        before=deepcopy(p)
        with patch("motivation.record_maintenance") as record:
            events=survival.update_needs(p,{},60,near_water=True,
                                          legacy_autocare=True)
        self.assertEqual(len(events),1)
        self.assertIn("agua",events[0])
        self.assertEqual(p["needs"]["hidratacion"],66.45)
        self.assertEqual(before["inventory"],p["inventory"])
        record.assert_called_once_with(p,"drink","Rutina",autonomous=True)

    def test_legacy_energy_cap_is_not_rewritten(self):
        p=actor(energy=80)
        survival.update_needs(p,{},60,resting=True,legacy_energy_cap=True)
        self.assertEqual(p["needs"]["energia"],79.6)

    def test_long_simulated_slice_is_bounded(self):
        p=actor(energy=50)
        survival.update_needs(p,{},3000,waiting=True)
        self.assertEqual(p["needs"]["energia"],40.4)
        self.assertGreaterEqual(p["needs"]["hidratacion"],0)

    def test_fatigue_multiplier_bounds_and_corrupt_inputs(self):
        self.assertEqual(policy.fatigue_multiplier({"energia":60,"hidratacion":50}),1.)
        self.assertEqual(policy.fatigue_multiplier({"energia":30,"hidratacion":50}),1.35)
        self.assertEqual(policy.fatigue_multiplier({"energia":19,"hidratacion":100}),1.7)
        self.assertEqual(policy.fatigue_multiplier({"energia":float("nan")}),1.7)

    def test_sensations_follow_exact_intervals_without_numerical_leak(self):
        p=actor(energy=11.99,thirst=14.99,hunger=29.99)
        perceived=survival.perceived_needs(p)
        self.assertEqual(perceived["energia"],"agotamiento severo")
        self.assertEqual(perceived["hidratacion"],"sed extrema")
        self.assertEqual(perceived["alimentacion"],"mucha hambre")
        self.assertIn("señal_adicional",perceived) if p.get("strain") else None

    def test_update_needs_zero_or_negative_duration_is_noop(self):
        p=actor()
        before=deepcopy(p)
        self.assertEqual(survival.update_needs(p,{},0),[])
        self.assertEqual(survival.update_needs(p,{},-30),[])
        self.assertEqual(p,before)


if __name__=="__main__":
    unittest.main()
