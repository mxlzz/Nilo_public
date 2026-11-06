"""Regresiones del contrato de arquitectura de Nilo 0.7."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.auditar_arquitectura import inspect


class TestArquitectura07(unittest.TestCase):
    def check(self, sources):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name, content in sources.items():
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
            return inspect(root)

    def test_modulos_sin_ciclos(self):
        report = self.check({"a.py": "import b\n", "b.py": "VALUE = 1\n"})
        self.assertFalse(report["errors"])
        self.assertEqual(report["local_edges"], 1)

    def test_ciclos_nuevos_se_rechazan(self):
        report = self.check({"a.py": "import b\n", "b.py": "import a\n"})
        self.assertTrue(any("Ciclo nuevo" in e for e in report["errors"]))

    def test_ciclo_heredado_identificado_no_bloquea_refactor(self):
        report = self.check({"world.py": "import construction\n",
                             "construction.py": "from world import passable\n"})
        self.assertEqual(report["errors"], [])
        self.assertEqual(len(report["legacy_cycles"]), 1)

    def test_dependencia_invertida_en_core_se_rechaza(self):
        report = self.check({
            "nilo_runtime/__init__.py": "",
            "nilo_runtime/core/__init__.py": "",
            "nilo_runtime/core/a.py": "from nilo_runtime.physics import x\n",
            "nilo_runtime/physics/__init__.py": "",
            "nilo_runtime/physics/x.py": "VALUE = 1\n",
        })
        self.assertTrue(any("Dependencia invertida" in e for e in report["errors"]))

    def test_ciclo_nuevo_en_paquete_se_rechaza(self):
        report = self.check({
            "nilo_runtime/__init__.py": "",
            "nilo_runtime/core/__init__.py": "",
            "nilo_runtime/core/a.py": "from . import b\n",
            "nilo_runtime/core/b.py": "from . import a\n",
        })
        self.assertTrue(any("Ciclo nuevo en paquete" in e for e in report["errors"]))

    def test_colision_entre_modulo_y_paquete_nilo(self):
        report = self.check({"nilo.py": "", "nilo/__init__.py": ""})
        self.assertTrue(any("Colisión" in e for e in report["errors"]))


if __name__ == "__main__":
    unittest.main()
