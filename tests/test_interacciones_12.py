"""Nilo 0.7 · Etapa 12: acciones físicas, reversiones y materiales."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import random
import unittest

import construction
import world
from nilo import initial_state
from nilo_runtime.worlds.resources import (
    ResourceBalanceError, check_materials, exchange_units, material_counts,
)
from nilo_runtime.worlds.intervention import execute_prepared
from nilo_runtime.worlds.fabrication import combine_action, fabricate_action
from nilo_runtime.worlds.island import set_tile, tile_key


class Stage12(unittest.TestCase):
    def setUp(self):
        state=initial_state(7321)
        self.w=state["world"]
        self.p=state["person"]
        self.p["pos"]=[15,10,0]
        self.p["items"]=[]
        self.p["inventory"].update({"madera":8,"piedra":7,"arcilla":5,"fibra":4})
        self.rng=random.Random(1234)

    def action(self,op,**kw):
        return world.execute_action(self.w,self.p,{"op":op,**kw},self.rng)

    def test_material_counts_and_exchange_conserve_exact_amount(self):
        self.assertEqual(material_counts(["madera","madera","piedra"]),
                         {"madera":2,"piedra":1})
        before=deepcopy(self.p["inventory"])
        receipt=exchange_units(self.p["inventory"],
                               {"madera":2,"piedra":1},{"producto":1})
        self.assertEqual(receipt["before"]["madera"],before["madera"])
        self.assertEqual(self.p["inventory"]["madera"],before["madera"]-2)
        self.assertEqual(self.p["inventory"]["piedra"],before["piedra"]-1)
        self.assertEqual(self.p["inventory"]["producto"],1)

    def test_invalid_batch_is_atomic_even_if_first_material_exists(self):
        original=deepcopy(self.p["inventory"])
        for costs,credits in (
            ({"madera":1,"piedra":999},{}),
            ({"madera":1},{"x":0}),
            ({"madera":True},{"x":1}),
            ({"madera":-1},{}),
            ({"madera":1},{"x":1.5}),
        ):
            with self.subTest(costs=costs,credits=credits):
                with self.assertRaises(ResourceBalanceError):
                    exchange_units(self.p["inventory"],costs,credits)
                self.assertEqual(self.p["inventory"],original)

    def test_corrupt_stock_is_rejected_without_repairing_save(self):
        inv={"madera":-2,"piedra":1}
        before=deepcopy(inv)
        with self.assertRaises(ResourceBalanceError):
            exchange_units(inv,{"piedra":1},{"madera":1})
        self.assertEqual(inv,before)
        with self.assertRaises(ResourceBalanceError):
            check_materials(inv,{"madera":1})

    def test_combine_spends_two_units_and_credits_one_composite(self):
        initial=deepcopy(self.p["inventory"])
        result=self.action("combine",materials=["madera","piedra"],method="unir")
        self.assertTrue(result[2],result)
        self.assertEqual(self.p["inventory"]["madera"],initial["madera"]-1)
        self.assertEqual(self.p["inventory"]["piedra"],initial["piedra"]-1)
        composites=[x for x in self.p["inventory"] if x.startswith("compuesto unir")]
        self.assertEqual(len(composites),1)
        self.assertEqual(self.p["inventory"][composites[0]],1)
        self.assertIn(composites[0],self.p["materials"])

    def test_combine_insufficient_material_changes_nothing(self):
        old=deepcopy([self.p["inventory"],self.p["materials"]])
        result=self.action("combine",materials=["madera","material imaginario"],
                           method="unir")
        self.assertFalse(result[2])
        self.assertEqual([self.p["inventory"],self.p["materials"]],old)

    def test_invalid_design_does_not_fabricate_or_consume(self):
        old=deepcopy([self.p["inventory"],self.p["items"]])
        result=self.action("craft",materials=["madera"],name="hacha",
                           form="filo",design_id="no existe")
        self.assertFalse(result[2],result)
        self.assertEqual([self.p["inventory"],self.p["items"]],old)

    def test_craft_and_build_debit_only_owned_material(self):
        initial=deepcopy(self.p["inventory"])
        c=self.action("craft",materials=["madera","piedra"],
                      name="pieza experimental",form="punta")
        self.assertTrue(c[2],c)
        self.assertEqual(self.p["inventory"]["madera"],initial["madera"]-1)
        self.assertEqual(self.p["inventory"]["piedra"],initial["piedra"]-1)
        self.assertEqual(Counter(self.p["items"][-1]["materials"]),
                         Counter({"madera":1,"piedra":1}))
        b=self.action("build",materials=["madera","madera"],name="apoyo")
        self.assertTrue(b[2],b)
        self.assertEqual(self.p["inventory"]["madera"],initial["madera"]-3)
        self.assertEqual(self.w["structures"][-1]["materials"],["madera","madera"])

    def test_fabricate_insufficient_does_not_create_phantom_entity(self):
        self.p["inventory"]["madera"]=0
        before=deepcopy([self.p["inventory"],self.p["items"],
                         self.w["structures"]])
        result=self.action("craft",materials=["madera"],form="filo",name="hacha")
        self.assertFalse(result[2])
        self.assertEqual([self.p["inventory"],self.p["items"],
                          self.w["structures"]],before)

    def test_assemble_invalid_joints_does_not_consume(self):
        before=deepcopy(self.p["inventory"])
        step={"parts":[{"name":"uno","material":"madera","shape":"macizo"},
                       {"name":"dos","material":"madera","shape":"macizo"}],
              "joints":[{"a":0,"b":0,"type":"fija"}]}
        result=self.action("assemble",**step)
        self.assertFalse(result[2],result)
        self.assertEqual(self.p["inventory"],before)
        self.assertEqual(self.p["items"],[])

    def test_assemble_valid_consumes_exact_lots(self):
        before=self.p["inventory"]["madera"]
        step={"parts":[{"name":"uno","material":"madera","shape":"rueda"},
                       {"name":"dos","material":"madera","shape":"eje"}],
              "joints":[{"a":0,"b":1,"type":"articulada"}]}
        result=self.action("assemble",**step)
        self.assertTrue(result[2],result)
        self.assertEqual(self.p["inventory"]["madera"],before-2)
        self.assertTrue(self.p["items"][-1]["joints"])

    def test_invalid_modification_does_not_migrate_legacy_object(self):
        old={"id":"legado","name":"legado","materials":["madera"],
             "resistance":5,"portable":True}
        self.p["items"].append(old)
        snap=deepcopy([old,self.p["inventory"],self.p["items"]])
        for mode in ("desconocido","repair"):
            result=self.action("modify",item="legado",mode=mode,
                               materials=["madera"],component="sin componente")
            self.assertFalse(result[2],result)
            self.assertEqual([old,self.p["inventory"],self.p["items"]],snap)
        self.assertNotIn("components",old)
        self.assertNotIn("revisions",old)

    def test_modify_add_is_one_commit_with_new_revision(self):
        self.assertTrue(self.action("craft",materials=["madera"],name="pieza",
                                    form="punta")[2])
        obj=self.p["items"][-1]
        before=(self.p["inventory"]["madera"],len(obj["components"]))
        result=self.action("modify",item=obj["id"],mode="add",materials=["madera"])
        self.assertTrue(result[2],result)
        self.assertIs(self.p["items"][-1],obj)
        self.assertEqual(self.p["inventory"]["madera"],before[0]-1)
        self.assertEqual(len(obj["components"]),before[1]+1)
        self.assertEqual(obj["revision"],2)
        self.assertFalse(obj.get("verified_function_current",False))

    def test_rejected_empty_repair_has_no_effect(self):
        self.assertTrue(self.action("craft",materials=["madera"],name="pieza",
                                    form="punta")[2])
        obj=self.p["items"][-1]
        snap=deepcopy([obj,self.p["inventory"]])
        result=self.action("modify",item=obj["id"],mode="repair",
                           component=obj["components"][0]["id"],materials=["madera"])
        self.assertFalse(result[2],result)
        self.assertEqual([obj,self.p["inventory"]],snap)

    def test_dismantle_legacy_object_archives_once_and_salvages_at_most_components(self):
        old={"id":"legado","name":"pila","materials":["madera","madera"],
             "resistance":5,"portable":True}
        self.p["items"].append(old)
        count=self.p["inventory"]["madera"]
        result=self.action("dismantle",item="legado")
        self.assertTrue(result[2],result)
        self.assertFalse(any(x is old for x in self.p["items"]))
        self.assertIs(self.p["retired_items"][-1],old)
        self.assertLessEqual(self.p["inventory"]["madera"]-count,2)
        self.assertGreaterEqual(self.p["inventory"]["madera"]-count,0)

    def test_full_vessel_rejects_dismantle_without_loss(self):
        obj={"id":"vaso","name":"vaso","form":"recipiente",
             "materials":["piedra","piedra"],"portable":True,
             "contents":{"material":"agua","quantity":0.5},
             "geometry":{"shape":"hueco","size":2}}
        self.p["items"].append(obj)
        before=deepcopy([obj,self.p["inventory"]])
        result=self.action("dismantle",item="vaso")
        self.assertFalse(result[2],result)
        self.assertEqual([obj,self.p["inventory"]],before)
        self.assertNotIn("components",obj)

    def test_loaded_structure_rejects_dismantle_without_side_effect(self):
        self.assertTrue(self.action("build",materials=["piedra","piedra"],
                                    name="plataforma",purpose="soporte")[2])
        obj=self.w["structures"][-1]
        obj["cargas_almacenadas"]={"piedra":1}
        before=deepcopy([obj,self.p["inventory"],self.w["structures"]])
        result=self.action("dismantle",item=obj["id"])
        self.assertFalse(result[2],result)
        self.assertEqual([obj,self.p["inventory"],self.w["structures"]],before)

    def test_unknown_interaction_is_not_physical_failure_or_material_spend(self):
        before=deepcopy([self.p["inventory"],self.p["items"]])
        result=self.action("interact",method="alquimia imposible")
        self.assertFalse(result[2])
        self.assertEqual([self.p["inventory"],self.p["items"]],before)
        self.assertIn("NO IMPLEMENTADA",result[1][0])

    def test_tool_cuts_exactly_one_tree_resource(self):
        self.assertTrue(self.action("craft",materials=["madera"],name="hacha",
                                    form="filo")[2])
        tool=self.p["items"][-1]
        x,y,z=16,10,0
        set_tile(self.w,x,y,z,"T")
        key=tile_key(x,y,z)
        self.w["deposits"][key]=3
        previous=self.p["inventory"]["madera"]
        result=self.action("use",item=tool["id"],method="cortar")
        self.assertTrue(result[2],result)
        self.assertEqual(self.p["inventory"]["madera"],previous+1)
        self.assertEqual(self.w["deposits"][key],2)
        self.assertEqual(tool["durability"],95)


    def test_legacy_world_tool_api_has_one_physical_implementation(self):
        from nilo_runtime.worlds.tool_use import (
            use_action, adjacent_rock, dig_with_tool,
        )
        self.assertIs(world.use_action,use_action)
        self.assertIs(world.adjacent_rock,adjacent_rock)
        self.assertIs(world.dig_with_tool,dig_with_tool)

    def test_ambiguous_partial_tool_name_does_not_select_at_random(self):
        self.assertTrue(self.action("craft",name="hacha corta",
                                    form="filo",materials=["madera"])[2])
        self.assertTrue(self.action("craft",name="hacha larga",
                                    form="filo",materials=["madera"])[2])
        before=deepcopy([self.p["inventory"],self.p["items"]])
        result=self.action("use",item="hacha",method="cortar")
        self.assertFalse(result[2],result)
        self.assertEqual([self.p["inventory"],self.p["items"]],before)

    def test_excavation_credits_stone_only_when_rock_opens(self):
        from nilo_runtime.worlds.island import tile
        for dx,dy in world.DIRS:
            set_tile(self.w,15+dx,10+dy,0,".")
        set_tile(self.w,16,10,0,"^")
        key=tile_key(16,10,0)
        self.w["excavation"][key]=0
        tool={"name":"punta","form":"punta"}
        before=self.p["inventory"]["piedra"]
        r1=world.dig_with_tool(self.w,self.p,tool,7,{"x":16,"y":10})
        self.assertTrue(r1[0],r1)
        self.assertEqual(self.p["inventory"]["piedra"],before)
        self.assertEqual(tile(self.w,16,10,0),"^")
        r2=world.dig_with_tool(self.w,self.p,tool,7,{"x":16,"y":10})
        self.assertTrue(r2[0],r2)
        self.assertEqual(self.p["inventory"]["piedra"],before+2)
        self.assertEqual(tile(self.w,16,10,0),".")
        r3=world.dig_with_tool(self.w,self.p,tool,7,{"x":16,"y":10})
        self.assertFalse(r3[0])
        self.assertEqual(self.p["inventory"]["piedra"],before+2)

    def test_corrupt_stone_inventory_blocks_excavation_without_clearing_tile(self):
        from nilo_runtime.worlds.island import tile
        for dx,dy in world.DIRS:
            set_tile(self.w,15+dx,10+dy,0,".")
        set_tile(self.w,16,10,0,"^")
        key=tile_key(16,10,0)
        self.w["excavation"][key]=2
        self.p["inventory"]["piedra"]=-1
        result=world.dig_with_tool(self.w,self.p,{"name":"punta"},8,{"x":16,"y":10})
        self.assertFalse(result[0])
        self.assertEqual(self.w["excavation"][key],2)
        self.assertEqual(tile(self.w,16,10,0),"^")
        self.assertEqual(self.p["inventory"]["piedra"],-1)

    def test_moving_rock_credits_once_and_no_repeated_extraction(self):
        from nilo_runtime.worlds.island import tile
        self.assertTrue(self.action("craft",name="palanca",
                                    form="palanca",materials=["piedra"])[2])
        tool=self.p["items"][-1]
        for dx,dy in world.DIRS:
            set_tile(self.w,15+dx,10+dy,0,".")
        set_tile(self.w,16,10,0,"^")
        before=self.p["inventory"]["piedra"]
        first=self.action("use",item=tool["id"],method="mover")
        self.assertTrue(first[2],first)
        self.assertEqual(self.p["inventory"]["piedra"],before+1)
        self.assertEqual(tile(self.w,16,10,0),".")
        second=self.action("use",item=tool["id"],method="mover")
        self.assertFalse(second[2])
        self.assertEqual(self.p["inventory"]["piedra"],before+1)


if __name__=="__main__":
    unittest.main()
