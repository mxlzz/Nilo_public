"""0.5.9.3.17 — ubicación observada y rutas sin revelar mapa oculto.

No prueba que el LLM necesariamente elija la ruta: confirma que la
información comprobada que necesita sigue presente en contexto compacto.
"""
import unittest
from brain import context_for, compact_context, known_site_routes
from nilo import initial_state
from world import set_tile, tile_key


class KnownLocations(unittest.TestCase):
    def setUp(self):
        state=initial_state(7321)
        self.world=state["world"]
        self.person=state["person"]
        self.person["pos"]=[7,10,0]

    def test_undiscovered_sites_are_not_exposed(self):
        w,p=self.world,self.person
        w["revealed"]=[key for key in w["revealed"] if key!="12,7,0"]
        self.assertNotIn("ruinas",[x["nombre"] for x in known_site_routes(w,p)])
        self.assertNotIn("ruinas",[x["nombre"] for x in context_for(w,p,[],"Día 2")["navegacion_a_lugares"]])

    def test_ruins_have_grounded_known_path_and_survive_compaction(self):
        w,p=self.world,self.person
        # Garantizar un pasillo de ocho tramos observado y transitable.
        for x in range(7,13):
            set_tile(w,x,10,0,".")
            key=tile_key(x,10,0)
            if key not in w["revealed"]:w["revealed"].append(key)
        for y in range(7,11):
            set_tile(w,12,y,0,"r" if y==7 else ".")
            key=tile_key(12,y,0)
            if key not in w["revealed"]:w["revealed"].append(key)
        ctx=context_for(w,p,[],"Día 2")
        ruin=next(x for x in ctx["navegacion_a_lugares"] if x["nombre"]=="ruinas")
        self.assertEqual(ruin["posicion"],[12,7,0])
        self.assertEqual(ruin["acceso"],"ruta_conocida")
        self.assertEqual(ruin["tramos_conocidos"],8)
        compact=compact_context(ctx,char_budget=1250)
        self.assertEqual(next(x for x in compact["navegacion_a_lugares"] if x["nombre"]=="ruinas"),ruin)

    def test_missing_route_is_not_described_as_proven_inaccessible(self):
        w,p=self.world,self.person
        w["revealed"].append("12,7,0")
        # Sitio conocido aislado: no afirmar que es imposible llegar.
        routes=known_site_routes(w,p)
        ruin=next(x for x in routes if x["nombre"]=="ruinas")
        self.assertEqual(ruin["acceso"],"sin_ruta_conocida")
        self.assertIsNone(ruin["tramos_conocidos"])

    def test_different_level_is_not_a_same_level_go_route(self):
        w,p=self.world,self.person
        p["pos"]=[23,7,-1]
        w["revealed"].append("12,7,0")
        ruin=next(x for x in known_site_routes(w,p) if x["nombre"]=="ruinas")
        self.assertEqual(ruin["acceso"],"otro_nivel")
        self.assertIsNone(ruin["tramos_conocidos"])

    def test_existing_saved_world_data_are_not_changed_by_context(self):
        import copy
        w,p=self.world,self.person
        original=copy.deepcopy(w)
        known_site_routes(w,p)
        context_for(w,p,[],"Día 2")
        self.assertEqual(w,original)


if __name__=="__main__":
    unittest.main()
