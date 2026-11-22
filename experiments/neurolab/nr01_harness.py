"""NR01.03-D: evaluator-owned, information-fair software harness.

See docs/neurolab/NR01_02_PREREGISTRO_DESAFIO_20261122.md and
NR01_03C_CONTRATO_DECODER_COSTOS_20261122.md.
Only evaluator code imports target_for_evaluator; models see x, chosen action
and subsequent reward. This module never enables confirmation seeds.
"""
from __future__ import annotations

from hashlib import sha256
import json
import pickle
import random
import time

from .nr01_decoder import RewardDecoder
from .nr01_knn import CaseMemory16, _vector
from .nr01_worlds import make_tape, target_for_evaluator

CHECKPOINTS = (8, 16, 32, 64)


class Arm:
    """Decoder is shared algorithmically, not privileged by latent labels."""

    def __init__(self, kind: str, encoder=None):
        if kind not in ("raw", "knn", "art", "kmeans"):
            raise ValueError("unknown preregistered arm")
        if (kind in ("raw", "knn")) != (encoder is None):
            raise ValueError("encoder present only for clustering arms")
        self.kind = kind
        self.encoder = encoder
        self.memory = CaseMemory16() if kind == "knn" else None
        self.decoder = None if kind == "knn" else RewardDecoder(
            16 if kind in ("raw", "art") else encoder.k
        )
        self.frozen = False

    def observe_unlabelled(self, x: tuple[float, ...]) -> None:
        observed = _vector(x)
        if self.frozen:
            raise RuntimeError("acquisition already frozen")
        if self.encoder is not None:
            self.encoder.observe_unlabelled(observed)

    def freeze_encoder(self):
        if self.encoder is not None:
            self.encoder.freeze_encoder()
        self.frozen = True

    @property
    def over_budget(self) -> bool:
        return bool(self.encoder is not None and
                    getattr(self.encoder, "over_budget", False))

    def _features(self, x):
        observed = _vector(x)
        if self.encoder is None:
            return observed
        return self.encoder.encode_read_only(observed)

    def choose(self, x):
        if not self.frozen:
            raise RuntimeError("encoder must be frozen before decisions")
        return (self.memory.choose(x) if self.memory is not None
                else self.decoder.choose(self._features(x)))

    def apply_reward(self, x, action, reward):
        if not self.frozen:
            raise RuntimeError("feedback before acquisition")
        if self.memory is not None:
            self.memory.apply_reward(x, action, reward)
        else:
            self.decoder.apply_reward(self._features(x), action, reward)

    def for_new_task(self):
        if not self.frozen:
            raise RuntimeError("cannot reuse an unfrozen encoder")
        clone = Arm(self.kind, self.encoder)
        clone.frozen = True
        return clone

    def snapshot(self) -> bytes:
        return pickle.dumps((
            self.kind, self.frozen,
            self.encoder.snapshot() if self.encoder is not None else None,
            self.decoder.snapshot() if self.decoder is not None else None,
            self.memory.snapshot() if self.memory is not None else None,
        ), protocol=5)

    def state_size_bytes(self):
        return len(self.snapshot())


def _target(family, case, task):
    # This function lives in the evaluator, NEVER in an encoder or decoder.
    return target_for_evaluator(family, case.latent, task=task)


def _observations_digest(cases):
    payload = [list(case.observation) for case in cases]
    return sha256(json.dumps(payload, separators=(",", ":"),
                             allow_nan=False).encode()).hexdigest()


def evaluate_read_only(arm, cases, family, task):
    """A holdout read cannot modify any component of an arm."""
    before = arm.snapshot()
    correct = 0
    actions = []
    for case in cases:
        action = arm.choose(case.observation)  # ONLY observation reaches arm
        actions.append(action)
        if action == _target(family, case, task):
            correct += 1
    if before != arm.snapshot():
        raise AssertionError("evaluation changed encoder/decoder or case memory")
    return {"accuracy": correct / len(cases), "correct": correct,
            "count": len(cases), "actions": tuple(actions)}


def negative_test_permutation(actions, cases, family, task, world_seed):
    """Diagnostic only. Never trains or rewards a model."""
    original = [_target(family, c, task) for c in cases]
    task_code = {"original": 1, "reversed": 2, "B1": 3, "B2": 4}[task]
    family_code = {"A": 1, "B": 2}[family]
    shuffled = list(original)
    random.Random(world_seed * 1000003 + family_code * 10007
                  + task_code * 1009 + 701).shuffle(shuffled)
    return {"accuracy": sum(a == y for a, y in zip(actions, shuffled)) /
            len(shuffled), "original_D0_count": original.count("D0"),
            "permuted_D0_count": shuffled.count("D0")}


