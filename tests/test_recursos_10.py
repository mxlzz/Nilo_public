"""Etapa 10: conservación de recursos, depósito ligado al viaje y compatibilidad."""
from __future__ import annotations

from copy import deepcopy
import random
from pathlib import Path
import tempfile
import unittest

import world
from nilo import Simulation
from nilo_runtime.worlds.island import tile_key, set_tile
from nilo_runtime.worlds.resources import (
    ResourceBalanceError, StockTransfer, stock_units, transfer_units,
    gather_material, nearest_known, forage_source, forage_action,
    harvest_at, cut_wood,
)


def work_site(stock=3):
    w=world.new_world(7321)
    x,y,z=15,10,0
    set_tile(w,x,y,z,"T")
    key=tile_key(x,y,z)
    w["revealed"]=[key]
    w["deposits"][key]=stock
    p={"pos":[x,y,z],"inventory":{"madera":0,"alimento":0},
       "clock_minutes":0,"vehicle_id":None,"items":[]}
    return w,p,key


class ResourceInvariants10(unittest.TestCase):
    def test_proprietary_functions_reexport_legacy_api(self):
        from nilo_runtime.worlds import resources
        for name in ("gather_material","nearest_known","forage_source"):
            self.assertIs(getattr(world,name),getattr(resources,name))
        self.assertEqual(gather_material(" arboleda "),"madera")
        self.assertEqual(gather_material("hongo luminoso"),"hongo luminoso")

    def test_transfer_conserves_and_records_both_ends(self):
        a={"d":6};b={"m":2}
        receipt=transfer_units(a,"d",b,"m",3)
        self.assertIsInstance(receipt,StockTransfer)
        self.assertEqual((a["d"],b["m"]),(3,5))
        self.assertEqual(receipt.source_before+receipt.destination_before,
                         receipt.source_after+receipt.destination_after)
        self.assertEqual(receipt.quantity,3)

    def test_invalid_transfers_are_atomic_and_finite_integers(self):
        for amount in (0,-1,True,1.1,float("nan"),float("inf"),"2",None,8):
            with self.subTest(amount=amount):
                source={"s":5};target={"d":1}
                before=deepcopy([source,target])
                with self.assertRaises(ResourceBalanceError):
                    transfer_units(source,"s",target,"d",amount)
                self.assertEqual([source,target],before)
        a={"s":5};b={"d":2}
        with self.assertRaises(ResourceBalanceError):
            transfer_units(a,"s",b,"d",2,maximum=3)
        self.assertEqual([a,b],[{"s":5},{"d":2}])
        with self.assertRaises(ResourceBalanceError):
            transfer_units(a,"s",a,"s",1)

    def test_corrupt_stock_does_not_get_clamped_or_generate_material(self):
        a={"s":-1};b={"d":0}
        with self.assertRaises(ResourceBalanceError):
            transfer_units(a,"s",b,"d",1)
        self.assertEqual((a["s"],b["d"]),(-1,0))
        with self.assertRaises(ResourceBalanceError):
            stock_units({"s":float("inf")},"s")

    def test_harvest_one_and_two_units_without_duplication(self):
        for count in (1,2,3):
            with self.subTest(count=count):
                w,p,key=work_site(count)
                before=w["deposits"][key]+p["inventory"]["madera"]
                duration,facts,success,notable=harvest_at(w,p,"madera",(15,10,0))
                self.assertTrue(success)
                self.assertEqual(duration,12+min(2,count)*5)
                self.assertEqual(p["inventory"]["madera"],min(2,count))
                self.assertEqual(w["deposits"][key],count-min(2,count))
                self.assertEqual(w["deposits"][key]+p["inventory"]["madera"],before)
                self.assertEqual(notable,count<=2)
                self.assertIn("Recogí",facts[0])

    def test_pinned_resource_cannot_be_replaced_by_closer_source(self):
        w,p,key=work_site(6)
        set_tile(w,16,10,0,"T")
        other=tile_key(16,10,0)
        w["revealed"].append(other)
        w["deposits"][other]=4
        result=world.execute_action(w,p,{"op":"gather","target":"madera",
                                          "_resource_at":[16,10,0]},random.Random(4))
        self.assertTrue(result[2],result)
        self.assertEqual(w["deposits"][key],6)
        self.assertEqual(w["deposits"][other],2)
        self.assertEqual(p["inventory"]["madera"],2)

    def test_pinned_resource_exhausted_or_hidden_cannot_switch(self):
        w,p,key=work_site(6)
        set_tile(w,16,10,0,"T")
        other=tile_key(16,10,0)
        w["revealed"].append(other)
        w["deposits"][other]=0
        before=deepcopy([w["deposits"],p["inventory"]])
        result=world.execute_action(w,p,{"op":"gather","target":"madera",
                                          "_resource_at":[16,10,0]},random.Random(4))
        self.assertFalse(result[2])
        self.assertEqual([w["deposits"],p["inventory"]],before)
        w["revealed"].remove(other)
        result=world.execute_action(w,p,{"op":"gather","target":"madera",
                                          "_resource_at":[16,10,0]},random.Random(4))
        self.assertFalse(result[2])
        self.assertEqual([w["deposits"],p["inventory"]],before)

    def test_remote_or_cross_level_source_cannot_be_collected(self):
        w,p,key=work_site(4)
        for pin in ([20,10,0],[15,10,-1],[999,10,0]):
            with self.subTest(pin=pin):
                _,_,ok,_=world.execute_action(
                    w,p,{"op":"gather","target":"madera","_resource_at":pin},
                    random.Random(3))
                self.assertFalse(ok)
                self.assertEqual(w["deposits"][key],4)
                self.assertEqual(p["inventory"]["madera"],0)

    def test_forage_with_consumption_and_regrowth(self):
        w,p,key=work_site(3)
        w["forage_deposits"]={key:1}
        self.assertEqual(forage_source(w,p),(15,10))
        before=deepcopy(w)
        self.assertEqual(forage_source(w,p),(15,10))
        self.assertEqual(w,before)
        duration,_,ok,_=forage_action(w,p)
        self.assertTrue(ok)
        self.assertEqual(duration,18)
        self.assertEqual(w["forage_deposits"][key],0)
        self.assertEqual(p["inventory"]["alimento"],1)
        self.assertFalse(forage_action(w,p)[2])
        p["clock_minutes"]+=2880
        self.assertTrue(forage_action(w,p)[2])
        self.assertEqual(w["forage_deposits"][key],0)
        self.assertEqual(p["inventory"]["alimento"],2)

    def test_forage_cap_never_overcredits(self):
        w,p,key=work_site(3)
        p["inventory"]["alimento"]=12
        old=deepcopy(w)
        _,_,ok,_=forage_action(w,p)
        self.assertFalse(ok)
        self.assertEqual(w,old)
        self.assertEqual(p["inventory"]["alimento"],12)

    def test_cutting_wood_conserves_deposit_stock(self):
        w,p,key=work_site(1)
        self.assertTrue(cut_wood(w,p,15,10,0))
        self.assertFalse(cut_wood(w,p,15,10,0))
        self.assertEqual(w["deposits"][key],0)
        self.assertEqual(p["inventory"]["madera"],1)

    def test_invalid_negative_deposit_does_not_create_material(self):
        w,p,key=work_site(1)
        w["deposits"][key]=-3
        _,_,ok,_=harvest_at(w,p,"madera",(15,10,0))
        self.assertFalse(ok)
        self.assertEqual(w["deposits"][key],-3)
        self.assertEqual(p["inventory"]["madera"],0)


