"""Etapa 05: contratos de tiempo y acciones sin efectos antes de completar fases."""
from __future__ import annotations

from copy import deepcopy
import math
from pathlib import Path
import tempfile
import unittest

from nilo import Simulation
from nilo_runtime.core.clock import (
    TimePlan, clamp_real_elapsed, plan_time, phase_progress, completion_contract,
)
from world import tile_key, set_tile
from timing import writing_tick, effective_speed


def run_minutes(sim: Simulation, minutes: float) -> None:
    """A velocidad x60: segundos reales == minutos simulados."""
    remaining = float(minutes)
    while remaining > 1e-8:
        step = min(remaining, 10.)
        sim.tick(step)
        remaining -= step


class TemporalContractTests(unittest.TestCase):
    def test_travel_and_work_are_distinct_and_additive(self):
        plan = plan_time("gather", 22, 9)
        self.assertEqual(plan.planned_total_minutes, 31)
        pending = {"total":31, "remaining":22, "timing":plan.to_pending()}
        phase = phase_progress(pending)
        self.assertEqual(phase["phase"],"work")
        self.assertEqual(phase["elapsed_travel_minutes"],9)
        self.assertEqual(phase["elapsed_work_minutes"],0)
        pending["remaining"]=11
        self.assertEqual(phase_progress(pending)["elapsed_work_minutes"],11)
        self.assertEqual(phase_progress(pending)["phase"],"work")
        pending["remaining"]=0
        result=completion_contract(pending, measured_minutes=31,
                                   declared_handler_minutes=22)
        self.assertEqual(result["status"],"completed")
        self.assertTrue(result["work_phase_completed"])
        self.assertEqual(result["measured_elapsed_minutes"],31)
        self.assertEqual(result["handler_declared_minutes"],22)

    def test_travel_only_never_adds_handler_time(self):
        for op in ("go","explore","ascend"):
            with self.subTest(op=op):
                plan=plan_time(op,20,9,travel_is_only_phase=True)
                self.assertEqual(plan.planned_work_minutes,0)
                self.assertEqual(plan.planned_total_minutes,9)

    def test_blocked_or_interrupted_works_are_not_credited(self):
        plan=plan_time("gather",20,9)
        pending={"total":29,"remaining":12,"timing":plan.to_pending()}
        blocked=completion_contract(pending,measured_minutes=17,
                                    declared_handler_minutes=0,blocked=True)
        interrupted=completion_contract(pending,measured_minutes=17,
                                        declared_handler_minutes=0,interrupted=True)
        self.assertEqual(blocked["status"],"blocked")
        self.assertFalse(blocked["work_phase_completed"])
        self.assertEqual(interrupted["status"],"interrupted")
        self.assertEqual(interrupted["elapsed_work_minutes"],8)

    def test_invalid_nonfinite_or_negative_durations_rejected(self):
        for raw in (float("nan"),float("inf"),-1,"5",True):
            with self.subTest(value=raw):
                with self.assertRaises(ValueError):
                    clamp_real_elapsed(raw)
        self.assertEqual(clamp_real_elapsed(200),20)
        with self.assertRaises(ValueError):
            plan_time("gather",float("nan"),1)
        with self.assertRaises(ValueError):
            plan_time("gather",5,-1)

    def test_write_speed_and_real_cooldown_are_distinct(self):
        self.assertEqual(effective_speed(80,{"step":{"op":"write"}}),2)
        self.assertEqual(effective_speed(80,{"step":{"op":"build"}}),80)
        self.assertEqual(effective_speed(80,None,planning=True),1)
        self.assertEqual(effective_speed(80,None,paused=True),0)
        total,left=writing_tick(5,4,80)
        self.assertEqual(left,0)
        self.assertEqual(total,4+3*80)


class RealEngineTimingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="nilo-time-07-")
        self.addCleanup(self.tmp.cleanup)
        self.db=Path(self.tmp.name)/"partida.sqlite3"
        self.sim=Simulation(db_path=self.db,world_seed=7321,rng_seed=9821)
        self.addCleanup(self.sim.conn.close)
        self.sim.think=lambda:None
        self.sim.s["speed"]=60
        self.sim.s["paused"]=False
        self.sim.s["mode"]="demo"
        self.person=self.sim.s["person"]
        self.world=self.sim.s["world"]

    def set_gather_source(self, *,remote=True):
        # Corredor conocido con una fuente de madera, sin descubrir otras:
        # la búsqueda de fuente no usa terrenos ocultos anticipadamente.
        w=self.world
        w["revealed"]=[tile_key(x,10,0) for x in range(15,21)]
        # El mundo inicial es parcialmente aleatorio: construir un corredor
        # real transitable en vez de asumir que «revelado» implica accesible.
        for x in range(16,21):
            set_tile(w,x,10,0,"=")
        source=(20,11) if remote else (16,10)
        if tile_key(*source,0) not in w["revealed"]:
            w["revealed"].append(tile_key(*source,0))
        set_tile(w,*source,0,"T")
        # Durante el viaje se revelan más casillas: ninguna fuente aleatoria
        # cercana debe desplazar el recurso elegido para este ensayo.
        for k in list(w["deposits"]):
            x,y,z=map(int,k.split(","))
            if z==0 and w["levels"]["0"][y][x]=="T" and k!=tile_key(*source,0):
                w["deposits"][k]=0
        w["deposits"][tile_key(*source,0)]=6
        self.person["pos"]=[15,10,0]
        self.person["inventory"]["madera"]=0
        return source

    def start(self, step):
        self.person["plan"]=[step]
        self.sim.tick(0)
        self.assertIsNotNone(self.person.get("pending"))
        return self.person["pending"]

    def test_remote_gather_credits_only_after_travel_plus_work(self):
        source=self.set_gather_source()
        stock=self.world["deposits"][tile_key(*source,0)]
        pending=self.start({"op":"gather","target":"madera"})
        self.assertIn("navigation",pending)
        schedule=pending["timing"]
        travel=schedule["planned_travel_minutes"]
        work=schedule["planned_work_minutes"]
        self.assertGreater(travel,0)
        self.assertEqual(work,20)
        self.assertAlmostEqual(schedule["planned_total_minutes"],travel+work)
        run_minutes(self.sim,travel)
        self.assertEqual(self.person["inventory"]["madera"],0)
        self.assertEqual(self.world["deposits"][tile_key(*source,0)],stock)
        self.assertEqual(self.person["pending"]["timing"]["phase"],"work")
        self.assertEqual(self.sim.public_state()["activity_timing"]["phase"],"work")
        run_minutes(self.sim,work-1)
        self.assertEqual(self.person["inventory"]["madera"],0)
        self.assertIsNotNone(self.person["pending"])
        run_minutes(self.sim,1)
        self.assertIsNone(self.person["pending"])
        self.assertEqual(self.person["inventory"]["madera"],2)
        self.assertEqual(self.world["deposits"][tile_key(*source,0)],stock-2)
        measured=self.person["measurements"][-1]
        contract=measured["time_contract"]
        self.assertEqual(contract["status"],"completed")
        self.assertTrue(contract["work_phase_completed"])
        self.assertAlmostEqual(contract["planned_total_minutes"],travel+work)
        self.assertAlmostEqual(contract["measured_elapsed_minutes"],travel+work,places=2)
        outcome=self.person["action_outcomes"][-1]
        self.assertEqual(outcome["time_contract"],contract)
        self.assertEqual(contract["handler_declared_minutes"],22)
        self.assertEqual(outcome["evaluation_status"],"verified_success")

    def test_adjacent_gather_requires_work_even_without_travel(self):
        source=self.set_gather_source(remote=False)
        pending=self.start({"op":"gather","target":"madera"})
        self.assertNotIn("navigation",pending)
        self.assertEqual(pending["timing"]["planned_travel_minutes"],0)
        run_minutes(self.sim,19)
        self.assertEqual(self.person["inventory"]["madera"],0)
        run_minutes(self.sim,1)
        self.assertEqual(self.person["inventory"]["madera"],2)

    def test_pause_and_speed_change_never_skip_the_work_phase(self):
        self.set_gather_source(remote=False)
        self.start({"op":"gather","target":"madera"})
        begin=self.person["clock_minutes"]
        self.sim.change_speed(paused=True)
        self.sim.tick(10)
        self.assertAlmostEqual(self.person["clock_minutes"],begin)
        self.assertEqual(self.person["inventory"]["madera"],0)
        self.assertEqual(self.person["pending"]["timing"]["phase"],"work")
        self.sim.change_speed(speed=80,paused=False)
        # 1 segundo real ahora son 80/60 minutos; todavía falta trabajo.
        self.sim.tick(1)
        self.assertEqual(self.person["inventory"]["madera"],0)
        self.assertIsNotNone(self.person["pending"])
        remaining=self.person["pending"]["remaining"]
        self.assertGreater(remaining,0)
        run_minutes(self.sim,15)  # a ×80: completa el trabajo restante
        self.assertIsNone(self.person["pending"])
        self.assertEqual(self.person["inventory"]["madera"],2)

    def test_go_travel_only_has_no_phantom_work(self):
        self.set_gather_source(remote=True)
        self.start({"op":"go","x":20,"y":10})
        pending=self.person["pending"]
        self.assertIn("navigation",pending)
        self.assertEqual(pending["timing"]["planned_work_minutes"],0)
        self.assertEqual(pending["timing"]["planned_travel_minutes"],15)
        run_minutes(self.sim,14)
        self.assertIsNotNone(self.person["pending"])
        run_minutes(self.sim,1)
        self.assertIsNone(self.person["pending"])
        self.assertEqual(self.person["pos"],[20,10,0])
        outcome=self.person["action_outcomes"][-1]
        self.assertEqual(outcome["time_contract"]["planned_travel_minutes"],15)
        self.assertEqual(outcome["time_contract"]["planned_work_minutes"],0)

    def test_obstacle_blocks_without_earning_materials(self):
        source=self.set_gather_source()
        stock=self.world["deposits"][tile_key(*source,0)]
        pending=self.start({"op":"gather","target":"madera"})
        nx,ny=pending["navigation"]["route"][0]
        set_tile(self.world,nx,ny,0,"~")
        run_minutes(self.sim,pending["travel_minutes_per_tile"])
        self.assertIsNone(self.person["pending"])
        self.assertEqual(self.person["inventory"]["madera"],0)
        self.assertEqual(self.world["deposits"][tile_key(*source,0)],stock)
        self.assertEqual(self.person["action_outcomes"][-1]["time_contract"]["status"],"blocked")

    def test_collapse_during_extraction_does_not_award_resources(self):
        source=self.set_gather_source()
        stock=self.world["deposits"][tile_key(*source,0)]
        pending=self.start({"op":"gather","target":"madera"})
        run_minutes(self.sim,pending["timing"]["planned_travel_minutes"])
        self.person["needs"]["energia"]=5.01
        self.sim.tick(1)
        self.assertTrue(self.person["unconscious"])
        self.assertIsNone(self.person["pending"])
        self.assertEqual(self.person["inventory"]["madera"],0)
        self.assertEqual(self.world["deposits"][tile_key(*source,0)],stock)
        interruption=self.person["interrupted_by_collapse"]["time_contract"]
        self.assertEqual(interruption["status"],"interrupted")
        self.assertFalse(interruption["work_phase_completed"])

    def test_restart_mid_extraction_keeps_remaining_and_no_early_results(self):
        source=self.set_gather_source()
        pending=self.start({"op":"gather","target":"madera"})
        travel=pending["timing"]["planned_travel_minutes"]
        run_minutes(self.sim,travel+7)
        self.assertEqual(self.person["inventory"]["madera"],0)
        self.sim.write()
        self.sim.conn.close()
        self.sim=Simulation(db_path=self.db)
        self.person=self.sim.s["person"];self.world=self.sim.s["world"]
        self.sim.think=lambda:None
        self.assertEqual(self.sim.entropy_origin,"restored_exact")
        self.assertEqual(self.person["pending"]["timing"]["phase"],"work")
        self.assertAlmostEqual(self.person["pending"]["remaining"],13)
        run_minutes(self.sim,12)
        self.assertEqual(self.person["inventory"]["madera"],0)
        run_minutes(self.sim,1)
        self.assertEqual(self.person["inventory"]["madera"],2)

    def test_multi_step_does_not_build_before_its_own_work(self):
        self.set_gather_source(remote=False)
        self.person["plan"]=[
            {"op":"gather","target":"madera"},
            {"op":"build","name":"ensayo de apoyo","materials":["madera"],
             "purpose":"estudiar tiempos"}
        ]
        self.sim.tick(0)
        run_minutes(self.sim,20)
        self.assertEqual(self.person["inventory"]["madera"],2)
        self.assertEqual(len(self.world["structures"]),0)
        self.sim.tick(0)
        self.assertEqual(self.person["pending"]["step"]["op"],"build")
        run_minutes(self.sim,89)
        self.assertEqual(len(self.world["structures"]),0)
        run_minutes(self.sim,1)
        self.assertEqual(len(self.world["structures"]),1)
        self.assertEqual(self.person["action_outcomes"][-1]["time_contract"]["planned_work_minutes"],90)


if __name__=="__main__":
    unittest.main()
