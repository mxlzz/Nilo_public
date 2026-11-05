"""Selección prudente de antecedentes para diagnósticos y solicitudes de Nilo.

Un resultado del motor es real; su relación con una afirmación puede no estar
acreditada. No convertir semejanza textual, fallo o revisión editorial en física.
"""
from __future__ import annotations

import re
import unicodedata


def _tokens(value):
    normalized = unicodedata.normalize("NFKD", str(value or "").casefold())
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))
    return set(re.findall(r"[a-z0-9]+", normalized))


def _same_phenomenon(candidate, recorded):
    """Equivalencia conservadora entre nombres; sin usar resultados narrados."""
    a, b = _tokens(candidate), _tokens(recorded)
    if not a or not b:
        return False
    if a == b:
        return True
    # Permite "condensación" ↔ "evaporación y condensación de agua",
    # pero no relaciona fenómenos distintos solo porque mencionan "agua".
    generic = {"agua", "material", "objeto", "fisica", "fenomeno", "efecto",
               "modelo", "proceso", "cambio", "prueba", "sistema", "mecanismo"}
    specific = {w for w in a & b if len(w) >= 7 and w not in generic}
    return bool(specific)


def select_physics_evidence(step, attempts):
    """Devolver antecedentes NO EVALUABLES y el modo de vinculación.

    IDs explícitos no válidos o ajenos al fenómeno nunca disparan fallback.
    Sin IDs, se permite coincidencia conservadora y se rotula como inferencia.
    """
    phenomenon = str(step.get("phenomenon") or "")
    available = {r.get("id"): r for r in attempts if isinstance(r, dict)
                 and r.get("id") and r.get("result") == "no_evaluable"}
    requested = step.get("evidence_ids")
    if isinstance(requested, list) and requested:
        selected = []
        for rid in requested[:8]:
            row = available.get(rid) if isinstance(rid, str) else None
            if row and _same_phenomenon(phenomenon, row.get("phenomenon"))                     and row not in selected:
                selected.append(row)
        return selected, "referencia_explicita" if selected else "sin_evidencia_coincidente"
    if requested is not None and not isinstance(requested, list):
        return [], "referencias_invalidas"
    matching = [r for r in attempts if isinstance(r, dict)
                and r.get("id") in available
                and _same_phenomenon(phenomenon, r.get("phenomenon"))]
    selected = matching[-3:]
    return selected, "coincidencia_de_fenomeno" if selected else "sin_evidencia_coincidente"


def select_debug_evidence(step, outcomes):
    """Conservar referencias reales sin fingir que un fallo prueba un defecto."""
    actual = {r.get("id"): r for r in outcomes if isinstance(r, dict) and r.get("id")}
    requested = step.get("evidence_ids")
    if isinstance(requested, list) and requested:
        selected = []
        for rid in requested[:8]:
            row = actual.get(rid) if isinstance(rid, str) else None
            if row and row not in selected:
                selected.append(row)
        return selected, "referencia_explicita" if selected else "sin_evidencia_coincidente"
    if requested is not None and not isinstance(requested, list):
        return [], "referencias_invalidas"
    related = str(step.get("related_action") or "").strip()
    if not related:
        return [], "sin_evidencia_coincidente"
    # Es solo un candidato contextual: ninguna coincidencia de operación
    # acredita que el fallo se relacione causalmente con el síntoma narrado.
    failures = [r for r in outcomes if isinstance(r, dict)
                and r.get("op") == related and r.get("success") is False]
    selected = failures[-3:]
    return selected, "misma_operacion_sin_relacion_verificada" if selected else "sin_evidencia_coincidente"


def human_review_feedback(proposals, limit=4):
    """Recuperar devoluciones humanas sin convertirlas en mediciones físicas."""
    reviews = []
    for proposal in proposals:
        if not isinstance(proposal, dict):
            continue
        snapshots = [r for r in proposal.get("review_history", []) if isinstance(r, dict)]
        if isinstance(proposal.get("review"), dict):
            snapshots.append(proposal["review"])
        for review in snapshots:
            reviews.append({
                "solicitud_id": proposal.get("id"),
                "tipo": proposal.get("type", "physics"),
                "asunto": proposal.get("title") or proposal.get("phenomenon"),
                "decision_humana": review.get("decision"),
                "fundamento_humano": review.get("reason"),
                "fecha": review.get("when"),
                "es_una_medicion_fisica": False,
            })
    # El sello del simulador es "Día N · HH:MM": una revisión tardía de
    # una propuesta vieja no debe desaparecer detrás de propuestas nuevas.
    def chronological(record):
        stamp = str(record.get("fecha") or "")
        match = re.search(r"D[ií]a\s+(\d+)\s*·\s*(\d{1,2}):(\d{2})", stamp)
        if match:
            day, hour, minute = map(int, match.groups())
            return day * 1440 + hour * 60 + minute
        return -1
    reviews.sort(key=chronological)
    return reviews[-max(0, limit):] if limit > 0 else []
