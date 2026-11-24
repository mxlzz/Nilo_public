"""E09.02g.10a: INTERNAL two-byte delayed decision-source gate (lab only).

Pre-registration: docs/neurolab/E09_02G_10A_GATE_INTERNO_PRE_REGISTRO.md.
No external context-change flag or block position is passed into step_intrinsic.
NOT a genetic C1 rule; NOT autonomy, and not a general credit solution.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import statistics

from .c1_context_brain import C1ContextBrain, ContextBrainState, ContextTick
from .e09_context_protocol import (
    BLOCK_TICKS, TRAIN_BLOCKS, TEST_BLOCKS, ZERO, REWARD, PUNISHMENT,
    MAPPING_A, MAPPING_B, blocks, train_brain, evaluate_brain,
)
from .e09_paired_pulse_protocol import train_variant


def _source(values: tuple[int, int] | None) -> int | None:
    if values is None:
        return None
    active = [index for index, value in enumerate(values) if value > 0]
    return active[0] if len(active) == 1 else None


@dataclass(frozen=True)
class InternalCreditState:
    brain: ContextBrainState
    last_choice_concepts: tuple[int, int] | None = None

    def __post_init__(self):
        if not isinstance(self.brain, ContextBrainState):
            raise TypeError("typed C1ContextBrain state required")
        if self.last_choice_concepts is not None and (
            type(self.last_choice_concepts) is not tuple or
            len(self.last_choice_concepts) != 2 or
            any(type(v) is not int or not 0 <= v <= 255
                for v in self.last_choice_concepts)
        ):
            raise ValueError("last_choice_concepts must be two bytes or None")


@dataclass(frozen=True)
class InternalCreditTick:
    before: InternalCreditState
    after: InternalCreditState
    original_pulse: tuple[int, int, int, int]
    applied_pulse: tuple[int, int, int, int]
    suppressed: bool
    neural: ContextTick


def step_intrinsic(
    brain: C1ContextBrain, state: InternalCreditState,
    current_sensory: int, pending_chemistry: tuple[int, int, int, int],
) -> InternalCreditTick:
    """Operate exclusively on current neuronal state and internal history.

    No external block boundary, evaluation target, schedule or time position
    is received. The current sensory input is only passed to original C1 brain.
    """
    if not isinstance(brain, C1ContextBrain) or not isinstance(state, InternalCreditState):
        raise TypeError("brain and internal state required")
    # Only available previous-choice and currently exposed Concept states.
    prior_choice_source = _source(state.last_choice_concepts)
    source_at_plasticity = _source(state.brain.concept_outputs)
    suppressed = (
        pending_chemistry != ZERO
        and prior_choice_source is not None
        and source_at_plasticity is not None
        and prior_choice_source != source_at_plasticity
    )
    applied = ZERO if suppressed else pending_chemistry
    neural = brain.step(state.brain, current_sensory, applied, learn=True)
    subsequent = InternalCreditState(
        neural.after,
        neural.old_concepts if neural.action is not None else None,
    )
    return InternalCreditTick(state, subsequent, pending_chemistry,
                              applied, suppressed, neural)


def train_internal(
    brain: C1ContextBrain, state: InternalCreditState,
    pending: tuple[int, int, int, int],
    schedule: tuple[int, ...], mapping: tuple[str, str],
) -> tuple[InternalCreditState, tuple[int, int, int, int], int]:
    suppressed = 0
    for context in schedule:
        for _ in range(BLOCK_TICKS):
            result = step_intrinsic(brain, state, context, pending)
            suppressed += int(result.suppressed)
            action = result.neural.action
            if action is None:
                pending = ZERO
            else:
                pending = REWARD if action == mapping[context] else PUNISHMENT
            state = result.after
    return state, pending, suppressed


def run_seed(seed: int) -> dict:
    original_brain = C1ContextBrain(seed)
    external_brain = C1ContextBrain(seed)
    internal_brain = C1ContextBrain(seed)
    original_state = original_brain.initial()
    external_state = external_brain.initial()
    internal_state = InternalCreditState(internal_brain.initial())
    original_pulse = external_pulse = internal_pulse = ZERO
    last_context = None
    phases = {}
    for phase, train_salt, test_salt, mapping in (
        ("first", 10000, 30000, MAPPING_A),
        ("reversed", 20000, 40000, MAPPING_B),
    ):
        training = blocks(seed, train_salt, TRAIN_BLOCKS)
        testing = blocks(seed, test_salt, TEST_BLOCKS)
        original_state, original_pulse = train_brain(
            original_brain, original_state, original_pulse,
            training, mapping, learn=True,
        )
        external_state, external_pulse, last_context, ignored = train_variant(
            external_brain, external_state, external_pulse, last_context,
            training, mapping, mode="G",
        )
        internal_state, internal_pulse, filtered = train_internal(
            internal_brain, internal_state, internal_pulse, training, mapping,
        )
        if (internal_state.brain != external_state
            or internal_pulse != external_pulse
            or filtered != ignored["nonzero_omissions"]):
            raise AssertionError(f"seed={seed}, phase={phase}: intrinsic credit != external oracle")
        metrics = {
            "C": evaluate_brain(original_brain, original_state, testing, mapping),
            "G": evaluate_brain(external_brain, external_state, testing, mapping),
            "IG": evaluate_brain(internal_brain, internal_state.brain, testing, mapping),
        }
        if metrics["G"] != metrics["IG"]:
            raise AssertionError("holdout mismatch against external oracle")
        phases[phase] = {
            "metrics": metrics,
            "intrinsic_suppressed": filtered,
            "external_suppressed": ignored["nonzero_omissions"],
            "exact_brain_state_match": True,
            "exact_pending_chemistry_match": True,
        }
    return {"seed": seed, **phases}


def run_all() -> dict:
    seeds = tuple(range(100,120))
    rows = [run_seed(seed) for seed in seeds]
    joint = {
        mode: sum(row["first"]["metrics"][mode]["steady"] >= .90 and
                  row["reversed"]["metrics"][mode]["steady"] >= .90
                  for row in rows)
        for mode in ("C","G","IG")
    }
    mean = {
        phase: {
            mode: {
                kind: statistics.mean(row[phase]["metrics"][mode][kind] for row in rows)
                for kind in ("steady","early","overall")
            } for mode in ("C","G","IG")
        } for phase in ("first","reversed")
    }
    return {
        "protocol": "E09_02G_10A_GATE_INTERNO_PRE_REGISTRO-v1",
        "seeds": list(seeds), "n": len(seeds),
        "exact_parity_all_seeds": True,
        "logical_extra_state": "two 8-bit Concept outputs + initialization marker",
        "mean": mean, "joint_steady_ge_0_90": joint,
        "per_seed": rows,
        "limitations": "Equivalence only in two one-hot contexts, not historical C1 or general delayed credit",
    }


def main() -> None:
    print(json.dumps(run_all(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
