"""G05-NX01 preregistered baseline-only saturation gate; no C1 model execution.
See docs/neurolab/G05_NX01_PREREGISTRO_20261122.md.
"""
from __future__ import annotations
from collections import defaultdict, deque
from dataclasses import dataclass
import hashlib
import json
import random
import statistics
import argparse
import copy
TRAIN=2400
DRAIN=7
TEST=600
DELAYS=(2,4,7)
@dataclass(frozen=True)
class Tape:
    contexts: tuple[int, ...]
    opportunities: tuple[bool, ...]
    delays: tuple[int, ...]
    priorities: tuple[float, ...]
    sham_signs: tuple[int, ...]
    holdout: tuple[int, ...]
    digest: str

def build_tape(seed: int, phase: int) -> Tape:
    base = seed * 1000 + phase * 100_000_000
    cx = random.Random(base + 11)
    op = random.Random(base + 37)
    lag = random.Random(base + 47)
    pri = random.Random(base + 59)
    sham = random.Random(base + 71)
    hx = random.Random(base + 83)

    def contexts(rng, count):
        x = rng.randrange(2)
        out = []
        for t in range(count):
            if t and rng.random() < .1:
                x = 1 - x
            out.append(x)
        return tuple(out)

    xs = contexts(cx, TRAIN + DRAIN)
    hs = contexts(hx, TEST)
    opportunities = tuple(op.random() < .2 for _ in range(TRAIN))
    delays = tuple(lag.choice(DELAYS) for _ in range(TRAIN))
    priorities = tuple(pri.random() for _ in range(TRAIN))
    sham_signs = tuple(1 if sham.randrange(2) else -1 for _ in range(TRAIN))
    payload = (xs, opportunities, delays, priorities, sham_signs, hs)
    digest = hashlib.sha256(repr(payload).encode("utf-8")).hexdigest()
    return Tape(xs, opportunities, delays, priorities, sham_signs, hs, digest)

@dataclass(frozen=True)
class Outcome:
    source: int
    due: int
    sign: int
    priority: float
    context: int
    action: int

class Table:
    def __init__(self, mode: str, seed: int):
        if mode not in ("T0", "TL", "TK"):
            raise ValueError(mode)
        self.mode = mode
        self.rng = random.Random(seed * 100 + {"T0": 17, "TL": 19, "TK": 23}[mode])
        self.q = [[0.0, 0.0], [0.0, 0.0]]
        self.trace = [0.0] * 4
        self.history = deque(maxlen=7)

    def step(self, context: int, pulse: int, *, learn: bool) -> int:
        qa, qb = self.q[context]
        if learn and self.rng.random() < .10:
            action = self.rng.randrange(2)
        elif qa == qb:
            action = self.rng.randrange(2) if learn else 0
        else:
            action = int(qb > qa)
        if learn and pulse:
            if self.mode == "T0":
                weights = [(context, action, 1.0)]
            elif self.mode == "TL":
                norm = sum(self.trace)
                weights = [(s, a, self.trace[s*2+a]/norm)
                           for s in (0, 1) for a in (0, 1)] if norm else []
            else:
                weights = []
                for k in DELAYS:
                    if len(self.history) >= k:
                        s, a = self.history[-k]
                        weights.append((s, a, 1/3))
            for s, a, weight in weights:
                self.q[s][a] = max(-1.0, min(1.0, self.q[s][a] + .10 * pulse * weight))
        if self.mode == "TL":
            self.trace = [e * .75 for e in self.trace]
            self.trace[context*2+action] += 1.0
        if self.mode == "TK":
            self.history.append((context, action))
        return action

    def state_bytes(self) -> int:
        return len(json.dumps({"q": self.q, "trace": self.trace,
                               "history": list(self.history)}, sort_keys=True).encode())

def correct(context: int, action: int | None, phase: int) -> bool:
    return action is not None and action == (context ^ phase)

def stable(contexts: tuple[int, ...], t: int) -> bool:
    return t >= 2 and contexts[t] == contexts[t-1] == contexts[t-2]

