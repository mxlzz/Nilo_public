"""Etapa 03: segmentación literal sin reformular la solicitud HTTP."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from auditar_contexto_llm import PROVIDERS, scenario_context
from nilo_runtime.agent.gateway import (
    build_chat_request, build_deliberation_request,
)
from nilo_runtime.labs.literal_segments import (
    index_request, index_saved_attempt,
)
from nilo_runtime.storage.llm_requests import RequestTraceStore


def wire(payload):
    # Es la serialización del _post real; no se usa para crear bloques.
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def all_messages_preserved(index):
    for msg in index["messages"]:
        reconstructed = "".join(segment["literal"] for segment in msg["segments"])
        assert reconstructed == msg["text"]
        assert all(
            segment["literal"] == msg["text"][segment["start"]:segment["end"]]
            for segment in msg["segments"]
        )
        assert all(
            msg["text"][field["start"]:field["end"]].startswith('"')
            for field in msg["field_index"]
        )


class LiteralSegmentationTests(unittest.TestCase):
    def test_gemini_roles_context_fields_subtitles_and_nested_offsets(self):
        cfg = dict(PROVIDERS["gemini"])
        ctx = scenario_context("proyecto_refugio")
        ctx["regla"] += ' Recuérdese "SITUACIÓN REAL: " como texto ordinario.'
        original = copy.deepcopy(ctx)
        _, payload, _ = build_deliberation_request(cfg, ctx)
        body = wire(payload)
        result = index_request(body, provider="gemini", purpose="deliberacion")
        self.assertEqual(ctx, original)
        self.assertEqual(result["body_sha256"], hashlib.sha256(body).hexdigest())
        self.assertEqual(result["body_bytes"], len(body))
        self.assertEqual([m["role"] for m in result["messages"]], ["system", "user"])
        self.assertEqual(result["messages"][0]["path"], "/systemInstruction/parts/0/text")
        self.assertEqual(result["messages"][0]["text"],
                         payload["systemInstruction"]["parts"][0]["text"])
        user = result["messages"][1]
        self.assertEqual(user["path"], "/contents/0/parts/0/text")
        self.assertEqual(user["text"], payload["contents"][0]["parts"][0]["text"])
        self.assertTrue(user["text"].startswith("Operaciones disponibles"))
        self.assertIsNotNone(user["context_interval"])
        self.assertEqual("".join(s["literal"] for s in user["segments"]), user["text"])
        sent = json.loads(user["text"][slice(*user["context_interval"])])
        blocks = [s for s in user["blocks"] if s["kind"] == "field"]
        names = [s["title"] for s in blocks]
        self.assertEqual(names, list(sent))
        self.assertIn("necesidades", names)
        self.assertIn("proyecto_actual", names)
        self.assertIn("regla", names)
        self.assertTrue(next(s for s in blocks if s["title"] == "necesidades")["subtitle"])
        for b in blocks:
            self.assertEqual(json.loads("{" + b["literal"] + "}"), {b["title"]:sent[b["title"]]})
        project = next(f for f in user["field_index"]
                       if f["json_pointer"] == "/proyecto_actual/title")
        self.assertEqual(json.loads(user["text"][project["value_start"]:project["value_end"]]),
                         sent["proyecto_actual"]["title"])
        self.assertEqual(user["segments"][0]["kind"], "text")
        self.assertEqual(user["segments"][0]["title"], "text")
        all_messages_preserved(result)

    def test_groq_and_compatible_keep_original_roles_and_final_budget(self):
        for provider in ("groq", "openai_compatible"):
            with self.subTest(provider=provider):
                cfg = dict(PROVIDERS[provider])
                _, payload, _ = build_deliberation_request(
                    cfg, scenario_context("contexto_extenso"))
                result = index_request(wire(payload), provider=provider,
                                       purpose="deliberacion")
                self.assertEqual([m["role"] for m in result["messages"]],
                                 ["system", "user"])
                self.assertEqual([m["path"] for m in result["messages"]],
                                 ["/messages/0/content", "/messages/1/content"])
                user = result["messages"][1]
                self.assertEqual(user["text"], payload["messages"][1]["content"])
                self.assertEqual(user["context_interval"], [0, len(user["text"])])
                self.assertIn("contexto_reducido",
                              [s["title"] for s in user["blocks"]])
                self.assertEqual(json.loads(user["text"]),
                                 json.loads(payload["messages"][1]["content"]))
                if provider == "groq":
                    self.assertEqual(payload["reasoning_effort"], "low")
                    self.assertLessEqual(len(wire(payload)), 14500)
                all_messages_preserved(result)

    def test_gemini_chat_preserves_grounding_and_conversation_suffix(self):
        cfg = dict(PROVIDERS["gemini"])
        history = [
            {"role":"user", "text":"Hola, ¿cómo estás?"},
            {"role":"assistant", "text":"Observando el territorio."},
            {"role":"user", "text":"¿Y qué más?"},
        ]
        _, payload, _ = build_chat_request(cfg,
            scenario_context("proyecto_refugio"),history)
        index = index_request(wire(payload),provider="gemini",purpose="chat")
        self.assertEqual([x["role"] for x in index["messages"]],
                         ["system","user","model","user"])
        for msg in index["messages"]:
            self.assertIn("text",msg)
        user = index["messages"][1]
        self.assertTrue(user["text"].startswith("CONTEXTO COMPROBADO"))
        self.assertTrue(user["text"].endswith("\n\nHola, ¿cómo estás?"))
        self.assertIsNotNone(user["context_interval"])
        interval = user["context_interval"]
        self.assertIsInstance(json.loads(user["text"][slice(*interval)]),dict)
        self.assertTrue(any(s["kind"]=="text" and "Hola" in s["literal"]
                            for s in user["segments"]))
        self.assertEqual(index["messages"][-1]["context_interval"],None)
        all_messages_preserved(index)

    def test_groq_chat_multiple_roles_and_no_false_json_segmentation(self):
        cfg = dict(PROVIDERS["groq"])
        history=[
            {"role":"user","text":"Hola"},
            {"role":"assistant","text":"Te escucho."},
            {"role":"user","text":"{esto no es JSON; no lo cambies}"},
        ]
        _, payload, _ = build_chat_request(
            cfg,scenario_context("pausa"),history)
        result=index_request(wire(payload),provider="groq",purpose="chat")
        self.assertEqual([m["role"] for m in result["messages"]],
                         [m["role"] for m in payload["messages"]])
        user=result["messages"][1]
        self.assertIsNotNone(user["context_interval"])
        self.assertEqual(user["text"],payload["messages"][1]["content"])
        last=result["messages"][-1]
        self.assertEqual(last["text"],"{esto no es JSON; no lo cambies}")
        self.assertIsNone(last["context_interval"])
        self.assertEqual(last["segments"][0]["literal"],last["text"])
        all_messages_preserved(result)

    def test_escaped_keys_unicode_whitespace_and_nested_pointer_preserved(self):
        context = ('{ \n  "na\\/me" : [1, {"camino" : "ñ\\u00e9"}],\n'
                   '  "emoji" : "🌱", "comillas" : "\\\"hola\\\""  }')
        payload={
            "model":"ejemplo",
            "messages":[{"role":"system","content":"Reglas \\n sin cambios"},
                        {"role":"user","content":context}],
        }
        body=wire(payload)
        index=index_request(body,provider="groq",purpose="deliberacion")
        user=index["messages"][1]
        self.assertEqual(user["text"],context)
        self.assertEqual("".join(p["literal"] for p in user["segments"]),context)
        self.assertEqual([p["title"] for p in user["blocks"]],
                         ["na/me","emoji","comillas"])
        block=user["blocks"][0]
        self.assertIn('"na\\/me" : [1, {"camino" : "ñ\\u00e9"}]',block["literal"])
        nested=next(f for f in user["field_index"]
                    if f["json_pointer"]=="/na~1me/1/camino")
        self.assertEqual(user["text"][nested["value_start"]:nested["value_end"]],
                         '"ñ\\u00e9"')
        self.assertEqual(json.loads(user["text"]),json.loads(context))
        all_messages_preserved(index)

    def test_misleading_marker_inside_instructions_or_value_is_not_used(self):
        msg=('El ejemplo dice SITUACIÓN REAL: datos inválidos\n'
             'SITUACIÓN REAL: {"regla":"Contiene SITUACIÓN REAL: texto"}')
        payload={"systemInstruction":{"parts":[{"text":"Sistema"}]},
                 "contents":[{"role":"user","parts":[{"text":msg}]}]}
        index=index_request(wire(payload),provider="gemini",purpose="deliberacion")
        user=index["messages"][1]
        self.assertEqual([b["title"] for b in user["blocks"] if b["kind"]=="field"],
                         ["regla"])
        self.assertTrue(user["text"][slice(*user["context_interval"])]
                        .startswith('{"regla"'))
        all_messages_preserved(index)

    def test_unknown_field_keeps_exact_name_without_invented_subtitle(self):
        inner='{"campo_hipotético":"<script>&{\\"x\\":true}"}'
        payload={"messages":[{"role":"user","content":inner}]}
        index=index_request(wire(payload),provider="groq",purpose="deliberacion")
        field=index["messages"][0]["blocks"][0]
        self.assertEqual(field["title"],"campo_hipotético")
        self.assertEqual(field["subtitle"],"")
        self.assertIn("<script>",field["literal"])
        all_messages_preserved(index)

    def test_unknown_nontext_part_fails_explicitly(self):
        payload={"contents":[{"role":"user","parts":[{"inlineData":{"mimeType":"image/png"}}]}]}
        with self.assertRaisesRegex(ValueError,"no textual"):
            index_request(wire(payload),provider="gemini",purpose="chat")

    def test_reject_corrupt_body_or_invalid_provider(self):
        with self.assertRaises(ValueError):
            index_request(b'{"mensajes":',provider="groq",purpose="chat")
        with self.assertRaises(ValueError):
            index_request(b"{}",provider="provider_desconocido",purpose="chat")

    def test_saved_attempts_share_call_id_but_not_body_and_do_not_write(self):
        with tempfile.TemporaryDirectory(prefix="nilo-visor-segments-") as folder:
            world=Path(folder)/"mundo.sqlite3"
            store=RequestTraceStore.for_world(world)
            bodies=[]
            for provider in ("gemini","groq"):
                cfg=dict(PROVIDERS[provider])
                _, payload, _=build_deliberation_request(
                    cfg,scenario_context("pausa"))
                body=wire(payload)
                bodies.append(body)
                store.begin(body=body,call_id="misma-deliberación",session_id=3,
                            purpose="deliberacion",source_id=None,
                            simulated_at="Día 2 · 12:00",
                            ordinal=len(bodies),provider=provider,model=cfg["MODEL"])
            originals=store.path.read_bytes()
            rows=sorted(store.recent(),key=lambda r:r["attempt_ordinal"])
            indexed=[index_saved_attempt(r) for r in rows]
            self.assertEqual([x["body_sha256"] for x in indexed],
                             [hashlib.sha256(b).hexdigest() for b in bodies])
            self.assertNotEqual(indexed[0]["body_sha256"],indexed[1]["body_sha256"])
            self.assertEqual({x["call_id"] for x in indexed},
                             {"misma-deliberación"})
            self.assertEqual([x["attempt_ordinal"] for x in indexed],[1,2])
            self.assertEqual(store.path.read_bytes(),originals)

    def test_saved_attempt_rejects_tampered_blob(self):
        with tempfile.TemporaryDirectory() as folder:
            store=RequestTraceStore.for_world(Path(folder)/"mundo.sqlite3")
            store.begin(body=b'{"messages":[{"role":"user","content":"ok"}]}',
                        call_id="c",session_id=None,purpose="chat",
                        source_id=None,simulated_at=None,ordinal=1,
                        provider="groq",model="simulado")
            row=store.recent()[0]
            row["body"]+=b"malicioso"
            with self.assertRaisesRegex(ValueError,"checksum"):
                index_saved_attempt(row)


if __name__=="__main__":
    unittest.main()