def feedback_phase(arm, feedback_cases, test_cases, family, task, world_seed):
    """Evaluates at 8/16/32/64 with no learning on tests or duplicate training."""
    if len(feedback_cases) != 64 or not test_cases:
        raise ValueError("expected 64 feedback events and non-empty holdout")
    result = {"feedback_observations_sha256":
              _observations_digest(feedback_cases),
              "test_observations_sha256": _observations_digest(test_cases),
              "checkpoints": {}}
    decision_cpu_ns = update_cpu_ns = holdout_cpu_ns = 0
    for i, case in enumerate(feedback_cases, 1):
        x = case.observation
        t0 = time.process_time_ns()
        chosen = arm.choose(x)
        decision_cpu_ns += time.process_time_ns() - t0
        # Reward only AFTER the model chose; no latent reaches the model.
        reward = 1 if chosen == _target(family, case, task) else -1
        t1 = time.process_time_ns()
        arm.apply_reward(x, chosen, reward)
        update_cpu_ns += time.process_time_ns() - t1
        if i in CHECKPOINTS:
            t2 = time.process_time_ns()
            evaluated = evaluate_read_only(arm, test_cases, family, task)
            holdout_cpu_ns += time.process_time_ns() - t2
            shuffled = negative_test_permutation(
                evaluated["actions"], test_cases, family, task, world_seed
            )
            result["checkpoints"][str(i)] = {
                "accuracy": evaluated["accuracy"],
                "count": evaluated["count"],
                "negative_accuracy": shuffled["accuracy"],
                "negative_D0_count": shuffled["permuted_D0_count"],
                "state_bytes": arm.state_size_bytes(),
                "decision_cpu_ns_cumulative": decision_cpu_ns,
                "feedback_update_cpu_ns_cumulative": update_cpu_ns,
                "holdout_cpu_ns_cumulative": holdout_cpu_ns,
            }
    return result


def run_world(family, world_seed, kind, parameter=None):
    """Development or toy worlds; confirmation and historical seeds locked."""
    if family not in ("A", "B"):
        raise ValueError("unknown family")
    if kind == "art":
        from .nr01_encoders import FuzzyART16
        encoder = FuzzyART16(parameter)
    elif kind == "kmeans":
        from .nr01_encoders import KMeansCategories
        encoder = KMeansCategories(parameter)
    else:
        if parameter is not None:
            raise ValueError("raw/knn have no hyperparameter")
        encoder = None

    arm = Arm(kind, encoder)
    unlabelled = make_tape(family, world_seed, "unsupervised")
    test = make_tape(family, world_seed, "test")
    start = time.process_time_ns()
    for case in unlabelled:
        arm.observe_unlabelled(case.observation)
    arm.freeze_encoder()
    acquisition_ns = time.process_time_ns() - start
    report = {"schema": "nr01-software-harness-v1",
              "family": family, "world_seed": world_seed,
              "kind": kind, "parameter": parameter,
              "unlabelled_sha256": _observations_digest(unlabelled),
              "test_sha256": _observations_digest(test),
              "acquisition_cpu_ns": acquisition_ns,
              "encoder_categories": getattr(encoder, "categories", None),
              "over_budget": arm.over_budget,
              "initial_state_bytes": arm.state_size_bytes()}
    if arm.over_budget:
        report["status"] = "over_budget"
        return report  # invalid candidate remains counted in denominator

    if family == "A":
        original = make_tape("A", world_seed, "feedback")
        reversed_ = make_tape("A", world_seed, "reversal")
        report["original"] = feedback_phase(arm, original, test, "A",
                                             "original", world_seed)
        # Important: SAME decoder and encoder, no reversal reset.
        report["reversed"] = feedback_phase(arm, reversed_, test, "A",
                                             "reversed", world_seed)
    else:
        b1 = make_tape("B", world_seed, "feedback")
        b2 = make_tape("B", world_seed, "feedback_b2")
        b2_arm = arm.for_new_task()  # NEW decoder, SAME frozen encoder
        report["B1"] = feedback_phase(arm, b1, test, "B", "B1", world_seed)
        report["B2"] = feedback_phase(b2_arm, b2, test, "B", "B2",
                                       world_seed)
    report["status"] = "software_executed_not_scientific_gate"
    return report
