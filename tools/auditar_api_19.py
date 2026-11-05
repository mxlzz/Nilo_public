"""Auditor de la frontera web y el contrato API v1 (etapa 19)."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
WEB=ROOT/"nilo_runtime"/"web"


def audit():
    errors=[]
    for name in ("http.py","api.py","security.py"):
        file=WEB/name
        if not file.is_file():
            errors.append("Falta "+str(file))
            continue
        try:ast.parse(file.read_text("utf-8"),filename=str(file))
        except SyntaxError as exc:errors.append("Sintaxis web inválida: "+str(exc))
    if errors:return errors
    http=(WEB/"http.py").read_text("utf-8")
    api=(WEB/"api.py").read_text("utf-8")
    security=(WEB/"security.py").read_text("utf-8")
    import sys
    if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
    from nilo_runtime.web.api import GET_PATHS,POST_PATHS,API_VERSION
    if API_VERSION!=1:errors.append("API v1 cambió sin migración contractual")
    if len(GET_PATHS)!=8 or len(POST_PATHS)!=13:
        errors.append("Rutas originales o versión API incompatibles")
    if GET_PATHS&POST_PATHS!={"/api/ui-preferences"}:
        errors.append("Métodos/rutas no declarados")
    if "from nilo_runtime.web.api import dispatch" not in http:
        errors.append("El transporte volvió a duplicar lógica de negocio")
    if "from nilo_runtime.web.security import authorize, parse_body" not in http:
        errors.append("Transporte sin validación de origen/cuerpo")
    for requirement in ("create_server","ThreadingHTTPServer((\"127.0.0.1\",port)",
                        "class Handler(BaseHTTPRequestHandler)","BoundHandler.sim=sim",
                        "except Exception:","X-Content-Type-Options"):
        if requirement not in http:errors.append("Falta aislamiento web: "+requirement)
    for requirement in ("def _authority","Origin","Host","Referer","Sec-Fetch-Site",
                        "Transfer-Encoding","Content-Length","application/json",
                        "size>maximum","isinstance(data,dict)"):
        if requirement not in security:errors.append("Falta frontera HTTP: "+requirement)
    from nilo_runtime.web.api import _get
    for key in ("sim.write(","sim.change_speed(","sim.mark_read(",
                "sim.start_chat(","sim.plan_ready(","sim.think("):
        if key in ast.get_source_segment(api, next(
                n for n in ast.parse(api).body
                if isinstance(n,ast.FunctionDef) and n.name=="_get")):
            errors.append("GET muta la simulación: "+key)
    if "GEMINI_API_KEY" in api or "GROQ_API_KEY" in api:
        errors.append("El contrato API conoce claves de proveedor")
    if "nilo_runtime.web" in (ROOT/"nilo_runtime/application/engine.py").read_text("utf-8"):
        errors.append("Dependencia inversa de UI en motor")
    if not (ROOT/"tests/test_api_19.py").is_file():
        errors.append("Faltan pruebas de integración HTTP")
    return errors


if __name__=="__main__":
    issues=audit()
    if issues:
        print("\n".join(issues))
        raise SystemExit(1)
    print("Etapa 19: HTTP aislado, API v1 estable, origen local y GET sin operaciones mutadoras.")
