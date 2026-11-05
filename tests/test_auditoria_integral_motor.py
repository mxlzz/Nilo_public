"""Auditoría de integración de Nilo 0.6.1: pruebas ejecutables y resultados observables.

Ejecutar en CI o localmente:
  python -m unittest tests.test_auditoria_integral_motor -v

Las decisiones de demostración NO son un LLM. Se emplean para recorrer el
ciclo completo de planificación, avance físico, registros y persistencia.
No escribe sobre bases de datos de personas ni llama a proveedores.
"""
from __future__ import annotations

import collections
import json
import random
import tempfile
import unittest
from pathlib import Path

from brain import demo_decision
from laboratorio_motor import MotorLab
from nilo import Simulation, initial_state
from world import execute_action, nearest_known, GATHER_SOURCES, reveal, prepare_navigation


def print_report(tag, value):
    print("\nAUDITORIA_" + tag + "=" + json.dumps(value, ensure_ascii=False, sort_keys=True, default=str), flush=True)


def simulate_main_loop(seed, deliberations):
    """Ejecuta el orquestador REAL, sustituyendo solamente la elección LLM por demo_decision."""
    with tempfile.TemporaryDirectory() as folder:
        filename = Path(folder) / "audit.sqlite3"
        sim = Simulation(db_path=filename, world_seed=seed, rng_seed=9821)
        sim.think = lambda: None  # No iniciar deliberaciones asincrónicas adicionales.
        sim.s["speed"] = 80
        sim.s["mode"] = "demo"
        sim.s["paused"] = False
        initial_time = sim.s["person"]["clock_minutes"]
        initial_known = len(sim.s["world"]["revealed"])
        early_stop = None
        rounds_done = 0
        total_ticks = 0
        try:
            for iteration in range(deliberations):
                p, w = sim.s["person"], sim.s["world"]
                if p.get("unconscious"):
                    early_stop = "pérdida de conciencia (sin nuevas decisiones voluntarias)"
                    break
                # El controlador demo se limita a elegir; el motor principal
                # ejecuta plan_ready, validaciones, tick, mediciones y persistencia.
                decision = demo_decision(w, p)
                sim.plan_ready(decision, "demo", {})
                rounds_done += 1
                for tick_count in range(150):
                    if not p.get("plan") and not p.get("pending"):
                        break
                    sim.tick(20.0)
                    total_ticks += 1
                else:
                    early_stop = "plan no concluido tras 150 iteraciones de reloj"
                    break
                # La simulación no debe crear recursos negativos por accidentes.
                if any(q < 0 for q in p.get("inventory", {}).values()):
                    early_stop = "inventario físico negativo"
                    break
            sim.write()
            p, w = sim.s["person"], sim.s["world"]
            categories = dict(sim.conn.execute(
                "SELECT category, COUNT(*) FROM history GROUP BY category").fetchall())
            # History almacena diagnósticos tipados de todas las acciones.
            records = sim.conn.execute(
                "SELECT payload FROM history WHERE category='diagnostic' ORDER BY seq").fetchall()
            outcomes = []
            for row in records:
                try:
                    value = json.loads(row[0])
                except (ValueError, TypeError):
                    continue
                outcomes.append(value)
            count_ops = collections.Counter(v.get("op") for v in outcomes)
            fails = collections.Counter(v.get("op") for v in outcomes if not v.get("success"))
            explore = [x for x in outcomes if x.get("op") == "explore"]
            not_discovered = sum(
                x.get("exploration_trace", {}).get("discovered_tiles", 0) == 0
                for x in explore if isinstance(x.get("exploration_trace"), dict))
            result = {
                "seed": seed,
                "requested_deliberations": deliberations,
                "performed_deliberations": rounds_done,
                "ticks": total_ticks,
                "simulated_minutes": round(p["clock_minutes"]-initial_time, 2),
                "simulated_days": round((p["clock_minutes"]-initial_time)/1440, 3),
                "known_tiles_before": initial_known,
                "known_tiles_after": len(w["revealed"]),
                "structures": len(w.get("structures", [])),
                "tools": len(p.get("items", [])),
                "projects_closed_or_paused": len(p.get("projects", [])),
                "history_categories": categories,
                "diagnostic_actions": len(outcomes),
                "ops": dict(count_ops),
                "failures": dict(fails),
                "explorations_with_no_new_tiles": not_discovered,
                "unconscious": bool(p.get("unconscious")),
                "stop": early_stop,
                "inventory_negative": any(q < 0 for q in p.get("inventory", {}).values()),
                "active_project_no_progress": (p.get("project") or {}).get("no_progress_steps"),
                "active_project_failures": (p.get("project") or {}).get("failed_actions"),
            }
            sim.conn.close()
            recovered = Simulation(db_path=filename, rng_seed=9821)
            result["persisted_time_matches"] = abs(
                recovered.s["person"]["clock_minutes"]-p["clock_minutes"]) < 1e-5
            result["persisted_world_matches"] = (
                recovered.s["world"]["revealed"] == w["revealed"]
                and recovered.s["person"]["pos"] == p["pos"])
            recovered.conn.close()
            return result
        finally:
            try:
                sim.conn.close()
            except Exception:
                pass


