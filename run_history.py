"""Sesiones verificables por versión dentro de la misma partida SQLite.

No reconstruye ni atribuye versiones a períodos previos a esta instrumentación.
El registro es técnico/observacional: Nilo no recibe estos metadatos como conocimiento.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def engine_identity(root):
    """Identifica el programa real; los ZIP sin metadatos Git quedan explícitos."""
    root = Path(root).resolve()
    try:
        version = (root / "VERSION").read_text(encoding="utf-8").strip()
    except OSError:
        version = "no_registrada"
    try:
        manifest_digest = hashlib.sha256(
            (root / "MANIFIESTO_SHA256.json").read_bytes()
        ).hexdigest()
    except OSError:
        manifest_digest = None
    commit = None
    try:
        top = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=2, check=False,
        )
        if top.returncode == 0 and Path(top.stdout.strip()).resolve() == root:
            response = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                capture_output=True, text=True, timeout=2, check=False,
            )
            if response.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", response.stdout.strip()):
                commit = response.stdout.strip()
    except (OSError, subprocess.TimeoutExpired, ValueError):
        pass
    return {"engine_version": version, "code_commit": commit,
            "manifest_sha256": manifest_digest}


class RunHistory:
    def __init__(self, conn, root):
        self.db = conn
        self.identity = engine_identity(root)
        self.session_id = None
        self.db.execute("""CREATE TABLE IF NOT EXISTS engine_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_utc TEXT NOT NULL,
            last_seen_utc TEXT NOT NULL,
            ended_utc TEXT,
            end_reason TEXT,
            engine_version TEXT NOT NULL,
            code_commit TEXT,
            manifest_sha256 TEXT,
            scenario_id TEXT NOT NULL,
            environment_id TEXT NOT NULL,
            simulated_start_min REAL NOT NULL,
            simulated_end_min REAL NOT NULL,
            configured_provider TEXT,
            configured_model TEXT
        )""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS session_model_usage (
            session_id INTEGER NOT NULL,
            provider TEXT NOT NULL,
            model TEXT NOT NULL,
            purpose TEXT NOT NULL CHECK(purpose IN ('deliberacion','chat')),
            calls INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(session_id,provider,model,purpose)
        )""")
        # Las partidas heredadas conservan las sesiones existentes sin fingir
        # que conocemos su snapshot inicial ni la semilla del RNG.
        columns={r[1] for r in self.db.execute("PRAGMA table_info(engine_sessions)")}
        for name,definition in (("start_state_sha256","TEXT"),("rng_seed","INTEGER"),
                                ("world_seed","INTEGER")):
            if name not in columns:
                self.db.execute(f"ALTER TABLE engine_sessions ADD COLUMN {name} {definition}")
        self.db.commit()

    def start(self, state, scenario_id, environment_id, configured_provider=None,
              configured_model=None, rng_seed=None):
        """Siempre nueva sesión al abrir una partida; no rellenar historia anterior."""
        if self.session_id is not None:
            raise RuntimeError("Ya hay una sesión abierta en esta instancia.")
        now = utc_now()
        minute = float(state["person"]["clock_minutes"])
        identity = self.identity
        # Fingerprint del estado de origen, sin relojes reales, proveedor, tokens,
        # mensajes al observador o campos temporales del coordinador.
        reference = {"world":state["world"],"person":state["person"],
                     "scenario_id":scenario_id,"environment_id":environment_id}
        digest=hashlib.sha256(json.dumps(reference,ensure_ascii=False,
                         sort_keys=True,separators=(",",":"),default=str).encode("utf-8")).hexdigest()
        seed=state["world"].get("seed")
        cursor = self.db.execute(
            """INSERT INTO engine_sessions(
                started_utc,last_seen_utc,engine_version,code_commit,manifest_sha256,
                scenario_id,environment_id,simulated_start_min,simulated_end_min,
                configured_provider,configured_model,start_state_sha256,rng_seed,world_seed
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (now, now, identity["engine_version"], identity["code_commit"],
             identity["manifest_sha256"], scenario_id, environment_id,
             minute, minute, configured_provider, configured_model,
             digest,int(rng_seed) if rng_seed is not None else None,
             int(seed) if seed is not None else None),
        )
        self.session_id = cursor.lastrowid
        # La transacción se confirma junto con el snapshot en Simulation.write().
        return self.session_id

    def touch(self, simulated_minutes):
        if self.session_id is None:
            return
        self.db.execute(
            """UPDATE engine_sessions SET last_seen_utc=?,simulated_end_min=?
               WHERE id=? AND ended_utc IS NULL""",
            (utc_now(), float(simulated_minutes), self.session_id),
        )

    def note_llm(self, provider, model, purpose="deliberacion"):
        """Contar el modelo REAL tras una respuesta correcta; no el de la configuración."""
        if self.session_id is None:
            return
        if purpose not in ("deliberacion", "chat"):
            raise ValueError("Propósito desconocido")
        provider = str(provider or "desconocido")[:100]
        model = str(model or "desconocido")[:160]
        self.db.execute(
            """INSERT INTO session_model_usage(session_id,provider,model,purpose,calls)
               VALUES (?,?,?,?,1)
               ON CONFLICT(session_id,provider,model,purpose)
               DO UPDATE SET calls=calls+1""",
            (self.session_id, provider, model, purpose),
        )

    def finish(self, simulated_minutes, reason="normal"):
        """Solo un cierre efectivo establece ended_utc."""
        if self.session_id is None:
            return
        now = utc_now()
        self.db.execute(
            """UPDATE engine_sessions SET last_seen_utc=?,ended_utc=?,
               simulated_end_min=?,end_reason=?
               WHERE id=? AND ended_utc IS NULL""",
            (now, now, float(simulated_minutes), str(reason)[:40], self.session_id),
        )
        self.db.commit()
        self.session_id = None

    def recent(self, limit=30):
        """Vista compacta; no exponer configuración privada ni mundo no observado."""
        limit = max(1, min(100, int(limit)))
        rows = self.db.execute(
            """SELECT id,started_utc,last_seen_utc,ended_utc,end_reason,
                      engine_version,code_commit,manifest_sha256,
                      scenario_id,environment_id,simulated_start_min,
                      simulated_end_min,configured_provider,configured_model,
                      start_state_sha256,rng_seed,world_seed
               FROM engine_sessions ORDER BY id DESC LIMIT ?""", (limit,),
        ).fetchall()
        keys = ("id","started_utc","last_seen_utc","ended_utc","end_reason",
                "engine_version","code_commit","manifest_sha256","scenario_id",
                "environment_id","simulated_start_min","simulated_end_min",
                "configured_provider","configured_model","start_state_sha256",
                "rng_seed","world_seed")
        sessions = [dict(zip(keys, row)) for row in rows]
        if not sessions:
            return sessions
        usages = self.db.execute(
            """SELECT session_id,provider,model,purpose,calls
               FROM session_model_usage
               WHERE session_id IN (%s)
               ORDER BY session_id DESC, purpose,provider,model""" % ",".join("?" for _ in sessions),
            [s["id"] for s in sessions],
        ).fetchall()
        by_id = {s["id"]: s for s in sessions}
        for s in sessions:
            s["models_used"] = []
            s["state"] = ("en_curso" if s["id"] == self.session_id else
                          "cerrada" if s["ended_utc"] else "sin_cierre_registrado")
        for sid, provider, model, purpose, calls in usages:
            by_id[sid]["models_used"].append(
                {"provider": provider, "model": model, "purpose": purpose, "calls": calls})
        return sessions
