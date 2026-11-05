"""HTTP y HTML de Nilo; nunca importado por el núcleo del motor.

La simulación se inyecta desde la fachada, por lo que las rutas conservan
la API de antes y el puerto/correo UI no forman parte de la lógica del mundo.
"""
from __future__ import annotations
import json, threading, time, webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlsplit, parse_qs
from pathlib import Path
from nilo_runtime.application.deps import HERE, config, available, SUPPORTED_SPEEDS, ProvidersUnavailable
from nilo_runtime.application.engine import Simulation
from interface_prefs import load as load_interface_prefs, save as save_interface_prefs

HTML_FILE=HERE/'interfaz.html'

class Handler(BaseHTTPRequestHandler):
    sim=None
    def log_message(self,*args):pass
    def send_json(self,obj,code=200):
        body=json.dumps(obj,ensure_ascii=False).encode('utf-8')
        self.send_response(code);self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)))
        self.end_headers();self.wfile.write(body)
    def do_GET(self):
        path=urlsplit(self.path).path
        if path in ('/','/index.html'):
            body=HTML_FILE.read_bytes();self.send_response(200)
            self.send_header('Content-Type','text/html; charset=utf-8')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'")
            self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        elif path=='/api/state':self.send_json(self.sim.public_state())
        elif path=='/api/summary-history':
            self.send_json({'summaries':self.sim.observer_summary_history()})
        elif path=='/api/unread':
            qs=parse_qs(urlsplit(self.path).query)
            category=(qs.get('category') or [''])[0]
            if category not in ('journal','news'):
                self.send_json({'error':'Categoría de archivo inválida'},400)
            else:
                with self.sim.lock:
                    self.send_json({'category':category,
                        'total':self.sim.archive.count_unread(category),
                        'entries':self.sim.archive.unread(category,limit=80)})
        elif path=='/api/record':
            qs=parse_qs(urlsplit(self.path).query)
            category=(qs.get('category') or [''])[0][:40]
            rid=(qs.get('id') or [''])[0][:101]
            try:self.send_json(self.sim.linked_record(category,rid))
            except ValueError as exc:self.send_json({'error':str(exc)},404)
        elif path=='/api/measurement':
            qs=parse_qs(urlsplit(self.path).query)
            mid=(qs.get('id') or [''])[0][:80]
            try:self.send_json(self.sim.measurement_record(mid))
            except ValueError as exc:self.send_json({'error':str(exc)},404)
        elif path=='/api/ui-preferences':
            with self.sim.lock:
                self.send_json(load_interface_prefs(HERE))
        elif path=='/api/diagnostic':
            qs=parse_qs(urlsplit(self.path).query)
            rid=(qs.get('id') or [''])[0][:80]
            try:self.send_json(self.sim.diagnostic_package(rid))
            except ValueError as exc:self.send_json({'error':str(exc)},404)
        else:self.send_json({'error':'No encontrado'},404)
    def do_POST(self):
        path=urlsplit(self.path).path
        if path not in ('/api/settings','/api/chat','/api/read-news','/api/read','/api/read-all','/api/read-summary','/api/review-rule','/api/retry-llm','/api/ui-preferences','/api/review-bootstrap','/api/review-mark','/api/summary-generate','/api/summary-ack'):return self.send_json({'error':'No encontrado'},404)
        try:
            size=int(self.headers.get('Content-Length','0'))
            if size<1 or size>(65000 if path in ('/api/review-bootstrap','/api/review-mark','/api/summary-generate') else 3000):return self.send_json({'error':'Solicitud demasiado grande o vacía'},413)
            data=json.loads(self.rfile.read(size))
            if path=='/api/review-bootstrap':
                return self.send_json(self.sim.bootstrap_reviews(data.get('seen',{})))
            if path=='/api/review-mark':
                return self.send_json(self.sim.mark_tab_reviewed(data.get('tab'),data.get('keys',[])))
            if path=='/api/summary-generate':
                try:return self.send_json(self.sim.observer_summary(data.get('candidates',[]),data.get('continuation')))
                except (ProvidersUnavailable,RuntimeError) as exc:
                    return self.send_json({'error':str(exc)[:450]},503)
            if path=='/api/summary-ack':
                return self.send_json(self.sim.acknowledge_observer_summary(str(data.get('id',''))[:80]))
            if path=='/api/ui-preferences':
                with self.sim.lock:
                    return self.send_json(save_interface_prefs(HERE,data))
            if path=='/api/retry-llm':
                result=self.sim.retry_llm()
                return self.send_json(result,200 if result['ok'] else 409)
            if path=='/api/review-rule':
                return self.send_json(self.sim.review_rule(str(data.get('id',''))[:80],
                    str(data.get('decision',''))[:15],str(data.get('reason',''))[:700]))
            if path in ('/api/read-news','/api/read'):
                category='news' if path=='/api/read-news' else str(data.get('category',''))
                if data.get('single') is True:
                    return self.send_json(self.sim.mark_one_read(category,str(data.get('id',''))[:60]))
                return self.send_json(self.sim.mark_read(category, str(data.get('id',''))[:60]))
            if path=='/api/read-all':
                categories=data.get('categories',['journal','news'])
                if not isinstance(categories,list) or len(categories)>2:raise ValueError('Categorías inválidas')
                return self.send_json(self.sim.mark_all_read(categories))
            if path=='/api/read-summary':return self.send_json(self.sim.mark_summarized_read())
            if path=='/api/chat':
                self.sim.start_chat(data.get('message',''))
                return self.send_json({'ok':True},202)
            speed=data.get('speed')
            if speed is not None and (type(speed) is not int or speed not in SUPPORTED_SPEEDS):raise ValueError('Velocidad inválida')
            paused=data.get('paused')
            if paused is not None and not isinstance(paused,bool):raise ValueError('Pausa inválida')
            auto_pause=data.get('auto_pause_on_wait')
            if auto_pause is not None and not isinstance(auto_pause,bool):raise ValueError('Ajuste de pausa inválido')
            self.sim.change_speed(speed,paused,auto_pause)
            self.send_json({'ok':True})
        except (ValueError,TypeError,KeyError) as exc:self.send_json({'error':str(exc)},400)



def main(simulation_factory=Simulation):
    sim=simulation_factory();Handler.sim=sim
    cfg=config();port=int(cfg.get('PORT','8765'))
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    threading.Thread(target=sim.run,daemon=True,name='NiloClock').start()
    print(f"\nNILO · {sim.sessions.identity['engine_version']}\nAbri en el navegador: http://127.0.0.1:{port}\n")
    print('LLM configurado: '+('SÍ ('+cfg.get('MODEL','')+')' if available(cfg) else 'NO; modo demostración claramente indicado'))
    print('Para detener la simulación: Ctrl+C o cerrar esta ventana.\n')
    threading.Timer(1.5,lambda:webbrowser.open(f'http://127.0.0.1:{port}')).start()
    try:server.serve_forever(poll_interval=.5)
    except KeyboardInterrupt:pass
    finally:
        sim.stopped=True
        with sim.lock:
            sim.write()
            sim.sessions.finish(sim.s['person']['clock_minutes'])
        server.server_close();sim.conn.close()

if __name__=='__main__':main()
