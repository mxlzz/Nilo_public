"""Selección modular experimental del contexto deliberativo (etapa 10).

Únicamente produce un payload calculado: no actualiza SQLite, memoria,
prompts permanentes, ni perfiles de instalación. El modo baseline sigue siendo
el predeterminado. Se conservan los contratos en su registro original.
"""
from __future__ import annotations

import json
import re

from nilo_runtime.agent.budget import brief_actions, compact_context, bounded_context
from nilo_runtime.agent.prompts import POLICY_RULES
from nilo_runtime.core.operations import registered_operations


# Una ausencia explícita sigue siendo informativa en el estado, la evidencia
# física y la identidad. No se ejecuta jamás un barrido recursivo de null/[].
_OMIT_IF_EMPTY = frozenset({
    "propuestas_pendientes", "fenomenos_pendientes_de_modelo",
    "predicciones_contrastadas", "evaluaciones_externas_recientes",
    "estrategias_que_ya_no_funcionaron", "inconsistencias_recoleccion_previas",
    "antecedentes_relacionados", "investigaciones_pausadas_relacionadas",
    "revision_de_intentos_verificados", "comparaciones_validas",
    "revision_de_estrategia", "repeticion_operativa_informativa",
    "estado_investigacion_descanso", "condiciones_de_ensayo_descanso",
})
_EVIDENCE_LISTS = frozenset({
    "memorias_relevantes", "mediciones_reales_recientes",
    "conocimiento_con_procedencia", "resultados_de_acciones",
    "conclusiones_verificadas", "revision_de_intentos_verificados",
})
_FOCUS_TERMS = {
    "navegacion": ("explor", "rutas", "ruta", "territor", "cueva",
                   "camino", "orilla", "costas", "recorr", "naveg"),
    "fabricacion": ("fabric", "diseñ", "disen", "herramient", "constru",
                    "modific", "ensambl", "recipiente", "mecanism", "material"),
    "experimentacion": ("experiment", "ensay", "medic", "compar",
                        "verific", "hipotes", "hipótes", "resisten", "dureza",
                        "conclu", "predic"),
    "subsistencia": ("hambre", "sed", "nutrici", "hidrat", "descans",
                     "energ", "sueño", "dormir", "aliment", "refugio"),
}
_OP_FOCUS = {
    "navegacion": frozenset(("go", "explore", "ascend", "descend", "inspect")),
    "fabricacion": frozenset(("design", "craft", "build", "assemble", "modify",
                              "combine", "dismantle", "interact", "use")),
    "experimentacion": frozenset(("experiment", "compare", "conclude", "use",
                                 "report_issue", "propose")),
    "subsistencia": frozenset(("rest", "wait", "forage", "drink", "eat")),
}
_POLICY_ALWAYS = frozenset((
    "identidad", "contrato", "conocimiento", "orientacion-necesidades",
    "incertidumbre", "plan", "formato", "esquema", "cuaderno",
    "resultado", "cierre",
))
_POLICY_FOCUS = {
    "navegacion": ("navegacion", "recoleccion"),
    "fabricacion": ("fisica-local", "investigacion"),
    "experimentacion": ("prediccion", "mediciones", "investigacion", "repeticion"),
    "subsistencia": ("orientacion-necesidades",),
}
_POLICY_FIELD = {
    "continuidad": ("proyectos_reanudables", "antecedentes_relacionados",
                    "ultimo_cierre_rechazado", "revision_de_estrategia",
                    "investigaciones_pausadas_relacionadas"),
    "evaluacion-externa": ("evaluaciones_externas_recientes",
                           "diagnosticos_operativos_recientes"),
    "recoleccion": ("inconsistencias_recoleccion_previas",),
    "prediccion": ("predicciones_contrastadas",),
    "mediciones": ("comparaciones_validas", "mediciones_reales_recientes"),
    "repeticion": ("revision_de_intentos_verificados",
                   "repeticion_operativa_informativa"),
    "agenda": ("agenda_diferida", "recordatorios_pendientes", "recordatorios_listos"),
    "recordatorio": ("recordatorios_pendientes", "recordatorios_listos"),
    "delegacion": ("preferencias_en_espera", "habilidades_verificadas"),
    "estancamiento": ("estrategia_bloqueada", "revision_de_estrategia"),
}


def _nonempty(value):
    # False y cero son observaciones válidas, no ausencias.
    return value is not None and value != "" and value != []


