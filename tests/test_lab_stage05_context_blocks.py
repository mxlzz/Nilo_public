"""Etapa 05: indexación literal por familias, vínculo de episodio y vistas previas.

No requiere proveedores reales ni modifica la partida guardada del usuario.
El modelo no recibe ningún texto ni regla adicional por estas pantallas.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from auditar_contexto_llm import PROVIDERS, scenario_context
from nilo_runtime.agent.gateway import build_deliberation_request
from nilo_runtime.labs.literal_segments import index_request
from laboratorio_contexto import solicitud_completa
from nilo_runtime.labs.hub import _request
from nilo_runtime.labs.profiles import baseline

ROOT=Path(__file__).resolve().parents[1]


def wire(payload):
    return json.dumps(payload,ensure_ascii=False).encode("utf-8")


def user_message(index):
    return next(x for x in index["messages"] if x["role"]=="user")


class LiteralFamiliesTests(unittest.TestCase):
    def test_gemini_groq_openai_keep_exact_original_message_and_sha(self):
        for provider in ("gemini","groq","openai_compatible"):
            with self.subTest(provider=provider):
                cfg=dict(PROVIDERS[provider])
                ctx=scenario_context("proyecto_refugio")
                original=copy.deepcopy(ctx)
                _,payload,_=build_deliberation_request(cfg,ctx)
                body=wire(payload)
                indexed=index_request(body,provider=provider,purpose="deliberacion")
                self.assertEqual(indexed["body_sha256"],hashlib.sha256(body).hexdigest())
                self.assertEqual(ctx,original)
                for msg in indexed["messages"]:
                    self.assertEqual(msg["segmentation_integrity"],
                                     "lossless_utf8_text_and_contiguous_offsets")
                    self.assertEqual(msg["display_order"],"original_message_order")
                    self.assertTrue(msg["display_groups_are_editorial"])
                    self.assertEqual(msg["text_sha256"],
                                     hashlib.sha256(msg["text"].encode()).hexdigest())
                    self.assertEqual("".join(s["literal"] for s in msg["segments"]),
                                     msg["text"])
                    offset=0
                    for seg in msg["segments"]:
                        self.assertEqual(seg["start"],offset)
                        self.assertEqual(seg["literal"],msg["text"][seg["start"]:seg["end"]])
                        self.assertEqual(seg["literal_sha256"],
                                         hashlib.sha256(seg["literal"].encode()).hexdigest())
                        offset=seg["end"]
                    self.assertEqual(offset,len(msg["text"]))

    def test_group_titles_do_not_replace_quoted_unicode_values(self):
        values={"momento":"Día 17","necesidades":{"fatiga":"con energía"},
                "proyecto_actual":{"titulo":"Refugio"},"resultados_de_acciones":[
                    {"op":"gather","resultado":"Guardé \"madera\""}],
                "memorias_relevantes":["Ensayé, fallé, aprendí."],
                "campo_que_nunca_vimos":{"interno":"Símbolos ~ / ñ"}}
        # JSON con saltos y espacios significativos. Sus bytes son el contrato.
        user=json.dumps(values,ensure_ascii=False,indent=3)
        original=json.dumps({"model":"probar","messages":[
            {"role":"system","content":"Instrucciones intactas."},
            {"role":"user","content":user}]},ensure_ascii=False).encode()
        result=index_request(original,provider="groq",purpose="deliberacion")
        msg=user_message(result)
        groups={b["title"]:b["display_group"] for b in msg["blocks"]
                if b["kind"]=="field"}
        self.assertEqual(groups["momento"],"situacion")
        self.assertEqual(groups["proyecto_actual"],"actividad")
        self.assertEqual(groups["resultados_de_acciones"],"evidencia")
        self.assertEqual(groups["memorias_relevantes"],"memoria")
        self.assertEqual(groups["campo_que_nunca_vimos"],"otros")
        self.assertEqual([b["title"] for b in msg["blocks"] if b["kind"]=="field"],
                         list(values))
        self.assertEqual("".join(s["literal"] for s in msg["segments"]),user)
        self.assertEqual(result["body_bytes"],len(original))
        self.assertIn('"resultado": "Guardé \\"madera\\""',user)

    def test_repeated_families_are_not_sorted_or_compacted(self):
        text='{"momento":"a","proyecto_actual":"b","necesidades":"c"}'
        payload=wire({"model":"test","messages":[
            {"role":"system","content":"Original"},{"role":"user","content":text}]})
        indexed=index_request(payload,provider="groq",purpose="deliberacion")
        blocks=[b for b in user_message(indexed)["blocks"] if b["kind"]=="field"]
        self.assertEqual([b["display_group"] for b in blocks],
                         ["situacion","actividad","situacion"])
        self.assertEqual(text,"".join(x["literal"] for x in user_message(indexed)["segments"]))

    def test_chat_stays_literal_without_fabricated_fields(self):
        body=wire({"model":"test","messages":[
            {"role":"system","content":"No cambies el texto."},
            {"role":"user","content":"¿Qué me perdí?"},
            {"role":"assistant","content":"Todavía no hay respuesta."}]})
        result=index_request(body,provider="groq",purpose="chat")
        self.assertEqual([m["role"] for m in result["messages"]],
                         ["system","user","assistant"])
        for msg in result["messages"]:
            self.assertEqual("".join(seg["literal"] for seg in msg["segments"]),
                             msg["text"])
        self.assertEqual(user_message(result)["blocks"][0]["display_group"],"texto")


class CalculatedPromptTests(unittest.TestCase):
    def test_scenario_preview_indexes_same_bytes_as_gateway_transport(self):
        for provider in ("gemini","groq"):
            with self.subTest(provider=provider):
                source=scenario_context("proyecto_refugio")
                prev=copy.deepcopy(source)
                preview=solicitud_completa(source,provider)
                self.assertEqual(source,prev)
                self.assertTrue(preview["segmentacion_verificada"])
                self.assertEqual(preview["procedencia"],
                                 "previsualizacion_calculada_sin_red")
                body=preview["solicitud_serializada"].encode("utf-8")
                self.assertEqual(preview["bytes_solicitud"],len(body))
                self.assertEqual(preview["huella_solicitud_calculada"],
                                 hashlib.sha256(body).hexdigest())
                self.assertEqual(body,wire(preview["solicitud_json"]))
                indexed=index_request(body,provider=provider,purpose="deliberacion")
                self.assertEqual(indexed["messages"],
                                 preview["mensajes_literal_estructurado"])
                self.assertIn("sin llamar a la API",preview["notas"])

    def test_profile_preview_uses_transport_serialization_and_never_sends(self):
        ctx=scenario_context("proyecto_refugio")
        for provider in ("gemini","groq"):
            with self.subTest(provider=provider):
                data=_request(baseline(),ctx,provider)
                self.assertIs(data["enviado_a_llm"],False)
                self.assertEqual(data["procedencia"],
                                 "previsualizacion_calculada_sin_red")
                body=wire(data["solicitud_json"])
                self.assertEqual(data["bytes"],len(body))
                self.assertEqual(data["huella_solicitud_calculada"],
                                 hashlib.sha256(body).hexdigest())
                indexed=index_request(body,provider=provider,purpose="deliberacion")
                self.assertEqual(indexed["messages"],data["mensaje_literal_por_rol"])
                self.assertTrue(data["segmentacion_verificada"])

    def test_internal_values_absent_from_prompt_are_never_added_to_blocks(self):
        ctx=scenario_context("proyecto_refugio")
        secret="PRIVADO_NO_SALIO_EN_SOLICITUD_553827"
        ctx["campo_interno_excluido"]={"credencial":secret}
        # Compactación del constructor excluye campos no permitidos.
        result=solicitud_completa(ctx,"gemini")
        body=result["solicitud_serializada"]
        self.assertNotIn(secret,body)
        indexed=json.dumps(result["mensajes_literal_estructurado"],ensure_ascii=False)
        self.assertNotIn(secret,indexed)


class PreviewBrowserTests(unittest.TestCase):
    def test_ui_shows_context_blocks_in_viewer_scenarios_and_profile(self):
        viewer=(ROOT/"laboratorio_visor_llm.html").read_text("utf-8")
        scenario=(ROOT/"laboratorio_escenarios.html").read_text("utf-8")
        profile=(ROOT/"laboratorio_ajustes.html").read_text("utf-8")
        self.assertIn("context-family",viewer)
        self.assertIn("display_group_title",viewer)
        self.assertIn("display_group_subtitle",viewer)
        self.assertIn("renderMessages(data,container)",viewer)
        self.assertIn("data.episode",viewer)
        self.assertIn("Reintentos",viewer.replace("reintentos","Reintentos"))
        self.assertIn("renderLiteralScenarioMessages",scenario)
        self.assertIn("mensajes_literal_estructurado",scenario)
        self.assertIn("no se envió a Gemini ni a Groq",scenario)
        self.assertIn("structured-preview",profile)
        self.assertIn("showLiteralPreview",profile)
        self.assertIn("mensaje_literal_por_rol",profile)
        self.assertIn("enviado_a_llm!==false",profile)

    def test_js_syntax_if_node_is_installed(self):
        node=shutil.which("node")
        if not node:self.skipTest("Node no disponible")
        with tempfile.TemporaryDirectory(prefix="nilo-js-stage05-") as folder:
            for name in ("laboratorio_visor_llm.html",
                         "laboratorio_escenarios.html",
                         "laboratorio_ajustes.html"):
                html=(ROOT/name).read_text("utf-8")
                js=html.split("<script>",1)[1].split("</script>",1)[0]
                file=Path(folder)/(name+".js")
                file.write_text(js,"utf-8")
                result=subprocess.run([node,"--check",str(file)],
                                      capture_output=True,text=True,timeout=15)
                self.assertEqual(result.returncode,0,name+": "+result.stderr)


if __name__=="__main__":
    unittest.main()
