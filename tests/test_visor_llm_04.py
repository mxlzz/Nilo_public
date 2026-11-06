"""Etapa 04: procedencia de campos y cambios observados, sin filtrar datos ocultos."""
from __future__ import annotations

from contextlib import closing
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from auditar_contexto_llm import PROVIDERS, scenario_context
from nilo_runtime.agent import gateway
from nilo_runtime.agent.provenance import (
    ROOT, _catalog, _changes, _source, build_metadata,
)
from nilo_runtime.agent.trace_context import capture_call
from nilo_runtime.storage.llm_requests import RequestTraceStore
from providers import route


class FakeResponse(io.BytesIO):
    def __enter__(self):return self
    def __exit__(self,kind,value,trace):self.close()


def response(provider):
    if provider=="gemini":
        data={"candidates":[{"content":{"parts":[{"text":'{"cuaderno":"Correcto"}'}]}}],
              "usageMetadata":{"promptTokenCount":3,"candidatesTokenCount":3}}
    else:
        data={"choices":[{"message":{"content":'{"cuaderno":"Correcto"}'}}],
              "usage":{"prompt_tokens":3,"completion_tokens":3}}
    return FakeResponse(json.dumps(data,ensure_ascii=False).encode("utf-8"))


class FieldProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="nilo-provenance-")
        self.addCleanup(self.temp.cleanup)
        self.store=RequestTraceStore.for_world(Path(self.temp.name)/"nilo.sqlite3")
        self.context=scenario_context("proyecto_refugio")

    def _deliberate(self, cfg, *, source=None, mock=None):
        """Ejecuta el constructor/HTTP real; solo se sustituye la red."""
        sent=[]
        def fake(request, timeout=40):
            sent.append(request.data)
            if mock is not None:
                return mock(request)
            provider=("gemini" if "generativelanguage.googleapis.com"
                      in request.full_url else "groq")
            return response(provider)
        with patch.object(gateway.urllib.request,"urlopen",side_effect=fake):
            with capture_call(self.store,purpose="deliberacion",
                              session_id=44,simulated_at="Día 2 · 12:00",
                              source_id=source) as call:
                (decision,_),provider,model=route(
                    cfg,{},threading.RLock(),
                    lambda c:gateway.request_llm(c,self.context),sleep=lambda _:None)
        return call.call_id,provider,sent

    def test_real_gateway_tracks_all_stages_and_omissions_without_values(self):
        secret="JAMAS GUARDAR ESTE VALOR INTERNO 879125"
        self.context["dato_privado_que_no_se_envia"]={"valor":secret}
        self.context["necesidades"]={
            "valores":{"energia":18,"hidratacion":44,"nutricion":71}}
        self.context["antecedentes_relacionados"]=[{"id":"anterior"}]
        cfg=dict(PROVIDERS["gemini"],_LAB_OMIT_CONTEXT=("antecedentes_relacionados",))
        call_id,provider,body=self._deliberate(cfg)
        self.assertEqual(provider,"gemini")
        self.assertNotIn(secret.encode("utf-8"),body[0])
        row=next(r for r in self.store.recent() if r["call_id"]==call_id)
        meta=self.store.provenance_for(row["attempt_id"])
        self.assertEqual(meta["payload_verification"],"verificado_con_payload_http")
        self.assertEqual(meta["first_stage"],"percepcion")
        self.assertEqual(meta["last_stage"],"solicitud_preparada")
        self.assertEqual(meta["stages"],["percepcion","proyeccion","perfil",
                                          "compactacion","presupuesto",
                                          "solicitud_preparada"])
        steps={t["stage"]:t for t in meta["transitions"]}
        self.assertIn("/antecedentes_relacionados",steps["perfil"]["removed"])
        self.assertIn("/dato_privado_que_no_se_envia",steps["compactacion"]["removed"])
        self.assertIn("/contexto_reducido",steps["compactacion"]["added"])
        self.assertIn("/necesidades/valores",steps["proyeccion"]["removed"])
        self.assertIn("/necesidades",steps["proyeccion"]["modified"])
        fields={field["json_pointer"]:field for field in meta["fields"]}
        self.assertIs(fields["/necesidades"]["in_http_payload"],True)
        self.assertIs(fields["/dato_privado_que_no_se_envia"]["in_http_payload"],False)
        self.assertIs(fields["/antecedentes_relacionados"]["in_http_payload"],False)
        self.assertEqual(fields["/necesidades/energia"]["origin_precision"],
                         "heredada_del_campo_raiz_no_exacta")
        self.assertIn("dato_privado_que_no_se_envia",meta["omitted_roots"])
        saved=json.dumps(meta,ensure_ascii=False)
        self.assertNotIn(secret,saved)
        self.assertNotIn('"energia": 18',saved)
        self.assertNotIn('"hidratacion": 44',saved)
        self.assertFalse("body" in meta)
        self.assertNotIn("requests",meta)  # no headers ni secretos de proveedor

    def test_source_catalog_references_code_with_real_hash_not_guess(self):
        catalog, hashes=_catalog()
        for file, digest in hashes.items():
            self.assertEqual(hashlib.sha256((ROOT/file).read_bytes()).hexdigest(),digest)
        needs=_source("necesidades")
        self.assertEqual(needs["status"],"referencias_de_codigo_no_traza_de_rama")
        refs=[r for r in needs["references"] if r["file"]=="brain.py"]
        self.assertTrue(refs)
        self.assertTrue(any("perceived_needs" in x["expression_excerpt"] for x in refs))
        current=_source("proyecto_actual")
        self.assertTrue(any(x["file"]=="brain.py" for x in current["references"]))
        chat=_source("conversaciones_recientes")
        self.assertTrue(any(x["function"]=="think" for x in chat["references"]))
        added=_source("antecedente_relevante")
        self.assertTrue(any(x["file"]=="cognitive_projection.py"
                            for x in added["references"]))
        budget=_source("contexto_reducido")
        self.assertTrue(any(x["function"] in ("compact_context","bounded_context")
                            for x in budget["references"]))
        unknown=_source("un_campo_sin_definicion")
        self.assertEqual(unknown["status"],"origen_no_instrumentado")
        self.assertEqual(unknown["references"],[])

    def test_groq_final_payload_and_provider_budget_in_same_trace(self):
        cfg=dict(PROVIDERS["groq"],BACKUP_PROVIDER="none")
        self.context=scenario_context("contexto_extenso")
        call_id,provider,send=self._deliberate(cfg)
        self.assertEqual(provider,"groq")
        row=next(x for x in self.store.recent() if x["call_id"]==call_id)
        meta=self.store.provenance_for(row["attempt_id"])
        self.assertEqual(meta["payload_verification"],"verificado_con_payload_http")
        self.assertIn("limite_proveedor",meta["stages"])
        self.assertEqual(meta["last_stage"],"solicitud_preparada")
        self.assertEqual(row["body"],send[0])
        self.assertLessEqual(row["body_bytes"],14500)
        self.assertTrue(any("GROQ_SYSTEM" in s
                            for s in meta["role_sources"]["system"]))

    def test_fallback_keeps_separate_real_traces_and_does_not_cross_models(self):
        cfg=dict(PROVIDERS["gemini"],GEMINI_FALLBACK_MODELS="",
                 BACKUP_PROVIDER="groq",GROQ_API_KEY="private_groq_header_667",
                 GROQ_MODEL="openai/gpt-oss-20b")
        bodies=[]
        def fake(request):
            bodies.append(request.data)
            if "generativelanguage.googleapis.com" in request.full_url:
                raise HTTPError(request.full_url,429,"synthetic",{},io.BytesIO(b"{}"))
            return response("groq")
        call_id,provider,_=self._deliberate(cfg,mock=fake)
        self.assertEqual(provider,"groq")
        rows=sorted((r for r in self.store.recent() if r["call_id"]==call_id),
                    key=lambda r:r["attempt_ordinal"])
        self.assertEqual(len(rows),2)
        self.assertEqual([r["provider"] for r in rows],["gemini","groq"])
        self.assertEqual([r["body"] for r in rows],bodies)
        metas=[self.store.provenance_for(r["attempt_id"]) for r in rows]
        self.assertEqual([m["payload_verification"] for m in metas],
                         ["verificado_con_payload_http"]*2)
        self.assertEqual(metas[0]["stages"][-1],"solicitud_preparada")
        self.assertIn("limite_proveedor",metas[1]["stages"])
        self.assertNotIn("limite_proveedor",metas[0]["stages"])
        self.assertTrue(all("private_groq_header_667" not in
                            json.dumps(m,ensure_ascii=False) for m in metas))

    def test_chat_records_provenance_of_filter_and_no_rewritten_prompt(self):
        cfg=dict(PROVIDERS["groq"],BACKUP_PROVIDER="none")
        history=[{"role":"user","text":"¿Qué me perdí?"},
                 {"role":"assistant","text":"Anoté algunas cosas."},
                 {"role":"user","text":"Seguí"}]
        original=self.context.copy()
        sent=[]
        def fake(request,timeout=40):
            sent.append(request.data)
            return response("groq")
        with patch.object(gateway.urllib.request,"urlopen",side_effect=fake):
            with capture_call(self.store,purpose="chat",session_id=9,
                              source_id="chat-05") as call:
                (answer,_),provider,_=route(cfg,{},threading.RLock(),
                     lambda c:gateway.request_chat(c,self.context,history),
                     purpose="chat",sleep=lambda _:None)
        row=next(r for r in self.store.recent() if r["call_id"]==call.call_id)
        meta=self.store.provenance_for(row["attempt_id"])
        self.assertEqual(meta["payload_verification"],"verificado_con_payload_http")
        self.assertIn("filtro_chat",meta["stages"])
        self.assertEqual(row["source_id"],"chat-05")
        self.assertEqual(row["body"],sent[0])
        self.assertEqual(self.context,original)
        self.assertIn("CHAT_SYSTEM",str(meta["role_sources"]["system"]))
        self.assertTrue(meta["transitions"][-1]["stage"]=="solicitud_preparada")

    def test_legacy_sidecar_migrates_additively_and_world_is_untouched(self):
        # Una base de etapa 02 sin la tabla de procedencia no es corrupta.
        store=self.store
        store.begin(body=b"{}",call_id="a",session_id=None,
                    purpose="chat",source_id=None,simulated_at=None,
                    ordinal=1,provider="groq",model="x")
        old=store.recent()[0]["attempt_id"]
        with closing(sqlite3.connect(store.path)) as db:
            db.execute("DROP TABLE llm_request_provenance")
            db.commit()
        self.assertIsNone(store.provenance_for(old))
        newid=store.begin(body=b"{}",call_id="b",session_id=None,
                          purpose="chat",source_id=None,simulated_at=None,
                          ordinal=1,provider="groq",model="x",
                          provenance={"schema_version":1,"trace_status":"test"})
        self.assertIsNone(store.provenance_for(old))
        self.assertEqual(store.provenance_for(newid)["trace_status"],"test")

    def test_pruning_attempts_prunes_metadata_without_orphans(self):
        from nilo_runtime.storage import llm_requests
        with patch.object(llm_requests,"MAX_RECORDS",2):
            ids=[]
            for x in range(3):
                ids.append(self.store.begin(
                    body=b'{"messages":[]}',call_id="call",
                    session_id=1,purpose="deliberacion",source_id=None,
                    simulated_at=None,ordinal=x+1,
                    provider="groq",model="model",
                    provenance={"schema_version":1,"index":x}))
        self.assertIsNone(self.store.provenance_for(ids[0]))
        self.assertEqual(self.store.provenance_for(ids[1])["index"],1)
        self.assertEqual(self.store.provenance_for(ids[2])["index"],2)
        with closing(sqlite3.connect(self.store.path)) as db:
            count=db.execute("SELECT COUNT(*) FROM llm_request_provenance").fetchone()[0]
        self.assertEqual(count,2)

    def test_mismatch_fails_closed_without_claiming_sent(self):
        snapshot=[
            ("percepcion",{"posición":[1,2],"necesidades":{"energia":"cansado"}}),
            ("solicitud_preparada",{"posición":[1,2]})
        ]
        body=json.dumps({"messages":[
            {"role":"system","content":"Regla"},
            {"role":"user","content":'{"posición":[5,6]}'}
        ]},ensure_ascii=False).encode("utf-8")
        meta=build_metadata(snapshot,body,"groq","deliberacion")
        self.assertEqual(meta["payload_verification"],"no_verificado_con_el_payload")
        self.assertTrue(all(f["in_http_payload"] is None for f in meta["fields"]))
        self.assertNotIn("cansado",json.dumps(meta,ensure_ascii=False))

    def test_comparison_by_pointer_does_not_forge_array_identity(self):
        changes=_changes({"lista":[{"id":"A"},{"id":"B"}]},
                         {"lista":[{"id":"B"}]})
        self.assertIn("/lista",changes["modified"])
        self.assertIn("/lista/0/id",changes["modified"])
        self.assertIn("/lista/1",changes["removed"])
        # No se afirma que el elemento B haya sido borrado: es un índice.
        self.assertNotIn("A",json.dumps(changes))
        self.assertNotIn("B",json.dumps(changes))


if __name__=="__main__":
    unittest.main()