def _row_fingerprint(row):
    return json.dumps(row, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def _deduplicate_exact(rows):
    """Solo elimina copias idénticas por ID dentro de una misma fuente.

    Registros con igual ID pero contenido distinto se conservan: pueden ser
    conflictos que el observador necesita investigar. Sin ID no se colapsan.
    """
    seen = set()
    kept = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"]:
            kept.append(row)
            continue
        mark = (row["id"], _row_fingerprint(row))
        if mark not in seen:
            seen.add(mark)
            kept.append(row)
    return kept


def semantic_context(context):
    """Filtra solo vacíos enumerados y duplicados verificables; copia los datos."""
    if not isinstance(context, dict):
        raise ValueError("El contexto debe ser un objeto.")
    selected = {}
    for key, value in context.items():
        if key in _OMIT_IF_EMPTY and not _nonempty(value):
            continue
        if key in _EVIDENCE_LISTS and isinstance(value, list):
            value = _deduplicate_exact(value)
        selected[key] = value
    return selected


def detect_focuses(context):
    """Focos simultáneos desde intereses ya abiertos y acciones registradas.

    No crea intereses ni transforma texto de la partida en instrucciones.
    """
    project = context.get("proyecto_actual") or {}
    chunks = []
    if isinstance(project, dict):
        chunks.extend(str(project.get(k) or "") for k in
                      ("title", "reason", "state", "last_action", "last_result"))
    research = context.get("investigaciones_activas") or []
    if isinstance(research, list):
        for row in research[-3:]:
            if isinstance(row, dict):
                chunks.extend(str(row.get(k) or "") for k in
                              ("question", "hypothesis", "state"))
    message = " ".join(chunks).casefold()
    result = []
    for focus, keywords in _FOCUS_TERMS.items():
        if any(term in message for term in keywords):
            result.append(focus)
    # Evidencia operativa reciente: no se infiere una actividad de un título.
    outcomes = context.get("resultados_de_acciones") or []
    if isinstance(outcomes, list):
        for row in outcomes[-3:]:
            if not isinstance(row, dict):
                continue
            op = row.get("operacion") or row.get("op")
            for focus, operations in _OP_FOCUS.items():
                if op in operations and focus not in result:
                    result.append(focus)
    return tuple(result or ("general",))


def policy_sections(context, provider):
    """Reglas seleccionadas por ID desde la ÚNICA fuente vigente."""
    if provider not in ("gemini", "groq", "openai_compatible"):
        raise ValueError("Proveedor desconocido.")
    focus = detect_focuses(context)
    ids = set(_POLICY_ALWAYS)
    for tag in focus:
        ids.update(_POLICY_FOCUS.get(tag, ()))
    for tag, keys in _POLICY_FIELD.items():
        if any(_nonempty(context.get(key)) for key in keys):
            ids.add(tag)
    # Las funciones no son misiones, pero se anuncian para que Nilo las conozca.
    # En ausencia de agenda o delegación, basta su síntesis, no recetas extensas.
    ids.update(("agenda", "delegacion"))
    compact = provider == "groq"
    return [(key, short if compact else long)
            for key, long, short in POLICY_RULES if key in ids]


def _detailed_operations(context):
    focus = detect_focuses(context)
    selected = []
    for tag in focus:
        for name in _OP_FOCUS.get(tag, ()):
            # Mantener orden determinista del registro; el set NO ordena.
            if name not in selected:
                selected.append(name)
    return tuple(op for op in registered_operations()
                 if op in selected)[:8]


def modular_instructions(context, provider):
    """Devuelve (sistema, manual); índice de TODAS las operaciones siempre."""
    sections = policy_sections(context, provider)
    system = "\n".join(text for _, text in sections)
    index = brief_actions()
    if provider == "groq":
        return system + "\n" + index, ""
    registry = registered_operations()
    detailed = _detailed_operations(context)
    detail = "\n".join("- " + name + ": " + registry[name].description
                       for name in detailed)
    manual = index
    if detail:
        manual += "\nDETALLES OPERATIVOS SEGÚN CONTEXTO (no son tareas):\n" + detail
    return system, manual


def modular_context(context, *, provider):
    """Compone contexto con las cuotas existentes, sin mutar el original."""
    if provider not in ("gemini", "groq", "openai_compatible"):
        raise ValueError("Proveedor desconocido.")
    filtered = semantic_context(context)
    target = 4100 if provider == "groq" else 9100
    selected = compact_context(filtered, char_budget=18000 if provider == "groq" else 25000)
    # El compactador legado siempre añade una marca, incluso sin recorte real.
    # Esta variante únicamente la envía cuando se eliminó/comprimió algo.
    selected.pop("contexto_reducido", None)
    selected = bounded_context(selected, target)
    changed = selected != context
    if changed and "contexto_reducido" not in selected:
        message = "Selección y presupuesto de contexto aplicados; la memoria original permanece registrada."
        marked = dict(selected, contexto_reducido=message)
        if len(json.dumps(marked, ensure_ascii=False, separators=(",", ":")).encode("utf-8")) <= target:
            selected = marked
    return selected
