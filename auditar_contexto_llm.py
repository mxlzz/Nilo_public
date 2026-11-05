"""Auditoría reproducible de la representación final enviada a los LLM.

NO llama a APIs ni carga partidas privadas: utiliza estados sintéticos, claves
ficticias y las MISMAS funciones que construyen las solicitudes reales.
Solo imprime nombres de campos, tamaños y señales; no persiste el prompt.
Uso: python auditar_contexto_llm.py [--json archivo.json]
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from brain import build_deliberation_request, context_for
from nilo import initial_state


PROVIDERS = {
    "gemini": {"PROVIDER": "gemini", "MODEL": "gemini-3.1-flash-lite",
               "GEMINI_API_KEY": "clave-ficticia-no-enviar"},
    "groq": {"PROVIDER": "groq", "MODEL": "openai/gpt-oss-20b",
             "GROQ_API_KEY": "clave-ficticia-no-enviar"},
    "openai_compatible": {"PROVIDER": "openai_compatible", "MODEL": "modelo-sintetico",
                          "OPENAI_API_KEY": "clave-ficticia-no-enviar"},
}


def extract_sent_context(provider, payload):
    """Parsear exactamente el JSON serializado para el proveedor."""
    if provider == "gemini":
        part = payload["contents"][0]["parts"][0]["text"]
        marker = "SITUACIÓN REAL: "
        if marker not in part:
            raise ValueError("No se encontró el contexto final de Gemini.")
        return json.loads(part.split(marker, 1)[1])
    return json.loads(payload["messages"][1]["content"])


def scenario_context(name):
    """Estados de laboratorio, no atribuidos a un run real de Nilo."""
    state = initial_state(world_seed=7321)
    p, w = state["person"], state["world"]
    if name in ("proyecto_refugio", "contexto_extenso"):
        p["project"] = {
            "id": "proyecto-sintetico", "title": "Investigar refugio de madera",
            "reason": "Evaluar posibilidades del refugio", "status": "activo",
            "progress": 95, "no_progress_steps": 8,
            "state": "Pendiente de una medición funcional"}
    if name in ("pausa", "contexto_extenso"):
        p["projects"] = [{
            "id": "proyecto-pausado", "title": "Estudiar refugio de madera",
            "status": "pausado", "reason": "Comprobar la cubierta",
            "state": "Sin protección climática demostrada",
            "closure_reason": "Las inspecciones no dieron información nueva",
            "no_progress_steps": 8}]
        p["research"] = [{
            "id": "investigacion-pausada",
            "question": "Cómo comprobar el abrigo del refugio de madera",
            "hypothesis": "El refugio de madera protege del clima",
            "state": "pausada", "evidence": [],
            "project_retirement": {"project_id": "proyecto-pausado",
                                   "status": "pausado",
                                   "conclusion_not_verified": True}}]
    context = context_for(w, p, [], "Día 2 · 12:00")
    if name in ("proyecto_refugio", "contexto_extenso"):
        # Proyecciones sintéticas con el formato actual de context_for.
        # No equivalen a afirmar que un refugio concreto haya sido construido.
        context["construcciones_fijas"] = [{
            "id": "obra-sintetica", "nombre": "Refugio", "categoria": "habitaculo",
            "posicion": [17, 19, 0], "version": 1,
            "condicion_abrigo": "cubierto_parcialmente",
            "piezas": [], "planta": {"width_m": 3, "height_m": 2},
            "estado": "función no comprobada"}]
        context["herramientas_que_llevo"] = [{
            "id": "herramienta-sintetica", "nombre": "Punta",
            "forma": "punta", "durabilidad": 89,
            "usos_por_verificar": {"excavar": 2.8}}]
    if name == "contexto_extenso":
        context["resultados_de_acciones"] = [
            {"id": f"accion-{i}", "operacion": "inspect",
             "resultado": ["Inspección sin nuevos datos físicos disponibles"],
             "exito": True} for i in range(70)]
        context["memorias_relevantes"] = [
            {"id": f"mem-{i}", "text": "Inspeccioné el refugio sin validar clima."}
            for i in range(20)]
    return context


def signals(selected):
    project = selected.get("proyecto_actual") or {}
    needs = selected.get("necesidades") or {}
    buildings = selected.get("construcciones_fijas") or []
    tools = selected.get("herramientas_que_llevo") or []
    return {
        "progreso_numerico_del_proyecto": (
            isinstance(project.get("progress"), (int, float))
            and not isinstance(project.get("progress"), bool)),
        "clasificacion_abrigo_esquematico": any(
            isinstance(row, dict) and "condicion_abrigo" in row
            for row in buildings),
        "durabilidad_numerica_sin_medicion_explicitada": any(
            isinstance(row, dict) and isinstance(row.get("durabilidad"), (int, float))
            for row in tools),
        "potencia_herramienta_precalculada": any(
            isinstance(row, dict) and isinstance((row.get("usos_por_verificar") or {}).get("excavar"),
                                              (int, float))
            for row in tools),
        "predisposiciones_numericas": "predisposiciones" in selected,
        "porcentaje_descubrimiento": "territorio_descubierto_pct" in selected,
        "necesidades_con_reservas_internas": any(
            isinstance(v, (int, float)) and not isinstance(v, bool)
            for v in needs.values()) or "valores" in needs,
        "antecedente_de_pausa_presente": bool(
            selected.get("antecedentes_relacionados")
            or selected.get("investigaciones_pausadas_relacionadas")),
    }


def audit_case(name, provider):
    original = scenario_context(name)
    # Verificar que producir prompts no reescriba el contexto fuente.
    before = copy.deepcopy(original)
    _, payload, headers = build_deliberation_request(PROVIDERS[provider], original)
    if original != before:
        raise AssertionError("El armado del payload mutó el contexto fuente.")
    selected = extract_sent_context(provider, payload)
    if "clave-ficticia-no-enviar" in json.dumps(payload, ensure_ascii=False):
        raise AssertionError("La credencial ficticia apareció dentro del prompt.")
    return {
        "escenario": name, "proveedor": provider, "datos": "sinteticos",
        "contexto_original_bytes": len(json.dumps(original, ensure_ascii=False).encode("utf-8")),
        "contexto_enviado_bytes": len(json.dumps(selected, ensure_ascii=False).encode("utf-8")),
        "campos_originales": sorted(original),
        "campos_enviados": sorted(selected),
        "campos_omitidos": sorted(set(original) - set(selected)),
        "senales": signals(selected),
    }


def audit_all():
    return {
        "metodo": "payload serializado con build_deliberation_request; cero llamadas de red",
        "alcance": "escenarios sintéticos; no sustituye corrida con LLM real",
        "resultados": [
            audit_case(name, provider)
            for name in ("inicio", "proyecto_refugio", "pausa", "contexto_extenso")
            for provider in PROVIDERS
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path,
                        help="Destino opcional de métricas sin contenido del prompt.")
    args = parser.parse_args(argv)
    output = audit_all()
    rendered = json.dumps(output, ensure_ascii=False, indent=2)
    if args.json:
        args.json.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return output


if __name__ == "__main__":
    main()
