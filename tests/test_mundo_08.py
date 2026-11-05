"""Etapa 08: topología/semillas/recursos de isla_v1 sin cambios respecto a 0.6.4."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import unittest
from unittest.mock import patch

import catalogo
import world
from environments import get_environment
from nilo_runtime.application.bootstrap import initial_state
from nilo_runtime.worlds.contracts import WorldDefinition, WorldGenerator
from nilo_runtime.worlds.island import (
    ISLAND_DEFINITION, ISLAND_GENERATOR,
    W, H, PASSABLE, DIRS, WorldTopologyError,
    tile_key, valid, tile, set_tile, new_world, reveal,
    validate_generated_world,
)

ROOT=Path(__file__).resolve().parent.parent

# Huellas calculadas con el GENERADOR ORIGINAL de Nilo 0.6.4 (no usando
# nilo_runtime.worlds.island), sobre todo el dict ordenado del mundo con
# json.dumps(... ensure_ascii=False, separators=(",",":")).
# Cubren topología, z, recursos, sitios, orden de descubrimiento y campos de save.
BASELINE_SHA256={
    0: "0ee59a26fe2eb4baa3ca65867e5972a10572459f59832729db46f43359f3f0e4",
    1: "17b55dfe193b4b3895e03d9d8816d53ce88eabab49c0b4555cc0f8b561580cb4",
    42: "663457a9a0213eca8629be1b605f61dfda03d9e94864afe51cc067855df7cb4c",
    7321: "ae1b04e016a93c1b2bad5ec0ce9297aab78f1ef828fb6fa0df93aab2409d39f9",
    9821: "7b6e50aa927118c3e4b4ab50ef09e90b928adef33929e08fa80b8541376e88ce",
    987654321: "9bf53ad60377ea7e8dabb0b31e57f420f0b4c61b065fcc7ca8a30df3193325d0",
}


def fingerprint(w):
    return hashlib.sha256(
        json.dumps(w,ensure_ascii=False,separators=(",",":")).encode("utf-8")
    ).hexdigest()


class IslandGenerationBaselineTests(unittest.TestCase):
    def test_seeded_world_exact_baseline_including_all_resources_and_order(self):
        for seed,expected in BASELINE_SHA256.items():
            with self.subTest(seed=seed):
                generated=new_world(seed)
                self.assertEqual(fingerprint(generated),expected)
                self.assertEqual(fingerprint(world.new_world(seed)),expected)
                self.assertEqual(fingerprint(ISLAND_GENERATOR.generate(seed)),expected)
                validate_generated_world(generated)

    def test_initial_state_and_environment_use_the_one_generator(self):
        self.assertIs(world.new_world,new_world)
        self.assertIs(world.tile,tile)
        self.assertIs(world.reveal,reveal)
        self.assertIs(world.DIRS,DIRS)
        self.assertIs(world.PASSABLE,PASSABLE)
        environment=get_environment("isla_v1")
        self.assertIs(environment.world_definition,ISLAND_DEFINITION)
        self.assertIsInstance(ISLAND_GENERATOR,WorldGenerator)
        for seed in (0,42,7321):
            with self.subTest(seed=seed):
                self.assertEqual(fingerprint(environment.make_world(seed)),
                                 BASELINE_SHA256[seed])
                with patch("nilo_runtime.application.bootstrap.time.time",
                           return_value=1700000000):
                    state=initial_state(seed)
                self.assertEqual(fingerprint(state["world"]),BASELINE_SHA256[seed])
                self.assertEqual(state["version"],5)
                self.assertEqual(state["person"]["pos"],[15,10,0])

    def test_topology_is_described_without_exposing_agent_knowledge(self):
        d=ISLAND_DEFINITION
        self.assertIsInstance(d,WorldDefinition)
        self.assertEqual((W,H),(37,21))
        self.assertEqual((d.width,d.height),(37,21))
        self.assertEqual(d.levels,("0","-1"))
        self.assertEqual(d.environment_id,"isla_v1")
        self.assertEqual(d.generator_version,1)
        self.assertEqual(d.site_positions,(
            ("refugio",15,10,0),("cueva",23,7,0),("ruinas",12,7,0)))
        self.assertEqual(d.terrain_symbols,frozenset(catalogo.TERRAINS))
        self.assertEqual(d.passable_symbols,frozenset(catalogo.PASSABLE))
        self.assertEqual(d.resource_symbols,frozenset(catalogo.YIELDS))
        self.assertEqual(set(PASSABLE),set(".,Tocrs=h:vse"))
        self.assertIsNot(PASSABLE,catalogo.PASSABLE)
        self.assertEqual(DIRS,[(0,-1),(1,0),(0,1),(-1,0)])
        description=d.describe()
        description["site_positions"][0]["name"]="otro"
        description["terrain_symbols"].append("X")
        self.assertEqual(d.site_positions[0][0],"refugio")
        self.assertNotIn("X",d.terrain_symbols)
        self.assertNotIn("actor",d.describe())
        self.assertNotIn("knowledge",d.describe())
        with self.assertRaises(Exception):
            d.width=123

    def test_generated_levels_portal_and_deposit_catalog(self):
        w=ISLAND_GENERATOR.generate(7321)
        self.assertEqual(tuple(w["levels"]),("0","-1"))
        for z in ("0","-1"):
            self.assertEqual(len(w["levels"][z]),H)
            self.assertTrue(all(len(row)==W for row in w["levels"][z]))
        self.assertEqual(tile(w,23,7,0),"c")
        self.assertEqual(tile(w,23,7,-1),"e")
        self.assertEqual(tile(w,15,10,0),"h")
        self.assertEqual(w["sites"]["ruinas"],{"x":12,"y":7,"z":0})
        self.assertEqual(w["structures"],[])
        self.assertEqual(w["trail"],[])
        deposits={tile_key(x,y,int(z))
                 for z,rows in w["levels"].items()
                 for y,row in enumerate(rows)
                 for x,symbol in enumerate(row)
                 if symbol in catalogo.YIELDS}
        self.assertEqual(set(w["deposits"]),deposits)
        self.assertTrue(all(type(q) is int and 2<=q<=6
                            for q in w["deposits"].values()))
        self.assertEqual(len(w["revealed"]),37)
        self.assertEqual(len(w["revealed"]),len(set(w["revealed"])))
        self.assertTrue(all(k.endswith(",0") for k in w["revealed"]))
        self.assertTrue(all(abs(int(k.split(",")[0])-15)<=3 for k in w["revealed"]))

    def test_generator_isolated_from_global_random_and_other_worlds(self):
        state=random.getstate()
        try:
            random.seed(5)
            before=random.getstate()
            a=ISLAND_GENERATOR.generate(42)
            self.assertEqual(random.getstate(),before)
            random.seed(90404)
            b=ISLAND_GENERATOR.generate(42)
            self.assertEqual(fingerprint(a),fingerprint(b))
            set_tile(a,16,12,0,"h")
            self.assertNotEqual(tile(a,16,12,0),tile(b,16,12,0))
            a["deposits"].clear()
            self.assertTrue(b["deposits"])
            self.assertEqual(fingerprint(b),BASELINE_SHA256[42])
            self.assertNotEqual(fingerprint(new_world(0)),fingerprint(new_world(1)))
        finally:
            random.setstate(state)

    def test_cross_process_hashseed_and_rng_do_not_change_topology(self):
        script=(
            "import hashlib,json,random,sys;"
            "random.seed(int(sys.argv[1]));"
            "from nilo_runtime.worlds.island import new_world;"
            "w=new_world(7321);"
            "print(hashlib.sha256(json.dumps(w,ensure_ascii=False,"
            "separators=(',',':')).encode()).hexdigest())"
        )
        for hashseed,randseed in ((11,1002),(97,3030)):
            with self.subTest(hashseed=hashseed):
                env=os.environ.copy()
                env["PYTHONHASHSEED"]=str(hashseed)
                env["PYTHONDONTWRITEBYTECODE"]="1"
                process=subprocess.run(
                    [sys.executable,"-B","-c",script,str(randseed)],
                    cwd=ROOT,env=env,capture_output=True,text=True,timeout=30,
                )
                self.assertEqual(process.returncode,0,process.stderr)
                self.assertEqual(process.stdout.strip(),BASELINE_SHA256[7321])

    def test_topology_validator_rejects_broken_new_generations_without_editing(self):
        original=new_world(7321)
        mutators={
            "missing_layer":lambda w:w["levels"].pop("-1"),
            "wrong_height":lambda w:w["levels"]["0"].pop(),
            "wrong_width":lambda w:w["levels"]["0"].__setitem__(3,"short"),
            "bad_symbol":lambda w:set_tile(w,12,12,0,"!"),
            "wrong_portal":lambda w:set_tile(w,23,7,-1,"#"),
            "wrong_site":lambda w:w["sites"]["cueva"].update({"x":24}),
            "negative_deposit":lambda w:w["deposits"].__setitem__(
                next(iter(w["deposits"])),-5),
            "missing_deposit":lambda w:w["deposits"].pop(next(iter(w["deposits"]))),
            "empty_initial_deposit":lambda w:w["deposits"].__setitem__(
                next(iter(w["deposits"])),0),
            "impossible_initial_quantity":lambda w:w["deposits"].__setitem__(
                next(iter(w["deposits"])),7),
            "invalid_key":lambda w:w["deposits"].__setitem__("100,8,0",5),
            "duplicate_reveal":lambda w:w["revealed"].append(w["revealed"][0]),
            "unknown_reveal":lambda w:w["revealed"].append("77,77,1"),
        }
        for label,mutate in mutators.items():
            with self.subTest(case=label):
                damaged=deepcopy(original)
                mutate(damaged)
                before=fingerprint(damaged)
                with self.assertRaises(WorldTopologyError):
                    validate_generated_world(damaged)
                self.assertEqual(fingerprint(damaged),before)
        self.assertEqual(fingerprint(original),BASELINE_SHA256[7321])

    def test_revealing_uses_same_order_and_does_not_regenerate(self):
        w=ISLAND_GENERATOR.generate(7321)
        before=fingerprint(w)
        self.assertEqual(reveal(w,15,10,0,3),[])
        self.assertEqual(fingerprint(w),before)
        newly=reveal(w,23,7,0,1)
        self.assertEqual(len(newly),9)
        self.assertEqual(len(w["revealed"]),46)
        self.assertEqual(newly[0][:2],(22,6))
        self.assertEqual(len(w["revealed"]),len(set(w["revealed"])))


if __name__=="__main__":
    unittest.main()
