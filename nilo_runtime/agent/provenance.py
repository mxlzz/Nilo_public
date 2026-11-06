"""Procedencia verificable del contexto LLM (etapa 04).

Esta capa solo observa: las instantáneas crudas viven temporalmente en memoria
del worker y nunca se escriben en la base técnica. Lo persistido contiene
rutas, operaciones observadas y referencias al código, nunca valores ocultos.
"""
from __future__ import annotations

import ast
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path

from nilo_runtime.agent.provenance_codec import encode_metadata

ROOT = Path(__file__).resolve().parents[2]
STAGE_NAMES = (
    "percepcion", "proyeccion", "perfil",
    "compactacion", "presupuesto", "limite_proveedor",
    "filtro_chat", "solicitud_preparada",
)
_MAX_FIELDS = 8000
_MAX_DEPTH = 9
_CHAT_PREFIX = "CONTEXTO COMPROBADO (no lo contradigas): "
_GEMINI_PREFIX = "SITUACIÓN REAL: "


def _escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _type(value):
    if value is None: return "null"
    if isinstance(value, bool): return "boolean"
    if isinstance(value, dict): return "object"
    if isinstance(value, list): return "array"
    if isinstance(value, str): return "string"
    if isinstance(value, (int, float)): return "number"
    return "unknown"


def _paths(value, max_depth=_MAX_DEPTH):
    """Campos presentes, sin copias de valores en la salida del observador."""
    paths = {}
    stack = [("", value, 0)]
    while stack:
        pointer, item, depth = stack.pop()
        if pointer:
            paths[pointer] = _type(item)
        if len(paths) >= _MAX_FIELDS:
            raise ValueError("Contexto demasiado grande para trazabilidad completa")
        if depth >= max_depth:
            continue
        if isinstance(item, dict):
            for name, child in reversed(list(item.items())):
                stack.append((pointer + "/" + _escape(str(name)), child, depth + 1))
        elif isinstance(item, list):
            for index in range(len(item) - 1, -1, -1):
                stack.append((pointer + "/" + str(index), item[index], depth + 1))
    return paths


def _changes(before, after, max_depth=_MAX_DEPTH):
    """Comparación de paths Y valores en memoria; solo sale su estado."""
    left, right = _paths(before, max_depth), _paths(after, max_depth)
    diffs = {"added": [], "removed": [], "modified": []}
    for path in sorted(left.keys() | right.keys()):
        if path not in left:
            diffs["added"].append(path)
        elif path not in right:
            diffs["removed"].append(path)
        else:
            # Consultar directamente el valor en los snapshots: NO se guarda,
            # ni siquiera su hash, cuando fue excluido del payload.
            if _at(before, path) != _at(after, path):
                diffs["modified"].append(path)
    return diffs


def _at(value, pointer):
    for token in pointer.split("/")[1:]:
        key = token.replace("~1", "/").replace("~0", "~")
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def _code_reference(path, func, node, source, *, kind):
    snippet = ast.get_source_segment(source, node) or ""
    if len(snippet) > 230:
        snippet = snippet[:230] + "…"
    return {
        "file": path, "function": func, "line": node.lineno,
        "expression_excerpt": snippet,
        "source_kind": kind,
    }


def _subscript_key(target, owner):
    if not isinstance(target, ast.Subscript):
        return None
    if not isinstance(target.value, ast.Name) or target.value.id != owner:
        return None
    raw = target.slice
    return raw.value if isinstance(raw, ast.Constant) and isinstance(raw.value, str) else None


def _collect_function_refs(relative, function, *, roots, owner="context"):
    """Índice AST de las expresiones realmente existentes en el código.

    Un lugar de asignación es una referencia comprobable del código, pero
    NO acredita ejecución de una rama condicional. Esa distinción es explícita.
    """
    file = ROOT / relative
    if not file.is_file():
        return {}
    source = file.read_text(encoding="utf-8")
    tree = ast.parse(source)
    matches = [item for item in ast.walk(tree) if isinstance(item, ast.FunctionDef)
               and item.name == function]
    if not matches:
        return {}
    func = matches[0]
    refs = {}
    for node in ast.walk(func):
        if isinstance(node, ast.Assign):
            if isinstance(node.value, ast.Dict) and any(
                    isinstance(t, ast.Name) and t.id == owner for t in node.targets):
                for key, expression in zip(node.value.keys, node.value.values):
                    if (isinstance(key, ast.Constant) and
                            isinstance(key.value, str) and key.value in roots):
                        refs.setdefault(key.value, []).append(_code_reference(
                            relative, function, expression, source,
                            kind="declaracion_en_codigo"))
            for target in node.targets:
                key = _subscript_key(target, owner)
                if key in roots:
                    refs.setdefault(key, []).append(_code_reference(
                        relative, function, node.value, source,
                        kind="asignacion_en_codigo"))
        elif isinstance(node, ast.AnnAssign):
            key = _subscript_key(node.target, owner)
            if key in roots and node.value is not None:
                refs.setdefault(key, []).append(_code_reference(
                    relative, function, node.value, source,
                    kind="asignacion_en_codigo"))
    return refs