class RemoteWork10(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.sim=Simulation(db_path=Path(self.temp.name)/"test.sqlite3",
                            world_seed=7321,rng_seed=9821)
        self.addCleanup(self.sim.conn.close)
        self.sim.think=lambda:None
        self.sim.s["speed"]=60
        self.sim.s["paused"]=False
        self.sim.s["mode"]="demo"
        self.p=self.sim.s["person"]
        self.w=self.sim.s["world"]
        self.p["pos"]=[15,10,0]
        self.p["inventory"]["madera"]=0
        self.w["revealed"]=[tile_key(x,10,0) for x in range(15,21)]
        for x in range(16,21):
            set_tile(self.w,x,10,0,"=")
        self.source=(20,11,0)
        self.source_key=tile_key(*self.source)
        set_tile(self.w,*self.source,"T")
        self.w["revealed"].append(self.source_key)
        for k in list(self.w["deposits"]):
            self.w["deposits"][k]=0
        self.w["deposits"][self.source_key]=6
        self.p["plan"]=[{"op":"gather","target":"madera"}]
        self.sim.tick(0)
        self.pending=self.p["pending"]
        self.assertIsNotNone(self.pending)
        self.assertIn("navigation",self.pending)
        self.assertEqual(self.pending["navigation"]["resource_at"],[20,11])

    def minutes(self,amount):
        while amount>1e-8:
            tick=min(amount,10)
            self.sim.tick(tick)
            amount-=tick

    def test_resource_pin_survives_travel_and_credits_only_after_work(self):
        travel=self.pending["timing"]["planned_travel_minutes"]
        work=self.pending["timing"]["planned_work_minutes"]
        self.minutes(travel)
        self.assertEqual(self.p["inventory"]["madera"],0)
        self.assertEqual(self.w["deposits"][self.source_key],6)
        # Aparece otro depósito *después* de seleccionar A, en el destino.
        local=tile_key(20,10,0)
        set_tile(self.w,20,10,0,"T")
        self.w["deposits"][local]=6
        self.minutes(work)
        self.assertEqual(self.p["inventory"]["madera"],2)
        self.assertEqual(self.w["deposits"][self.source_key],4)
        self.assertEqual(self.w["deposits"][local],6)

    def test_exhausted_source_after_travel_fails_without_substitution(self):
        travel=self.pending["timing"]["planned_travel_minutes"]
        work=self.pending["timing"]["planned_work_minutes"]
        self.minutes(travel)
        self.w["deposits"][self.source_key]=0
        local=tile_key(20,10,0)
        set_tile(self.w,20,10,0,"T")
        self.w["deposits"][local]=6
        self.minutes(work)
        self.assertEqual(self.p["inventory"]["madera"],0)
        self.assertEqual(self.w["deposits"][local],6)
        self.assertIsNone(self.p["pending"])


if __name__=="__main__":
    unittest.main()
