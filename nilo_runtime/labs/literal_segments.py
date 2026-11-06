"""Índice literal y de solo lectura de los mensajes HTTP del LLM.

Los fragmentos se extraen de la cadena de cada rol, no de un JSON reserializado.
Los textos originales se conservan; títulos/subtítulos son metadatos externos.
No importa Simulation ni almacena datos; la API/HTML pertenecen a etapas 05/06.
"""
from __future__ import annotations

import hashlib
import json

_CONTEXT_MARKER = "SITUACIÓN REAL: "
_CHAT_MARKER = "CONTEXTO COMPROBADO (no lo contradigas): "
_PROVIDERS = frozenset(("gemini", "groq", "openai_compatible"))
_PURPOSES = frozenset(("deliberacion", "chat"))
_DECODER = json.JSONDecoder()
_MAX_DEPTH = 32
_MAX_FIELDS = 20000

# Aclaraciones de la UI; NUNCA son parte del prompt ni reemplazan sus valores.
_SUBTITLES = {
    "momento": "Momento que figura en el contexto.",
    "posición": "Coordenadas conocidas por Nilo.",
    "mundo": "Entorno indicado en el contexto.",
    "necesidades": "Sensaciones corporales transmitidas al modelo.",
    "inventario_materiales": "Materiales disponibles en el inventario.",
    "percepción_local": "Información del entorno inmediato.",
    "proyecto_actual": "Datos del proyecto activo incluidos en la solicitud.",
    "ultimo_cierre_rechazado": "Diagnóstico comunicado sobre el cierre anterior.",
    "investigaciones_activas": "Investigaciones abiertas incluidas en el contexto.",
    "memorias_relevantes": "Recuerdos seleccionados para esta consulta.",
    "mediciones_reales_recientes": "Mediciones recientes transmitidas al modelo.",
    "resultados_de_acciones": "Resultados recientes de acciones registradas.",
    "conclusiones_verificadas": "Conclusiones incluidas como verificadas.",
    "conocimiento_con_procedencia": "Conocimientos acompañados de su procedencia.",
    "herramientas_que_llevo": "Herramientas que constan en el contexto.",
    "construcciones_fijas": "Construcciones registradas en el entorno conocido.",
    "antecedente_relevante": "Antecedente seleccionado para esta decisión.",
    "antecedentes_relacionados": "Antecedentes relacionados con la actividad.",
    "navegacion_a_lugares": "Rutas conocidas hacia lugares registrados.",
    "orillas_agua_conocidas_alcanzables": "Orillas conocidas y alcanzables.",
    "regla": "Reglas del entorno comunicadas en el contexto.",
    "contexto_reducido": "Aviso de recorte incorporado a la solicitud.",
}
_ROLE_SUBTITLES = {
    "system": "Instrucciones originales enviadas al modelo.",
    "user": "Texto original enviado como mensaje de usuario.",
    "assistant": "Mensaje previo del asistente incluido en el historial.",
    "model": "Mensaje previo del modelo incluido en el historial.",
}


def _pointer(value):
    return str(value).replace("~", "~0").replace("/", "~1")


def _skip_spaces(text, index):
    while index < len(text) and text[index] in " \t\n\r":
        index += 1
    return index