def train_phase(agent, tape: Tape, phase: int, mode: str) -> dict:
    queue = defaultdict(list)
    n_delivered = n_dropped = n_created = n_none = n_collision_ticks = 0
    scores = [[], [], [], []]
    events = []
    for t, ctx in enumerate(tape.contexts):
        due = queue[t]
        chosen = min(due, key=lambda ev: (ev.priority, ev.source)) if due else None
        if len(due) > 1:
            n_collision_ticks += 1
        n_dropped += max(0, len(due) - 1)
        pulse = chosen.sign if chosen else 0
        if chosen:
            n_delivered += 1
            events.append((chosen.source, t, chosen.context, chosen.action,
                           chosen.sign, len(due), ctx))
        action = agent.step(ctx, pulse, learn=True)
        if action is None:
            n_none += 1
        if t < TRAIN:
            if stable(tape.contexts, t):
                scores[t//600].append(int(correct(ctx, action, phase)))
            if tape.opportunities[t] and action is not None:
                sign = tape.sham_signs[t] if mode == "P" else (1 if correct(ctx, action, phase) else -1)
                lag = tape.delays[t]
                due_tick = t + lag
                queue[due_tick].append(Outcome(t, due_tick, sign,
                           tape.priorities[t], ctx, action))
                n_created += 1
    assert n_created == n_delivered + n_dropped, (n_created, n_delivered, n_dropped)
    return {"created": n_created, "delivered": n_delivered, "dropped": n_dropped,
            "collision_ticks": n_collision_ticks, "none": n_none,
            "train_stable_quarters": [sum(s)/len(s) if s else None for s in scores],
            "events": events}

def evaluate(agent, tape: Tape, phase: int, *, learn: bool) -> dict:
    # Evaluation runs on a clone: the training state and RNG remain intact.
    agent = copy.deepcopy(agent)
    correct_all = correct_stable = stable_count = none = 0
    by_age = {"switch": [0, 0], "one_after": [0, 0], "stable": [0, 0]}
    age = 0
    for t, ctx in enumerate(tape.holdout):
        age = 0 if t == 0 or ctx != tape.holdout[t-1] else age + 1
        a = agent.step(ctx, 0, learn=learn)
        hit = int(correct(ctx, a, phase))
        correct_all += hit
        none += int(a is None)
        if stable(tape.holdout, t):
            stable_count += 1
            correct_stable += hit
        key = "switch" if age == 0 else "one_after" if age == 1 else "stable"
        by_age[key][0] += hit
        by_age[key][1] += 1
    return {"all": correct_all / TEST,
            "stable": correct_stable / stable_count if stable_count else None,
            "stable_ticks": stable_count, "none": none,
            "by_age": {k: (v[0]/v[1] if v[1] else None) for k,v in by_age.items()}}

def run_development_baselines() -> dict:
    rows = []
    for seed in range(25000, 25020):
        outputs = {}
        checksums = []
        for mode in ("T0", "TL", "TK"):
            agent = Table(mode, seed)
            measurements = []
            for phase in (0, 1):
                tape = build_tape(seed, phase)
                if mode == "T0":
                    checksums.append(tape.digest)
                meta = train_phase(agent, tape, phase, mode)
                holdout = evaluate(agent, tape, phase, learn=False)
                measurements.append({"stable": holdout["stable"], "all": holdout["all"],
                                     "created": meta["created"], "delivered": meta["delivered"],
                                     "dropped": meta["dropped"], "state_bytes": agent.state_bytes()})
            outputs[mode] = measurements
        rows.append({"seed": seed, "tape_sha256": checksums, "models": outputs})
    means = {}
    for mode in ("T0", "TL", "TK"):
        score = [sum(row["models"][mode][p]["stable"] for p in (0,1))/2 for row in rows]
        means[mode] = {"mean_composite": statistics.mean(score), "minimum_world": min(score),
                       "both_phases_perfect": sum(v == 1.0 for v in score)}
    assert means["TK"]["mean_composite"] == 1.0
    assert means["TK"]["both_phases_perfect"] == 20
    return {"protocol": "G05-NX01/dev-baselines-v1", "development_only": True,
            "confirmatory_seeds_untouched": [26000, 26019], "rows": rows, "summary": means,
            "stop": "best control TK=1.0 across all 20 worlds; neural +0.05 unattainable"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run_development_baselines()
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps({"summary": result["summary"], "n_worlds": len(result["rows"]),
                      "stop": result["stop"]}, sort_keys=True))

if __name__ == "__main__":
    main()
