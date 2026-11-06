"""Etapa 07: motor de aplicación sin HTTP, fachada 0.6.x y trazabilidad real."""
from __future__ import annotations

from pathlib import Path
import inspect
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import nilo
from nilo_runtime.application.engine import Simulation as EngineSimulation
from nilo_runtime.application.deps import RuntimeServices
from nilo_runtime.storage.timeline import TimelineStore
from historical_lab import TimelineStore as LegacyTimelineStore
from laboratorio_casos import run

ROOT=Path(__file__).resolve().parent.parent


class HeadlessArchitectureTests(unittest.TestCase):
    def test_engine_imports_in_fresh_process_without_http_or_legacy_facade(self):
        code=r"""
import sys
from nilo_runtime.application.engine import Simulation
assert 'nilo' not in sys.modules, 'El motor depende del entrypoint histórico'
assert 'nilo_runtime.web.http' not in sys.modules, 'Importó interfaz'
assert 'http.server' not in sys.modules, 'Importó servidor HTTP'
from pathlib import Path
import tempfile
with tempfile.TemporaryDirectory() as directory:
    sim=Simulation(db_path=Path(directory)/'partida.sqlite3',world_seed=7321,rng_seed=9821)
    try:
        sim.s['speed']=60
        sim.s['paused']=False
        sim.think=lambda:None
        sim.s['person']['plan']=[{'op':'wait','minutes':5}]
        sim.tick(0)
        sim.tick(5)
        assert sim.s['person']['clock_minutes']>=5
        assert sim.s['person']['pending'] is None
        sim.write()
        print('headless-engine-v1 OK')
    finally:
        sim.conn.close()
"""
        env=os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"]="1"
        for key in list(env):
            if any(x in key.upper() for x in
                   ("API_KEY","GEMINI","GROQ","OPENAI","ANTHROPIC","TOKEN","SECRET")):
                env.pop(key,None)
        r=subprocess.run([sys.executable,"-B","-c",code],cwd=ROOT,
                         env=env, text=True,capture_output=True,timeout=45)
        self.assertEqual(r.returncode,0,r.stderr[-6000:])
        self.assertIn("headless-engine-v1 OK",r.stdout)

    def test_engine_is_composed_of_use_cases_not_http(self):
        mixins=[cls.__name__ for cls in EngineSimulation.__bases__]
        self.assertEqual(mixins,[
            "SessionLifecycle","RecordsUseCases",
            "DecisionUseCases","ClockUseCases"])
        checks={"migrate":"session.py","write":"session.py",
                "plan_ready":"decisions.py","think":"decisions.py",
                "tick":"clockwork.py","_tick_slice":"clockwork.py",
                "public_state":"records.py","start_chat":"decisions.py",
                "event":"records.py","observer_summary":"records.py"}
        for method,expected in checks.items():
            with self.subTest(method=method):
                origin=inspect.getsourcefile(inspect.unwrap(getattr(EngineSimulation,method)))
                self.assertEqual(Path(origin).name,expected)
        self.assertFalse(hasattr(EngineSimulation,"do_GET"))
        self.assertFalse(hasattr(EngineSimulation,"do_POST"))

    def test_session_timeline_has_one_storage_owner(self):
        self.assertIs(TimelineStore,LegacyTimelineStore)
        self.assertIsNotNone(inspect.getsourcefile(TimelineStore))
        self.assertEqual(Path(inspect.getsourcefile(TimelineStore)).name,"timeline.py")

    def test_http_handler_is_compatibility_alias_and_server_is_opt_in(self):
        from nilo_runtime.web.http import Handler
        self.assertIs(nilo.Handler,Handler)
        self.assertEqual(nilo.HTML_FILE,ROOT/"interfaz.html")
        self.assertTrue(nilo.HTML_FILE.is_file())


