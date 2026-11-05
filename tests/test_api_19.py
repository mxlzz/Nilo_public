"""Etapa 19: integración real HTTP, API, origen local y observador."""
from __future__ import annotations

import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from nilo_runtime.application.engine import Simulation
from nilo_runtime.application.deps import RuntimeServices
from nilo_runtime.web.api import API_VERSION, dispatch, GET_PATHS, POST_PATHS
from nilo_runtime.web.http import Handler, create_server
from nilo_runtime.web.security import RequestError, authorize

ROOT=Path(__file__).resolve().parent.parent


class HttpApi19(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix="nilo-api-19-")
        cls.sim=Simulation(db_path=Path(cls.tmp.name)/"api.sqlite3",
                           world_seed=7321,rng_seed=9821)
        cls.server=create_server(cls.sim,0)
        cls.port=cls.server.server_address[1]
        cls.thread=threading.Thread(
            target=cls.server.serve_forever,
            kwargs={"poll_interval":0.02},daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=4)
        cls.sim.conn.close()
        cls.tmp.cleanup()

    def request(self,method,path,body=None,headers=None,raw=False):
        conn=http.client.HTTPConnection("127.0.0.1",self.port,timeout=10)
        try:
            h=dict(headers or {})
            if body is not None and not raw:
                body=json.dumps(body,ensure_ascii=False).encode("utf-8")
                h.setdefault("Content-Type","application/json")
            conn.request(method,path,body=body,headers=h)
            resp=conn.getresponse()
            content=resp.read()
            ct=resp.getheader("Content-Type","")
            parsed=json.loads(content) if ct.startswith("application/json") else content
            return resp.status,parsed,dict(resp.getheaders())
        finally:
            conn.close()

    def test_get_contract_and_version_not_world_schema_mixed(self):
        self.assertEqual(API_VERSION,1)
        status,body,headers=self.request("GET","/api/version")
        self.assertEqual(status,200)
        self.assertEqual(body["api_version"],1)
        self.assertEqual(body["schema_version"],5)
        self.assertIn("engine_version",body)
        self.assertEqual(headers["Cache-Control"],"no-store")
        self.assertEqual(headers["X-Content-Type-Options"],"nosniff")

    def test_state_read_is_pure_and_secrets_are_not_exposed(self):
        before=json.dumps(self.sim.s,sort_keys=True,default=str)
        total=self.sim.conn.total_changes
        prior=self.sim.services
        self.sim.services=RuntimeServices(
            config=lambda: {"PROVIDER":"gemini","MODEL":"prueba",
                            "GEMINI_API_KEY":"secreto_no_exponer_19"},
            available=lambda cfg:False,
            route=lambda *a,**k:None)
        try:
            for _ in range(2):
                status,body,_=self.request("GET","/api/state")
                self.assertEqual(status,200)
                self.assertEqual(body["version"],5)
                self.assertIn("map",str(body).lower())
                self.assertNotIn("secreto_no_exponer_19",json.dumps(body))
        finally:
            self.sim.services=prior
        self.assertEqual(json.dumps(self.sim.s,sort_keys=True,default=str),before)
        self.assertEqual(self.sim.conn.total_changes,total)

    def test_state_projection_does_not_return_credential_fingerprints(self):
        raw={"version":5,"name":"Nilo","ai":{
            "provider":"gemini","model":"modelo",
            "routing":{"last_provider":"gemini","providers":[
                {"name":"gemini","health_key":"gemini:secreto-derivado",
                 "model":"modelo","status":"disponible",
                 "attempts":0,"successes":0,"failures":0}]}}}
        with patch.object(self.sim,"public_state",return_value=raw):
            status,body,_=self.request("GET","/api/state")
        self.assertEqual(status,200)
        self.assertEqual(body["name"],"Nilo")
        self.assertEqual(body["ai"]["routing"]["providers"][0]["name"],"gemini")
        self.assertNotIn("health_key",body["ai"]["routing"]["providers"][0])
        self.assertNotIn("secreto-derivado",json.dumps(body))
        # La proyección no modifica el objeto retornado por el motor.
        self.assertIn("health_key",raw["ai"]["routing"]["providers"][0])

    def test_html_root_is_served_with_legacy_inline_compat(self):
        status,body,headers=self.request("GET","/")
        self.assertEqual(status,200)
        self.assertTrue(body.lstrip().startswith(b"<!DOCTYPE") or b"<html" in body[:300].lower())
        self.assertIn("'unsafe-inline'",headers["Content-Security-Policy"])
        self.assertEqual(headers["X-Frame-Options"],"DENY")

    def test_unread_and_summary_history_do_not_mark_anything(self):
        before={cat:self.sim.archive.position(cat) for cat in ("news","journal")}
        for url in ("/api/unread?category=journal",
                    "/api/unread?category=news",
                    "/api/summary-history","/api/ui-preferences"):
            status,body,_=self.request("GET",url)
            self.assertEqual(status,200,url)
            self.assertIsInstance(body,dict)
        self.assertEqual({cat:self.sim.archive.position(cat)
                          for cat in ("news","journal")},before)

    def test_read_record_and_unknown_id_mapping(self):
        status,body,_=self.request("GET","/api/record?category=project&id=ausente")
        self.assertEqual(status,404)
        self.assertIn("error",body)
        status,body,_=self.request("GET","/api/measurement?id=med-inexistente")
        self.assertEqual(status,404)
        self.assertIn("error",body)
        status,body,_=self.request("GET","/api/diagnostic?id=ausente")
        self.assertEqual(status,404)

    def test_read_invalid_queries_never_execute_action(self):
        for url in ("/api/unread?category=other",
                    "/api/unread?category=journal&category=news",
                    "/api/record?category=project&id=x&id=y",
                    "/api/record?category=project&id="+("x"*150)):
            with self.subTest(url=url):
                status,body,_=self.request("GET",url)
                self.assertEqual(status,400)
                self.assertIn("error",body)

    def test_unknown_route_is_404_and_unsupported_method_is_405(self):
        for method,url,code in (("GET","/api/desconocido",404),
                                ("POST","/api/desconocido",404),
                                ("OPTIONS","/api/settings",405)):
            status,body,_=self.request(method,url)
            self.assertEqual(status,code)
            self.assertIn("error",body)

    def test_setting_speed_and_pause_uses_old_contract(self):
        previous=self.sim.s["paused"]
        try:
            status,body,_=self.request("POST","/api/settings",{"paused":True})
            self.assertEqual(status,200)
            self.assertEqual(body,{"ok":True})
            self.assertTrue(self.sim.s["paused"])
            for bad in ({"speed":"60"},{"paused":1},
                        {"auto_pause_on_wait":"false"},{"speed":999}):
                status,body,_=self.request("POST","/api/settings",bad)
                self.assertEqual(status,400)
                self.assertIn("error",body)
        finally:
            self.sim.s["paused"]=previous

    def test_chat_contract_202_and_strict_message(self):
        with patch.object(self.sim,"start_chat",return_value=None) as method:
            status,body,_=self.request("POST","/api/chat",{"message":"Hola"})
            self.assertEqual(status,202)
            self.assertEqual(body,{"ok":True})
            method.assert_called_once_with("Hola")
        for value in (None,12,[],{"text":"hola"}):
            status,body,_=self.request("POST","/api/chat",{"message":value})
            self.assertEqual(status,400)
        status,body,_=self.request("POST","/api/chat",{"message":"x"*3500})
        self.assertIn(status,(400,413))

    def test_observer_summary_uses_api_and_not_read_until_ack(self):
        before=self.sim.archive.position("journal")
        with patch.object(self.sim,"observer_summary",
                          return_value={"id":"resumen-sintetico","text":"Hechos documentados."}) as impl:
            status,data,_=self.request("POST","/api/summary-generate",
                                      {"candidates":[]})
            self.assertEqual(status,200)
            self.assertEqual(data["id"],"resumen-sintetico")
            impl.assert_called_once_with([],None)
        self.assertEqual(self.sim.archive.position("journal"),before)

    def test_post_root_and_read_objects_require_json_object(self):
        for body in (b"[]",b"true",b"null",b'"texto"'):
            with self.subTest(body=body):
                status,data,_=self.request(
                    "POST","/api/settings",body,
                    {"Content-Type":"application/json"},raw=True)
                self.assertEqual(status,400)
                self.assertIn("error",data)

    def test_invalid_utf8_and_malformed_json_fail_without_500(self):
        for body in (b"\xff",b'{"x":',b"{invalido}"):
            status,data,_=self.request(
                "POST","/api/settings",body,
                {"Content-Type":"application/json"},raw=True)
            self.assertEqual(status,400)
            self.assertIn("error",data)

    def test_nonstandard_json_nan_and_infinity_rejected_without_write(self):
        previous=self.sim.s["paused"]
        for invalid in (b'{"paused": NaN}',b'{"paused": Infinity}',
                        b'{"paused": -Infinity}'):
            status,data,_=self.request(
                "POST","/api/settings",invalid,
                {"Content-Type":"application/json"},raw=True)
            self.assertEqual(status,400)
            self.assertIn("error",data)
        self.assertEqual(self.sim.s["paused"],previous)

    def test_requires_json_content_type(self):
        for ct in ("text/plain","application/x-www-form-urlencoded",""):
            status,data,_=self.request("POST","/api/settings",b'{"paused":true}',
                         {"Content-Type":ct},raw=True)
            self.assertEqual(status,415)
            self.assertIn("error",data)

    def test_rejects_oversized_post(self):
        payload=b'{"message":"'+b"x"*3500+b'"}'
        status,data,_=self.request("POST","/api/chat",payload,
                                   {"Content-Type":"application/json"},raw=True)
        self.assertEqual(status,413)

    def test_cross_site_origin_cannot_change_settings(self):
        before=self.sim.s["paused"]
        for headers in (
            {"Origin":"https://evil.example"},
            {"Origin":"null"},
            {"Origin":"http://127.0.0.1:65534"},
            {"Referer":"https://evil.example/page"},
            {"Sec-Fetch-Site":"cross-site"},
            {"Host":"evil.example:"+str(self.port)},
            {"Host":"127.0.0.1.evil.example:"+str(self.port)},
        ):
            with self.subTest(headers=headers):
                status,data,_=self.request(
                    "POST","/api/settings",{"paused":not before},headers)
                self.assertEqual(status,403)
                self.assertIn("error",data)
                self.assertEqual(self.sim.s["paused"],before)

    def test_same_origin_browser_request_is_allowed(self):
        status,body,_=self.request("GET","/api/version",headers={
            "Origin":f"http://127.0.0.1:{self.port}",
            "Referer":f"http://127.0.0.1:{self.port}/",
            "Sec-Fetch-Site":"same-origin"})
        self.assertEqual(status,200)

    def test_unexpected_exception_returns_500_without_traceback(self):
        with patch.object(self.sim,"public_state",
                          side_effect=RuntimeError("token_hipotetico_prive_19")):
            status,data,_=self.request("GET","/api/state")
            self.assertEqual(status,500)
            self.assertEqual(data,{"error":"Error interno del servidor"})
            self.assertNotIn("token_hipotetico",str(data))

    def test_query_cannot_modify_world_or_advance_rng(self):
        before=json.dumps(self.sim.s,sort_keys=True,default=str)
        cp=self.sim.entropy.to_record(agent_rng=self.sim.rng)
        for url in ("/api/version","/api/unread?category=journal",
                    "/api/summary-history","/api/diagnostic?id=inexistente",
                    "/api/record?category=research&id=ninguno"):
            self.request("GET",url)
        self.assertEqual(json.dumps(self.sim.s,sort_keys=True,default=str),before)
        self.assertEqual(self.sim.entropy.to_record(agent_rng=self.sim.rng),cp)

    def test_bound_handlers_do_not_share_simulation_between_servers(self):
        with tempfile.TemporaryDirectory(prefix="nilo-api-second-") as directory:
            second=Simulation(db_path=Path(directory)/"second.sqlite3",rng_seed=55)
            server=create_server(second,0)
            th=threading.Thread(target=server.serve_forever,
                                kwargs={"poll_interval":0.02},daemon=True)
            th.start()
            other=second.s["paused"]
            try:
                # Ejercer una mutación solo en la primera instancia.
                first=self.sim.s["paused"]
                status,_,_=self.request("POST","/api/settings",{"paused":not first})
                self.assertEqual(status,200)
                self.assertEqual(second.s["paused"],other)
                conn=http.client.HTTPConnection("127.0.0.1",
                                                server.server_address[1],timeout=10)
                try:
                    conn.request("GET","/api/version")
                    res=conn.getresponse()
                    self.assertEqual(res.status,200)
                    self.assertEqual(json.loads(res.read())["api_version"],1)
                finally:
                    conn.close()
            finally:
                self.sim.s["paused"]=first
                server.shutdown()
                server.server_close()
                th.join(timeout=4)
                second.conn.close()

    def test_aliases_and_contract_lists_complete(self):
        from nilo import Handler as OldHandler
        self.assertIs(OldHandler,Handler)
        self.assertIn("/api/state",GET_PATHS)
        self.assertIn("/api/ui-preferences",POST_PATHS)
        self.assertIn("/api/review-bootstrap",POST_PATHS)
        self.assertIn("/api/summary-ack",POST_PATHS)
        self.assertIn("/api/retry-llm",POST_PATHS)


if __name__=="__main__":
    unittest.main()