def systematic_actions(seed=7321):
    """Prueba cada contrato desde formularios estructurados sobre el motor real."""
    lab = MotorLab()
    lab.reset("nuevo", seed, True)
    p, w = lab.person, lab.world
    p["pos"] = [15, 10, 0]
    reveal(w, 15, 10, 0, 2)
    cases = [
        {"op":"explore"},
        {"op":"inspect", "x":15, "y":10},
        {"op":"gather", "target":"piedra"},
        {"op":"gather", "target":"madera"},
        {"op":"experiment", "target":"piedra", "method":"golpear"},
        {"op":"combine", "materials":["madera","fibra"], "method":"atar"},
        {"op":"craft", "name":"punta experimental", "purpose":"excavar roca",
         "materials":["madera","mineral oscuro"],"form":"punta",
         "geometry":{"shape":"macizo","size":1}},
        {"op":"use", "item":"punta experimental", "method":"excavar", "target":"roca"},
        {"op":"excavate"},
        {"op":"build", "name":"superficie sin función presupuesta",
         "purpose":"observar efectos", "materials":["madera","madera"],
         "geometry":{"shape":"plataforma","size":2}},
        {"op":"forage"},
        {"op":"eat"},
        {"op":"rest", "minutes":45},
        {"op":"wait", "minutes":30},
        {"op":"drink"},
        {"op":"go", "x":15, "y":10},
        {"op":"go", "target":"agua"},
        {"op":"descend"},
        {"op":"ascend"},
        {"op":"assemble","name":"mecanismo experimental",
         "parts":[{"name":"cuerpo","material":"madera","shape":"eje"},
                  {"name":"móvil","material":"madera","shape":"rueda"}],
         "joints":[{"a":0,"b":1,"type":"articulada"}]},
        {"op":"design", "name":"Experimento integral", "purpose":"medir uso",
         "principle":"transmitir una carga","procedure":"ensayar un soporte",
         "requirements":"madera","prediction":"soporta carga",
         "components":[{"name":"base","material":"madera","function":"sostener","connection":"fija"}]},
        {"op":"propose","phenomenon":"física no modelada","missing_capability":"viscosidad",
         "rationale":"ensayo no representado","experiment":"comparar flujo"},
        {"op":"report_issue","title":"Informe técnico de prueba",
         "expected":"resultado verificable", "observed":"probar el diagnóstico",
         "rationale":"auditoría de contratos"},
        {"op":"compare","topic":"Resistencia", "metric":"resistencia","evidence_ids":[]},
        {"op":"conclude","topic":"Resultados observados","evidence_ids":[]},
    ]
    results = []
    for step in cases:
        try:
            state = lab.act(step)
            r = state["last"]["result"]
            results.append({"op":step["op"],"status":r["status"],
                            "success":r["success"],"duration":r["duration_minutes"],
                            "trace_functions":len(state["last"]["trace"]),
                            "facts":r["facts"][:2]})
        except Exception as exc:
            results.append({"op":step["op"],"exception":type(exc).__name__,
                            "error":str(exc)[:160]})
    structure = next((obj for obj in w.get("structures",[])
                      if obj.get("name") == "superficie sin función presupuesta"), None)
    if structure is not None:
        for method in ("probar_carga","depositar_carga","recuperar_carga"):
            step = {"op":"interact","method":method,"item":structure["id"],
                    "material":"piedra","quantity":2}
            try:
                state = lab.act(step)
                r=state["last"]["result"]
                results.append({"op":"interact/"+method,"status":r["status"],
                                "success":r["success"],"facts":r["facts"][:2],
                                "physical":r.get("physical")})
            except Exception as exc:
                results.append({"op":"interact/"+method,"exception":type(exc).__name__,
                                "error":str(exc)[:160]})
        for step in (
            {"op":"modify","item":structure["id"],"mode":"add","materials":["madera","madera"]},
            {"op":"dismantle","item":structure["id"]}
        ):
            try:
                state=lab.act(step)
                r=state["last"]["result"]
                results.append({"op":step["op"],"status":r["status"],
                                "success":r["success"],"facts":r["facts"][:2]})
            except Exception as exc:
                results.append({"op":step["op"],"exception":type(exc).__name__,
                                "error":str(exc)[:160]})
    return {
        "seed":seed,
        "operations_covered":sorted(set(r["op"].split("/")[0] for r in results)),
        "cases":results,
        "cases_total":len(results),
        "exceptions":sum("exception" in r for r in results),
        "successes":sum(r.get("success",False) for r in results),
        "world_time":round(lab.person["clock_minutes"],3),
        "inventory":dict(lab.person["inventory"]),
        "structures":len(w.get("structures",[])),
        "tools":len(lab.person.get("items",[])),
    }