class LegacyAdapterTests(unittest.TestCase):
    def test_no_db_argument_uses_patched_nilo_db(self):
        with tempfile.TemporaryDirectory(prefix="nilo-07-legacydb-") as d:
            path=Path(d)/"legacy.sqlite3"
            with patch.object(nilo,"DB",path):
                sim=nilo.Simulation(world_seed=7321)
                try:
                    self.assertEqual(sim.conn.execute("PRAGMA database_list").fetchone()[2],
                                     str(path))
                finally:
                    sim.conn.close()

    def test_old_config_available_route_hooks_are_live(self):
        old={"PROVIDER":"fake","MODEL":"test","MAX_LLM_CALLS_PER_DAY":"100"}
        with tempfile.TemporaryDirectory(prefix="nilo-07-ports-") as d:
            with (patch.object(nilo,"config",return_value=old) as config,
                  patch.object(nilo,"available",return_value=True) as available,
                  patch.object(nilo,"route",return_value=(("resultado",{}),"test","stub")) as route):
                sim=nilo.Simulation(db_path=Path(d)/"test.sqlite3")
                try:
                    self.assertIsInstance(sim,EngineSimulation)
                    self.assertEqual(sim.services.config(),old)
                    self.assertTrue(sim.services.available(old))
                    self.assertEqual(sim.services.route("x"),(("resultado",{}),"test","stub"))
                    self.assertGreaterEqual(config.call_count,1)
                    available.assert_called()
                    route.assert_called_once()
                finally:
                    sim.conn.close()

    def test_core_accepts_ports_without_legacy_nilo_globals(self):
        calls={"config":0,"available":0}
        def cfg():
            calls["config"]+=1
            return {"PROVIDER":"none"}
        def is_available(value):
            calls["available"]+=1
            return False
        services=RuntimeServices(
            config=cfg,
            available=is_available,
            route=lambda *a,**kw: (_ for _ in ()).throw(
                AssertionError("La sesión headless no llama un LLM"))
        )
        with tempfile.TemporaryDirectory(prefix="nilo-07-coreports-") as d:
            sim=EngineSimulation(db_path=Path(d)/"core.sqlite3",services=services)
            try:
                sim.public_state()
                self.assertGreater(calls["config"],0)
                self.assertGreater(calls["available"],0)
            finally:
                sim.conn.close()

    def test_exact_same_wait_effects_through_both_entrypoints(self):
        with tempfile.TemporaryDirectory(prefix="nilo-07-routing-") as d:
            sims=[EngineSimulation(db_path=Path(d)/"core.sqlite3",rng_seed=771),
                  nilo.Simulation(db_path=Path(d)/"legacy.sqlite3",rng_seed=771)]
            try:
                results=[]
                for sim in sims:
                    sim.think=lambda:None
                    sim.s["speed"]=60
                    sim.s["paused"]=False
                    sim.s["person"]["plan"]=[{"op":"wait","minutes":6}]
                    sim.tick(0)
                    self.assertIsNotNone(sim.s["person"]["pending"])
                    sim.tick(6)
                    p=sim.s["person"]
                    results.append((
                        round(p["clock_minutes"],4),
                        p["pending"],p["plan"],
                        [(o["op"],o["evaluation_status"])
                         for o in p["action_outcomes"]],
                    ))
                self.assertEqual(results[0],results[1])
            finally:
                for sim in sims:
                    sim.conn.close()

    def test_laboratory_trace_follows_moved_action_modules(self):
        r=run("go-coord")
        self.assertTrue(r["cumple_expectativa"],r.get("pasos"))
        traces=[call for stage in r["pasos"]
                for call in stage.get("codigo",[])
                if isinstance(call,dict)]
        self.assertTrue(traces,"La traza no puede desaparecer tras reubicar métodos")
        observed={entry.get("archivo") for entry in traces}
        self.assertIn("nilo_runtime/application/clockwork.py",observed)
        self.assertIn("nilo_runtime/application/decisions.py",observed)


if __name__=="__main__":
    unittest.main()
