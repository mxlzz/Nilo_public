"""Nilo 0.7 / etapa 11: materiales, objetos, formas y componentes."""
from __future__ import annotations

from copy import deepcopy
import random
import unittest
from unittest.mock import patch

import catalogo
from catalogo import MATERIALS, MATERIAL_PHYSICS, FORMS, SHAPES, JOINTS
import construction
import mechanics
import physics
import world
from nilo import initial_state
from nilo_runtime.worlds import objects, components


class ObjectMaterial11(unittest.TestCase):
    def state(self):
        s=initial_state(7321)
        p=s["person"]
        p["inventory"]["madera"]=4
        return s["world"],p

    def test_single_proprietor_legacy_public_exports(self):
        for name in ("infer_form","is_portable","item_effects","make_item",
                     "classify_structure","structure_symbol","enrich_structure"):
            self.assertIs(getattr(world,name),getattr(objects,name))

    def test_name_only_is_legacy_classification_not_physical_evidence(self):
        self.assertEqual(world.infer_form("hacha"),"filo")
        self.assertEqual(world.infer_form("recipiente"),"recipiente")
        self.assertEqual(objects.declared_form(None),"simple")
        self.assertEqual(objects.declared_form(" HUECO "),"simple")
        self.assertEqual(objects.declared_form(" punta "),"punta")
        self.assertEqual(objects.declared_form("hacha"),"simple")

    def test_new_craft_without_form_does_not_gain_capacity_from_name(self):
        w,p=self.state()
        result=world.execute_action(w,p,{"op":"craft","materials":["madera"],
                         "name":"hacha inmensa"},random.Random(1))
        self.assertTrue(result[2],result)
        tool=p["items"][-1]
        self.assertEqual(tool["form"],"simple")
        self.assertEqual(tool["possible_uses"],{})
        self.assertEqual(world.item_effects(tool),{})
        self.assertEqual(tool["components"][0]["material"],"madera")

    def test_explicit_form_gives_same_physics_despite_different_labels(self):
        output=[]
        for label in ("hacha", "frasco de agua", "nada relacionado"):
            w,p=self.state()
            step={"op":"craft","materials":["madera"],"name":label,
                  "purpose":"probar un diseño","form":"punta",
                  "geometry":{"shape":"macizo","size":1}}
            done=world.execute_action(w,p,step,random.Random(7))
            self.assertTrue(done[2],done)
            tool=p["items"][-1]
            output.append((tool["form"],tool["possible_uses"],tool["physics"],
                           tool["resistance"],tool["hardness"],tool["weight"]))
        self.assertEqual(output[0],output[1])
        self.assertEqual(output[0],output[2])
        self.assertIn("excavar",output[0][1])

    def test_build_named_tool_without_form_is_a_structure(self):
        w,p=self.state()
        result=world.execute_action(w,p,{"op":"build","materials":["madera"],
                                     "name":"martillo"},random.Random(7))
        self.assertTrue(result[2],result)
        self.assertEqual(len(w["structures"]),1)
        self.assertEqual(len(p["items"]),0)

    def test_nonhollow_container_has_no_contenedor_affordance(self):
        item={"form":"recipiente","resistance":8,"hardness":6,
              "materials":["piedra"],"geometry":{"shape":"macizo","size":1}}
        self.assertEqual(objects.item_effects(item),{})
        self.assertFalse(physics.evaluate_containment(item)["possible"])
        item["geometry"]={"shape":"hueco","size":1}
        self.assertIn("contener",objects.item_effects(item))

    def test_empty_materials_cannot_displace_float_or_store_water(self):
        item={"form":"recipiente","materials":[],
              "geometry":{"shape":"hueco","size":9}}
        body=physics.body_physics([],item["geometry"])
        self.assertEqual(body["capacity"],0.0)
        self.assertEqual(body["displacement"],0.0)
        self.assertFalse(physics.evaluate_containment(item)["possible"])
        self.assertFalse(physics.evaluate_buoyancy(item)["floats"])

    def test_explicit_density_permeability_override_is_data_not_label(self):
        self.assertEqual(physics.properties("madera"),MATERIAL_PHYSICS["madera"])
        a={"madera":{"density":1.5,"permeability":.4}}
        b={"madera":{"density":1.5,"permeability":.4}}
        self.assertEqual(physics.properties("madera",a),physics.properties("madera",b))
        self.assertEqual(physics.properties("madera",a),{"density":1.5,"permeability":.4})
        self.assertEqual(physics.properties("madera",{"madera":{"density":float("nan"),
                                                       "permeability":float("inf")}}),
                         MATERIAL_PHYSICS["madera"])
        self.assertEqual(physics.properties("otro",{"otro":{"density":.7,
                                                            "permeability":.8}}),
                         {"density":.7,"permeability":.8})

    def test_item_effects_nonfinite_resistance_fails_closed(self):
        item={"form":"punta","hardness":float("nan"),"resistance":float("inf")}
        self.assertEqual(objects.item_effects(item),{"excavar":0.0,"golpear":0.0})
        item["hardness"]=9
        self.assertGreater(objects.item_effects(item)["excavar"],0)

    def test_legacy_inference_available_for_migrated_items(self):
        props={"resistencia":4,"dureza":5,"peso":3}
        legacy=world.make_item("hacha","",["madera"],props,10,rng=random.Random(1))
        self.assertEqual(legacy["form"],"filo")
        fresh=objects.physical_item("hacha","",["madera"],props,10,rng=random.Random(1))
        self.assertEqual(fresh["form"],"simple")
        self.assertFalse(fresh["possible_uses"])

    def test_component_preview_is_pure_and_does_not_create_ids(self):
        obj={"name":"etiqueta","materials":["madera","arcilla"]}
        original=deepcopy(obj)
        self.assertEqual(objects.component_summary(obj),(("madera",None),("arcilla",None)))
        self.assertEqual(obj,original)
        obj["components"]=[{"id":"c1","material":"madera","condition":.5}]
        self.assertEqual(objects.component_summary(obj),(("madera",.5),))
        self.assertEqual(obj["components"][0]["id"],"c1")

    def test_ensure_object_does_not_allocate_discarded_component_ids(self):
        obj={"id":"t","materials":["madera"],"components":[
            {"id":"existing","material":"madera","condition":.8}]}
        with patch.object(construction,"_components",side_effect=AssertionError(
                "No se deben generar identidades si ya existen")):
            construction.ensure_object(obj,structure=False)
            construction.ensure_object(obj,structure=False)
        self.assertEqual([c["id"] for c in obj["components"]],["existing"])
        self.assertEqual(len(obj["revisions"]),1)

    def test_legacy_missing_components_migrates_once(self):
        obj={"id":"x","materials":["madera","arcilla"]}
        calls=[]
        def make(mats):
            calls.append(tuple(mats))
            return [{"id":f"c{i}","material":m,"condition":1} for i,m in enumerate(mats)]
        with patch.object(construction,"_components",side_effect=make):
            construction.ensure_object(obj)
            construction.ensure_object(obj)
        self.assertEqual(calls,[("madera","arcilla")])
        self.assertEqual([c["id"] for c in obj["components"]],["c0","c1"])

    def test_catalog_forms_fail_closed_on_invalid_names(self):
        raw={"portable_words":["hacha"],"forms":{None:["martillo"]},
             "shapes":["macizo"],"joints":["fija"]}
        with self.assertRaises(ValueError):
            catalogo._validated_objects(raw)
        raw["forms"]={"golpe":["martillo"]}
        self.assertEqual(catalogo._validated_objects(raw)[1]["golpe"],("martillo",))
        self.assertIn("hueco",SHAPES)
        self.assertIn("fija",JOINTS)

    def test_shape_and_joint_graph_are_not_inferred_from_names(self):
        raw=[{"name":"rueda","material":"madera","shape":"macizo"},
             {"name":"eje","material":"madera","shape":"macizo"}]
        parts,error=components.normalize_parts(raw,MATERIALS)
        self.assertIsNone(error)
        self.assertEqual(parts,raw)
        joints,error=components.normalize_joints([{"a":0,"b":1,"type":"fija"}],2)
        self.assertIsNone(error)
        self.assertTrue(components.connected_parts(2,joints))
        renamed=deepcopy(raw)
        renamed[0]["name"]="un objeto desconocido"
        self.assertEqual(components.normalize_parts(renamed,MATERIALS)[0][0]["shape"],"macizo")
        self.assertEqual(joints,[{"a":0,"b":1,"type":"fija"}])

    def test_invalid_joint_indexes_fail_without_mutating_inputs(self):
        for bad in ({"a":True,"b":1,"type":"fija"},
                    {"a":0.5,"b":1,"type":"fija"},
                    {"a":"-1","b":"1","type":"fija"},
                    {"a":0,"b":0,"type":"fija"},
                    {"a":0,"b":99,"type":"fija"},
                    {"a":0,"b":1,"type":"inventada"}):
            with self.subTest(bad=bad):
                before=deepcopy(bad)
                result,reason=components.normalize_joints([bad],2)
                self.assertIsNone(result)
                self.assertTrue(reason)
                self.assertEqual(bad,before)
        self.assertFalse(components.connected_parts(2,[
            {"a":True,"b":1,"type":"fija"}]))

    def test_disconnected_assembly_does_not_spend_inventory(self):
        w,p=self.state()
        before=deepcopy(p["inventory"])
        result=world.execute_action(w,p,{"op":"assemble","parts":[
                 {"name":"uno","material":"madera","shape":"macizo"},
                 {"name":"dos","material":"madera","shape":"macizo"},
                 {"name":"tres","material":"madera","shape":"macizo"}],
                 "joints":[{"a":0,"b":1,"type":"fija"}]},random.Random(3))
        self.assertFalse(result[2],result)
        self.assertEqual(p["inventory"],before)
        self.assertFalse(p.get("items"))

    def test_valid_assembly_uses_catalog_joints_and_real_materials(self):
        w,p=self.state()
        result=world.execute_action(w,p,{"op":"assemble","parts":[
            {"name":"círculo","material":"madera","shape":"rueda"},
            {"name":"barra","material":"madera","shape":"eje"}],
            "joints":[{"a":0,"b":1,"type":"articulada"}]},random.Random(3))
        self.assertTrue(result[2],result)
        self.assertEqual(p["inventory"]["madera"],2)
        self.assertEqual(p["items"][-1]["parts"][0]["shape"],"rueda")
        self.assertEqual(p["items"][-1]["joints"][0]["type"],"articulada")

if __name__=="__main__":
    unittest.main()
