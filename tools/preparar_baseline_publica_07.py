"""Verifica y extrae seis partidas sinteticas sin acceder a repositorios privados."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sqlite3
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    fixtures = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
    manifest = json.loads((fixtures / "baseline_historico_07.json").read_text())
    assert manifest["synthetic"] is True
    entries = manifest["files"]
    assert len(entries) == 6
    expected = {entry["path"]: entry for entry in entries}
    assert len(expected) == 6
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(fixtures / "baseline_historico_07.zip") as archive:
        names = [entry.filename for entry in archive.infolist() if not entry.is_dir()]
        assert set(names) == set(expected) and len(names) == 6
        content = {}
        for name in names:
            relative = PurePosixPath(name)
            assert not relative.is_absolute() and ".." not in relative.parts
            data = archive.read(name)
            assert len(data) == expected[name]["bytes"]
            assert hashlib.sha256(data).hexdigest() == expected[name]["sha256"]
            content[name] = data
        for name, data in content.items():
            destination = output / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            with sqlite3.connect(f"{destination.as_uri()}?mode=ro", uri=True) as db:
                assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
                state = json.loads(db.execute("SELECT payload FROM snapshot WHERE id=1").fetchone()[0])
                assert state["world"]["seed"] == manifest["worldSeed"]
                assert 0 <= state["person"]["clock_minutes"] <= 31
    print(json.dumps({"synthetic_fixtures": len(content), "sha256_verified": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
