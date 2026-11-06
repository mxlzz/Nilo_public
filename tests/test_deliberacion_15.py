"""Etapa 15: pruebas del contrato común, gateway y parseo, sin red."""
from __future__ import annotations
import copy
import json
import threading
import unittest
from unittest.mock import patch

from auditar_contexto_llm import PROVIDERS, extract_sent_context, scenario_context
from brain import build_deliberation_request, normalize_decision, request_llm, request_chat
from nilo_runtime.agent import prompts, budget, responses, gateway
from nilo_runtime.core.operations import registered_operations, get_spec
from providers import ProviderFailure, route


def decision():
    return {"cuaderno":"Voy a mirar mi entorno.","accion_proyecto":"sin_proyecto",
            "plan":[{"op":"inspect","target":"suelo"}]}


class Contract15(unittest.TestCase):
    def test_single_policy_and_wait_semantics(self):
        rules=prompts.POLICY_RULES
        self.assertEqual(len(rules),24)
        self.assertEqual(len(set(prompts.POLICY_IDS)),len(rules))
        self.assertEqual(prompts.SYSTEM,"\n".join(r[1] for r in rules))
        self.assertEqual(prompts.GROQ_SYSTEM,"\n".join(r[2] for r in rules))
        self.assertIn("no recibís misiones",prompts.GROQ_SYSTEM)
        self.assertIn("wait no aporta recuperación energética",prompts.SYSTEM)
        self.assertIn("no recupera energía como descanso",get_spec("wait").description)

    def test_single_operation_catalog_and_valid_compact_examples(self):
        self.assertEqual(set(budget.SHORT_OPERATIONS),set(registered_operations()))
        for op,description in budget.SHORT_OPERATIONS.items():
            with self.subTest(op=op):
                example,_=json.JSONDecoder().raw_decode(description)
                self.assertEqual(example["op"],op)
                self.assertIn("[síntesis]",description)

    def test_legacy_facades_have_same_function_objects(self):
        import brain
        import prompt_budget
        self.assertIs(brain.compact_context,budget.compact_context)
        self.assertIs(brain.normalize_decision,responses.normalize_decision)
        self.assertIs(brain.build_deliberation_request,gateway.build_deliberation_request)
        self.assertIs(prompt_budget.bounded_context,budget.bounded_context)

    def test_previews_match_semantic_filter_without_mutating_state(self):
        raw=scenario_context("contexto_extenso")
        before=copy.deepcopy(raw)
        for name,cfg in PROVIDERS.items():
            with self.subTest(name=name):
                url,payload,headers=build_deliberation_request(cfg,raw)
                selected=extract_sent_context(name,payload)
                self.assertEqual(before,raw)
                self.assertIn("necesidades",selected)
                self.assertNotIn("valores",selected["necesidades"])
                self.assertNotIn("progress",selected.get("proyecto_actual") or {})
                self.assertTrue(url.startswith("https://"))
                key=next(cfg[k] for k in ("GEMINI_API_KEY","GROQ_API_KEY","OPENAI_API_KEY") if k in cfg)
                self.assertNotIn(key,json.dumps(payload))
                self.assertIn(key,json.dumps(headers))
                if name=="groq":
                    self.assertLessEqual(len(json.dumps(payload,ensure_ascii=False).encode()),14500)

    def test_network_receives_same_wire_payload_as_preview(self):
        context=scenario_context("inicio")
        answer=json.dumps(decision(),ensure_ascii=False)
        for name,cfg in PROVIDERS.items():
            if name=="gemini":
                response={"candidates":[{"content":{"parts":[{"text":answer}]}}],
                          "usageMetadata":{"promptTokenCount":12,"candidatesTokenCount":9}}
            else:
                response={"choices":[{"message":{"content":answer}}],
                          "usage":{"prompt_tokens":12,"completion_tokens":9}}
            with self.subTest(provider=name):
                with patch.object(gateway,"_post",return_value=response) as post:
                    got,tokens=request_llm(cfg,context)
                self.assertEqual(got,decision())
                self.assertEqual((tokens["entrada"],tokens["salida"]),(12,9))
                self.assertEqual(post.call_args.args[1],
                                 build_deliberation_request(cfg,context)[1])

    def test_invalid_json_and_structure_fail_for_router(self):
        for name in ("gemini","groq"):
            for response in ({},{"choices":[]},{"candidates":[]}):
                with self.subTest(name=name,response=response):
                    with self.assertRaises(ProviderFailure):
                        gateway._response(response,name)
        with self.assertRaises(ValueError):
            normalize_decision({"cuaderno":"Hola","plan":"no es lista"})
        with self.assertRaises(ValueError):
            normalize_decision({"cuaderno":"Hola","plan":[]})

    def test_fallback_does_not_accept_unusable_decision(self):
        cfg={"PROVIDER":"gemini","MODEL":"gemini-3.1-flash-lite",
             "GEMINI_API_KEY":"falsa","GEMINI_FALLBACK_MODELS":"gemini-3.5-flash-lite",
             "BACKUP_PROVIDER":"none"}
        seen=[]
        def handler(pcfg):
            seen.append(pcfg["MODEL"])
            if len(seen)==1:
                return normalize_decision({"cuaderno":"Sin plan","plan":[]})
            return normalize_decision(decision())
        result,name,model=route(cfg,{},threading.RLock(),handler,sleep=lambda _x:None)
        self.assertEqual(len(seen),2)
        self.assertEqual(name,"gemini")
        self.assertEqual(model,"gemini-3.5-flash-lite")
        self.assertEqual(result["plan"][0]["op"],"inspect")

    def test_https_and_exact_localhost_validation(self):
        cfg=dict(PROVIDERS["openai_compatible"])
        for base in ("http://localhost.evil.example/v1",
                     "http://127.0.0.1.attacker/v1",
                     "http://remote.example/v1"):
            with self.subTest(base=base):
                cfg["OPENAI_BASE_URL"]=base
                with self.assertRaises(ValueError):
                    build_deliberation_request(cfg,scenario_context("inicio"))
        cfg["OPENAI_BASE_URL"]="http://localhost:18000/v1"
        url,_,_=build_deliberation_request(cfg,scenario_context("inicio"))
        self.assertEqual(url,"http://localhost:18000/v1/chat/completions")

    def test_chat_system_and_observation_are_different_roles(self):
        ctx={"posición":[15,10,0],"necesidades":{"valores":{"energia":50}},
             "resumen_de_lo_no_leido":{"entradas":[{"id":"hit-uno"}],"restantes":1}}
        messages=[{"role":"user","text":"Qué me perdí?"}]
        before=copy.deepcopy(ctx)
        for name,cfg in PROVIDERS.items():
            with self.subTest(name=name):
                url,payload,headers=gateway.build_chat_request(cfg,ctx,messages)
                self.assertEqual(before,ctx)
                encoded=json.dumps(payload,ensure_ascii=False)
                self.assertIn("hit-uno",encoded)
                self.assertNotIn('"valores"',encoded)
                if name=="gemini":
                    self.assertIn("CONTEXTO COMPROBADO",payload["contents"][0]["parts"][0]["text"])
                else:
                    self.assertNotIn("CONTEXTO COMPROBADO",payload["messages"][0]["content"])
                    self.assertIn("CONTEXTO COMPROBADO",payload["messages"][1]["content"])
                self.assertNotIn("clave-ficticia-no-enviar",encoded)

    def test_chat_response_without_network(self):
        context={"momento":"Día 1","necesidades":{"hidratacion":"sin sed"}}
        for provider,cfg in PROVIDERS.items():
            if provider=="gemini":
                response={"candidates":[{"content":{"parts":[{"text":"No lo sé todavía."}]}}],
                          "usageMetadata":{}}
            else:
                response={"choices":[{"message":{"content":"No lo sé todavía."}}],
                          "usage":{}}
            with self.subTest(provider=provider):
                with patch.object(gateway,"_post",return_value=response):
                    message,tokens=request_chat(cfg,context,
                        [{"role":"user","text":"Qué pasó?"}])
                self.assertEqual(message,"No lo sé todavía.")
                self.assertIn("entrada",tokens)


if __name__=="__main__":
    unittest.main()
