from ui_fixture import legacy_markup, legacy_html_path
"""0.5.9.2.5 — importación de preferencias y lectura visual por registro."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from interface_prefs import FILENAME, import_settings, load, save, validate

ROOT=Path(__file__).resolve().parent.parent
HTML=legacy_markup(Path(__file__).resolve().parents[1])
JS=HTML.split("<script>",1)[1].split("</script>",1)[0]
CSS=HTML.split("<style>",1)[1].split("</style>",1)[0]


class VisualPreferences(unittest.TestCase):
    def test_roundtrip_rejects_injected_secrets_and_unknown_settings(self):
        with tempfile.TemporaryDirectory() as d:
            data={
                "theme":"terracota",
                "mapDisplay":"map",
                "mapZoom":{"near":28,"full":14},
                "mapView":{"view":"full","mapLayer":"0","showTrail":False},
                "notifications":{"mode":"off","source":"news"},
                "indicators":{"measurements":"subtle","notes":"off"},
                "api_key":"SHOULD_NOT_BE_STORED",
                "other":{"text":"secret"}
            }
            stored=save(Path(d),data)
            self.assertEqual(load(Path(d)),stored)
            raw=(Path(d)/FILENAME).read_text(encoding="utf-8")
            self.assertNotIn("SHOULD_NOT_BE_STORED",raw)
            self.assertNotIn("secret",raw)
            self.assertEqual(stored["mapZoom"]["near"],28)
            self.assertEqual(stored["indicators"]["measurements"],"subtle")
            self.assertEqual(stored["notifications"]["mode"],"off")

    def test_copy_preferences_does_not_override_destination(self):
        with tempfile.TemporaryDirectory() as d:
            a,b=Path(d)/"old",Path(d)/"new"
            a.mkdir();b.mkdir()
            save(a,{"theme":"grafito","mapZoom":{"near":36,"full":12}})
            self.assertTrue(import_settings(a,b))
            self.assertEqual(load(b)["theme"],"grafito")
            save(b,{"theme":"bosque"})
            self.assertFalse(import_settings(a,b))
            self.assertEqual(load(b)["theme"],"bosque")

    def test_invalid_file_is_not_imported(self):
        with tempfile.TemporaryDirectory() as d:
            a,b=Path(d)/"old",Path(d)/"new";a.mkdir();b.mkdir()
            (a/FILENAME).write_text("{broken",encoding="utf-8")
            self.assertFalse(import_settings(a,b))
            self.assertFalse((b/FILENAME).exists())

    def test_validation_bounds(self):
        values=validate({"mapZoom":{"near":100000,"full":16},
                         "theme":"extranjero","mapDisplay":"bogus",
                         "indicators":{"measurements":"off","invalid":"normal"}})
        self.assertNotIn("mapZoom",values)
        self.assertNotIn("theme",values)
        self.assertNotIn("mapDisplay",values)
        self.assertEqual(values["indicators"],{"measurements":"off"})


class VisualEntries(unittest.TestCase):
    def test_notes_use_real_individual_read_status_and_no_long_button(self):
        self.assertIn("item['read']=", (ROOT/"nilo_runtime/application/records.py").read_text(encoding="utf-8"))
        self.assertNotIn("data-read-note=",HTML)
        self.assertIn("markRead(tab==='notes'?'journal':'news',id,true)",JS)
        self.assertNotIn("Leído hasta aquí",HTML)
        self.assertIn(".feedentry.unread{border-left:none}",CSS)
        self.assertIn(".news-entry.unread",CSS)

    def test_measurements_highlight_the_record_not_only_tab(self):
        self.assertIn("function decorateRecords(){",JS)
        self.assertIn("tab==='measurements'",JS)
        self.assertIn("mark('[data-measurement-record]'",JS)
        self.assertIn("node.classList.add('new-record')",JS)
        self.assertIn("data-review-entry-key",JS)
        self.assertIn("async function markLocalEntryRead(key,entryTab=tab)",JS)
        self.assertIn("await Promise.all(Object.entries(updates)",JS)

    def test_explanations_are_in_compact_help_without_hiding_memory(self):
        self.assertIn("function relocateExplainer(){",JS)
        self.assertIn("function helpButton(title,html)",JS)
        self.assertIn("card.replaceWith(bar)",JS)
        self.assertIn("filters.appendChild(help)",JS)
        self.assertIn("section-help-popover",HTML)
        self.assertIn("Etapas de vida (30 días simulados)",HTML)

    def test_portable_tools_not_shown_as_square_meters(self):
        self.assertIn("type==='obra'?esc(o.space?.area_m2||'—')+' m²':'forma y superficie sin modelar'",HTML)
        self.assertNotIn("Identificadores técnicos",HTML)
        self.assertNotIn("data-open-plans",HTML)
        self.assertIn("El esquema indica cantidad y material",HTML)
        self.assertIn("historicMaterialDiff",HTML)

    def test_import_uses_installer_and_browser_sync_without_llm(self):
        self.assertIn("from interface_prefs import import_settings",(ROOT/"primer_inicio.py").read_text())
        self.assertIn("import_settings(source, HERE)",(ROOT/"migrar.py").read_text())
        self.assertIn("/api/ui-preferences",(ROOT/"nilo_runtime/web/http.py").read_text())
        self.assertIn("bootstrapUIPrefs().finally(()=>refresh())",JS)
        self.assertIn("nilo.mapZoom.v2",JS)
        self.assertIn("nilo.tabIndicators.v1",JS)

    def test_measurement_card_keys_match_what_tab_marks_unread(self):
        if not shutil.which("node"):
            self.skipTest("Node.js no disponible")
        runner=r"""
const fs=require('fs'),assert=require('assert');
const html=fs.readFileSync(process.argv[1],'utf8');
const js=html.split('<script>')[1].split('</script>')[0];
const source=js.slice(js.indexOf('function decorateRecords(){'),js.indexOf('function drawFeed(){'));
function node(){
 const classes=new Set(),label={appendChild(b){this.button=b}};
 return {classList:{add(v){classes.add(v)},contains(v){return classes.has(v)}},
         label,dataset:{},querySelector(){return label},classes};
}
const conclusion=node(),measurement=node();
conclusion.dataset.conclusionRecord='c1';measurement.dataset.measurementRecord='m1';
const container={querySelectorAll(selector){
 if(selector==='[data-conclusion-record]')return [conclusion];
 if(selector==='[data-measurement-record]')return [measurement];
 return [];
}};
const el=id=>{assert.equal(id,'feed');return container};
const document={createElement(){return {dataset:{},setAttribute(){}}}};
const tab='measurements',focusedMeasurement=null,data={measurements:[{id:'m1'}]},locallyReviewed={measurements:[]};
const tabEntries=()=>['m1','c1'];
eval(source+'\ndecorateRecords();');
assert.equal(conclusion.dataset.reviewEntryKey,'c1');
assert.equal(measurement.dataset.reviewEntryKey,'m1');
assert(measurement.classes.has('new-record'));
console.log('per-record highlights OK');
"""
        result=subprocess.run(["node","-e",runner,str(legacy_html_path(ROOT))],
                              capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn("per-record highlights OK",result.stdout)

    def test_node_syntax(self):
        if not shutil.which("node"):
            self.skipTest("Node.js no disponible")
        script=JS
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"nilo.js";p.write_text(script,encoding="utf-8")
            result=subprocess.run(["node","--check",str(p)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)


if __name__=="__main__":
    unittest.main()
