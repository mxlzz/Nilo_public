"""Vista monolítica exclusivamente para pruebas históricas de interfaz.

El navegador usa los cinco assets REALES. Los tests que buscaban <script> y
<style> inline obtienen los mismos bytes lógicos reconstruidos desde los
archivos de producción, sin mantener una segunda implementación de la UI.
"""
from __future__ import annotations

import atexit
from pathlib import Path
import tempfile

_ASSETS=("state.js","records.js","feed.js","actions.js")
_temp=None

def legacy_markup(root):
    root=Path(root)
    page=(root/"interfaz.html").read_text("utf-8")
    css=(root/"assets"/"nilo.css").read_text("utf-8")
    scripts="".join((root/"assets"/item).read_text("utf-8") for item in _ASSETS)
    stylesheet='<link rel="stylesheet" href="/assets/nilo.css">'
    script_tags="\n".join('<script defer src="/assets/'+item+'"></script>' for item in _ASSETS)
    if page.count(stylesheet)!=1 or page.count(script_tags)!=1:
        raise ValueError("La interfaz cambió su contrato de assets")
    return page.replace(stylesheet,"<style>"+css+"</style>").replace(
        script_tags,"<script>"+scripts+"</script>")

def legacy_html_path(root):
    global _temp
    if _temp is None:
        _temp=tempfile.TemporaryDirectory(prefix="nilo-ui-legacy-")
        atexit.register(_temp.cleanup)
    path=Path(_temp.name)/"interfaz.html"
    path.write_text(legacy_markup(root),encoding="utf-8")
    return path
