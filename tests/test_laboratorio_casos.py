"""Contrato del banco de escenarios: no simular éxitos, usar Simulation real."""
import unittest

from action_contracts import SUPPORTED_OPERATIONS
from laboratorio_casos import CASES, INDEX, catalog, run


class ScenarioBankTests(unittest.TestCase):
    def test_catalogo_cubre_todas_las_operaciones(self):
        data=catalog()
        self.assertEqual(data["total"],len(CASES))
        self.assertEqual(data["sin_escenario"],[])
        self.assertEqual(len(data["operaciones"]),len(SUPPORTED_OPERATIONS))
        self.assertGreaterEqual(data["total"],50)

    def test_orden_que_no_existe_no_se_sustituye_por_exito(self):
        result=run("go-tree-name")
        self.assertEqual(result["diagnosticos_totales"],0)
        self.assertEqual(result["pasos"][0]["estado"],"rechazado")
        self.assertEqual(result["cambios"],{})
        self.assertTrue(result["pasos"][0]["codigo"])

    def test_desplazamiento_real_y_mediciones(self):
        result=run("go-coord")
        self.assertGreater(result["tiempo_simulado"],0)
        self.assertEqual(result["final"]["posicion"][:2],[16,10])
        self.assertGreaterEqual(result["diagnosticos_totales"],1)
        self.assertTrue(any(p["tipo"]=="ejecucion" for p in result["pasos"]))

    def test_cierre_no_verificado_no_es_exito_inventado(self):
        result=run("plan-close-unproven")
        self.assertTrue(any(s["tipo"]=="plan" for s in result["pasos"]))
        self.assertNotIn("cerré exitosamente",str(result["pasos"]).lower())

    def test_recorrido_complejo_con_factores_distintos(self):
        result=run("plan-craft-excavate")
        self.assertTrue(any("validar" in (s.get("titulo","").lower()) for s in result["pasos"]))
        self.assertGreater(result["tiempo_simulado"],0)

    def test_semilla_reproducible_en_efectos_fisicos(self):
        a=run("gather-stone",seed=7321)
        b=run("gather-stone",seed=7321)
        print("LAB_GATHER_STONE", {"cambios":a["cambios"],"etapas": [(s["tipo"],s.get("descripcion")) for s in a["pasos"]],"estados":a["estados"]},flush=True)
        self.assertEqual(a["cambios"].get("inventario_delta"),b["cambios"].get("inventario_delta"))
        self.assertGreaterEqual(a["diagnosticos_totales"],1)

    def test_suite_representativa_por_grupo(self):
        ids=("explore-auto","inspect-invisible","go-rock","go-water","explore-exhausted",
             "gather-remote","gather-empty","experiment","craft","excavate-no-tool",
             "interact-load","interact-store","interact-overload","modify","design",
             "plan-rejected-step","plan-with-project","plan-reconsider","plan-collapse","plan-paused")
        for id in ids:
            with self.subTest(id=id):
                value=run(id)
                self.assertTrue(value["pasos"])
                self.assertIn(value["objetivo_esperado"],("accion","fallo","rechazo","interrupcion"))
                self.assertTrue(all("titulo" in x for x in value["pasos"]))


    def test_catalogo_completo(self):
        import json
        mismatches=[]
        for spec in CASES:
            try:
                report=run(spec["id"])
                if not report["cumple_expectativa"]:
                    mismatches.append({"id":spec["id"],"esperado":spec["expected"],
                                       "estados":report["estados"],
                                       "pasos":[(p["tipo"],p.get("descripcion")) for p in report["pasos"]][-3:]})
            except Exception as exc:
                mismatches.append({"id":spec["id"],"excepcion":repr(exc)})
        print("LAB_COBERTURA="+json.dumps({"total":len(CASES),"revisar":mismatches},ensure_ascii=False),flush=True)
        self.assertEqual(mismatches,[],mismatches)

    def test_sintaxis_js_del_laboratorio_nuevo(self):
        import shutil
        import subprocess
        import tempfile
        from pathlib import Path
        from laboratorio_motor import SCENARIO_HTML_FILE
        html=SCENARIO_HTML_FILE.read_text(encoding="utf-8")
        self.assertIn("Catálogo de escenarios",html)
        node=shutil.which("node")
        if not node:
            self.skipTest("Node no disponible")
        js=html.split("<script>",1)[1].split("</script>",1)[0]
        with tempfile.TemporaryDirectory() as dir:
            path=Path(dir)/"interfaz.js"
            path.write_text(js,encoding="utf-8")
            result=subprocess.run([node,"--check",str(path)],
                                  capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)


if __name__=="__main__":
    unittest.main()
