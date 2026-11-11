"""Regresión 0.7.1: Historial, Visor LLM y Análisis leen la misma partida seleccionada.

No hay proveedores externos ni escrituras al mundo original.
"""
from __future__ import annotations

import http.client
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch

from laboratorio_motor import HistorySource, create_lab_server
from nilo_runtime.labs.hub import LabHub
from nilo_runtime.storage.llm_requests import RequestTraceStore


def _world_and_trace(path: Path, marker: str):
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE fixture (marker TEXT)")
        db.execute("INSERT INTO fixture VALUES (?)", (marker,))
    store = RequestTraceStore.for_world(path)
    payload = json.dumps({
        "systemInstruction": {"parts": [{"text": "INSTRUCCIONES"}]},
        "contents": [{"role": "user", "parts": [{"text": marker}]}],
    }).encode("utf-8")
    attempt = store.begin(
        body=payload, call_id=("a" if marker == "ORIGEN" else "b") * 32,
        session_id=1, purpose="chat", source_id=None,
        simulated_at="Día 1 · 08:00", ordinal=1,
        provider="gemini", model="modelo_" + marker.lower(),
    )
    store.finish(attempt, "accepted")
    return attempt


class SelectedWorldConsistencyTests(unittest.TestCase):
    def test_viewer_and_analysis_follow_history_selection(self):
        with tempfile.TemporaryDirectory(prefix="nilo-selected-source-") as folder:
            root = Path(folder)
            original = root / "original.sqlite3"
            selected = root / "selected.sqlite3"
            absent = root / "without_sidecar.sqlite3"
            origin_attempt = _world_and_trace(original, "ORIGEN")
            selected_attempt = _world_and_trace(selected, "SELECCIONADA")
            with sqlite3.connect(absent) as db:
                db.execute("CREATE TABLE fixture (marker TEXT)")
            source = HistorySource()
            source.path = selected
            source.display_name = selected.name
            source.origin = "carpeta"
            server = create_lab_server(
                0, history=source, hub=LabHub(root, original)
            )
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()

            def get(url):
                conn = http.client.HTTPConnection(
                    "127.0.0.1", server.server_address[1], timeout=6
                )
                try:
                    conn.request("GET", url)
                    response = conn.getresponse()
                    return response.status, json.loads(response.read().decode("utf-8"))
                finally:
                    conn.close()

            try:
                with patch(
                    "nilo_runtime.labs.cross_analysis.analyze",
                    side_effect=lambda world, limit: {
                        "world": Path(world).name, "limit": limit
                    },
                ):
                    status, analysis = get("/api/lab/analysis?limit=8")
                self.assertEqual(status, 200)
                self.assertEqual(analysis, {"world": selected.name, "limit": 8})
                status, listing = get("/api/lab/llm/attempts")
                self.assertEqual(status, 200)
                self.assertTrue(listing["available"])
                self.assertEqual(
                    [x["attempt_id"] for x in listing["attempts"]],
                    [selected_attempt],
                )
                status, detail = get("/api/lab/llm/attempt?id=" + selected_attempt)
                self.assertEqual(status, 200)
                self.assertIn("SELECCIONADA", detail["body_utf8"])
                self.assertEqual(get(
                    "/api/lab/llm/attempt?id=" + origin_attempt
                )[0], 404)

                # Una partida sin sidecar NO debe mostrar capturas de otra.
                source.path = absent
                status, listing = get("/api/lab/llm/attempts")
                self.assertEqual(status, 200)
                self.assertFalse(listing["available"])
                self.assertEqual(listing["attempts"], [])
                self.assertEqual(get(
                    "/api/lab/llm/attempt?id=" + origin_attempt
                )[0], 404)
            finally:
                server.shutdown()
                server.server_close()
                source.temp_directory.cleanup()


if __name__ == "__main__":
    unittest.main()
