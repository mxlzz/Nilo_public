"""Identidades reproducibles y generadores aislados por partida.

No importa mundo, SQLite, LLM ni el reloj. La identidad se serializa fuera
del save JSON v5 para no introducir una segunda verdad física ni modificar
replays antiguos. La vinculación entre hilos se hace con ContextVar.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
import hashlib
import random
import uuid
from typing import Any

ENTROPY_FORMAT = "nilo-entropy-v1"
_active: ContextVar["EntropySession | None"] = ContextVar("nilo_entropy", default=None)
_legacy_global: ContextVar[bool] = ContextVar("nilo_legacy_global_rng", default=False)


def _id_seed(world_seed: int, rng_seed: int) -> int:
    material = f"nilo-ids-v1|{world_seed}|{rng_seed}".encode("ascii")
    return int.from_bytes(hashlib.sha256(material).digest()[:16], "big")


def _to_json(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_to_json(x) for x in value]
    if value is None or type(value) in (int, float, str, bool):
        return value
    raise TypeError("Estado PRNG no serializable")


def _to_tuple(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(_to_tuple(x) for x in value)
    if value is None or type(value) in (int, float, str, bool):
        return value
    raise ValueError("Estado PRNG corrupto")


class EntropyError(ValueError):
    """Un estado RNG guardado no puede recuperarse sin pérdida de continuidad."""


class EntropySession:
    """RNG físico y secuencia de IDs independientes, con checkpoint serializable."""

    def __init__(self, world_seed: int, rng_seed: int):
        if type(world_seed) is not int or type(rng_seed) is not int:
            raise ValueError("Las semillas deben ser enteros, no booleanos")
        self.world_seed = world_seed
        self.rng_seed = rng_seed
        self.agent_rng = random.Random(rng_seed)
        self.id_seed = _id_seed(world_seed, rng_seed)
        self.id_rng = random.Random(self.id_seed)
        self.uuid_counter = 0
        self.physical_counter = 0

    def uuid4(self) -> uuid.UUID:
        # Los primeros 32 bits son una permutación biyectiva del contador:
        # mantiene únicos incluso los viejos prefijos uuid.hex[:8] y
        # str(uuid)[:8] hasta 2**32 asignaciones en la misma partida.
        if self.uuid_counter >= (1 << 32) - 1:
            raise OverflowError("Se agotó el espacio de IDs de esta partida")
        self.uuid_counter += 1
        salt = self.id_seed & 0xFFFFFFFF
        prefix = (self.uuid_counter * 0x9E3779B1 + salt) & 0xFFFFFFFF
        rest = self.id_rng.getrandbits(96)
        return uuid.UUID(int=(prefix << 96) | rest, version=4)

    def physical_suffix(self) -> int:
        """ID numérico monotónico en namespace nuevo, disjunto del legado.

        IDs antiguos: obj-<0..2**52> / obra-N-<0..2**16>.
        IDs nuevos mantienen formato, pero su sufijo es >=2**96. No pueden
        repetirse tras desarmar o retirar obras ni coincidir con IDs oficiales
        anteriores, aun cuando se recicle el índice visible de una obra.
        """
        if self.physical_counter >= (1 << 48) - 1:
            raise OverflowError("Se agotó la numeración física del mundo")
        self.physical_counter += 1
        namespace = self.id_seed & ((1 << 48) - 1)
        return (1 << 96) | (namespace << 48) | self.physical_counter

    def getrandbits(self, count: int) -> int:
        if type(count) is not int or count <= 0 or count > 128:
            raise ValueError("El número de bits debe estar entre 1 y 128")
        return self.id_rng.getrandbits(count)

    def to_record(self, *, agent_rng: random.Random | None = None) -> dict[str, Any]:
        physical = agent_rng if agent_rng is not None else self.agent_rng
        return {
            "format": ENTROPY_FORMAT,
            "world_seed": self.world_seed,
            "rng_seed": self.rng_seed,
            "id_seed": str(self.id_seed),
            "uuid_counter": self.uuid_counter,
            "physical_counter": self.physical_counter,
            "agent_rng_state": _to_json(physical.getstate()),
            "id_rng_state": _to_json(self.id_rng.getstate()),
        }

    @classmethod
    def from_record(cls, data: Any, *, world_seed: int) -> "EntropySession":
        if not isinstance(data, dict) or data.get("format") != ENTROPY_FORMAT:
            raise EntropyError("Formato de secuencias aleatorias desconocido")
        try:
            stored_seed = data["rng_seed"]
            count = data["uuid_counter"]
            physical_count = data["physical_counter"]
            if type(data.get("world_seed")) is not int or data["world_seed"] != world_seed:
                raise EntropyError("La semilla del mundo cambió respecto del checkpoint")
            if (type(stored_seed) is not int or type(count) is not int
                    or not 0 <= count < (1 << 32)
                    or type(physical_count) is not int
                    or not 0 <= physical_count < (1 << 48)):
                raise EntropyError("Semilla o contador de identidad inválido")
            result = cls(world_seed, stored_seed)
            if data.get("id_seed") != str(result.id_seed):
                raise EntropyError("El origen de la secuencia de IDs no coincide")
            result.agent_rng.setstate(_to_tuple(data["agent_rng_state"]))
            result.id_rng.setstate(_to_tuple(data["id_rng_state"]))
            result.uuid_counter = count
            result.physical_counter = physical_count
            return result
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            if isinstance(exc, EntropyError):
                raise
            raise EntropyError(
                "Checkpoint RNG inválido: conservá la partida; no se regenerarán IDs"
            ) from exc

    @contextmanager
    def bind(self):
        token = _active.set(self)
        try:
            yield self
        finally:
            _active.reset(token)


def new_uuid() -> uuid.UUID:
    """API UUID histórica, determinista sólo dentro de un contexto de partida."""
    active = _active.get()
    return (active.uuid4() if active is not None and not _legacy_global.get()
            else uuid.uuid4())


def id_bits(n: int) -> int:
    """API del constructor físico de IDs, sin consumir RNG del movimiento."""
    active = _active.get()
    return active.getrandbits(n) if active is not None else random.getrandbits(n)


def entropy_scoped(method):
    """Asociar operaciones de Simulation a su partida; replays usan ruta anterior."""
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        entropy = getattr(self, "entropy", None)
        if (getattr(self, "historical_replay", False)
                or getattr(self, "legacy_replay_rules", False)
                or getattr(self, "legacy_identity_mode", False)):
            # Reproducciones publicadas consumen el RNG global antiguo de
            # world.py, incluso si se pasó un Random explícito al handler.
            token = _legacy_global.set(True)
            try:
                return method(self, *args, **kwargs)
            finally:
                _legacy_global.reset(token)
        if entropy is None:
            return method(self, *args, **kwargs)
        with entropy.bind():
            return method(self, *args, **kwargs)
    return wrapped



@contextmanager
def staged_identity():
    """Reserva de IDs reversible para una operación física aún sin confirmar.

    El PRNG de identidades no pertenece al RNG de decisiones. Un rechazo
    restaura sus contadores y secuencia, sin afectar los IDs de otros mundos.
    Las partidas legacy sin EntropySession mantienen el camino histórico.
    """
    session=_active.get()
    if session is None or _legacy_global.get():
        yield lambda: None
        return
    original_uuid=session.uuid_counter
    original_physical=session.physical_counter
    original_rng=session.id_rng.getstate()
    accepted=False

    def confirm():
        nonlocal accepted
        accepted=True

    try:
        yield confirm
    finally:
        if not accepted:
            session.uuid_counter=original_uuid
            session.physical_counter=original_physical
            session.id_rng.setstate(original_rng)


def physical_suffix(legacy_bits: int, *, rng: random.Random | None = None) -> int:
    """UUID físico moderno o RNG explícito; legado conserva el RNG global.

    Fuera de una Simulation con scope, execute_action(w,p,step,rng) es
    determinista aun si otro proceso cambia random.seed().
    """
    active = _active.get()
    if active is not None and not _legacy_global.get():
        return active.physical_suffix()
    if _legacy_global.get() or rng is None:
        return random.getrandbits(legacy_bits)
    return rng.getrandbits(legacy_bits)
