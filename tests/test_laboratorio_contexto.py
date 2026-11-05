"""Verifica valores literales, roles y serialización del contexto del laboratorio."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from laboratorio_casos import run
from laboratorio_contexto import contexto_de_deliberacion, solicitud_completa, vista_de_contexto
from laboratorio_motor import SCENARIO_HTML_FILE
from nilo import Simulation


class LabPayloadTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="nilo-contexto-")
        self.addCleanup(self.temp.cleanup)
        self.sim=Simulation(db_path=Path(self.temp.name)/"ensayo.sqlite3",
                            world_seed=7321,rng_seed=9821)
        self.addCleanup(self.sim.conn.close)

    def test_el_contexto_contiene_valores_y_no_solo_nombres(self):
        base=contexto_de_deliberacion(self.sim)
        self.assertEqual(base["posición"],self.sim.s["person"]["pos"])
        self.assertIn("necesidades",base)
        self.assertIn("conversaciones_recientes",base)
        self.assertEqual(base["conversaciones_recientes"],[])
        for provider in ("gemini","groq"):
            req=solicitud_completa(base,provider)
            sent=req["datos_recibidos_con_valores"]
            self.assertIsInstance(sent,dict)
            self.assertEqual(sent["posición"],base["posición"])
            self.assertIn("necesidades",sent)
            self.assertIn("inventario_materiales",sent)
            self.assertGreater(len(req["mensaje_sistema"]),200)
            self.assertGreater(len(req["mensaje_usuario"]),100)
            self.assertIn("op",req["solicitud_serializada"])
            self.assertEqual(json.loads(req["solicitud_serializada"]),
                             req["solicitud_json"])
            self.assertEqual(req["solicitud_serializada"],
                             json.dumps(req["solicitud_json"],ensure_ascii=False))
            self.assertEqual(req["bytes_solicitud"],
                             len(req["solicitud_serializada"].encode("utf-8")))
            self.assertTrue(set(req["campos_omitidos"]).isdisjoint(sent))
            self.assertNotIn("previsualizacion-sin-red",req["solicitud_serializada"])

    def test_roles_reales_y_contratos_diferenciados(self):
        base=contexto_de_deliberacion(self.sim)
        gemini=solicitud_completa(base,"gemini")
        groq=solicitud_completa(base,"groq")
        self.assertIn("systemInstruction",gemini["solicitud_json"])
        self.assertIn("SITUACIÓN REAL:",gemini["mensaje_usuario"])
        self.assertIn("OPERACIONES DISPONIBLES",groq["mensaje_sistema"])
        self.assertTrue(groq["mensaje_usuario"].startswith("{"))
        self.assertEqual(groq["solicitud_json"]["messages"][1]["role"],"user")
        self.assertIn("plan",gemini["mensaje_sistema"])

    def test_escenario_rest_expone_vista_antes_y_despues(self):
        report=run("rest",seed=7321)
        self.assertIn("solicitudes",report["contexto_final"])
        self.assertIn("gemini",report["contexto_final"]["solicitudes"])
        self.assertIn("groq",report["contexto_final"]["solicitudes"])
        self.assertGreater(report["tiempo_simulado"],0)
        self.assertEqual(report["contexto_final"]["solicitudes"]["gemini"]
                         ["datos_recibidos_con_valores"]["posición"],
                         report["final"]["posicion"])
        self.assertIn("minuto",report["final"])
        self.assertNotIn("contexto_previo_con_valores",
                         report["contexto_final"]["solicitudes"]["gemini"]
                         ["datos_recibidos_con_valores"])

    def test_interfaz_dos_columnas_y_ayudas(self):
        html=SCENARIO_HTML_FILE.read_text(encoding="utf-8")
        self.assertIn('id="leftColumn"',html)
        self.assertIn('id="llmBody"',html)
        self.assertIn('id="helpDialog"',html)
        self.assertIn("solicitud_serializada",html)
        self.assertNotIn('id="runAll"',html)
        self.assertNotIn('id="coverage"',html)
        self.assertNotIn('id="total"',html)
        node=shutil.which("node")
        if node:
            js=html.split("<script>",1)[1].split("</script>",1)[0]
            file=Path(self.temp.name)/"interfaz.js"
            file.write_text(js,encoding="utf-8")
            check=subprocess.run([node,"--check",str(file)],capture_output=True,text=True,timeout=10)
            self.assertEqual(check.returncode,0,check.stderr)


if __name__=="__main__":
    unittest.main()
