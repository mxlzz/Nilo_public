"""NR01.03: *evaluator-only* synthetic worlds and observation tapes.

Design preregistered BEFORE this module:
  docs/neurolab/NR01_02_PREREGISTRO_DESAFIO_20261122.md
  docs/neurolab/NR01_02A_CONTRATO_GENERADOR_PRECODIGO.md

NO learner/model and NO scientific cohort is executed by importing this.
Caller must expose only case.observation to the encoder/decoder. The case's
latent factors and target_for_evaluator() must stay within the evaluator.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
import json
import random
from typing import Literal

Family = Literal["A", "B"]
Phase = Literal["unsupervised", "feedback", "reversal", "feedback_b2", "test"]
_PHASE = {"parameters": 11, "unsupervised": 23, "feedback": 37,
          "reversal": 41, "feedback_b2": 43, "test": 47}
_FAMILY = {"A": 1, "B": 2}
_DIM = 16
_HISTORIC_RESERVED = frozenset(range(1400, 1420))
_CONFIRMATION_RESERVED = frozenset(range(24000, 24020))


@dataclass(frozen=True)
class EvaluatorCase:
    """Private evaluator record; NEVER pass this whole object to models."""
    observation: tuple[float, ...]
    latent: tuple[int, ...]

    def __post_init__(self) -> None:
        if len(self.observation) != _DIM or any(
            type(v) is not float or not (0.0 <= v <= 1.0)
            for v in self.observation
        ):
            raise ValueError("16 scalar observations in [0,1] required")


def seed_for(world_seed: int, family: Family,
             phase: str, stage: int = 0) -> int:
    if type(world_seed) is not int or world_seed < 0:
        raise ValueError("world_seed must be nonnegative int")
    if family not in _FAMILY or phase not in _PHASE:
        raise ValueError("unknown family or phase")
    if type(stage) is not int or stage < 0:
        raise ValueError("stage must be nonnegative int")
    return (world_seed * 1000003 + _FAMILY[family] * 10007
            + _PHASE[phase] * 1009 + stage * 17)


def legal_latents(family: Family, *, test: bool) -> tuple[tuple[int, ...], ...]:
    if family == "A":
        return tuple((z, c) for z in range(4) for c in range(4)
                     if (c == (z + 3) % 4) == test)
    if family == "B":
        return tuple((a, b, c) for a in range(3) for b in range(3)
                     for c in range(4) if (a == b) == test)
    raise ValueError("unknown family")


def _signs(rng: random.Random, n: int) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(rng.choice((-1, +1)) for _ in range(_DIM))
                 for _ in range(n))


def _parameters(world_seed: int, family: Family):
    rng = random.Random(seed_for(world_seed, family, "parameters"))
    if family == "A":
        return _signs(rng, 4), _signs(rng, 4)
    if family == "B":
        return _signs(rng, 3), _signs(rng, 3), _signs(rng, 4)
    raise ValueError("unknown family")


def _observation(family: Family, latent: tuple[int, ...],
                 parameters, rng: random.Random) -> tuple[float, ...]:
    if family == "A":
        z, c = latent
        p, q = parameters
        return tuple(min(1.0, max(0.0, 0.5 + 0.18*p[z][i]
                        + 0.08*q[c][i] + rng.uniform(-0.06, 0.06)))
                     for i in range(_DIM))
    a, b, c = latent
    u, v, w = parameters
    return tuple(min(1.0, max(0.0, 0.5 + 0.12*u[a][i]
                    + 0.12*v[b][i] + 0.07*w[c][i]
                    + rng.uniform(-0.06, 0.06)))
                 for i in range(_DIM))


def _phase_count(family: Family, phase: Phase) -> int:
    if phase == "unsupervised":
        return 1200
    if phase == "test":
        return 160 if family == "A" else 120
    if phase in ("feedback", "reversal", "feedback_b2"):
        if (phase == "reversal" and family != "A") or (
            phase == "feedback_b2" and family != "B"
        ):
            raise ValueError("phase not available for this family")
        return 64
    raise ValueError("unsupported phase")


def make_tape(family: Family, world_seed: int, phase: Phase,
              *, stage: int = 0,
              allow_confirmation: bool = False) -> tuple[EvaluatorCase, ...]:
    """Create a deterministic, balanced evaluator tape.

    Never call with 24000..24019 during software tests or hyperparameter
    selection. Confirmation requires the explicit allow_confirmation flag.
    """
    if world_seed in _HISTORIC_RESERVED:
        raise ValueError("historic NeuroLab confirmation seeds forbidden")
    if world_seed in _CONFIRMATION_RESERVED and not allow_confirmation:
        raise ValueError("NR01 confirmation seeds are locked")
    n = _phase_count(family, phase)
    allowed = legal_latents(family, test=(phase == "test"))
    rng_order = random.Random(seed_for(world_seed, family, phase, stage))
    tape = list(allowed) * (n // len(allowed))
    tape.extend(rng_order.sample(list(allowed), n % len(allowed)))
    rng_order.shuffle(tape)
    noise = random.Random(seed_for(world_seed, family, phase, stage+100000))
    params = _parameters(world_seed, family)
    return tuple(EvaluatorCase(_observation(family, x, params, noise), x)
                 for x in tape)


def target_for_evaluator(family: Family, latent: tuple[int, ...],
                         *, task: str) -> str:
    """Action label is restricted to evaluator after action has been chosen."""
    if family == "A":
        if len(latent) != 2 or task not in ("original", "reversed"):
            raise ValueError("invalid A task")
        z, _ = latent
        correct = z in (0, 1)
        if task == "reversed":
            correct = not correct
        return "D0" if correct else "D1"
    if family == "B":
        if len(latent) != 3 or task not in ("B1", "B2"):
            raise ValueError("invalid B task")
        a, b, _ = latent
        correct = (a == 0) if task == "B1" else (b == 2)
        return "D0" if correct else "D1"
    raise ValueError("unknown family")


def tape_digest(tape: tuple[EvaluatorCase, ...]) -> str:
    """Canonical JSON of evaluator records, for traceability only."""
    data = [{"latent": x.latent, "observation": x.observation} for x in tape]
    raw = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    return sha256(raw).hexdigest()


def counts(tape: tuple[EvaluatorCase, ...]) -> dict[tuple[int, ...], int]:
    """EVALUATOR-ONLY reporting; do not pass these counts to a model."""
    return dict(Counter(x.latent for x in tape))