def _scan_value(text, start, pointer, depth, fields):
    """Localizar offsets en el texto existente, sin regenerar valores."""
    start = _skip_spaces(text, start)
    if depth > _MAX_DEPTH:
        return _DECODER.raw_decode(text, start)[1]
    if start >= len(text):
        raise ValueError("JSON incompleto en la captura")
    char = text[start]
    if char == "{":
        cursor = _skip_spaces(text, start + 1)
        if cursor < len(text) and text[cursor] == "}":
            return cursor + 1
        while True:
            key_start = cursor
            key, key_end = _DECODER.raw_decode(text, cursor)
            if not isinstance(key, str):
                raise ValueError("Nombre de campo JSON inválido")
            cursor = _skip_spaces(text, key_end)
            if cursor >= len(text) or text[cursor] != ":":
                raise ValueError("Objeto JSON sin separador de campo")
            value_start = _skip_spaces(text, cursor + 1)
            field_pointer = pointer + "/" + _pointer(key)
            end = _scan_value(text, value_start, field_pointer,
                              depth + 1, fields)
            if len(fields) >= _MAX_FIELDS:
                raise ValueError("Demasiados campos para indexar")
            fields.append({
                "json_pointer": field_pointer,
                "depth": depth + 1,
                "title": key,
                "start": key_start,
                "end": end,
                "value_start": value_start,
                "value_end": end,
            })
            cursor = _skip_spaces(text, end)
            if cursor < len(text) and text[cursor] == "}":
                return cursor + 1
            if cursor >= len(text) or text[cursor] != ",":
                raise ValueError("Objeto JSON sin separador de elementos")
            cursor = _skip_spaces(text, cursor + 1)
    if char == "[":
        cursor = _skip_spaces(text, start + 1)
        if cursor < len(text) and text[cursor] == "]":
            return cursor + 1
        index = 0
        while True:
            cursor = _scan_value(text, cursor,
                                 pointer + "/" + str(index),
                                 depth + 1, fields)
            cursor = _skip_spaces(text, cursor)
            if cursor < len(text) and text[cursor] == "]":
                return cursor + 1
            if cursor >= len(text) or text[cursor] != ",":
                raise ValueError("Array JSON sin separador de elementos")
            cursor = _skip_spaces(text, cursor + 1)
            index += 1
    return _DECODER.raw_decode(text, start)[1]


def _json_interval(text, provider, purpose, role):
    """Retorna el objeto JSON real dentro del mensaje, si lo hay."""
    if role != "user":
        return None
    if purpose == "deliberacion" and provider == "gemini":
        cursor = 0
        while True:
            marker = text.find(_CONTEXT_MARKER, cursor)
            if marker == -1:
                return None
            start = _skip_spaces(text, marker + len(_CONTEXT_MARKER))
            try:
                obj, end = _DECODER.raw_decode(text, start)
            except ValueError:
                cursor = marker + len(_CONTEXT_MARKER)
                continue
            if isinstance(obj, dict) and not text[end:].strip():
                return start, end
            cursor = marker + len(_CONTEXT_MARKER)
    if purpose == "deliberacion":
        start = _skip_spaces(text, 0)
        try:
            obj, end = _DECODER.raw_decode(text, start)
        except ValueError:
            return None
        return (start, end) if isinstance(obj, dict) and not text[end:].strip() else None
    if purpose == "chat" and text.startswith(_CHAT_MARKER):
        start = _skip_spaces(text, len(_CHAT_MARKER))
        try:
            obj, end = _DECODER.raw_decode(text, start)
        except ValueError:
            return None
        if isinstance(obj, dict):
            return start, end
    return None


def _message(path, role, content, provider, purpose, title):
    if not isinstance(content, str):
        raise ValueError("Contenido de rol no textual; no ocultar sin avisar")
    interval = _json_interval(content, provider, purpose, role)
    fields = []
    if interval is not None:
        start, end = interval
        parsed_end = _scan_value(content, start, "", 0, fields)
        if parsed_end != end:
            raise ValueError("Offset del JSON enviado inconsistente")
    fields.sort(key=lambda f: (f["start"], f["end"]))
    top = [f for f in fields if f["depth"] == 1]
    segments = []

    def add(kind, a, b, *, name=None, pointer=None):
        if a >= b:
            return
        item = {"kind": kind, "start": a, "end": b,
                "literal": content[a:b]}
        if name is not None:
            item["title"] = name
            item["subtitle"] = _SUBTITLES.get(name, "")
        elif kind == "text":
            item["title"] = title
            item["subtitle"] = _ROLE_SUBTITLES.get(role, "")
        if pointer is not None:
            item["json_pointer"] = pointer
        segments.append(item)

    def gap(a, b):
        if interval is None:
            add("text", a, b)
            return
        js, je = interval
        if a < js:
            add("text", a, min(b, js))
        inner_a, inner_b = max(a, js), min(b, je)
        if inner_a < inner_b:
            add("syntax", inner_a, inner_b)
        if b > je:
            add("text", max(a, je), b)

    cursor = 0
    for field in top:
        gap(cursor, field["start"])
        add("field", field["start"], field["end"],
            name=field["title"], pointer=field["json_pointer"])
        cursor = field["end"]
    gap(cursor, len(content))
    if "".join(s["literal"] for s in segments) != content:
        raise ValueError("La segmentación no conserva el texto original")
    return {
        "path": path, "role": role, "title": title,
        "text": content, "length_codepoints": len(content),
        "context_interval": list(interval) if interval else None,
        "segments": segments,
        "blocks": [s for s in segments if s["kind"] in ("text", "field")],
        # Índice anidado para procedencia: offsets sobre el MISMO texto,
        # sin copias ni valores reinterpretados.
        "field_index": fields,
    }


