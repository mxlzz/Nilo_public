"""Etapa 01 del visor: contratos de la solicitud real, sin red ni partidas privadas."""
import copy
import json
import threading
import unittest
from unittest.mock import patch

from auditar_contexto_llm import PROVIDERS, extract_sent_context, scenario_context
from nilo_runtime.agent import gateway
from providers import ProviderFailure, route


class RequestBoundaryBaseline(unittest.TestCase):
    def test_real_request_function_uses_same_payload_as_builder_for_each_provider(self):
        for provider in ("gemini", "groq", "openai_compatible"):
            with self.subTest(provider=provider):
                cfg=dict(PROVIDERS[provider])
                context=scenario_context("contexto_extenso")
                untouched=copy.deepcopy(context)
                url,expected,headers=gateway.build_deliberation_request(cfg,context)
                captured=[]

                def record(actual_url,payload,actual_headers,name):
                    captured.append((actual_url,copy.deepcopy(payload),
                                     actual_headers,name,
                                     json.dumps(payload,ensure_ascii=False).encode("utf-8")))
                    return {"synthetic":True}

                with patch.object(gateway,"_post",side_effect=record), \
                     patch.object(gateway,"_response",
                                  return_value=('{"cuaderno":"decisión sintética"}',
                                                {"entrada":1,"salida":1})):
                    result,stats=gateway.request_llm(cfg,context)
                self.assertEqual(context,untouched)
                self.assertEqual(result["cuaderno"],"decisión sintética")
                self.assertEqual(len(captured),1)
                actual_url,payload,actual_headers,name,body=captured[0]
                self.assertEqual(actual_url,url)
                self.assertEqual(payload,expected)
                self.assertEqual(name,provider)
                self.assertEqual(body,json.dumps(expected,ensure_ascii=False).encode("utf-8"))
                self.assertIsInstance(extract_sent_context(provider,payload),dict)
                self.assertNotIn("predisposiciones",extract_sent_context(provider,payload))
                self.assertNotIn("territorio_descubierto_pct",
                                 extract_sent_context(provider,payload))
                self.assertNotIn(cfg.get("GEMINI_API_KEY","never-this"),body.decode("utf-8"))
                if provider=="gemini":
                    self.assertIn("systemInstruction",payload)
                    self.assertIn("SITUACIÓN REAL: ",payload["contents"][0]["parts"][0]["text"])
                else:
                    self.assertEqual([m["role"] for m in payload["messages"]],["system","user"])

    def test_failed_gemini_and_successful_groq_have_different_actual_bodies(self):
        cfg={
            "PROVIDER":"gemini","MODEL":"gemini-3.1-flash-lite",
            "GEMINI_API_KEY":"test-gemini-key-not-sent",
            "GEMINI_FALLBACK_MODELS":"",
            "BACKUP_PROVIDER":"groq","GROQ_API_KEY":"test-groq-key-not-sent",
            "GROQ_MODEL":"openai/gpt-oss-20b"
        }
        context=scenario_context("proyecto_refugio")
        attempts=[]

        def fake_post(url,payload,headers,provider):
            attempts.append((provider,json.dumps(payload,ensure_ascii=False).encode("utf-8")))
            if provider=="gemini":
                raise ProviderFailure("Fallo sintético controlado","invalid")
            return {"synthetic":True}

        with patch.object(gateway,"_post",side_effect=fake_post), \
             patch.object(gateway,"_response",
                          return_value=('{"cuaderno":"respuesta sintetica"}',
                                        {"entrada":1,"salida":1})):
            (result,stats),provider,model=route(
                cfg,{},threading.RLock(),
                lambda current:gateway.request_llm(current,context),
                purpose="deliberación",sleep=lambda _:None)
        self.assertEqual(provider,"groq")
        self.assertEqual(model,"openai/gpt-oss-20b")
        self.assertEqual(result["cuaderno"],"respuesta sintetica")
        self.assertEqual([a[0] for a in attempts],["gemini","groq"])
        self.assertNotEqual(attempts[0][1],attempts[1][1])
        self.assertTrue(all(b"test-gemini-key-not-sent" not in body
                            and b"test-groq-key-not-sent" not in body
                            for _,body in attempts))


if __name__=="__main__":
    unittest.main()
