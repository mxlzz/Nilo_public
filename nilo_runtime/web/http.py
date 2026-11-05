"""Transporte HTTP de Nilo, aislado de las operaciones y del motor.

El contrato está en web.api y la frontera de acceso local en web.security.
El nombre Handler permanece como import compatible con nilo.Handler.
"""
from __future__ import annotations

import json
import threading
import webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlsplit

from nilo_runtime.application.deps import HERE, config, available
from nilo_runtime.application.engine import Simulation
from nilo_runtime.web.api import dispatch, POST_PATHS, LARGE_REQUESTS
from nilo_runtime.web.security import authorize, parse_body, RequestError
from nilo_runtime.web.assets import ASSETS, read_asset

HTML_FILE=HERE/"interfaz.html"


class Handler(BaseHTTPRequestHandler):
    sim=None

    def log_message(self,*args):
        pass

    def send_json(self,obj,code=200):
        body=json.dumps(obj,ensure_ascii=False,allow_nan=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(body)))
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("X-Frame-Options","DENY")
        self.send_header("Referrer-Policy","no-referrer")
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self):
        authorize(self.headers,self.server.server_address[1])

    def _dispatch(self,method,path,*,query="",data=None):
        response=dispatch(self.sim,method,path,query=query,data=data,root=HERE)
        self.send_json(response.body,response.status)

    def do_GET(self):
        try:
            self._authorized()
            route=urlsplit(self.path)
            if route.path in ("/","/index.html"):
                body=HTML_FILE.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type","text/html; charset=utf-8")
                self.send_header("Cache-Control","no-store")
                self.send_header("X-Content-Type-Options","nosniff")
                self.send_header("X-Frame-Options","DENY")
                self.send_header("Referrer-Policy","no-referrer")
                self.send_header("Content-Security-Policy",
                    "default-src 'self'; script-src 'self'; object-src 'none'; "
                    "style-src 'self' 'unsafe-inline'")
                self.send_header("Content-Length",str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if route.path in ASSETS:
                content_type,body=read_asset(route.path)
                self.send_response(200)
                self.send_header("Content-Type",content_type)
                self.send_header("Cache-Control","no-store")
                self.send_header("Content-Length",str(len(body)))
                self.send_header("X-Content-Type-Options","nosniff")
                self.send_header("X-Frame-Options","DENY")
                self.send_header("Referrer-Policy","no-referrer")
                self.end_headers()
                self.wfile.write(body)
                return
            self._dispatch("GET",route.path,query=route.query)
        except RequestError as exc:
            self.send_json({"error":str(exc)},exc.status)
        except Exception:
            # No filtrar traceback, configuración, rutas internas ni claves LLM.
            self.send_json({"error":"Error interno del servidor"},500)

    def do_POST(self):
        try:
            self._authorized()
            path=urlsplit(self.path).path
            if path not in POST_PATHS:
                self.send_json({"error":"No encontrado"},404)
                return
            data=parse_body(self.headers,self.rfile,
                            maximum=65000 if path in LARGE_REQUESTS else 3000)
            # /api/ui-preferences continúa siendo un contrato de observador.
            self._dispatch("POST",path,data=data)
        except RequestError as exc:
            self.send_json({"error":str(exc)},exc.status)
        except Exception:
            self.send_json({"error":"Error interno del servidor"},500)

    def do_OPTIONS(self):
        self.send_json({"error":"Método no admitido"},405)


def create_server(sim,port=8765):
    """Servicio local aislado: cada servidor conserva SU simulación."""
    class BoundHandler(Handler):
        pass
    BoundHandler.sim=sim
    return ThreadingHTTPServer(("127.0.0.1",port),BoundHandler)


def main(simulation_factory=Simulation):
    sim=simulation_factory()
    try:
        cfg=config()
        port=int(cfg.get("PORT","8765"))
        if not 1<=port<=65535:
            raise ValueError("Puerto fuera de rango")
        server=create_server(sim,port)
    except BaseException:
        sim.conn.close()
        raise
    threading.Thread(target=sim.run,daemon=True,name="NiloClock").start()
    print(f"\nNILO · {sim.sessions.identity['engine_version']}\n"
          f"Abri en el navegador: http://127.0.0.1:{port}\n")
    print("LLM configurado: "+("SÍ ("+cfg.get("MODEL","")+")"
          if available(cfg) else "NO; modo demostración claramente indicado"))
    print("Para detener la simulación: Ctrl+C o cerrar esta ventana.\n")
    threading.Timer(1.5,
        lambda:webbrowser.open(f"http://127.0.0.1:{port}")).start()
    try:
        server.serve_forever(poll_interval=.5)
    except KeyboardInterrupt:
        pass
    finally:
        sim.stopped=True
        with sim.lock:
            sim.write()
            sim.sessions.finish(sim.s["person"]["clock_minutes"])
        server.server_close()
        sim.conn.close()


if __name__=="__main__":
    main()
