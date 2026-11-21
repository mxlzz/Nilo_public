"""NeuroLab E01: núcleo neuronal experimental sin aprendizaje ni mundo.

ESTE MÓDULO NO ES UNA REPRODUCCIÓN DEL EJECUTABLE DE CREATURES 1.

Las convenciones exactas de actualización de C1 no están todas verificadas.
La función de salida históricamente disputada es seleccionable:
  * above_threshold: output = max(0, state - threshold)
  * full_state: output = state si state > threshold; 0 si no
Referencias: docs/neurolab/E00_INFORME_HISTORICO_01.md.

Las neuronas se evalúan contra un snapshot de las salidas anteriores
(actualización sincrónica), una decisión deliberada de NeuroLab. Los
estímulos externos son números enteros; no existe cuerpo, recompensa, LLM
ni modificación de pesos.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from typing import Literal, Mapping, Sequence

OutputMode = Literal["above_threshold", "full_state"]
NeuronKind = Literal["input", "compute"]
SynapseSign = Literal["exc", "inh"]


def _byte(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 255:
        raise ValueError(f"{name} debe ser entero entre 0 y 255: {value!r}")
    return value


def _clamp(value: int) -> int:
    return min(255, max(0, value))


@dataclass(frozen=True)
class NeuronSpec:
    id: str
    kind: NeuronKind = "compute"
    threshold: int = 0
    rest: int = 0
    decay: int = 0
    output_mode: OutputMode = "above_threshold"

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id:
            raise ValueError("id neuronal inválido")
        if self.kind not in ("input", "compute"):
            raise ValueError(f"kind inválido: {self.kind}")
        for name in ("threshold", "rest", "decay"):
            _byte(getattr(self, name), name)
        if self.output_mode not in ("above_threshold", "full_state"):
            raise ValueError(f"output_mode inválido: {self.output_mode}")


@dataclass(frozen=True)
class SynapseSpec:
    source: str
    target: str
    weight: int
    sign: SynapseSign = "exc"

    def __post_init__(self) -> None:
        if not isinstance(self.source, str) or not self.source:
            raise ValueError("origen sináptico inválido")
        if not isinstance(self.target, str) or not self.target:
            raise ValueError("destino sináptico inválido")
        _byte(self.weight, "weight")
        if self.sign not in ("exc", "inh"):
            raise ValueError(f"sign inválido: {self.sign}")


@dataclass(frozen=True)
class NeuronState:
    state: int = 0
    output: int = 0

    def __post_init__(self) -> None:
        _byte(self.state, "state")
        _byte(self.output, "output")


@dataclass(frozen=True)
class BrainState:
    tick: int
    neurons: dict[str, NeuronState] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.tick, bool) or not isinstance(self.tick, int) or self.tick < 0:
            raise ValueError("tick inválido")
        if not isinstance(self.neurons, dict) or any(
            not isinstance(k, str) or not isinstance(v, NeuronState)
            for k, v in self.neurons.items()
        ):
            raise ValueError("estado neuronal inválido")


def neuron_step(
    previous: NeuronState,
    spec: NeuronSpec,
    *,
    excitation: int = 0,
    inhibition: int = 0,
    stimulus: int = 0,
) -> NeuronState:
    """Transición pura sobre enteros, SIN representar una SVRule C1 general.

    Computación: pre=clamp(previous.state + excitation - inhibition).
    Entrada: pre=stimulus (no suma el estado anterior).
    Salida se calcula de pre, ANTES de relajar.
    Estado siguiente: rest + sign(pre-rest) * floor(abs(pre-rest)*(256-decay)/256).
    """
    for name, value in (("excitation", excitation), ("inhibition", inhibition), ("stimulus", stimulus)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} debe ser entero no negativo")
    pre = _byte(stimulus, "stimulus") if spec.kind == "input" else _clamp(
        previous.state + excitation - inhibition
    )
    if pre <= spec.threshold:
        out = 0
    elif spec.output_mode == "above_threshold":
        out = pre - spec.threshold
    else:
        out = pre
    delta = pre - spec.rest
    residual = (abs(delta) * (256 - spec.decay)) // 256
    next_state = spec.rest + (residual if delta >= 0 else -residual)
    return NeuronState(state=_clamp(next_state), output=out)


class Brain:
    """Red determinista de conexiones fijas. No aprende en E01."""

    def __init__(
        self,
        neurons: Sequence[NeuronSpec],
        synapses: Sequence[SynapseSpec] = (),
    ) -> None:
        self.neurons = tuple(neurons)
        self.synapses = tuple(synapses)
        ids = [n.id for n in self.neurons]
        if len(ids) != len(set(ids)) or not ids:
            raise ValueError("se requieren neuronas con IDs únicos")
        self._specs = {n.id: n for n in self.neurons}
        self._incoming: dict[str, list[SynapseSpec]] = {n.id: [] for n in self.neurons}
        for syn in self.synapses:
            if syn.source not in self._specs or syn.target not in self._specs:
                raise ValueError("sinapsis hacia neurona inexistente")
            if self._specs[syn.target].kind == "input":
                raise ValueError("una neurona de entrada no recibe sinapsis")
            self._incoming[syn.target].append(syn)
        payload = {
            "neurons": [asdict(n) for n in self.neurons],
            "synapses": [asdict(s) for s in self.synapses],
            "model": "neurolab-e01-v1"
        }
        self.configuration_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    def initial(self, states: Mapping[str, NeuronState] | None = None) -> BrainState:
        initial_states = dict(states or {})
        if set(initial_states) - self._specs.keys():
            raise ValueError("se especificó estado de neurona inexistente")
        return BrainState(
            tick=0,
            neurons={n.id: initial_states.get(n.id, NeuronState()) for n in self.neurons}
        )

    def _check(self, previous: BrainState) -> None:
        if set(previous.neurons) != set(self._specs):
            raise ValueError("el estado no corresponde a esta topología")

    def step(
        self, previous: BrainState, stimuli: Mapping[str, int] | None = None
    ) -> BrainState:
        self._check(previous)
        inputs = dict(stimuli or {})
        for key, value in inputs.items():
            if key not in self._specs or self._specs[key].kind != "input":
                raise ValueError(f"estímulo dirigido a neurona no-input: {key}")
            _byte(value, "estímulo")
        next_neurons: dict[str, NeuronState] = {}
        for spec in self.neurons:
            excitation = 0
            inhibition = 0
            for syn in self._incoming[spec.id]:
                old_signal = previous.neurons[syn.source].output
                value = (old_signal * syn.weight) // 255
                if syn.sign == "exc":
                    excitation += value
                else:
                    inhibition += value
            next_neurons[spec.id] = neuron_step(
                previous.neurons[spec.id], spec,
                excitation=excitation, inhibition=inhibition,
                stimulus=inputs.get(spec.id, 0),
            )
        return BrainState(tick=previous.tick + 1, neurons=next_neurons)

    def checkpoint(self, state: BrainState) -> str:
        self._check(state)
        return json.dumps(
            {"version": 1, "configuration_hash": self.configuration_hash,
             "tick": state.tick,
             "neurons": {nid: asdict(v) for nid, v in state.neurons.items()}},
            sort_keys=True, separators=(",", ":"),
        )

    def restore(self, text: str) -> BrainState:
        data = json.loads(text)
        if data.get("version") != 1 or data.get("configuration_hash") != self.configuration_hash:
            raise ValueError("checkpoint incompatible con el motor o su topología")
        if set(data.get("neurons", {})) != set(self._specs):
            raise ValueError("checkpoint de neuronas incompatible")
        return BrainState(
            tick=data["tick"],
            neurons={nid: NeuronState(**item) for nid, item in data["neurons"].items()}
        )
