"""E09.02f.5b: C1 dendrite migration core reconstructed from x86.

Source: user-supplied Creatures.exe (PE32 x86; SHA-256
548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7).
Type1 VA 0x404A80–0x404B8C; Type2 VA 0x404B90–0x404EA1.

Directly supported semantics: rand() % n, duplicate source checks,
in-place shuffle, exclusive-group rejection, checksum collisions,
rewiring whole concept class, range initialization, and failure restore.

The caller's cursor scheduler and global Microsoft CRT PRNG state are
NOT reconstructed. RandStream explicitly supplies raw rand() outputs.
This code does not run or distribute the original executable.
"""
from __future__ import annotations

from dataclasses import dataclass, replace


def _byte(value: int, name: str) -> int:
    if type(value) is not int or not 0 <= value <= 255:
        raise ValueError(f"{name}: byte 0..255 necesario")
    return value


def _pointer(value: int) -> int:
    if type(value) is not int or not 0 < value <= 0xFFFFFFFF:
        raise ValueError("puntero de origen de 32 bits no nulo requerido")
    return value


@dataclass(frozen=True)
class SourceNeuron:
    pointer: int
    exclusive_lobe: int = 0

    def __post_init__(self):
        _pointer(self.pointer)
        _byte(self.exclusive_lobe, "exclusive_lobe")


@dataclass(frozen=True)
class Dendrite:
    source_pointer: int
    stw: int
    ltw: int
    strength: int
    susceptibility: int = 0

    def __post_init__(self):
        _pointer(self.source_pointer)
        for name in ("stw", "ltw", "strength", "susceptibility"):
            _byte(getattr(self, name), name)


@dataclass(frozen=True)
class MigrationConfig:
    initial_ltw_min: int
    initial_ltw_max: int
    initial_strength_min: int
    initial_strength_max: int

    def __post_init__(self):
        for name in ("initial_ltw_min", "initial_ltw_max",
                     "initial_strength_min", "initial_strength_max"):
            _byte(getattr(self, name), name)
        if (self.initial_ltw_max < self.initial_ltw_min
                or self.initial_strength_max < self.initial_strength_min):
            raise ValueError("rango genético invertido")


@dataclass(frozen=True)
class MigrationState:
    dendrites: tuple[Dendrite, ...]
    loose_counter: int = 0

    def __post_init__(self):
        if not isinstance(self.dendrites, tuple) or not self.dendrites:
            raise ValueError("se necesitan dendritas de una clase")
        if any(not isinstance(d, Dendrite) for d in self.dendrites):
            raise TypeError("dendrita inválida")
        if type(self.loose_counter) is not int or self.loose_counter < 0:
            raise ValueError("contador de conexiones agotadas inválido")


@dataclass(frozen=True)
class RandStream:
    """Lista de resultados YA DEVUELTOS por rand() de la CRT; no PRNG Python."""
    draws: tuple[int, ...]
    cursor: int = 0

    def __post_init__(self):
        if not isinstance(self.draws, tuple) or any(
            type(v) is not int or not 0 <= v <= 32767 for v in self.draws
        ):
            raise ValueError("rand() Microsoft devuelve entero 0..32767")
        if type(self.cursor) is not int or not 0 <= self.cursor <= len(self.draws):
            raise ValueError("cursor de secuencia de azar inválido")

    def pick(self, size: int) -> tuple[int, "RandStream"]:
        if type(size) is not int or size <= 0:
            raise ValueError("rango de rand()%n inválido")
        if self.cursor >= len(self.draws):
            raise RuntimeError("se agotó la secuencia inyectada de rand()")
        return self.draws[self.cursor] % size, replace(self, cursor=self.cursor + 1)


@dataclass(frozen=True)
class MigrationResult:
    state: MigrationState
    random: RandStream
    sources_order: tuple[SourceNeuron, ...]
    migrated: bool
    reason: str
    attempts: tuple[str, ...] = ()


def _source_pool(sources: tuple[SourceNeuron, ...]) -> None:
    if not isinstance(sources, tuple) or any(not isinstance(s, SourceNeuron) for s in sources):
        raise TypeError("pool de neuronas activas incorrecto")
    addresses = [source.pointer for source in sources]
    if len(set(addresses)) != len(addresses):
        raise ValueError("fuentes activas duplicadas en pool")


def _random_initialized(
    original: Dendrite,
    source_pointer: int,
    config: MigrationConfig,
    tape: RandStream,
) -> tuple[Dendrite, RandStream]:
    ltw_index, tape = tape.pick(config.initial_ltw_max - config.initial_ltw_min + 1)
    strength_index, tape = tape.pick(
        config.initial_strength_max - config.initial_strength_min + 1
    )
    ltw = config.initial_ltw_min + ltw_index
    strength = config.initial_strength_min + strength_index
    return Dendrite(source_pointer, ltw, ltw, strength, susceptibility=0), tape


def concept_checksum(source_pointers: tuple[int, ...]) -> int:
    """x86: (sum raw source-pointers <<16) | (product &0xffff).

    The game compares checksums, not full sorted source combinations.
    Different combinations can collide; sum/product are 32-bit x86.
    """
    if not isinstance(source_pointers, tuple):
        raise TypeError("se requieren punteros en tupla")
    sum32 = 0
    product32 = 1
    for pointer in source_pointers:
        _pointer(pointer)
        sum32 = (sum32 + pointer) & 0xFFFFFFFF
        product32 = (product32 * pointer) & 0xFFFFFFFF
    return ((sum32 & 0xFFFF) << 16) | (product32 & 0xFFFF)


