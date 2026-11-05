"""Regresiones del selector de importación y del paquete descargable versionado."""
from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import primer_inicio
from empaquetar_version import build_package


class FirstRunImport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.new = self.root / "Nilo-0.5.9.2.4"
        self.old = self.root / "Nilo-0.5.9.2.3"
        self.new.mkdir()
        self.old.mkdir()
        (self.old / "nilo.py").write_text("pass\n", encoding="utf-8")
        (self.old / "config.env").write_text("TEST_KEY=local\n", encoding="utf-8")
        (self.old / "nilo_mundo.sqlite3").write_bytes(b"base anterior sin modificar")
        (self.new / "config.env.example").write_text("TEST_KEY=\n", encoding="utf-8")

    def prompt(self, values):
        sequence = iter(values)
        return lambda _: next(sequence)

    def test_zero_opens_manual_folder_and_imports_previous_world(self):
        with patch.object(primer_inicio, "candidates", return_value=[self.old]), \
             patch("migrar.import_from") as importer:
            result = primer_inicio.first_run(
                prompt=self.prompt(["0", str(self.old), "s"]), here=self.new)
        self.assertEqual(result, "configured")
        importer.assert_called_once_with(self.old.resolve())
        self.assertEqual((self.new / "config.env").read_text(), "TEST_KEY=local\n")
        self.assertEqual((self.old / "nilo_mundo.sqlite3").read_bytes(), b"base anterior sin modificar")
        self.assertTrue((self.new / primer_inicio.MARKER).is_file())

    def test_letter_o_keeps_backward_compatibility(self):
        with patch.object(primer_inicio, "candidates", return_value=[self.old]), \
             patch("migrar.import_from") as importer:
            primer_inicio.first_run(
                prompt=self.prompt(["O", str(self.old), "n"]), here=self.new)
        importer.assert_not_called()
        self.assertEqual((self.new / "config.env").read_text(), "TEST_KEY=local\n")

    def test_invalid_choice_does_not_create_a_new_world(self):
        with patch.object(primer_inicio, "candidates", return_value=[self.old]):
            with self.assertRaisesRegex(ValueError, "Opción no válida"):
                primer_inicio.first_run(
                    prompt=self.prompt(["99"]), here=self.new)
        self.assertFalse((self.new / primer_inicio.MARKER).exists())
        self.assertFalse((self.new / "config.env").exists())

    def test_cancelled_manual_folder_is_not_silently_a_new_world(self):
        with patch.object(primer_inicio, "candidates", return_value=[self.old]):
            with self.assertRaisesRegex(ValueError, "No se eligió"):
                primer_inicio.first_run(
                    prompt=self.prompt(["0", ""]), here=self.new)
        self.assertFalse((self.new / primer_inicio.MARKER).exists())

    def test_explicit_n_creates_new_world_without_import(self):
        with patch.object(primer_inicio, "candidates", return_value=[self.old]), \
             patch("migrar.import_from") as importer:
            result = primer_inicio.first_run(
                prompt=self.prompt(["N"]), here=self.new)
        self.assertEqual(result, "configured")
        importer.assert_not_called()
        self.assertTrue((self.new / primer_inicio.MARKER).exists())

    def test_candidates_recognize_versioned_and_github_zip_names(self):
        github = self.root / "Nilo-main"
        github.mkdir()
        (github / "nilo.py").write_text("pass\n", encoding="utf-8")
        (github / "config.env").write_text("demo\n", encoding="utf-8")
        paths = primer_inicio.candidates(self.new)
        self.assertIn(self.old, paths)
        self.assertIn(github, paths)
        self.assertNotIn(self.new, paths)


class VersionPackage(unittest.TestCase):
    def test_output_name_inner_folder_and_no_user_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            files = {
                "VERSION": "0.5.9.2.4\n",
                "INICIAR_NILO.bat": "@echo off\n",
                "primer_inicio.py": "pass\n",
                "nilo.py": "pass\n",
                "config.env.example": "GEMINI_API_KEY=\n",
                "README.md": "Bienvenido a Nilo.\n",
            }
            for name, data in files.items():
                (root / name).write_text(data, encoding="utf-8")
            manifest = {"version": "0.5.9.2.4", "files": {name:"not-needed-for-package" for name in files}}
            (root / "MANIFIESTO_SHA256.json").write_text(json.dumps(manifest), encoding="utf-8")
            (root / "config.env").write_text("SECRET=private\n", encoding="utf-8")
            (root / "nilo_mundo.sqlite3").write_bytes(b"database")
            (root / "private_keys.txt").write_text("SECRET=private\n", encoding="utf-8")
            with tempfile.TemporaryDirectory() as output:
                package = build_package(root, Path(output))
                self.assertEqual(package.name, "Nilo-0.5.9.2.4.zip")
                with zipfile.ZipFile(package) as z:
                    names = z.namelist()
                    self.assertTrue(names)
                    self.assertTrue(all(name.startswith("Nilo-0.5.9.2.4/") for name in names))
                    self.assertIn("Nilo-0.5.9.2.4/INICIAR_NILO.bat", names)
                    self.assertIn("Nilo-0.5.9.2.4/config.env.example", names)
                    self.assertFalse(any("config.env/" in name or name.endswith("/config.env") for name in names))
                    self.assertFalse(any("sqlite" in name or "private_keys" in name for name in names))
                    self.assertEqual(z.read("Nilo-0.5.9.2.4/README.md"), files["README.md"].encode())
                first = package.read_bytes()
                build_package(root, Path(output))
                self.assertEqual(first, package.read_bytes())  # Reproducible.

    def test_manifest_and_version_cannot_disagree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "VERSION").write_text("0.5.9.2.4")
            (root / "MANIFIESTO_SHA256.json").write_text(json.dumps({"version":"0.5.9.2.3","files":{}}))
            with self.assertRaisesRegex(ValueError, "versión del manifiesto"):
                build_package(root, root / "dist")


if __name__ == "__main__":
    unittest.main()
