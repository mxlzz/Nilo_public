"""E09.02f.6: C1 State Value Rule interpreter with frozen value snapshot.

Derived from user's C1 Creatures.exe PE32 x86 (SHA256:
548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7)
and gene opcode indexes. Interpreter behavior:
- 0 terminates
- 1..21 load named table value
- 22 TRUE aborts with zero unless accumulator nonzero
- 23/24/25 consume next operand ID (PLUS/MINUS/TIMES)
- 26/27 increment/decrement saturating

Safety divergences: malformed/unterminated rules raise explicitly instead of
emulating potential out-of-bounds reads in the original executable.

One dendrite's C1SVTable is captured BEFORE any change in SUSCEPT/STW/LTW
or strength during that tick. Do not mutate or silently refresh the table.
"""
from __future__ import annotations

from dataclasses import dataclass

from .c1_runtime_math import plus, minus, times, incr, decr


@dataclass(frozen=True)
class C1SVTable:
    chem0: int = 0
    chem1: int = 0
    chem2: int = 0
    chem3: int = 0
    state: int = 0
    output: int = 0
    threshold: int = 0
    type0: int = 0
    type1: int = 0
    and_type0: int = 0
    and_type1: int = 0
    input: int = 0
    conduct: int = 0
    susceptibility: int = 0
    stw: int = 0
    ltw: int = 0
    strength: int = 0

    def __post_init__(self):
        for field in self.__dataclass_fields__:
            value=getattr(self,field)
            if type(value) is not int or not 0 <= value <= 255:
                raise ValueError(f"{field}: byte 0..255 esperado")

    def values(self) -> tuple[int,...]:
        return (
            0, 0, 1, 64, 255,
            self.chem0, self.chem1, self.chem2, self.chem3,
            self.state, self.output, self.threshold, self.type0,
            self.type1, self.and_type0, self.and_type1,
            self.input, self.conduct, self.susceptibility,
            self.stw, self.ltw, self.strength,
        )


@dataclass(frozen=True)
class SVStep:
    index: int
    opcode: int
    result: int


@dataclass(frozen=True)
class SVResult:
    result: int
    gated: bool
    trace: tuple[SVStep,...]


def evaluate_trace(rule: bytes, table: C1SVTable) -> SVResult:
    if not isinstance(rule, bytes) or len(rule) != 8:
        raise ValueError("C1 SVRule debe ocupar ocho bytes")
    if not isinstance(table, C1SVTable):
        raise TypeError("tabla SVRule C1 requerida")

    values=table.values()
    acc=0
    trace=[]
    pc=0
    while pc < len(rule):
        op=rule[pc]
        if op == 0:
            return SVResult(acc, False, tuple(trace))
        position=pc
        pc+=1
        if 1 <= op <= 21:
            acc=values[op]
        elif op == 22:
            if acc == 0:
                trace.append(SVStep(position,op,0))
                return SVResult(0,True,tuple(trace))
        elif op in (23,24,25):
            if pc >= len(rule) or not 1 <= rule[pc] <= 21:
                raise ValueError("falta operando válido para PLUS/MINUS/TIMES")
            operand=values[rule[pc]]
            pc+=1
            acc=plus(acc,operand) if op==23 else (
                minus(acc,operand) if op==24 else times(acc,operand))
        elif op == 26:
            acc=incr(acc)
        elif op == 27:
            acc=decr(acc)
        else:
            raise ValueError(f"opcode C1 no soportado: {op}")
        trace.append(SVStep(position,op,acc))
    raise ValueError("SVRule no terminada en ocho bytes")


def evaluate(rule: bytes, table: C1SVTable) -> int:
    return evaluate_trace(rule,table).result
