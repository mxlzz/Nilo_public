"""Etapa 24: paquete distribuible e identidad de build sin red ni datos privados."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
import zipfile
from unittest.mock import patch

from empaquetar_version import build_package
from run_history import engine_identity


class ReleasePackaging(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="nilo24-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "source"
        self.root.mkdir()
        self.version = "0.7.0"
        sources = {
            "VERSION": self.version + "\n",
            "nilo.py": "print('nilo')\n",
            "primer_inicio.py": "print('inicio')\n",
            "INICIAR_NILO.bat": "@echo off\r\n",
            "config.env.example": "GEMINI_API_KEY=\n",
            "README.md": "# Nilo\n",
        }
        for name, value in sources.items():
            (self.root / name).write_text(value, encoding="utf-8")
        (self.root / "MANIFIESTO_SHA256.json").write_text(
            json.dumps({"version": self.version,
                        "files": {k: "sha256-calculated-during-packaging"
                                  for k in sources}}, ensure_ascii=False), "utf-8")

    def test_zip_provenance_and_every_hash(self):
        sha = "a" * 40
        (self.root / "config.env").write_text("GEMINI_API_KEY=private", "utf-8")
        (self.root / "nilo_mundo.sqlite3").write_bytes(b"private sqlite")
        with patch.dict(os.environ, {"GITHUB_SHA": sha}):
            package = build_package(self.root, self.root / "dist")
        with zipfile.ZipFile(package) as z:
            names = z.namelist()
            prefix = "Nilo-0.7.0/"
            self.assertTrue(all(x.startswith(prefix) for x in names))
            self.assertFalse(any(x.endswith("config.env") or
                                 x.endswith(".sqlite3") for x in names))
            info = json.loads(z.read(prefix + "BUILD_INFO.json"))
            self.assertEqual(info["code_commit"], sha)
            manifest = json.loads(z.read(prefix + "MANIFIESTO_SHA256.json"))
            self.assertEqual(set(manifest["files"]),
                             {k[len(prefix):] for k in names
                              if k != prefix + "MANIFIESTO_SHA256.json"})
            for name, expected in manifest["files"].items():
                self.assertEqual(hashlib.sha256(z.read(prefix + name)).hexdigest(),
                                 expected)

    def test_portable_engine_identity_without_git(self):
        self.assertIsNone(engine_identity(self.root)["code_commit"])
        (self.root / "BUILD_INFO.json").write_text(
            json.dumps({"product": "Nilo", "version": self.version,
                        "code_commit": "b" * 40}), "utf-8")
        self.assertEqual(engine_identity(self.root)["code_commit"], "b" * 40)
        (self.root / "BUILD_INFO.json").write_text(
            json.dumps({"product": "Nilo", "version": "0.6.4",
                        "code_commit": "c" * 40}), "utf-8")
        self.assertIsNone(engine_identity(self.root)["code_commit"])

    def test_mismatched_release_version_is_rejected(self):
        path = self.root / "MANIFIESTO_SHA256.json"
        data = json.loads(path.read_text("utf-8"))
        data["version"] = "0.6.4"
        path.write_text(json.dumps(data), "utf-8")
        with self.assertRaises(ValueError):
            build_package(self.root, self.root / "dist")


if __name__ == "__main__":
    unittest.main()
