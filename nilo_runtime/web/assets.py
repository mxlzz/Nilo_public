"""Única lista explícita de assets de la interfaz principal de Nilo.

Ningún GET puede construir rutas de disco desde una URL proporcionada por el
cliente. Las rutas son allowlisted y viajan dentro del ZIP portable.
"""
from __future__ import annotations
from pathlib import Path
from nilo_runtime.application.deps import HERE

ASSETS={
    "/assets/nilo.css": ("text/css; charset=utf-8", HERE/"assets"/"nilo.css"),
    "/assets/state.js": ("text/javascript; charset=utf-8", HERE/"assets"/"state.js"),
    "/assets/records.js": ("text/javascript; charset=utf-8", HERE/"assets"/"records.js"),
    "/assets/feed.js": ("text/javascript; charset=utf-8", HERE/"assets"/"feed.js"),
    "/assets/actions.js": ("text/javascript; charset=utf-8", HERE/"assets"/"actions.js"),
}
SCRIPT_ORDER=tuple(path for path in ASSETS if path.endswith(".js"))

def read_asset(route):
    content_type,path=ASSETS[route]
    return content_type,path.read_bytes()
