"""Etapa 01: correcciones semánticas y regresiones de interfaz del laboratorio.

No requiere claves LLM, red, archivos del usuario ni el motor en ejecución.
"""
from __future__ import annotations

from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGES = (
    "laboratorio_motor.html", "laboratorio_escenarios.html",
    "laboratorio_historico.html", "laboratorio_ajustes.html",
    "laboratorio_visor_llm.html",
)


def page(name):
    return (ROOT / name).read_text(encoding="utf-8")


def script(name):
    match = re.search(r"<script(?:\\s[^>]*)?>([\\s\\S]*?)</script>", page(name))
    if not match:
        raise AssertionError("La pantalla no contiene script: " + name)
    return match.group(1)


class LabUiAudit01(unittest.TestCase):
    def test_labels_distinguish_real_from_calculated(self):
        sandbox = page("laboratorio_motor.html")
        scenarios = page("laboratorio_escenarios.html")
        viewer = page("laboratorio_visor_llm.html")
        self.assertIn("Solicitud calculada</button>", sandbox)
        self.assertIn("Cuerpo JSON que se enviaría al proveedor", sandbox)
        self.assertIn("Órdenes predefinidas de prueba", scenarios)
        self.assertIn("Solicitudes reales archivadas", viewer)
        self.assertNotIn("Contexto exacto enviado al proveedor", sandbox)
        self.assertNotIn("Órdenes que habría generado el LLM", scenarios)

    def test_provenance_and_transport_states_have_clear_labels(self):
        text = page("laboratorio_visor_llm.html")
        for marker in (
            'accepted:"Aceptado por el validador"',
            'transport_attempted:"Envío iniciado; sin resultado archivado"',
            'available:"Completa"',
            'not_recorded:"No registrada"',
            "Procedencia del campo",
            "Este vínculo no demuestra que la acción se haya ejecutado.",
            "statusLabel(item.status)",
            "provenanceLabel(data.provenance_status)",
        ):
            self.assertIn(marker, text)
        self.assertIn("Estado original del intento", text)
        self.assertIn("detailEpoch", text)
        self.assertIn("listEpoch", text)
        self.assertNotIn("Origen y transformaciones", text)

    def test_historical_view_invalidates_pending_data_and_selection(self):
        text = script("laboratorio_historico.html")
        for marker in (
            "let sourceToken=0,detailToken=0;",
            'if(requestToken!==detailToken||!selected||selected.id!==r.id)return;',
            "if(requestToken===sourceToken)showData(data);",
            "function clearSelection(",
            'clearSelection("Esta partida no tiene momentos para inspeccionar.");',
            'clearSelection("No hay momentos que coincidan con los filtros.");',
            "if(replayToken!==detailToken)return;",
        ):
            self.assertIn(marker, text)

    def test_no_false_version_or_unverified_source_links(self):
        self.assertIn("<title>Nilo · Laboratorio de acciones</title>",
                      page("laboratorio_motor.html"))
        scenario = page("laboratorio_escenarios.html")
        self.assertIn("Referencia local sin commit verificado", scenario)
        self.assertNotIn("github.com/mxlzz/Nilo/blob/", scenario)
        self.assertNotIn('let ref=last&&last.version?', scenario)

    def test_checkbox_exclusion_is_explicit(self):
        settings = page("laboratorio_ajustes.html")
        self.assertIn("Excluir información opcional del contexto LLM", settings)
        self.assertIn("Una casilla marcada excluye ese campo", settings)
        self.assertIn("una casilla desmarcada lo incluye", settings)

    def test_all_frontend_scripts_parse_with_node(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js no instalado")
        with tempfile.TemporaryDirectory(prefix="nilo-ui-01-js-") as tmp:
            for name in PAGES:
                target = Path(tmp) / (name + ".js")
                target.write_text(script(name), encoding="utf-8")
                proc = subprocess.run(
                    [node, "--check", str(target)], capture_output=True,
                    text=True, timeout=12,
                )
                self.assertEqual(proc.returncode, 0, name + ": " + proc.stderr)

    def test_historial_ignores_old_detail_after_opening_empty_world(self):
        """Prueba del bug real: respuesta tardía de A no contamina partida B."""
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js no instalado")
        js = script("laboratorio_historico.html")
        harness = r"""
const assert = require("node:assert/strict");
const vm = require("node:vm");
const nodes = new Map();
function el(id) {
  if (!nodes.has(id)) nodes.set(id, {
    value: id === "filter" ? "all" : "", textContent: "", innerHTML: "",
    max: 0, disabled: false, hidden: false, style: {},
    querySelectorAll: () => [],
  });
  return nodes.get(id);
}
let resolveOld = null;
const worldA = {source:"Mundo A",checkpoint_count:1,entries:[
  {id:"a",label:"Día 1",kind:"decision",op:"examinar",title:"Antiguo",
   replayable:true,engine_version:"0.7.0"}]};
const worldB = {source:"Mundo B",checkpoint_count:0,entries:[]};
function response(data) {return {ok:true,json:async()=>data};}
const fetch = (url) => {
  if (url === "/api/history/catalog") return Promise.resolve(response(worldA));
  if (url === "/api/history/default") return Promise.resolve(response(worldB));
  if (url.startsWith("/api/history/event?")) {
    return new Promise(done => {resolveOld = () => done(response({
      id:"a",command:{op:"examinar"},replayable:true,related:[]}));
    });
  }
  throw Error("Ruta inesperada: " + url);
};
const context = {document:{getElementById:el},fetch,console};
vm.runInNewContext(SOURCE,context,{timeout:3500});
const flush = () => new Promise(resolve => setImmediate(resolve));
(async () => {
  await flush();await flush();
  assert.equal(el("eventTitle").textContent,"examinar");
  assert.equal(typeof resolveOld,"function");
  await el("defaultFile").onclick();
  assert.equal(el("eventTitle").textContent,"Elegí un momento");
  assert.equal(el("replay").disabled,true);
  assert.equal(el("count").textContent,"0 momentos visibles");
  resolveOld();
  await flush();await flush();
  assert.equal(el("eventTitle").textContent,"Elegí un momento");
  assert.equal(el("command").textContent,"—");
  assert.equal(el("replay").disabled,true);
  assert.ok(el("resultView").textContent.includes("no tiene momentos"));
})().catch(error=>{console.error(error);process.exitCode=1;});
"""
        harness = harness.replace("SOURCE", repr(js).replace("\\u", "\\u"))
        # repr() no es un literal JS confiable ante escapes de Python: usar JSON.
        import json
        harness = harness.replace(repr(js).replace("\\u", "\\u"), json.dumps(js, ensure_ascii=False))
        proc = subprocess.run(
            [node, "-e", harness], text=True, capture_output=True, timeout=15,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main()
