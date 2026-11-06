"""Lossless, bounded encoding of provenance metadata; legacy JSON stays readable."""
from __future__ import annotations

import base64
import hashlib
import json
import zlib

MAX_STORED_BYTES = 400000
MAX_DECODED_BYTES = 8 * 1024 * 1024


def encode_metadata(metadata):
    raw = json.dumps(metadata, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(raw) > MAX_DECODED_BYTES:
        raise ValueError("Procedencia demasiado grande al decodificar")
    packed = json.dumps({
        "storage_encoding": "zlib-base64-v1",
        "decoded_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "data": base64.b64encode(zlib.compress(raw)).decode("ascii"),
    }, separators=(",", ":"))
    encoded = packed if len(packed) < len(raw) else raw.decode("utf-8")
    if len(encoded.encode("utf-8")) > MAX_STORED_BYTES:
        raise ValueError("Procedencia demasiado grande para almacenar")
    return encoded


def decode_metadata(encoded):
    # Legacy records were bounded at 400 KB, too. Reject before decompressing.
    if len(encoded.encode("utf-8")) > MAX_STORED_BYTES:
        raise ValueError("Registro de procedencia fuera de límite")
    result = json.loads(encoded)
    if isinstance(result, dict) and "storage_encoding" in result:
        if result["storage_encoding"] != "zlib-base64-v1":
            raise ValueError("Codificación de procedencia desconocida")
        size = result.get("decoded_bytes")
        if type(size) is not int or not 0 <= size <= MAX_DECODED_BYTES:
            raise ValueError("Tamaño de procedencia inválido")
        try:
            packed = base64.b64decode(result["data"], validate=True)
            decoder = zlib.decompressobj()
            raw = decoder.decompress(packed, size + 1)
            if (len(raw) != size or not decoder.eof or decoder.unconsumed_tail
                    or decoder.unused_data):
                raise ValueError("Procedencia comprimida incompleta o fuera de límite")
            if hashlib.sha256(raw).hexdigest() != result.get("sha256"):
                raise ValueError("Checksum de procedencia incorrecto")
            result = json.loads(raw.decode("utf-8"))
        except (zlib.error, KeyError, TypeError) as exc:
            raise ValueError("Procedencia comprimida inválida") from exc
    if not isinstance(result, dict) or result.get("schema_version") != 1:
        raise ValueError("Metadatos de procedencia incompatibles")
    return result
