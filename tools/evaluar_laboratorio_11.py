"""Etapa 11: matriz offline reproducible baseline/modular, sin claves ni LLM.

Ejemplo:
  python tools/evaluar_laboratorio_11.py --seeds 7321 315 2026 \
    --output-json evaluacion_11.json --output-md evaluacion_11.md
El JSON solo contiene metadatos, huellas, bytes y ausencias, no prompts.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from nilo_runtime.core.lab_settings import baseline
from nilo_runtime.labs.ab_experiment import context_pair
from nilo_runtime.labs.evaluation_11 import SCHEMA, analyze_context_ab
from nilo_runtime.labs.hub import LabHub

DEFAULT_SEEDS = (7321, 315, 2026)
DEFAULT_PROVIDERS = ("gemini", "groq")


def evaluate(seeds=DEFAULT_SEEDS, providers=DEFAULT_PROVIDERS):
    if not isinstance(seeds, (tuple, list)) or not 1 <= len(seeds) <= 8:
        raise ValueError("Se requieren entre 1 y 8 semillas")
    if any(type(s) is not int or not 0 <= s <= 1_000_000_000 for s in seeds):
        raise ValueError("Semilla inválida")
    if len(set(seeds)) != len(seeds):
        raise ValueError("Las semillas deben ser diferentes")
    if not isinstance(providers, (tuple, list)) or not providers or any(
        p not in DEFAULT_PROVIDERS for p in providers
    ) or len(set(providers)) != len(providers):
        raise ValueError("Solo Gemini y Groq, sin repeticiones")
    rows = []
    with tempfile.TemporaryDirectory(prefix="nilo-eval-11-") as td:
        hub = LabHub(Path(td))
        for provider in providers:
            for seed in seeds:
                comparison = context_pair(
                    hub, baseline(), provider=provider, seed=seed,
                    context_mode="modular", source="new")
                rows.append(analyze_context_ab(comparison))
    return {
        "schema": SCHEMA, "kind": "offline_matrix",
        "seeds": list(seeds), "providers": list(providers),
        "rows": rows, "cases": len(rows),
        "llm_calls": 0, "original_worlds_modified": False,
        "causal_claim_allowed": False, "behavior_evaluated": False,
        "interpretation": (
            "Matriz de solicitudes calculadas. No representa respuestas del "
            "modelo, evolución autónoma, ganancia de calidad ni ahorro de tokens."
        ),
    }


def markdown(report):
    out = [
        "# Nilo 0.7.1 — Evaluación técnica A/B (etapa 11)",
        "", "Sin red ni proveedores reales. Baseline frente a contexto modular.",
        "", "| Proveedor | Semilla | Baseline (bytes) | Modular (bytes) | Diferencia (bytes) | Reglas esenciales |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in report["rows"]:
        out.append(
            f'| {row["provider"]} | {row["seed"]} '
            f'| {row["baseline"]["bytes_request"]} '
            f'| {row["variant"]["bytes_request"]} '
            f'| {row["request_bytes_delta"]:+} '
            f'| {"presentes" if row["both_preserve_required_fields"] else "revisar ausencias"} |'
        )
    out += [
        "", "## Límites",
        "",
        "- Todos los tamaños son bytes UTF-8 del cuerpo HTTP serializable, no tokens.",
        "- Mismos mundos y semillas; se consignan huellas de percepción y solicitudes.",
        "- No se evaluó ninguna decisión real ni se modificaron partidas.",
        "- Una reducción de bytes no demuestra mejora de autonomía o continuidad.",
        "- Para evaluar comportamiento, ejecutar después los ensayos reales de dos ramas bajo consentimiento y conservar los resultados originales.",
        "",
    ]
    return "\n".join(out)


def _write_new(filename, content):
    p = Path(filename).expanduser().resolve()
    if p.exists():
        raise ValueError("El archivo ya existe, no se sobrescriben resultados: " + str(p))
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(content)
    return str(p)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seeds", nargs="+", type=int, default=list(DEFAULT_SEEDS))
    p.add_argument("--providers", nargs="+", choices=DEFAULT_PROVIDERS,
                   default=list(DEFAULT_PROVIDERS))
    p.add_argument("--output-json")
    p.add_argument("--output-md")
    args = p.parse_args(argv)
    if not args.output_json and not args.output_md:
        p.error("Especificar --output-json o --output-md")
    data = evaluate(tuple(args.seeds), tuple(args.providers))
    if args.output_json:
        print(_write_new(args.output_json, json.dumps(
            data, ensure_ascii=False, sort_keys=True, indent=2) + "\n"))
    if args.output_md:
        print(_write_new(args.output_md, markdown(data)))
    print(f"Se evaluaron {data['cases']} pares de contextos; 0 llamadas al LLM.")


if __name__ == "__main__":
    main()
