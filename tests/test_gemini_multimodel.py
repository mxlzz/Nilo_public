"""Regresiones del respaldo automático por modelo de Gemini.

No hacen llamadas a APIs; simulan 429/credenciales diferentes.
"""
import threading
import time
import unittest

from providers import (
    ProviderFailure, ProvidersUnavailable, candidate_configs,
    public_info, route, routing_signature,
)


class GeminiFallbackTests(unittest.TestCase):
    def config(self, key="key-1", fallback="gemini-3.5-flash-lite,gemini-3.8-flash"):
        return {
            "PROVIDER": "gemini", "MODEL": "gemini-3.1-flash-lite",
            "GEMINI_API_KEY": key, "GEMINI_FALLBACK_MODELS": fallback,
            "BACKUP_PROVIDER": "groq", "GROQ_API_KEY": "groq-key",
            "GROQ_MODEL": "openai/gpt-oss-20b",
        }

    def test_order_and_unique_models(self):
        config = self.config(fallback="gemini-3.1-flash-lite,gemini-3.5-flash-lite; gemini-3.8-flash")
        results = candidate_configs(config)
        self.assertEqual(
            [(name, cfg["MODEL"]) for name, cfg in results],
            [
                ("gemini", "gemini-3.1-flash-lite"),
                ("gemini", "gemini-3.5-flash-lite"),
                ("gemini", "gemini-3.8-flash"),
                ("groq", "openai/gpt-oss-20b"),
            ],
        )

    def test_429_on_one_gemini_uses_next_gemini_before_groq(self):
        state = {}
        seen = []
        def handler(cfg):
            seen.append((cfg["PROVIDER"], cfg["MODEL"]))
            if cfg["MODEL"] == "gemini-3.1-flash-lite":
                raise ProviderFailure("Gemini RPD daily quota", category="daily_quota", status=429, retry_after=600)
            return {"plan": []}
        result, name, model = route(self.config(), state, threading.RLock(), handler)
        self.assertEqual(result, {"plan": []})
        self.assertEqual((name, model), ("gemini", "gemini-3.5-flash-lite"))
        self.assertEqual(len(seen), 2)
        status = public_info(self.config(), state)["providers"]
        self.assertEqual(status[0]["status"], "en espera")
        self.assertEqual(status[1]["status"], "disponible")
        self.assertNotEqual(status[0]["health_key"], status[1]["health_key"])

    def test_key_rotation_does_not_inherit_cooldown(self):
        state = {}
        first = self.config(key="old", fallback="")
        first["BACKUP_PROVIDER"] = "none"
        with self.assertRaises(ProvidersUnavailable):
            route(first, state, threading.RLock(),
                  lambda cfg: (_ for _ in ()).throw(
                      ProviderFailure("quota", "daily_quota", 429, 7200)))
        second = self.config(key="new", fallback="")
        second["BACKUP_PROVIDER"] = "none"
        self.assertNotEqual(routing_signature(first), routing_signature(second))
        result, name, model = route(second, state, threading.RLock(),
                                    lambda cfg: ("ok", cfg["MODEL"]))
        self.assertEqual(result, ("ok", "gemini-3.1-flash-lite"))
        self.assertEqual(name, "gemini")

    def test_old_legacy_gemini_cooldown_does_not_block_new_model(self):
        state = {"provider_health": {"gemini": {"cooldown_until": time.time() + 100000}}}
        result, name, model = route(self.config(fallback=""), state,
                                    threading.RLock(), lambda cfg: "ok")
        self.assertEqual((result, name, model), ("ok", "gemini", "gemini-3.1-flash-lite"))

    def test_fallback_can_be_disabled(self):
        models = candidate_configs(self.config(fallback=""))
        self.assertEqual(len([n for n, _ in models if n == "gemini"]), 1)

    def test_restart_with_new_key_unfreezes_old_provider_wait(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        import nilo
        old = self.config(key="old-key", fallback="")
        new = self.config(key="new-key", fallback="gemini-3.5-flash-lite")
        with TemporaryDirectory() as folder:
            db = Path(folder) / "save.sqlite"
            with patch.object(nilo, "config", return_value=old):
                sim = nilo.Simulation(db_path=db)
                sim.s["mode"] = "espera"
                sim.s["next_deliberation_real"] = time.time() + 5000
                sim.s["auto_wait_frozen"] = True
                sim.write()
                sim.conn.close()
            with patch.object(nilo, "config", return_value=new):
                reopened = nilo.Simulation(db_path=db)
                self.assertEqual(reopened.s["next_deliberation_real"], 0)
                self.assertFalse(reopened.s["auto_wait_frozen"])
                self.assertEqual(reopened.s["routing_signature"], routing_signature(new))
                reopened.conn.close()


if __name__ == "__main__":
    unittest.main()