@lru_cache(maxsize=1)
def _catalog():
    # Los archivos se leen en la instalación local, no desde GitHub.
    # La referencia indica un lugar declarativo en el código actual; si el
    # código cambia sin reiniciar, no se puede inferir que fue ejecutado.
    primary = [
        ("brain.py", "context_for", "context"),
        ("nilo_runtime/application/decisions.py", "think", "context"),
        ("nilo_runtime/application/decisions.py", "start_chat", "context"),
        ("cognitive_projection.py", "project_context", "view"),
        ("nilo_runtime/agent/budget.py", "compact_context", "selected"),
        ("nilo_runtime/agent/budget.py", "bounded_context", "value"),
    ]
    catalog = {}
    hashes = {}
    # Extraemos claves del código automáticamente para no mantener un
    # catálogo paralelo y frágil de nombres JSON.
    for relative, func, owner in primary:
        srcfile = ROOT / relative
        if not srcfile.is_file():
            continue
        data = srcfile.read_bytes()
        hashes[relative] = hashlib.sha256(data).hexdigest()
        parsed = ast.parse(data.decode("utf-8-sig"))
        keys = set()
        for fn in ast.walk(parsed):
            if not isinstance(fn, ast.FunctionDef) or fn.name != func:
                continue
            for node in ast.walk(fn):
                if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict)
                        and any(isinstance(t, ast.Name) and t.id == owner
                                for t in node.targets)):
                    keys.update(key.value for key in node.value.keys
                                if isinstance(key, ast.Constant) and isinstance(key.value, str))
                if isinstance(node, ast.Assign):
                    keys.update(k for target in node.targets
                                if (k := _subscript_key(target, owner)) is not None)
                if isinstance(node, ast.AnnAssign):
                    k = _subscript_key(node.target, owner)
                    if k is not None:
                        keys.add(k)
        for key, rows in _collect_function_refs(relative, func, roots=keys,
                                                owner=owner).items():
            for row in rows:
                row = dict(row, file_sha256=hashes[relative])
                catalog.setdefault(key, []).append(row)
    return catalog, hashes


def _source(root):
    catalog, _ = _catalog()
    rows = catalog.get(root, [])
    if rows:
        return {
            "status": "referencias_de_codigo_no_traza_de_rama",
            "references": rows,
        }
    return {
        "status": "origen_no_instrumentado",
        "references": [],
    }


def _roles(provider, purpose):
    """Puntos reales del constructor; no se guardan textos de instrucciones."""
    if purpose == "chat":
        return {
            "system": ["nilo_runtime/agent/prompts.py:CHAT_SYSTEM",
                       "nilo_runtime/agent/gateway.py:build_chat_request(system_instruction)"],
            "user": ["nilo_runtime/agent/gateway.py:build_chat_request",
                     "nilo_runtime/application/decisions.py:start_chat"],
            "assistant": ["nilo_runtime/agent/gateway.py:build_chat_request(history)"],
            "model": ["nilo_runtime/agent/gateway.py:build_chat_request(history)"],
        }
    if provider == "gemini":
        return {
            "system": ["nilo_runtime/agent/prompts.py:SYSTEM",
                       "nilo_runtime/core/lab_settings.py:prompt_note"],
            "user": ["action_contracts.py:instructions",
                     "nilo_runtime/agent/gateway.py:build_deliberation_request"],
        }
    return {
        "system": (["nilo_runtime/agent/prompts.py:GROQ_SYSTEM",
                    "nilo_runtime/agent/budget.py:brief_actions",
                    "nilo_runtime/core/lab_settings.py:prompt_note"]
                   if provider == "groq"
                   else ["nilo_runtime/agent/prompts.py:SYSTEM",
                         "action_contracts.py:instructions",
                         "nilo_runtime/core/lab_settings.py:prompt_note"]),
        "user": ["nilo_runtime/agent/gateway.py:build_deliberation_request"],
    }


def _json_sent(body: bytes, provider: str, purpose: str):
    payload = json.loads(body.decode("utf-8"))
    texts = []
    if provider == "gemini":
        for entry in payload.get("contents", []):
            if isinstance(entry, dict) and entry.get("role") == "user":
                texts.extend(part["text"] for part in entry.get("parts", [])
                             if isinstance(part, dict) and isinstance(part.get("text"), str))
    else:
        for entry in payload.get("messages", []):
            if isinstance(entry, dict) and entry.get("role") == "user" and isinstance(
                    entry.get("content"), str):
                texts.append(entry["content"])
    if purpose == "chat":
        for text in texts:
            if text.startswith(_CHAT_PREFIX):
                obj, _ = json.JSONDecoder().raw_decode(text, len(_CHAT_PREFIX))
                if isinstance(obj, dict):
                    return obj
        return None
    if provider == "gemini":
        for text in texts:
            start = 0
            while True:
                index = text.find(_GEMINI_PREFIX, start)
                if index == -1:
                    break
                begin = index + len(_GEMINI_PREFIX)
                try:
                    obj, end = json.JSONDecoder().raw_decode(text, begin)
                except ValueError:
                    start = begin
                    continue
                if isinstance(obj, dict) and not text[end:].strip():
                    return obj
                start = begin
        return None
    for text in texts:
        try:
            obj = json.loads(text)
        except (ValueError, TypeError):
            continue
        if isinstance(obj, dict):
            return obj
    return None


