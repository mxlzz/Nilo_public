"""NR01.03-C2: adapters for existing libraries, no scientific data.

Canonical PRE-CODE contract:
docs/neurolab/NR01_03C_CONTRATO_DECODER_COSTOS_20261122.md

Only raw observations enter these classes. No evaluator, target or latent imports.
The library calls here must pass toy software tests before development cohorts.
"""
from __future__ import annotations

import pickle

from .nr01_knn import _vector


def _one_hot(category: int, width: int) -> tuple[float, ...]:
    if type(category) is not int or not 0 <= category < width:
        raise ValueError("category index out of range; no latent-based fallback")
    return tuple(1.0 if i == category else 0.0 for i in range(width))


class FuzzyART16:
    """ARTlib FuzzyART, complement-coded, max 16 categories; never truncate."""

    CAPACITY = 16

    def __init__(self, rho: float):
        if rho not in (.60, .80, .90):
            raise ValueError("rho must be preregistered")
        import numpy as np
        from artlib import FuzzyART
        self._np = np
        self.rho = float(rho)
        self.model = FuzzyART(rho=self.rho, alpha=.001, beta=1.0)
        self.model.set_data_bounds(np.zeros(16), np.ones(16))
        self.frozen = False
        self.observed = 0
        self.over_budget = False

    @property
    def categories(self) -> int:
        return len(self.model.W)

    def _prepared(self, x):
        raw = self._np.array([_vector(x)], dtype=float)
        prepared = self.model.prepare_data(raw)
        if prepared.shape != (1, 32):
            raise RuntimeError("ART complement-code contract violated")
        return prepared

    def observe_unlabelled(self, x: tuple[float, ...]) -> None:
        if self.frozen:
            raise RuntimeError("encoder frozen")
        self.model.partial_fit(self._prepared(x))
        self.observed += 1
        if self.categories > self.CAPACITY:
            self.over_budget = True

    def freeze_encoder(self) -> None:
        if self.observed < 1:
            raise RuntimeError("cannot freeze untrained ART encoder")
        self.frozen = True

    def encode_read_only(self, x: tuple[float, ...]):
        if not self.frozen:
            raise RuntimeError("encoder must be frozen before decoding")
        before = self.categories
        label = int(self.model.predict(self._prepared(x))[0])
        if self.categories != before:
            raise RuntimeError("ART prediction created a category")
        # This fixed width preserves the same 16-slot decoder budget.
        return _one_hot(label, self.CAPACITY)

    def snapshot(self) -> bytes:
        # Includes all library state, data bounds and learned category weights.
        return pickle.dumps((self.rho, self.model, self.frozen,
                             self.observed, self.over_budget), protocol=5)


class KMeansCategories:
    """scikit-learn MiniBatchKMeans, sequential blocks of 32, no extra shuffle."""

    BATCH = 32

    def __init__(self, k: int):
        if k not in (4, 8, 16):
            raise ValueError("K must be preregistered")
        import numpy as np
        from sklearn.cluster import MiniBatchKMeans
        self._np = np
        self.k = k
        self.model = MiniBatchKMeans(
            n_clusters=k, batch_size=self.BATCH, n_init=1,
            init="k-means++", random_state=42,
        )
        self.buffer: list[tuple[float, ...]] = []
        self.observed = 0
        self.frozen = False
        self.fitted = False
        self.over_budget = False

    @property
    def categories(self):
        return self.k if self.fitted else 0

    def _fit_buffer(self):
        if not self.buffer:
            return
        block = self._np.asarray(self.buffer, dtype=float)
        if not self.fitted and block.shape[0] < self.k:
            raise RuntimeError("not enough observations for initial KMeans fit")
        self.model.partial_fit(block)
        self.fitted = True
        self.buffer.clear()

    def observe_unlabelled(self, x: tuple[float, ...]) -> None:
        if self.frozen:
            raise RuntimeError("encoder frozen")
        self.buffer.append(_vector(x))
        self.observed += 1
        if len(self.buffer) == self.BATCH:
            self._fit_buffer()

    def freeze_encoder(self) -> None:
        if self.frozen:
            return
        self._fit_buffer()
        if not self.fitted:
            raise RuntimeError("cannot freeze untrained KMeans encoder")
        self.frozen = True

    def encode_read_only(self, x: tuple[float, ...]):
        if not self.frozen or self.buffer:
            raise RuntimeError("encoder must be fully frozen before decoding")
        label = int(self.model.predict(self._np.array([_vector(x)], dtype=float))[0])
        return _one_hot(label, self.k)

    def snapshot(self) -> bytes:
        # Snapshot of the full reconstructible training state, incl. pending buffer.
        return pickle.dumps((self.k, self.model, self.buffer, self.frozen,
                             self.fitted, self.observed), protocol=5)
