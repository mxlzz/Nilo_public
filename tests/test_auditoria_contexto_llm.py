"""Pruebas de la auditoría de payloads. No realiza solicitudes externas."""
import json
import unittest

from auditar_contexto_llm import (
    PROVIDERS, audit_all, audit_case, extract_sent_context, scenario_context,
    signals,
)
from brain import build_deliberation_request


class PayloadAudit(unittest.TestCase):
    def test_all_synthetic_cases_and_providers_are_auditable(self):
        report = audit_all()
        self.assertEqual(len(report["resultados"]), 4 * len(PROVIDERS))
        for row in report["resultados"]:
            self.assertTrue(row["contexto_enviado_bytes"] > 0)
            self.assertTrue(set(row["campos_enviados"]) <=
                            set(row["campos_originales"]) | {"contexto_reducido", "antecedente_relevante"})
            self.assertEqual(row["datos"], "sinteticos")

    def test_no_internal_needs_reach_any_provider(self):
        for provider in PROVIDERS:
            for kind in ("inicio", "proyecto_refugio", "pausa", "contexto_extenso"):
                with self.subTest(provider=provider, kind=kind):
                    result = audit_case(kind, provider)
                    self.assertFalse(
                        result["senales"]["necesidades_con_reservas_internas"])

    def test_extraction_catches_real_payload_not_precompaction(self):
        for provider, cfg in PROVIDERS.items():
            with self.subTest(provider=provider):
                context = scenario_context("contexto_extenso")
                _, payload, _ = build_deliberation_request(cfg, context)
                selected = extract_sent_context(provider, payload)
                self.assertIn("necesidades", selected)
                self.assertIn("proyecto_actual", selected)
                self.assertIn("regla", selected)
                self.assertTrue(len(selected) > 2)
                self.assertEqual(
                    signals(selected),
                    audit_case("contexto_extenso", provider)["senales"])

    def test_report_contains_metadata_not_model_prompts(self):
        report = audit_all()
        encoded = json.dumps(report, ensure_ascii=False)
        self.assertNotIn("clave-ficticia-no-enviar", encoded)
        self.assertNotIn("Inspección sin nuevos datos físicos disponibles", encoded)
        self.assertIn("campos_omitidos", encoded)
        self.assertIn("senales", encoded)

    def test_instrument_flags_numeric_project_without_demanding_it_exist(self):
        self.assertTrue(signals({"proyecto_actual": {"progress": 95}})
                        ["progreso_numerico_del_proyecto"])
        self.assertFalse(signals({"proyecto_actual": {"estado": "sin comprobar"}})
                         ["progreso_numerico_del_proyecto"])


if __name__ == "__main__":
    unittest.main()
