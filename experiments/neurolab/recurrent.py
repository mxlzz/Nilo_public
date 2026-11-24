"""E08: inspectable recurrent two-neuron dynamics with no external world.

Everything uses the already tested E01 kernel. Recurrence gives a
period-two oscillation, not spontaneous thought. Preregistered in
docs/neurolab/E08_PRE_REGISTRO.md.
"""
from __future__ import annotations

import json
import random
from .kernel import Brain, BrainState, NeuronSpec, NeuronState, SynapseSpec


def make_recurrent(*, weight: int | None) -> Brain:
    neurons = (NeuronSpec("A", decay=255), NeuronSpec("B", decay=255))
    synapses = () if weight is None else (
        SynapseSpec("A", "B", weight), SynapseSpec("B", "A", weight)
    )
    return Brain(neurons, synapses)


def trajectory(brain: Brain, a: int, b: int, ticks: int) -> tuple[tuple[int, int], ...]:
    if not isinstance(ticks, int) or ticks < 0:
        raise ValueError("ticks inválidos")
    state = brain.initial({"A": NeuronState(0, a), "B": NeuronState(0, b)})
    values = []
    for _ in range(ticks):
        state = brain.step(state)
        values.append((state.neurons["A"].output, state.neurons["B"].output))
    return tuple(values)


def run_all() -> dict:
    no_links = trajectory(make_recurrent(weight=None), 120, 0, 16)
    loop = trajectory(make_recurrent(weight=255), 120, 0, 16)
    damped = trajectory(make_recurrent(weight=200), 120, 0, 64)
    perturbed = trajectory(make_recurrent(weight=255), 120, 50, 16)
    random_traces = [
        trajectory(make_recurrent(weight=255), *(
            (lambda rng: (rng.randint(0,255), rng.randint(0,255)))(random.Random(seed))
        ), ticks=100) for seed in range(20)
    ]
    passed = (
        all(pair == (0, 0) for pair in no_links)
        and all(pair == ((0,120) if i % 2 == 0 else (120,0))
                for i,pair in enumerate(loop))
        and damped[-1] == (0,0)
        and all(pair == ((50,120) if i % 2 == 0 else (120,50))
                for i,pair in enumerate(perturbed))
        and all(0 <= v <= 255 for trace in random_traces for pair in trace for v in pair)
    )
    return {
        "protocol": "E08_PRE_REGISTRO v1",
        "passed": passed,
        "no_links": no_links,
        "period2": loop,
        "damped_last": damped[-1],
        "perturbed": perturbed,
        "random_seeds": 20,
        "interpretation": "only activity dynamics, not cognition",
    }


def main() -> None:
    result = run_all()
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["passed"]:
        raise SystemExit("E08 preregistered dynamics gate NOT met")


if __name__ == "__main__":
    main()