def index_request(body: bytes, *, provider: str, purpose: str):
    """Interpretar únicamente para ubicar fragmentos; devolver texto intacto.

    body es el BLOB UTF-8 capturado al invocar el transporte. Ningún
    json.dumps de reconstrucción interviene en los bloques.
    """
    if not isinstance(body, bytes):
        raise TypeError("Se requieren bytes del cuerpo HTTP original")
    if provider not in _PROVIDERS or purpose not in _PURPOSES:
        raise ValueError("Proveedor o propósito no soportado")
    payload = json.loads(body.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Cuerpo HTTP sin objeto JSON")
    messages = []
    if provider == "gemini":
        system = payload.get("systemInstruction") or {}
        parts = system.get("parts", [])
        for n, part in enumerate(parts):
            if not isinstance(part, dict) or "text" not in part:
                raise ValueError("Parte del sistema no textual o inválida")
            path = f"/systemInstruction/parts/{n}/text"
            messages.append(_message(path, "system", part["text"],
                                     provider, purpose, "text"))
        for i, entry in enumerate(payload.get("contents", [])):
            if not isinstance(entry, dict):
                raise ValueError("Contenido Gemini sin objeto")
            role = entry.get("role")
            if role not in ("user", "model"):
                raise ValueError("Rol Gemini no reconocido")
            for n, part in enumerate(entry.get("parts", [])):
                if not isinstance(part, dict) or "text" not in part:
                    raise ValueError("Parte Gemini no textual o inválida")
                path = f"/contents/{i}/parts/{n}/text"
                messages.append(_message(path, role, part["text"],
                                         provider, purpose, "text"))
        if not messages:
            raise ValueError("Solicitud Gemini sin mensajes textuales")
    else:
        for i, entry in enumerate(payload.get("messages", [])):
            if not isinstance(entry, dict):
                raise ValueError("Mensaje no es un objeto")
            role = entry.get("role")
            if role not in ("system", "user", "assistant"):
                raise ValueError("Rol de mensaje desconocido")
            path = f"/messages/{i}/content"
            messages.append(_message(path, role, entry.get("content"),
                                     provider, purpose, "content"))
        if not messages:
            raise ValueError("Solicitud sin mensajes")
    return {
        "provider": provider, "purpose": purpose,
        "body_sha256": hashlib.sha256(body).hexdigest(),
        "body_bytes": len(body),
        # El cuerpo HTTP se conserva por separado en la sidecar. Aquí solo
        # se muestran mensajes decodificados realmente enviados al modelo.
        "messages": messages,
    }


def index_saved_attempt(row):
    """Indexar una lectura local verificada sin modificar la partida/sidecar."""
    body = row["body"]
    if (hashlib.sha256(body).hexdigest() != row["body_sha256"]
            or len(body) != row["body_bytes"]):
        raise ValueError("La captura no coincide con su checksum")
    result = index_request(body, provider=row["provider"], purpose=row["purpose"])
    result["attempt_id"] = row["attempt_id"]
    result["call_id"] = row["call_id"]
    result["attempt_ordinal"] = row["attempt_ordinal"]
    return result