def test_rng_isolation():
    """Mismo mundo y RNG del motor, distinto RNG global: buscar IDs inestables."""
    def sample(global_seed):
        random.seed(global_seed)
        state=initial_state(7321)
        w,p=state["world"],state["person"]
        p["inventory"]["madera"]=10
        ret=execute_action(w,p,{"op":"build","name":"superficie sin función presupuesta",
                               "purpose":"observar efectos",
                               "materials":["madera","madera"],
                               "geometry":{"shape":"plataforma","size":2}},
                           random.Random(17))
        return {"ok":bool(ret[2]),"structure":w["structures"][-1]["id"] if w["structures"] else None}
    return {"global_seed_1":sample(1),"global_seed_2":sample(999),
            "same_structure_id":sample(1)["structure"]==sample(999)["structure"]}


def inspect_gather_duration():
    """Diferencia entre viajar + recolectar y recolectar junto al recurso."""
    state=initial_state(7321)
    w,p=state["world"],state["person"]
    src=nearest_known(w,p,GATHER_SOURCES["piedra"])
    if src is None:
        return {"available":False}
    tx,ty,wx,wy=src
    base_inventory=p["inventory"].get("piedra",0)
    p["pos"]=[wx,wy,0]
    reveal(w,wx,wy,0,2)
    close=execute_action(w,p,{"op":"gather","target":"piedra"},random.Random(17))
    on_site={"success":close[2],"duration":close[0],
             "inventory_added":p["inventory"].get("piedra",0)-base_inventory}
    # Reset para ensayar desde un punto que requiera traslado con fuente conocida.
    state2=initial_state(7321)
    w2,p2=state2["world"],state2["person"]
    nav=prepare_navigation(w2,p2,{"op":"gather","target":"piedra"},random.Random(17))
    if nav is None:
        return {"available":True,"on_site":on_site,"remote_nav":False}
    lab=MotorLab()
    lab.world=w2
    lab.person=p2
    lab.environment=__import__("environments").get_environment("isla_v1")
    before=p2["inventory"].get("piedra",0)
    remote=lab.act({"op":"gather","target":"piedra"})["last"]["result"]
    return {"available":True,"on_site":on_site,"remote_nav":True,
            "remote":{"success":remote["success"],"duration":remote["duration_minutes"],
                      "inventory_added":p2["inventory"].get("piedra",0)-before,
                      "route_tiles":len(nav["route"])},
            "remote_duration_contains_extraction":remote["duration_minutes"]>=len(nav["route"])*3+12}


