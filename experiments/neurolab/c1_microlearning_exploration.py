"""E09.02d: forced epsilon exploration over E09.02c unchanged plasticity.

Hypothesis: a greedy preference can become absorbing after weight saturation.
This variant changes ONLY the action-selection policy; reward/weights remain
exactly as in MiniLearner. Source: E09_02D_EXPLORACION_PRE_REGISTRO.md.
"""
from __future__ import annotations

import random

from .c1_microlearning import MiniLearner, MiniState, MiniTrial


class EpsilonLearner(MiniLearner):
    EPSILON = 0.10

    def respond(self, state: MiniState,
                stimulus: tuple[int, int] = (255, 255)) -> MiniTrial:
        baseline = super().respond(state, stimulus)
        rng = random.Random(self.seed * 1_000_000 + state.trials)
        force_explore = rng.random() < self.EPSILON
        if force_explore:
            chosen = rng.choice(("D0", "D1"))
        elif baseline.trace.action is None:
            # Preserve baseline tie policy unless exploration was triggered.
            chosen = baseline.chosen
        else:
            chosen = baseline.trace.action
        return MiniTrial(
            number=baseline.number,
            weights_at_choice=baseline.weights_at_choice,
            trace=baseline.trace,
            chosen=chosen,
        )
