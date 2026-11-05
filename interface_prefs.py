"""Preferencias visuales del observador, fuera del estado cognitivo y físico de Nilo.

Archivo portable de configuración. No incluye claves de API, mensajes ni información
de la partida; cada campo se valida antes de guardarlo o importarlo.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

FILENAME = "preferencias_interfaz.json"
THEMES = {"bosque", "grafito", "terracota", "grises-oscuros", "grises-claros"}
MAP_DISPLAY = {"both", "none"}
RESOURCE_TABS = {"materials", "tools", "buildings"}
INDICATORS = {"normal", "subtle", "off"}
NOTIFICATION_MODES = {"brief", "full", "off"}
NOTIFICATION_SOURCES = {"both", "news", "journal"}
TABS = {"notes", "news", "events", "identity", "versions", "research",
        "measurements", "predictions", "designs", "plans", "projects",
        "agenda", "habits", "chat", "proposals"}
MAX_JSON_BYTES = 8000


def validate(raw):
    """Retornar solo preferencias reconocidas; nunca aceptar datos arbitrarios."""
    if not isinstance(raw, dict):
        raise ValueError("Preferencias inválidas")
    cleaned = {}
    if raw.get("theme") in THEMES:
        cleaned["theme"] = raw["theme"]
    if raw.get("mapDisplay") == "map":
        cleaned["mapDisplay"] = "both"  # Migrar el modo «solo mapa».
    elif raw.get("mapDisplay") in MAP_DISPLAY:
        cleaned["mapDisplay"] = raw["mapDisplay"]
    if raw.get("resources") in RESOURCE_TABS:
        cleaned["resources"] = raw["resources"]
    z = raw.get("mapZoom")
    if isinstance(z, dict) and all(
        isinstance(z.get(k), (int, float)) and not isinstance(z.get(k), bool)
        and 10 <= z[k] <= 38 for k in ("near", "full")
    ):
        cleaned["mapZoom"] = {k: z[k] for k in ("near", "full")}
    v = raw.get("mapView")
    if isinstance(v, dict):
        view = {}
        if v.get("view") in {"near", "full"}: view["view"] = v["view"]
        if str(v.get("mapLayer")) in {"follow", "0", "-1"}:
            view["mapLayer"] = str(v["mapLayer"])
        if isinstance(v.get("showTrail"), bool):
            view["showTrail"] = v["showTrail"]
        if view: cleaned["mapView"] = view
    notif = raw.get("notifications")
    if isinstance(notif, dict):
        cleaned["notifications"] = {
            "mode": notif.get("mode") if notif.get("mode") in NOTIFICATION_MODES else "brief",
            "source": notif.get("source") if notif.get("source") in NOTIFICATION_SOURCES else "both",
        }
    indicators = raw.get("indicators")
    if isinstance(indicators, dict):
        cleaned["indicators"] = {k: val for k, val in indicators.items()
                                  if k in TABS and val in INDICATORS}
    return cleaned


def load(root: Path) -> dict:
    path = Path(root) / FILENAME
    if not path.is_file():
        return {}
    try:
        data = path.read_bytes()
        if len(data) > MAX_JSON_BYTES:
            return {}
        return validate(json.loads(data.decode("utf-8")))
    except (OSError, UnicodeError, ValueError, TypeError):
        return {}


def save(root: Path, value: dict) -> dict:
    root = Path(root)
    validated = validate(value)
    payload = json.dumps(validated, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    if len(payload) > MAX_JSON_BYTES:
        raise ValueError("Preferencias demasiado grandes")
    path = root / FILENAME
    temp = root / (FILENAME + ".tmp")
    try:
        temp.write_bytes(payload)
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)
    return validated


def import_settings(source: Path, destination: Path) -> bool:
    """Importar opciones visuales preexistentes sin sustituir las locales."""
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if source == destination or (destination / FILENAME).exists():
        return False
    if not (source / FILENAME).is_file():
        return False
    values = load(source)
    if not values:
        return False
    save(destination, values)
    return True
