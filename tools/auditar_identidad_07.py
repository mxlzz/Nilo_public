"""Etapa 04: impedir que vuelva a infiltrarse RNG/UUID global en el motor.

No prohíbe la aleatoriedad de backoff de HTTP en providers.py ni el uso de
random.seed/uuid patch en reproducir.py para emular replays históricos.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BANNED = {
    ("uuid", "uuid4"),
    ("random", "getrandbits"),
    ("random", "random"),
    ("random", "randint"),
    ("random", "randrange"),
    ("random", "choice"),
    ("random", "choices"),
    ("random", "shuffle"),
    ("random", "sample"),
}
# Sólo el transporte puede necesitar jitter aleatorio no físico;
# los históricos siguen usando la API clásica y su instrumentación explícita.
EXEMPT = {"providers.py", "reproducir.py", "historical_lab.py"}

def violations() -> list[str]:
    findings = []
    for file in sorted(ROOT.glob("*.py")):
        if file.name in EXEMPT:
            continue
        tree = ast.parse(file.read_text(encoding="utf-8-sig"), filename=str(file))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if (isinstance(func, ast.Attribute)
                    and isinstance(func.value, ast.Name)
                    and (func.value.id, func.attr) in BANNED):
                findings.append(
                    f"{file.name}:{node.lineno}: prohibido {func.value.id}.{func.attr}; "
                    "usar nilo_runtime.core.identity o un RNG inyectado"
                )
    return findings


if __name__ == "__main__":
    problems = violations()
    if problems:
        print("\n".join(problems))
        raise SystemExit(1)
    print("Identidad v0.7: sin RNG/UUID global en módulos físicos y cognitivos")
