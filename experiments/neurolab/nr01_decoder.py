"""NR01.03-C common binary reward decoder. No evaluator or models imported."""
from __future__ import annotations
import json
import math

class RewardDecoder:
    def __init__(self, n_features: int, learning_rate: float = 0.25):
        if type(n_features) is not int or n_features < 1 or learning_rate != 0.25:
            raise ValueError("invalid frozen NR01 decoder configuration")
        self.n_features = n_features
        self.learning_rate = learning_rate
        self.weights = [0.0] * (n_features + 1)

    def _phi(self, features):
        if len(features) != self.n_features:
            raise ValueError("incorrect feature count")
        vals = tuple(float(v) for v in features)
        if not all(math.isfinite(v) for v in vals):
            raise ValueError("features must be finite")
        return vals + (1.0,)

    def score(self, features):
        return math.fsum(w*x for w,x in zip(self.weights,self._phi(features)))

    def choose(self, features):
        return "D1" if self.score(features) > 0 else "D0"

    def apply_reward(self, features, chosen_action, reward):
        if chosen_action not in ("D0","D1") or type(reward) is not int or reward not in (-1,1):
            raise ValueError("invalid reward/action")
        phi = self._phi(features)
        score = math.fsum(w*x for w,x in zip(self.weights,phi))
        if ("D1" if score > 0 else "D0") != chosen_action:
            raise ValueError("action inconsistent with decoder state")
        correct = chosen_action if reward == 1 else ("D0" if chosen_action == "D1" else "D1")
        y = 1.0 if correct == "D1" else 0.0
        p = 1.0/(1.0+math.exp(-max(-30.0,min(30.0,score))))
        self.weights = [w+0.25*(y-p)*x for w,x in zip(self.weights,phi)]

    def snapshot(self):
        return json.dumps({"schema":"nr01-decoder-v1","n_features":self.n_features,
                           "learning_rate":self.learning_rate,"weights":self.weights},
                          allow_nan=False,sort_keys=True,separators=(",",":")).encode()

    @classmethod
    def restore(cls, data):
        d=json.loads(data)
        if set(d)!={"schema","n_features","learning_rate","weights"} or d["schema"]!="nr01-decoder-v1":
            raise ValueError("invalid snapshot")
        obj=cls(d["n_features"],d["learning_rate"])
        if not isinstance(d["weights"],list) or len(d["weights"])!=len(obj.weights):
            raise ValueError("invalid weights")
        if any(type(w) not in (float,int) or not math.isfinite(w) for w in d["weights"]):
            raise ValueError("nonfinite weights")
        obj.weights=[float(w) for w in d["weights"]]
        return obj
