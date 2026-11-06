"""Etapa 20: contrato de assets, navegación, empaquetado y paridad del frontend."""
from __future__ import annotations

from html.parser import HTMLParser
import hashlib
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
if str(ROOT/"tests") not in sys.path:sys.path.insert(0,str(ROOT/"tests"))

from nilo_runtime.web.assets import ASSETS,SCRIPT_ORDER
from ui_fixture import legacy_markup

OLD_GIT_BLOB="b2140f365ac0344189096cf615b5cf97d69fa8d2"


class Catalog(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids=set()
        self.duplicates=set()
        self.inline=[]
        self.scripts=[]
        self.styles=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get("id"):
            if a["id"] in self.ids:self.duplicates.add(a["id"])
            self.ids.add(a["id"])
        self.inline.extend(k for k,v in attrs if k.startswith("on"))
        if tag=="script":self.scripts.append((a.get("src"),"defer" in a))
        if tag=="link" and a.get("rel")=="stylesheet":
            self.styles.append(a.get("href"))


def audit():
    errors=[]
    html=(ROOT/"interfaz.html").read_text("utf-8")
    if "<style>" in html or "<script>" in html or "onclick=" in html:
        errors.append("El HTML reintrodujo código embebido o handlers inline")
    catalog=Catalog();catalog.feed(html)
    if catalog.duplicates:errors.append("IDs duplicados: "+repr(catalog.duplicates))
    if catalog.inline:errors.append("Eventos inline en DOM: "+repr(catalog.inline))
    if catalog.styles!=["/assets/nilo.css"]:
        errors.append("CSS de producción no referenciado como único asset")
    if catalog.scripts!=[(name,True) for name in SCRIPT_ORDER]:
        errors.append("Orden de scripts clásicos/defer incompatible")
    for route,(mime,path) in ASSETS.items():
        if not path.is_file():errors.append("Falta asset "+route)
        if ".." in route or not route.startswith("/assets/"):
            errors.append("Ruta de assets insegura "+route)
    script="".join((ROOT/"assets"/Path(s).name).read_text("utf-8")
                    for s in SCRIPT_ORDER)
    refs={m.group(2) for m in re.finditer(r"\bel\((['\"])([^'\"]+)\1\)",script)}
    missing=refs-catalog.ids
    if missing:errors.append("Referencias al DOM sin ID: "+repr(sorted(missing)))
    # Etapa 24 solo actualiza la etiqueta de la versión; la paridad
    # estructural con el frontend previo a etapa 20 debe mantenerse exacta.
    legacy=legacy_markup(ROOT)
    current_version=(ROOT/"VERSION").read_text("utf-8").strip()
    expected_label="Una vida en curso · Nilo "+current_version
    if expected_label not in legacy:
        errors.append("El encabezado visible no coincide con VERSION")
    legacy=legacy.replace(expected_label,
                          "Una vida en curso · Nilo 0.6.4").encode("utf-8")
    git_hash=hashlib.sha1(f"blob {len(legacy)}\0".encode()+legacy).hexdigest()
    if git_hash!=OLD_GIT_BLOB:
        errors.append("Perdió paridad byte a byte con interfaz anterior a etapa 20")
    from nilo_runtime.web.http import Handler
    import inspect
    code=inspect.getsource(Handler.do_GET)
    if "if route.path in ASSETS:" not in code:
        errors.append("El servidor no entrega assets por allowlist")
    from nilo_runtime.application.deps import HERE
    if (HERE/"interfaz.html")!=ROOT/"interfaz.html":
        errors.append("El punto de entrada HTML cambió")
    import json
    manifest=json.loads((ROOT/"MANIFIESTO_SHA256.json").read_text("utf-8"))
    required=["interfaz.html","nilo_runtime/web/assets.py",
              "assets/nilo.css",*(f"assets/{Path(s).name}" for s in SCRIPT_ORDER)]
    for path in required:
        if path not in manifest.get("files",{}):
            errors.append("El ZIP no incluiría el asset "+path)
    verifier=(ROOT/"tools/verificar_paquete_07.py").read_text("utf-8")
    for path in required:
        if path not in verifier and path!="interfaz.html":
            errors.append("Smoke ZIP no comprueba el asset "+path)
    # Los tests antiguos se migran al fixture calculado, no a un HTML clonado.
    for path in (ROOT/"tests").glob("test_*.py"):
        if path.name=="test_interfaz_20.py":continue
        text=path.read_text("utf-8")
        if re.search(r'interfaz\.html["\x27]\)\.read_text\(',text):
            errors.append("Test histórico lee HTML directamente: "+path.name)
    return errors


if __name__=="__main__":
    problems=audit()
    if problems:
        raise SystemExit("\n".join(problems))
    print("Etapa 20: paridad exacta, CSS y JS externos, rutas allowlisted y ZIP íntegro.")
