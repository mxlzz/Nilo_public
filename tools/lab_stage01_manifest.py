#!/usr/bin/env python3
"""Inventario de SOLO LECTURA de un mundo Nilo y su sidecar HTTP.

Emite exclusivamente métricas, nombres de categorías y hashes; nunca prompts,
mensajes, planes, IDs internos ni claves API.
Uso: python tools/lab_stage01_manifest.py --world MUNDO.sqlite3 --requests TRAZAS.sqlite3 --output manifest.json
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import zlib

MAX_META_COMPRESSED = 400_000
MAX_META_DECODED = 8 * 1024 * 1024


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_db(path: Path):
    if not path.is_file():
        raise FileNotFoundError(f"No existe la base: {path}")
    db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=2)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA query_only=ON")
    return db


def has_table(db, name):
    return bool(db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone())


def parse_provenance(encoded):
    if encoded is None:
        return None
    if len(encoded.encode("utf-8")) > MAX_META_COMPRESSED:
        raise ValueError("Metadatos de procedencia demasiado grandes")
    obj = json.loads(encoded)
    if obj.get("storage_encoding") == "zlib-base64-v1":
        size = obj.get("decoded_bytes")
        if type(size) is not int or not 0 <= size <= MAX_META_DECODED:
            raise ValueError("Tamaño decodificado inválido")
        packed = base64.b64decode(obj["data"], validate=True)
        decoder = zlib.decompressobj()
        raw = decoder.decompress(packed, size + 1)
        if (len(raw) != size or not decoder.eof or decoder.unconsumed_tail
                or decoder.unused_data or sha(raw) != obj.get("sha256")):
            raise ValueError("Procedencia corrupta")
        obj = json.loads(raw)
    if obj.get("schema_version") != 1:
        raise ValueError("Versión de procedencia desconocida")
    return obj


def make_manifest(world_path: Path, requests_path: Path) -> dict:
    world_path = Path(world_path)
    requests_path = Path(requests_path)
    with closing(read_db(world_path)) as world, closing(read_db(requests_path)) as requests:
        required = {"history", "timeline_checkpoints", "engine_sessions"}
        if not all(has_table(world, t) for t in required):
            raise ValueError("El mundo no contiene todas las tablas modernas de auditoría")
        if not has_table(requests, "llm_requests"):
            raise ValueError("Falta la tabla de solicitudes HTTP")

        hc = Counter(dict(world.execute(
            "SELECT category,COUNT(*) FROM history GROUP BY category")))
        cp = Counter(dict(world.execute(
            "SELECT kind,COUNT(*) FROM timeline_checkpoints GROUP BY kind")))
        versions = sorted({row[0] for row in world.execute(
            "SELECT DISTINCT engine_version FROM engine_sessions") if row[0]})

        cp_valid = cp_invalid = 0
        for row in world.execute("SELECT blob,blob_sha256 FROM timeline_checkpoints"):
            if sha(row["blob"]) == row["blob_sha256"]:
                cp_valid += 1
            else:
                cp_invalid += 1
        ops = Counter(dict(world.execute(
            "SELECT operation,COUNT(*) FROM timeline_checkpoints "
            "WHERE kind='action' GROUP BY operation")))

        linked_calls = []
        linked_without_id = 0
        for row in world.execute("SELECT payload FROM history WHERE category='llm_decision'"):
            record = json.loads(row["payload"])
            call = record.get("trace_call_id")
            if isinstance(call, str) and call:
                linked_calls.append(call)
            else:
                linked_without_id += 1
        # Los IDs solo se usan para el join local, nunca para exportar.
        links = Counter(linked_calls)

        attempts = []
        hash_errors = len_errors = 0
        for row in requests.execute(
                "SELECT call_id,attempt_ordinal,status,body,body_bytes,body_sha256 "
                "FROM llm_requests ORDER BY rowid"):
            body = row["body"]
            hash_errors += int(sha(body) != row["body_sha256"])
            len_errors += int(len(body) != row["body_bytes"])
            attempts.append({
                "call": row["call_id"], "ordinal": row["attempt_ordinal"],
                "status": row["status"], "bytes": row["body_bytes"],
                "hash": row["body_sha256"],
            })
        status = Counter(a["status"] for a in attempts)
        by_call = Counter(a["call"] for a in attempts)
        joined = sum(1 for call in linked_calls if call in by_call)
        accepted_orphans = sum(
            a["status"] == "accepted" and a["call"] not in links
            for a in attempts)

        verification = Counter()
        coverage = Counter()
        provenance_errors = 0
        prov_count = 0
        if has_table(requests, "llm_request_provenance"):
            for row in requests.execute("SELECT metadata_json FROM llm_request_provenance"):
                try:
                    p = parse_provenance(row["metadata_json"])
                    prov_count += 1
                    verification[str(p.get("payload_verification", "no_reportado"))] += 1
                    coverage[str(p.get("trace_status", "no_reportado"))] += 1
                except (ValueError, TypeError, KeyError, zlib.error, json.JSONDecodeError):
                    provenance_errors += 1

        candidates = []
        if attempts:
            candidates.append(("primera_solicitud", attempts[0]))
        for name, predicate in (
            ("error_transporte", lambda a: a["status"] == "transport_error"),
            ("reintento_aceptado", lambda a: a["status"] == "accepted" and a["ordinal"] > 1),
            ("aceptada_sin_decision_archivada",
             lambda a: a["status"] == "accepted" and a["call"] not in links),
        ):
            found = next((a for a in attempts if predicate(a)), None)
            if found is not None:
                candidates.append((name, found))

        return {
            "schema": "nilo-lab-stage01-inventory-v1",
            "privacy": "Solo agregados y SHA-256; sin contenidos de mundo, prompts, respuestas ni identificadores",
            "source_files": {
                "world_sha256": file_sha(world_path),
                "requests_sha256": file_sha(requests_path),
            },
            "world": {
                "engine_versions": versions,
                "history_total": sum(hc.values()),
                "history_by_category": dict(sorted(hc.items())),
                "checkpoints_total": sum(cp.values()),
                "checkpoints_by_kind": dict(sorted(cp.items())),
                "checkpoint_hash_valid": cp_valid,
                "checkpoint_hash_invalid": cp_invalid,
                "checkpoint_actions_by_op": dict(sorted(
                    (str(k), v) for k, v in ops.items())),
            },
            "requests": {
                "attempts_total": len(attempts),
                "unique_calls": len(by_call),
                "status_counts": dict(sorted(status.items())),
                "duplicate_body_hashes": len(attempts) - len({
                    a["hash"] for a in attempts}),
                "body_sha256_invalid": hash_errors,
                "body_length_invalid": len_errors,
                "provenance_count": prov_count,
                "provenance_errors": provenance_errors,
                "provenance_payload_verification": dict(sorted(
                    verification.items())),
                "provenance_trace_status": dict(sorted(coverage.items())),
            },
            "links": {
                "archived_llm_decisions": hc.get("llm_decision", 0),
                "decisions_with_call_id": len(linked_calls),
                "decisions_with_matching_request": joined,
                "decisions_without_call_id": linked_without_id,
                "accepted_attempts_without_archived_decision": accepted_orphans,
            },
            "reference_cases": [
                {
                    "kind": kind, "body_sha256": a["hash"],
                    "body_bytes": a["bytes"], "status": a["status"],
                }
                for kind, a in candidates
            ],
            "limitations": [
                "La solicitud HTTP aceptada no garantiza decisión archivada",
                "No hay respuesta textual cruda en la sidecar de solicitudes de esta versión",
                "Los checkpoints no garantizan replay idéntico con versiones o fuentes externas distintas",
                "Los vínculos de acciones con decisiones requieren trazabilidad específica adicional",
            ],
        }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--world", required=True, type=Path)
    p.add_argument("--requests", required=True, type=Path)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    data = json.dumps(make_manifest(args.world, args.requests),
                      ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(data, encoding="utf-8")
    else:
        print(data, end="")


if __name__ == "__main__":
    main()