class FullEngineAuditTests(unittest.TestCase):
    def test_01_full_orchestrator_cycle_without_llm(self):
        first=simulate_main_loop(7321, 60)
        second=simulate_main_loop(2026, 35)
        print_report("ORQUESTADOR", [first, second])
        for result in (first,second):
            self.assertTrue(result["persisted_world_matches"])
            self.assertTrue(result["persisted_time_matches"])
            self.assertFalse(result["inventory_negative"])
            self.assertGreater(result["diagnostic_actions"],0)
            self.assertGreater(result["simulated_minutes"],0)
            self.assertGreater(result["known_tiles_after"],0)

    def test_02_all_operations_real_engine(self):
        audit=systematic_actions()
        print_report("ACCIONES",audit)
        self.assertGreaterEqual(len(audit["operations_covered"]),22)
        self.assertGreater(audit["cases_total"],24)
        self.assertGreater(audit["successes"],7)

    def test_03_rng_structure_identifiers(self):
        audit=test_rng_isolation()
        print_report("RNG",audit)
        self.assertTrue(audit["global_seed_1"]["ok"])
        self.assertTrue(audit["global_seed_2"]["ok"])

    def test_04_gather_travel_extraction_duration(self):
        audit=inspect_gather_duration()
        print_report("GATHER_TIEMPO",audit)
        self.assertTrue(audit["available"])
        self.assertTrue(audit["on_site"]["success"])


    def test_05_long_demo_plateau(self):
        result=simulate_main_loop(7321, 235)
        print_report("PLATEAU_LARGO", result)
        self.assertFalse(result["inventory_negative"])
        self.assertTrue(result["persisted_world_matches"])
        self.assertGreater(result["diagnostic_actions"], 200)

    def test_06_cave_two_level_cycle(self):
        from world import cave_exit, reveal
        lab=MotorLab()
        ex,ey=cave_exit(lab.world)
        lab.person["pos"]=[ex,ey,0]
        reveal(lab.world,ex,ey,0,2)
        down=lab.act({"op":"descend"})["last"]["result"]
        pos_down=list(lab.person["pos"])
        up=lab.act({"op":"ascend"})["last"]["result"]
        result={"entrance":[ex,ey],"descend":down["status"],
                "position_down":pos_down,"ascend":up["status"],
                "position_up":list(lab.person["pos"])}
        print_report("CUEVA", result)
        self.assertTrue(down["success"], down["facts"])
        self.assertEqual(pos_down[2], -1)
        self.assertTrue(up["success"], up["facts"])
        self.assertEqual(lab.person["pos"][2], 0)

    def test_07_structures_storage_and_reinforcement(self):
        from world import reveal
        lab=MotorLab()
        lab.person["pos"]=[15,10,0]
        reveal(lab.world,15,10,0,2)
        build=lab.act({"op":"build","name":"superficie de prueba aislada",
                       "purpose":"ensayo físico", "materials":["madera","madera"],
                       "geometry":{"shape":"plataforma","size":2}})["last"]["result"]
        self.assertTrue(build["success"],build["facts"])
        ident=lab.world["structures"][-1]["id"]
        inventory0=lab.person["inventory"]["piedra"]
        tested=lab.act({"op":"interact","method":"probar_carga",
                        "item":ident,"material":"piedra","quantity":2})["last"]["result"]
        inventory1=lab.person["inventory"]["piedra"]
        deposited=lab.act({"op":"interact","method":"depositar_carga",
                           "item":ident,"material":"piedra","quantity":2})["last"]["result"]
        inventory2=lab.person["inventory"]["piedra"]
        changed=lab.act({"op":"modify","item":ident,"mode":"add",
                         "materials":["madera","madera"]})["last"]["result"]
        retrieved=lab.act({"op":"interact","method":"recuperar_carga",
                           "item":ident,"material":"piedra","quantity":2})["last"]["result"]
        inventory3=lab.person["inventory"]["piedra"]
        report={"built":build["status"],"trial":tested["status"],
                "deposit":deposited["status"],"modify":changed["status"],
                "retrieve":retrieved["status"],
                "stone_before":inventory0,"stone_after_trial":inventory1,
                "stone_after_deposit":inventory2,
                "stone_after_recovery":inventory3,
                "revision":lab.world["structures"][-1]["revision"]}
        print_report("CARGAS", report)
        self.assertTrue(tested["success"],tested["facts"])
        self.assertTrue(deposited["success"],deposited["facts"])
        self.assertTrue(changed["success"],changed["facts"])
        self.assertTrue(retrieved["success"],retrieved["facts"])
        self.assertEqual((inventory0,inventory1,inventory2,inventory3),
                         (inventory0,inventory0,inventory0-2,inventory0))
        self.assertGreaterEqual(report["revision"],2)

    def test_08_gather_nav_time(self):
        from world import PASSABLE, tile
        lab=MotorLab()
        step={"op":"gather","target":"piedra"}
        w,p=lab.world,lab.person
        original=list(p["pos"])
        chosen=None
        for key in sorted(w["revealed"]):
            x,y,z=map(int,key.split(","))
            if z!=0 or tile(w,x,y,0) not in PASSABLE:continue
            p["pos"]=[x,y,0]
            nav=prepare_navigation(w,p,step,random.Random(15))
            if nav and 1 <= len(nav["route"]) <= 9:
                chosen=nav
                break
        if not chosen:
            # Aumenta solo la región revelada para hacer posible el caso físico.
            p["pos"]=original
            for x in range(11,21):
                for y in range(8,17):
                    reveal(w,x,y,0,1)
            for key in sorted(w["revealed"]):
                x,y,z=map(int,key.split(","))
                if z!=0 or tile(w,x,y,0) not in PASSABLE:continue
                p["pos"]=[x,y,0]
                nav=prepare_navigation(w,p,step,random.Random(15))
                if nav and 1<=len(nav["route"])<=9:
                    chosen=nav
                    break
        self.assertIsNotNone(chosen,"No se encontró recurso distante en la semilla de prueba")
        before=p["inventory"].get("piedra",0)
        state=lab.act(step)
        physical=state["last"]["result"]
        after=p["inventory"].get("piedra",0)
        report={"position":list(p["pos"]),"route_len":len(chosen["route"]),
                "duration":physical["duration_minutes"],
                "inventory_gained":after-before,
                "status":physical["status"],
                "would_take_more_with_harvesting":len(chosen["route"])*3+22}
        print_report("GATHER_REMOTO",report)
        self.assertTrue(physical["success"],physical["facts"])
        self.assertGreater(after-before,0)


if __name__ == "__main__":
    unittest.main()