def _decrement_counter(current: int) -> int:
    return max(0, current - 1)


def decision_migrate(
    state: MigrationState,
    sources: tuple[SourceNeuron, ...],
    config: MigrationConfig,
    random: RandStream,
    *,
    recipient_output: int,
) -> MigrationResult:
    """One type1 attempt: choose 1 active source, abort on duplicate."""
    _byte(recipient_output, "recipient_output")
    _source_pool(sources)
    if not isinstance(config, MigrationConfig) or not isinstance(random, RandStream):
        raise TypeError("config y random requeridos")
    if recipient_output == 0:
        return MigrationResult(state, random, sources, False, "inactive_recipient")
    if not sources:
        return MigrationResult(state, random, sources, False, "no_active_source")
    disconnected = next(
        (i for i, d in enumerate(state.dendrites) if d.strength == 0), None
    )
    if disconnected is None:
        return MigrationResult(state, random, sources, False, "no_disconnected_dendrite")

    selected, random = random.pick(len(sources))
    candidate = sources[selected].pointer
    if any(d.source_pointer == candidate for d in state.dendrites):
        return MigrationResult(state, random, sources, False, "duplicate_source",
                               ("duplicate",))
    replacement, random = _random_initialized(
        state.dendrites[disconnected], candidate, config, random,
    )
    dendrites = list(state.dendrites)
    dendrites[disconnected] = replacement
    return MigrationResult(
        MigrationState(tuple(dendrites), _decrement_counter(state.loose_counter)),
        random, sources, True, "accepted", ("accepted",),
    )


def _exclusive_conflict(sources: tuple[SourceNeuron, ...]) -> bool:
    nonzero = [s.exclusive_lobe for s in sources if s.exclusive_lobe != 0]
    return len(nonzero) != len(set(nonzero))


def concept_migrate(
    state: MigrationState,
    active_sources: tuple[SourceNeuron, ...],
    config: MigrationConfig,
    random: RandStream,
    *,
    selected_recipient: bool = True,
    other_active_wirings: tuple[tuple[int, ...], ...] = (),
) -> MigrationResult:
    """One selected recipient's type2 migration; scheduler is external.

    The original active source pointer array is shuffled IN PLACE by x86.
    An immutable replacement order is returned so a caller can persist
    it. Every source combination uses the entire class, not just loose
    dendrites.
    """
    _source_pool(active_sources)
    if not isinstance(config, MigrationConfig) or not isinstance(random, RandStream):
        raise TypeError("config y random requeridos")
    if (not isinstance(other_active_wirings, tuple)
            or any(not isinstance(group, tuple) for group in other_active_wirings)):
        raise TypeError("otras neuronas deben ser tuplas de punteros")
    for group in other_active_wirings:
        for ptr in group:
            _pointer(ptr)
    if not isinstance(selected_recipient, bool):
        raise ValueError("selected_recipient debe ser bool")
    if not selected_recipient:
        return MigrationResult(state, random, active_sources, False, "not_selected")
    if not any(d.strength == 0 for d in state.dendrites):
        return MigrationResult(state, random, active_sources, False, "no_disconnected_dendrite")

    count = len(active_sources)
    degree = len(state.dendrites)
    if count < degree:
        return MigrationResult(state, random, active_sources, False, "insufficient_sources")

    # MS CRT rand()%count, n draws; shuffling changes the lobe active list.
    sources = list(active_sources)
    for i in range(count):
        j, random = random.pick(count)
        sources[i], sources[j] = sources[j], sources[i]
    shuffled = tuple(sources)

    comparisons = set(
        concept_checksum(group) for group in other_active_wirings
        if len(group) == degree
    )
    attempts = []
    for start in range(count - degree + 1):
        window = shuffled[start:start + degree]
        if _exclusive_conflict(window):
            attempts.append(f"exclusive:{start}")
            continue

        # The x86 routine initializes ALL dendrites before checking the
        # recipient-lobe checksum, so even a rejected candidate consumes
        # 2*degree rand calls.
        prepared = []
        for old, source in zip(state.dendrites, window):
            new_d, random = _random_initialized(old, source.pointer, config, random)
            prepared.append(new_d)
        signature = concept_checksum(tuple(s.pointer for s in window))
        if signature in comparisons:
            attempts.append(f"checksum:{start}")
            continue

        attempts.append(f"accepted:{start}")
        return MigrationResult(
            MigrationState(tuple(prepared), _decrement_counter(state.loose_counter)),
            random, shuffled, True, "accepted", tuple(attempts),
        )

    # Failure restores all OLD pointer addresses, while invalidating all
    # synaptic weights/strengths; original x86 does not retry indefinitely.
    restored = tuple(
        Dendrite(d.source_pointer, 0, 0, 0, susceptibility=d.susceptibility)
        for d in state.dendrites
    )
    return MigrationResult(
        MigrationState(restored, state.loose_counter), random, shuffled,
        False, "no_valid_wiring", tuple(attempts),
    )
