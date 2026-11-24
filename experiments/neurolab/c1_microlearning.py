"""E09.02c: aprendizaje inmediato en microcircuito C1 de cinco unidades.

Neuronas: ANDTYPE0 (Concept) y STATE + TYPE0 - TYPE1 (Decision)
extraídas del genoma. Plasticidad y exploración son convenciones NUEVAS:
reward positivo fortalece TYPE0 elegido, negativo fortalece TYPE1 elegido.
El agente jamás recibe el nombre de la acción correcta.
"""
from __future__ import annotations
from dataclasses import dataclass
import json
import random

from .c1_microcircuit import MicroWeights,MicroTrace,run_once


@dataclass(frozen=True)
class MiniState:
    weights: tuple[int,int,int,int]=(0,0,0,0)  # D0-exc,D0-inh,D1-exc,D1-inh
    trials: int=0

    def __post_init__(self):
        if len(self.weights)!=4 or any(type(w) is not int or not 0<=w<=255
                                       for w in self.weights):
            raise ValueError("Cuatro pesos byte requeridos")
        if type(self.trials) is not int or self.trials<0:
            raise ValueError("trials inválido")


@dataclass(frozen=True)
class MiniTrial:
    number: int
    weights_at_choice: tuple[int,int,int,int]
    trace: MicroTrace
    chosen: str


class MiniLearner:
    def __init__(self, seed:int, rate:int=16):
        if type(seed) is not int or type(rate) is not int or not 1<=rate<=255:
            raise ValueError("seed/rate inválido")
        self.seed=seed
        self.rate=rate

    def initial(self)->MiniState:
        return MiniState()

    def respond(self,state:MiniState,stimulus:tuple[int,int]=(255,255))->MiniTrial:
        w=state.weights
        trace=run_once(*stimulus,weights=MicroWeights(
            d0_exc=w[0],d0_inh=w[1],d1_exc=w[2],d1_inh=w[3]
        ))
        choice=trace.action
        if choice is None:
            choice=random.Random(self.seed*1000000+state.trials).choice(("D0","D1"))
        return MiniTrial(state.trials,w,trace,choice)

    def feedback(self,state:MiniState,trial:MiniTrial,reward:int,
                 *,learn:bool=True)->MiniState:
        if type(reward) is not int or reward not in (-1,+1):
            raise ValueError("feedback debe ser -1 o +1")
        if trial.number!=state.trials or trial.weights_at_choice!=state.weights:
            raise ValueError("feedback obsoleto")
        weights=list(state.weights)
        if learn and trial.trace.concept>0:
            i=0 if trial.chosen=="D0" else 2
            j=i if reward>0 else i+1
            weights[j]=min(255,weights[j]+self.rate)
        return MiniState(tuple(weights),state.trials+1)

    def checkpoint(self,state:MiniState)->str:
        return json.dumps({"protocol":"E09.02c-v1","seed":self.seed,
                           "rate":self.rate,"weights":list(state.weights),
                           "trials":state.trials},sort_keys=True)

    def restore(self,saved:str)->MiniState:
        data=json.loads(saved)
        if (data.get("protocol")!="E09.02c-v1" or data.get("seed")!=self.seed
                or data.get("rate")!=self.rate):
            raise ValueError("checkpoint de otro experimento")
        return MiniState(tuple(data["weights"]),data["trials"])
