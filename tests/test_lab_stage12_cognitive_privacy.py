"""Etapa 12 · privacidad del contexto en mundo con memoria, sin claves ni red.

Regresión basada en la ESTRUCTURA de una partida de cuatro días: no copia
recuerdos, identificadores ni contenido privado de ninguna partida de usuario.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cognitive_projection import project_context
from nilo_runtime.agent.gateway import build_chat_request
from nilo_runtime.application.engine import Simulation
from nilo_runtime.labs.ab_experiment import live_pair, _sent_evidence_differences
from nilo_runtime.labs.evaluation_11 import analyze_live_ab, _contains_internal_reserves
from nilo_runtime.labs.hub import LabHub
from nilo_runtime.core.lab_settings import baseline
from nilo_runtime.labs.hub import _request


def mature_context():
    return {
        "momento": "Día 4 · 20:39",
        "posición": [12, 7, 0],
        "necesidades": {"alimentacion": "sin hambre",
                       "hidratacion": "bien hidratado",
                       "energia": "algo cansado"},
        "inventario_materiales": {"madera": 26, "piedra": 18},
        "proyecto_actual": {"id": "proyecto-sintetico",
                            "title": "Explorar las ruinas y revisar salidas",
                            "status": "activo", "state": "Inspección del terreno"},
        "investigaciones_activas": [{
            "id": "pregunta-sintetica",
            "question": "¿Hay un paso accesible desde las ruinas?",
            "hypothesis": "Podría haber otra ruta.",
            "state": "abierta",
        }],
        "antecedentes_relacionados": [{
            "id": "proyecto-previo",
            "titulo": "Explorar la zona",
            "estado": "pausado",
            "motivo_de_pausa_o_cierre": "Tres rutas inaccesibles",
        }],
        "memorias_relevantes": [{
            "id": "experiencia-sintetica", "accion": "explore", "exito": False,
            "hecho": "No encuentro una frontera transitable hacia el norte.",
            "medicion_id": "med-explore",
        }],
        "mediciones_reales_recientes": [{
            "id": "med-inspeccion", "op": "inspect",
            "duracion_min": 9.417, "condicion": "intemperie",
            "energia_inicial": 48.61, "energia_final": 48.4,
            "energia_por_hora": None, "comparable": False, "fisica": None,
            "resultado": ["Inspeccioné el terreno: roca."],
        }, {
            "id": "med-recipiente", "op": "use",
            "duracion_min": 2, "comparable": True,
            "fisica": {"capacidad_util_agua": 0.49},
            "resultado": ["Se confirmó que contiene una muestra de agua."],
        }],
        "resultados_de_acciones": [{
            "id": "act-inspect", "operacion": "inspect",
            "metadata": {"energia_inicial": 48.61,
                         "energia_final": 48.4,
                         "needs_before": {"energia": 48.61}},
            "facts": ["Se observó roca."],
        }],
        "conclusiones_verificadas": [],
        "ultimo_cierre_rechazado": {
            "estado_verificacion": "evidencia_sin_cita",
            "ids_evidencia_pertinente": ["med-verificable"],
        },
        "regla": "La verdad física proviene del motor.",
    }


class Stage12PrivacyTests(unittest.TestCase):
    def test_projection_never_mutates_original_and_preserves_evidence(self):
        original = mature_context()
        frozen = copy.deepcopy(original)
        view = project_context(original)
        self.assertEqual(original, frozen)
        blob = json.dumps(view, ensure_ascii=False)
        for secret in ("energia_inicial", "energia_final", "energia_por_hora",
                       "needs_before", "48.61", "48.4"):
            self.assertNotIn(secret, blob)
        rows = view["mediciones_reales_recientes"]
        self.assertEqual([row["id"] for row in rows],
                         ["med-inspeccion", "med-recipiente"])
        self.assertEqual(rows[0]["duracion_min"], 9.417)
        self.assertFalse(rows[0]["comparable"])
        self.assertEqual(rows[0]["resultado"], ["Inspeccioné el terreno: roca."])
        self.assertEqual(rows[1]["fisica"]["capacidad_util_agua"], 0.49)
        self.assertEqual(view["memorias_relevantes"][0]["id"], "experiencia-sintetica")
        self.assertEqual(view["proyecto_actual"]["id"], "proyecto-sintetico")

    def test_both_context_modes_all_providers_share_privacy_boundary(self):
        raw = mature_context()
        preserved = copy.deepcopy(raw)
        with patch("nilo_runtime.agent.gateway._post",
                   side_effect=AssertionError("No invocar proveedores")):
            for provider in ("gemini", "groq"):
                for mode in ("baseline", "modular"):
                    with self.subTest(provider=provider, mode=mode):
                        view = _request(baseline(), raw, provider, context_mode=mode)
                        wire = view["solicitud_serializada"]
                        data = view["datos_enviados"]
                        for secret in ("energia_inicial", "energia_final",
                                       "energia_por_hora", "needs_before",
                                       "48.61", "48.4"):
                            self.assertNotIn(secret, wire)
                        self.assertEqual(data["necesidades"]["energia"],
                                         "algo cansado")
                        self.assertEqual(data["proyecto_actual"]["id"],
                                         "proyecto-sintetico")
                        self.assertTrue(view["segmentacion_verificada"])
                        self.assertFalse(view["enviado_a_llm"])
        self.assertEqual(raw, preserved)

    def test_chat_uses_the_same_projection_and_does_not_expose_raw_reserves(self):
        cfg = {"PROVIDER": "gemini", "MODEL": "gemini-3.1-flash-lite",
               "GEMINI_API_KEY": "sintetica"}
        _, payload, _ = build_chat_request(
            cfg, mature_context(), [{"role": "user", "text": "¿Qué averigüé?"}])
        wire = json.dumps(payload, ensure_ascii=False)
        self.assertNotIn("energia_inicial", wire)
        self.assertNotIn("energia_final", wire)
        self.assertNotIn("48.61", wire)
        self.assertIn("algo cansado", wire)

    def test_no_loss_of_real_physical_measurement_with_nested_body_metadata(self):
        data = mature_context()
        measurement = data["mediciones_reales_recientes"][1]
        measurement["meta"] = {"needs_after": {"energia": 70.2},
                               "inspection_code": "verified_success"}
        projected = project_context(data)
        recorded = projected["mediciones_reales_recientes"][1]
        self.assertNotIn("needs_after", recorded["meta"])
        self.assertEqual(recorded["meta"]["inspection_code"], "verified_success")
        self.assertEqual(recorded["fisica"]["capacidad_util_agua"], 0.49)


    def test_comparison_reports_same_source_but_different_sent_evidence(self):
        common = {"memorias_relevantes": [
            {"id": "recuerdo-1", "hecho": "No hay ruta al norte."}],
            "mediciones_reales_recientes": []}
        variant = copy.deepcopy(common)
        variant["mediciones_reales_recientes"].append({
            "id": "med-inspeccion", "op": "inspect",
            "resultado": ["Roca sin paso."]})
        difference = _sent_evidence_differences(
            {"datos_enviados": common},
            {"datos_enviados": variant})
        self.assertEqual(list(difference), ["mediciones_reales_recientes"])
        self.assertEqual(difference["mediciones_reales_recientes"]["only_variant_ids"],
                         ["med-inspeccion"])
        self.assertFalse(_contains_internal_reserves(variant))
        variant["mediciones_reales_recientes"][0]["energia_final"] = 48.4
        self.assertTrue(_contains_internal_reserves(variant))

    def test_synthetic_mature_saved_world_multiturn_no_network(self):
        # Contrato de 4 deliberaciones y efectos físicos, sin claves reales.
        with tempfile.TemporaryDirectory() as td:
            original = Path(td) / "mundo_guardado.sqlite3"
            sim = Simulation(db_path=original, world_seed=7321, rng_seed=9821)
            try:
                sim.s["person"]["clock_minutes"] = 4 * 1440 + 1239
                sim.write()
            finally:
                sim.conn.close()
            digest = hashlib.sha256(original.read_bytes()).hexdigest()
            seen = []

            def poster(url, payload, headers, provider):
                self.assertEqual(provider, "groq")
                self.assertEqual(headers.get("Authorization"), "Bearer simulada")
                seen.append(copy.deepcopy(payload))
                return {"choices": [{"message": {"content": json.dumps({
                    "cuaderno": "Dejo transcurrir tiempo.",
                    "accion_proyecto": "sin_proyecto",
                    "revisar_en_minutos": 90,
                    "plan": [{"op": "wait", "minutes": 20}],
                })}}],
                        "usage": {"prompt_tokens": 80, "completion_tokens": 40}}

            with patch("nilo_runtime.labs.ab_experiment.config",
                       return_value={"GROQ_API_KEY": "simulada",
                                     "MIN_REAL_SECONDS_BETWEEN_CALLS": "15"}):
                result = live_pair(
                    LabHub(Path(td)), baseline(), source="saved", world_path=original,
                    provider="groq", seed=7321, turns=2, context_mode="modular",
                    confirm=True, poster=poster, sleep_fn=lambda _: None)
            self.assertEqual(result["llm_calls"], 4)
            self.assertEqual(len(seen), 4)
            self.assertEqual(result["source"], "readonly_copy_of_saved_world")
            self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(), digest)
            for payload in seen:
                self.assertNotIn("energia_inicial", json.dumps(payload))
                self.assertNotIn("energia_final", json.dumps(payload))
            summary = analyze_live_ab(result)
            self.assertTrue(summary["behavior_evaluated"])
            self.assertEqual(summary["baseline"]["normalized_decisions"], 2)
            self.assertEqual(summary["variant"]["normalized_decisions"], 2)
            self.assertFalse(summary["causal_claim_allowed"])


if __name__ == "__main__":
    unittest.main()
