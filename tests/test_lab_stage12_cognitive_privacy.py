"""Etapa 12 · privacidad del contexto en mundo con memoria, sin claves ni red.

Regresión basada en la ESTRUCTURA de una partida de cuatro días: no copia
recuerdos, identificadores ni contenido privado de ninguna partida de usuario.
"""
from __future__ import annotations

import copy
import json
import unittest
from unittest.mock import patch

from cognitive_projection import project_context
from nilo_runtime.agent.gateway import build_deliberation_request, build_chat_request
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


if __name__ == "__main__":
    unittest.main()