def _build_metadata(snapshots, body: bytes, provider: str, purpose: str, *, max_depth=_MAX_DEPTH):
    """Compila etapas observadas; omite valores internos del JSON persistido.

    La igualdad contra el cuerpo capturado se verifica antes de atribuir
    el estado 'en_payload'. Si falla, el propio registro indica incertidumbre.
    """
    if not snapshots:
        return None
    if any(name not in STAGE_NAMES or not isinstance(value, dict)
           for name, value in snapshots):
        raise ValueError("Etapas de observación incorrectas")
    sent = _json_sent(body, provider, purpose)
    last_stage, final = snapshots[-1]
    verified = (last_stage == "solicitud_preparada" and sent == final)
    # Una comparación semántica JSON confirma los valores; los bytes exactos
    # se conservan en la tabla de la etapa 02.
    sequence = []
    all_paths = set()
    initial = None
    introduced = {}
    final_paths = _paths(final, max_depth)
    for index, (name, value) in enumerate(snapshots):
        paths = _paths(value, max_depth)
        for p in paths:
            all_paths.add(p)
            introduced.setdefault(p, name)
            if len(all_paths) >= _MAX_FIELDS:
                raise ValueError("Demasiadas rutas acumuladas")
        if index:
            prev_name, prev = snapshots[index - 1]
            delta = _changes(prev, value, max_depth)
            sequence.append({
                "stage": name, "previous_stage": prev_name, **delta,
                "added_count": len(delta["added"]),
                "removed_count": len(delta["removed"]),
                "modified_count": len(delta["modified"]),
            })
        else:
            initial = name

    if not verified:
        # Nunca atribuir "recibido" o "enviado" sobre una copia construida
        # que no coincida con el cuerpo capturado.
        exposure = "no_verificado_con_el_payload"
    else:
        exposure = "verificado_con_payload_http"
    origins = {}
    for p in sorted(all_paths):
        root = p.split("/")[1].replace("~1", "/").replace("~0", "~")
        if root not in origins:
            origins[root] = _source(root)
    fields = []
    for pointer in sorted(all_paths):
        root = pointer.split("/")[1].replace("~1", "/").replace("~0", "~")
        fields.append({
            "json_pointer": pointer,
            "origin_root": "/" + _escape(root),
            "origin_precision": ("campo_raiz" if pointer == "/" + _escape(root)
                                 else "heredada_del_campo_raiz_no_exacta"),
            "introduced_at": introduced[pointer],
            "present_at_last_stage": pointer in final_paths,
            "in_http_payload": (pointer in final_paths if verified else None),
            "type_at_last_stage": final_paths.get(pointer),
        })
    meta = {
        "schema_version": 1,
        "coverage": {"max_depth": max_depth, "list_identity": "index"},
        "source_scope": "referencias_ast_no_registro_de_ramas_ejecutadas",
        "comparison_scope": "mismo_json_pointer_por_etapa; listas_por_indice",
        "payload_verification": exposure,
        "first_stage": initial, "last_stage": last_stage,
        "stages": [name for name, _ in snapshots],
        "transitions": sequence,
        "fields": fields,
        "origins": origins,
        "role_sources": _roles(provider, purpose),
        "field_count": len(fields),
        "omitted_roots": sorted(root for root in origins
                                if "/" + _escape(root) not in final_paths),
    }
    # Identify the exact boundary of depth-limited coverage. No hidden values.
    cut = set()
    for _, value in snapshots:
        for pointer in _paths(value, max_depth):
            if pointer.count("/") == max_depth:
                child = _at(value, pointer)
                if isinstance(child, (dict, list)) and child:
                    cut.add(pointer)
    meta["coverage"]["unexpanded_paths"] = sorted(cut)
    meta["trace_status"] = "partial" if cut else "complete"
    return meta


def build_metadata(snapshots, body: bytes, provider: str, purpose: str):
    """Preserve full metadata when compressible; retain explicit root coverage otherwise."""
    if not snapshots:
        return None
    # Invalid contracts must not be disguised as size degradation.
    if any(name not in STAGE_NAMES or not isinstance(value, dict)
           for name, value in snapshots):
        raise ValueError("Etapas de observación incorrectas")
    try:
        meta = _build_metadata(snapshots, body, provider, purpose)
        encode_metadata(meta)  # Apply the bound to stored bytes, not repeated JSON labels.
        return meta
    except ValueError:
        # Root changes compare full in-memory values, including changes below
        # the boundary; only the nested attribution is omitted.
        meta = _build_metadata(snapshots, body, provider, purpose, max_depth=1)
        meta["trace_status"] = "partial"
        meta["coverage"]["reason"] = "nested_detail_exceeds_budget"
        encode_metadata(meta)
        return meta


def snapshot_context(value):
    """Copia privada efímera; el motor no comparte mutables con el observador."""
    return deepcopy(value) if isinstance(value, dict) else None
