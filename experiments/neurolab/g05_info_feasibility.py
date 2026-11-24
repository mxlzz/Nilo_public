"""NeuroLab G05-INFO.03: synthetic integrity witnesses (not scientific worlds)."""
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
from itertools import product
import hashlib
import json
import random

DELAYS = (2, 4, 7)
TOY_SEEDS = (0, 1, 42)
N_TICKS = 20_000


@dataclass(frozen=True)
class Event:
    source: int
    due: int
    sign: int
    priority: float


def resolve_due(due: list[Event]) -> tuple[Event | None, int]:
    if not due:
        return None, 0
    # Priority comes from a policy-independent random stream.
    selected = min(due, key=lambda ev: (ev.priority, ev.source))
    return selected, len(due) - 1


def legacy_witnesses() -> int:
    count = 0
    for targets in product((0, 1), repeat=3):
        for delays in product((1, 2, 3), repeat=3):
            observed = []
            expected = []
            for i, (source, delay) in enumerate(zip(targets, delays)):
                for j in range(4):
                    action = (i + j + source + delay) % 2
                    observed.append((source, action, False))
                    if j == 3:
                        expected.append((source, action))
                for j in range(delay + 1):
                    action = (i + j + 1 + source) % 2
                    observed.append((1 - source, action, j == delay))
            previous = last_switch = None
            index = 0
            for context, action, pulse in observed:
                if previous is not None and context != previous[0]:
                    last_switch = previous
                if pulse:
                    assert last_switch == expected[index]
                    index += 1
                    count += 1
                previous = (context, action)
            assert index == 3
    assert count == 648
    return count


def ambiguity_witness() -> bool:
    contexts = (0, 0, 0, 0, 0)
    actions = (0, 0, 0, 0, 0)
    # Hidden event source at tick 0 or tick 2; both arrive at 4.
    h4 = [Event(0, 4, +1, .5)]
    h2 = [Event(2, 4, +1, .5)]
    def visible(events):
        return tuple((contexts[t], actions[t],
                      resolve_due([ev for ev in events if ev.due == t])[0].sign
                      if any(ev.due == t for ev in events) else 0)
                     for t in range(5))
    assert visible(h4) == visible(h2)
    assert h4[0].source != h2[0].source
    return True


def toy_stream(seed: int, n: int = N_TICKS, *, action_mode: str = "random") -> dict:
    if action_mode not in ("random", "flip", "none_every_five"):
        raise ValueError("invalid action mode")
    rng_context = random.Random(seed + 11)
    rng_action = random.Random(seed + 23)
    rng_event = random.Random(seed + 37)
    rng_lag = random.Random(seed + 47)
    rng_priority = random.Random(seed + 59)
    x = []
    acts = []
    z = []
    schedule = defaultdict(list)
    opportunity_trace = []
    context = rng_context.randrange(2)
    for t in range(n):
        if t and rng_context.random() < .10:
            context = 1 - context
        raw_action = rng_action.randrange(2)
        action = (1 - raw_action if action_mode == "flip" else
                  None if action_mode == "none_every_five" and t % 5 == 0
                  else raw_action)
        opportunity = rng_event.random() < .20
        lag = rng_lag.choice(DELAYS)
        priority = rng_priority.random()
        quality = (0 if action is None else +1 if action == context else -1)
        opportunity_trace.append((t, opportunity, lag, priority))
        x.append(context)
        acts.append(action)
        z.append(quality)
        if opportunity and action is not None:
            schedule[t + lag].append(Event(t, t + lag, quality, priority))
    rewards = [0] * (n + max(DELAYS) + 1)
    sources = []
    dropped = 0
    colliding_ticks = 0
    for t in range(len(rewards)):
        due = schedule[t]
        selected, rejected = resolve_due(due)
        if len(due) > 1:
            colliding_ticks += 1
        dropped += rejected
        if selected:
            rewards[t] = selected.sign
            sources.append((selected.source, t, selected.sign))
    created = sum(len(v) for v in schedule.values())
    assert created == len(sources) + dropped
    assert all(due - source in DELAYS and due > source for source, due, _ in sources)
    assert all(v in (-1, 0, +1) for v in rewards)
    digest = hashlib.sha256(json.dumps({"contexts": x, "actions": acts,
                 "rewards": rewards, "sources": sources}, separators=(',', ':')).encode()).hexdigest()
    def corr(values, lag):
        return sum(values[t] * z[t - lag] for t in range(8, n)) / (n - 8)
    correlations = {str(k): corr(rewards, k) for k in range(1, 9)}
    if action_mode == "random" and n == N_TICKS:
        for lag in DELAYS:
            assert correlations[str(lag)] > .025, (seed, lag, correlations)
        for lag in (1, 3, 5, 6, 8):
            assert abs(correlations[str(lag)]) < .025, (seed, lag, correlations)
    rng_perm = random.Random(seed + 71)
    occupied = [t for t in range(n) if rewards[t]]
    shuffled = [rewards[t] for t in occupied]
    rng_perm.shuffle(shuffled)
    scrambled = rewards.copy()
    for t, s in zip(occupied, shuffled):
        scrambled[t] = s
    permuted_correlations = {str(k): corr(scrambled, k) for k in DELAYS}
    return {
        'seed': seed, 'ticks': n, 'created': created,
        'delivered': len(sources), 'dropped_collision': dropped,
        'colliding_ticks': colliding_ticks, 'correlations': correlations,
        'permuted_correlations': permuted_correlations, 'stream_sha256': digest,
        'opportunity_sha256': hashlib.sha256(json.dumps(opportunity_trace).encode()).hexdigest(),
        'action_mode': action_mode,
    }


def main() -> None:
    assert legacy_witnesses() == 648
    assert ambiguity_witness()
    winner, rejected = resolve_due([
        Event(2, 5, +1, .7), Event(3, 5, -1, .1), Event(1, 5, +1, .6)
    ])
    assert (winner.source, winner.sign, rejected) == (3, -1, 2)
    rows = [toy_stream(seed) for seed in TOY_SEEDS]
    assert rows == [toy_stream(seed) for seed in TOY_SEEDS]
    assert len({r['stream_sha256'] for r in rows}) == len(rows)
    original = toy_stream(0, 100)
    inverted = toy_stream(0, 100, action_mode="flip")
    missing = toy_stream(0, 100, action_mode="none_every_five")
    assert original['opportunity_sha256'] == inverted['opportunity_sha256']
    assert original['opportunity_sha256'] == missing['opportunity_sha256']
    assert original['created'] == inverted['created']
    assert missing['created'] < original['created']
    assert original['stream_sha256'] != inverted['stream_sha256']
    print(json.dumps({'protocol': 'G05-INFO.03/toy-v1',
                      'legacy_pulses_verified': 648,
                      'ambiguous_hidden_histories_verified': True,
                      'collision_priority_verified': True,
                      'exogenous_schedule_independent_of_actions': True,
                      'rows': rows}, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
