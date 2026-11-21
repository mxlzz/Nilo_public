"""E07 preregistered capacity-limited rewiring vs fixed and LRU."""
from __future__ import annotations
import json
import statistics

from .rewiring import WiringModel, WiringState

OLD = ((0, 2), (1, 3))
NEW = ((0, 3), (1, 2))
TARGET = {(0, 2): "D0", (1, 3): "D1", (0, 3): "D1", (1, 2): "D0"}


def training_order(seed: int, pair: tuple[tuple[int,int],tuple[int,int]],
                   repetitions: int) -> tuple[tuple[int,int], ...]:
    """Intercalación estricta; fase I y II con orientación dependiente de seed."""
    a,b = pair if seed % 2 == 0 else tuple(reversed(pair))
    return tuple(x for _ in range(repetitions) for x in (a,b))


def train(model: WiringModel, state: WiringState,
          events: tuple[tuple[int,int], ...]) -> WiringState:
    for pattern in events:
        prepared, choice = model.choose(state, pattern, structural=True)
        reward = 1 if choice.action == TARGET[pattern] else -1
        state = model.update(prepared, choice, pattern, reward, learning=True)
    return state


def accuracy(model: WiringModel, state: WiringState,
             patterns: tuple[tuple[int,int], ...]) -> float:
    correct = 0
    for pattern in patterns:
        before, choice = model.choose(state, pattern, structural=False)
        if choice.action == TARGET[pattern]:
            correct += 1
        if before != state:
            raise RuntimeError("evaluación modificó memoria estructural")
    return correct / len(patterns)


def run_seed(seed: int) -> dict:
    old = training_order(seed, OLD, 30)
    new = training_order(seed, NEW, 30)
    old_holdout = training_order(seed+100, OLD, 40)
    new_holdout = training_order(seed+101, NEW, 40)
    result: dict[str, object] = {"seed": seed}
    for mode in ("fixed", "migratory", "lru"):
        model = WiringModel(seed, mode)
        state = model.initial()
        state = train(model, state, old)
        old_before = accuracy(model, state, old_holdout)
        state = train(model, state, new)
        result[mode] = {
            "old_before": old_before,
            "old_after": accuracy(model, state, old_holdout),
            "new_after": accuracy(model, state, new_holdout),
            "slots": [list(s.pattern) if s.pattern is not None else None for s in state.slots],
            "strength": [s.strength for s in state.slots],
            "capacity": len(state.slots),
        }
    return result


def run_all() -> dict:
    all_seeds = [run_seed(s) for s in range(20)]
    good = sum(r["migratory"]["new_after"] >= .90 for r in all_seeds)
    delta_fixed = statistics.mean(r["migratory"]["new_after"] - r["fixed"]["new_after"]
                                  for r in all_seeds)
    old_loss = statistics.mean(r["migratory"]["old_before"] - r["migratory"]["old_after"]
                               for r in all_seeds)
    return {
        "protocol": "E07_PRE_REGISTRO v1",
        "n_seeds": len(all_seeds),
        "new_90_percent_seeds": good,
        "migration_vs_fixed_new": delta_fixed,
        "migration_old_loss": old_loss,
        "avg_lru_new": statistics.mean(r["lru"]["new_after"] for r in all_seeds),
        "avg_migration_new": statistics.mean(r["migratory"]["new_after"] for r in all_seeds),
        "avg_fixed_new": statistics.mean(r["fixed"]["new_after"] for r in all_seeds),
        "passed": good >= 18 and delta_fixed >= .30,
        "per_seed": all_seeds,
        "scope": "two concept slots; migration trades forgetting for new learning; LRU control",
    }


def main() -> None:
    result = run_all()
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["passed"]:
        raise SystemExit("E07 preregistered capacity test NOT met")


if __name__ == "__main__":
    main()
