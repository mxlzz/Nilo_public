"""Benchmark reproducible del núcleo E01, no capacidad cognitiva."""
from __future__ import annotations

import json
import platform
import time

from experiments.neurolab.kernel import Brain, NeuronSpec, SynapseSpec


def main():
    brain = Brain(
        [NeuronSpec("i", kind="input"), NeuronSpec("h", decay=128),
         NeuronSpec("o", decay=128)],
        [SynapseSpec("i", "h", 220), SynapseSpec("h", "o", 180)],
    )
    state = brain.initial()
    ticks = 100000
    started = time.perf_counter()
    for i in range(ticks):
        state = brain.step(state, {"i": (i * 73 + 19) % 256})
    seconds = time.perf_counter() - started
    print(json.dumps({
        "suite": "neurolab-e01-benchmark-v1", "ticks": ticks,
        "neurons": 3, "synapses": 2,
        "elapsed_s": round(seconds, 5),
        "ticks_per_s": round(ticks / seconds, 2),
        "python": platform.python_version(), "platform": platform.platform(),
        "checkpoint_sha256": brain.configuration_hash,
        "final_tick": state.tick, "final_state": {k: v.state for k, v in state.neurons.items()},
    }, sort_keys=True))


if __name__ == "__main__":
    main()
