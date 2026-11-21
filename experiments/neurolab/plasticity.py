"""E03: modificación de pesos tras refuerzo, experimento NeuroLab propio.

NO reproduce las reglas C1 de STW/LTW/chemicals; esas fases siguen
pendientes de arqueología y experimentos E04/E05.

La elección sucede ANTES del feedback. El módulo no conoce etiquetas
correctas ni mapping de estímulos→respuestas; recibe solo reward (+1/-1)
que aporta un evaluador externo después de observar la elección.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from typing import Sequence

from .circuit import Choice, choose_action, make_six_neuron, run_episode
from .kernel import Brain, BrainState, SynapseSpec

EDGES = (("C0", "D0"), ("C0", "D1"), ("C1", "D0"), ("C1", "D1"))


@dataclass(frozen=True)
class PlasticState:
    weights: tuple[int, int, int, int]
    trials: int = 0

    def __post_init__(self) -> None:
        if len(self.weights) != 4 or any(
            isinstance(w, bool) or not isinstance(w, int) or not 0 <= w <= 255
            for w in self.weights
        ):
            raise ValueError("pesos sinápticos inválidos")
        if isinstance(self.trials, bool) or not isinstance(self.trials, int) or self.trials < 0:
            raise ValueError("conteo de ensayos inválido")


@dataclass(frozen=True)
class Trial:
    trial_number: int
    stimulus: tuple[int, int]
    action: str | None
    active_concepts: tuple[str, ...]
    scores: tuple[tuple[str, int], ...]
    weights_at_choice: tuple[int, int, int, int]
    brain_hash_at_choice: str


class PlasticLearner:
    def __init__(self, seed: int, *, rate: int = 16) -> None:
        if isinstance(rate, bool) or not isinstance(rate, int) or not 1 <= rate <= 255:
            raise ValueError("rate inválido")
        self.template = make_six_neuron(seed)
        self.seed = seed
        self.rate = rate
        initial = {(s.source, s.target): s.weight for s in self.template.synapses}
        self.initial_weights = tuple(initial[edge] for edge in EDGES)

    def initial(self) -> PlasticState:
        return PlasticState(self.initial_weights)

    def brain_for(self, state: PlasticState) -> Brain:
        new_weight_by_edge = dict(zip(EDGES, state.weights))
        synapses = tuple(
            SynapseSpec(s.source, s.target,
                        new_weight_by_edge.get((s.source, s.target), s.weight),
                        sign=s.sign)
            for s in self.template.synapses
        )
        return Brain(self.template.neurons, synapses)

    def respond(self, state: PlasticState, stimulus: tuple[int, int]) -> Trial:
        brain = self.brain_for(state)
        end, trace, _ = run_episode(brain, stimulus)
        choice = choose_action(end, tie_policy="first")
        active = tuple(name for name in ("C0", "C1") if trace[1].neurons[name].output > 0)
        return Trial(
            trial_number=state.trials, stimulus=stimulus, action=choice.action,
            active_concepts=active, scores=choice.scores,
            weights_at_choice=state.weights,
            brain_hash_at_choice=brain.configuration_hash
        )

    def update(
        self, state: PlasticState, trial: Trial, reward: int,
        *, learning: bool = True
    ) -> PlasticState:
        if isinstance(reward, bool) or reward not in (-1, 1):
            raise ValueError("refuerzo debe ser +1 o -1")
        if trial.trial_number != state.trials or trial.weights_at_choice != state.weights:
            raise ValueError("feedback obsoleto o dirigido a otros pesos")
        if self.brain_for(state).configuration_hash != trial.brain_hash_at_choice:
            raise ValueError("feedback de otra configuración")
        weights = list(state.weights)
        if learning and trial.action is not None:
            for i, (concept, decision) in enumerate(EDGES):
                if concept in trial.active_concepts and decision == trial.action:
                    weights[i] = min(255, max(0, weights[i] + self.rate * reward))
        return PlasticState(tuple(weights), trials=state.trials + 1)

    def checkpoint(self, state: PlasticState) -> str:
        return json.dumps({
            "version": 1, "seed": self.seed, "rate": self.rate,
            "template_hash": self.template.configuration_hash,
            "state": asdict(state),
        }, sort_keys=True, separators=(",", ":"))

    def restore(self, checkpoint: str) -> PlasticState:
        data = json.loads(checkpoint)
        if (
            data.get("version") != 1 or data.get("seed") != self.seed
            or data.get("rate") != self.rate
            or data.get("template_hash") != self.template.configuration_hash
        ):
            raise ValueError("checkpoint de plasticidad incompatible")
        data_state = data["state"]
        return PlasticState(tuple(data_state["weights"]), trials=data_state["trials"])
