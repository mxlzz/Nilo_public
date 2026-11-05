from ui_fixture import legacy_markup, legacy_html_path
"""0.5.9.2.6 — títulos legibles basados en evidencias y agenda sin atribuciones falsas."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parent.parent
HTML=legacy_markup(Path(__file__).resolve().parents[1])


class LegibilityTests(unittest.TestCase):
    def test_rendering_and_epistemic_distinction_on_real_examples(self):
        if not shutil.which("node"):self.skipTest("Node.js no disponible")
        runner=r"""
const assert=require('assert'),fs=require('fs'),vm=require('vm');
const src=fs.readFileSync(process.argv[2],'utf8').split('<script>')[1].split('</script>')[0];
const extract=(a,b)=>{
 const s=src.indexOf(a),e=src.indexOf(b,s);
 assert(s>=0&&e>s,a);return src.slice(s,e)
};
const source=[
 extract('const ACTION_LABELS=', 'function showMap(){'),
 extract('function agendaCondition(', 'function renderIdentity(){'),
 extract('function measurementActionTitle(', 'function oneProject(p)')
].join('\n');
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const measurement={
 id:'med-c4f51c20964c',when:'Día 2 · 02:11',op:'go',target:'',duration_minutes:18.13,
 start:{position:[10,16,0],needs:{energia:75.02}},
 end:{position:[16,16,0],needs:{energia:74.66}},
 needs_delta:{energia:-0.36},inventory_delta:{},verified_facts:[
 'Avancé 6 tramos hasta [16, 16]; destino propuesto: (16, 16).'
 ],success:true,evaluation_status:'comprobado'
};
const task={
 id:'tar-08dbe22ff1',titulo:'Comparar descanso',
 motivo:'Completar la medición de recuperación en refugio para cerrar el experimento.',
 estado:'completada',cuando:{tipo:'despues_de_minutos',minutos:60},
 indice:1,ultimo_motivo:'Secuencia terminada',
 pasos:[{op:'conclude',topic:'notas del refugio',evidence_ids:['med-d9e9e4fef5f5']}],
 resultados:[{when:'Día 1 · 07:38',paso:1,op:'conclude',exito:true,
 hecho:"Registré una conclusión descriptiva apoyada en pruebas reales: build (med-d9e9e4fef5f5; éxito): Construí 'refugio_base' en [13, 19, 0]."}]
};
const data={measurements:[measurement,{id:'med-d9e9e4fef5f5',op:'build'}],
 conclusions:[],experiment_status:{},agenda:[task],agenda_history:[]};
const ctx={data,esc,focusedMeasurement:null,essayView:'all',recordLinks:()=>''};
vm.runInNewContext(source,ctx);
assert.equal(ctx.measurementActionTitle(measurement),'Desplazamiento hasta (16, 16)');
assert.equal(ctx.measurementSummary(measurement),'6 tramos recorridos · 18,13 min');
assert.equal(ctx.actionName({op:'conclude'}),'Registrar conclusión');
const assays=ctx.renderMeasurements();
assert(assays.includes('Desplazamiento hasta (16, 16)'),assays);
assert(!assays.includes('<strong>go</strong>'),assays);
assert(assays.includes('Operación: go'));
assert(assays.includes('75.02')&&assays.includes('74.66'));
const agenda=ctx.renderAgenda();
assert(agenda.includes('Activar después de 60 min simulados'));
assert(agenda.includes('no implica descansar ese tiempo'));
assert(agenda.includes('Registrar conclusión'));
assert(agenda.includes('no incluye descansar ni comparar mediciones'));
assert(agenda.includes('tampoco corresponden a descansos'));
assert(agenda.includes('Secuencia completada'));
assert(agenda.includes('Construí'));
assert(!agenda.includes('<strong>Condición:</strong> {'));
const delays=[
 {tipo:'cuando_haya_material',material:'madera',cantidad:3},
 {tipo:'cuando_necesidad',necesidad:'energia',menor_que:40},
 {tipo:'ahora'}
];
assert(ctx.agendaCondition(delays[0]).includes('3 unidades de madera'));
assert(ctx.agendaCondition(delays[1]).includes('energía'));
assert(ctx.agendaCondition(delays[2]).includes('Activar en cuanto'));
assert.equal(ctx.measurementActionTitle({op:'go',end:{},start:{},duration_minutes:4}),'Desplazamiento registrado');
assert.equal(ctx.measurementActionTitle({op:'rest',condition:'refugio'}),'Descanso en refugio');
assert.equal(ctx.measurementActionTitle({op:'gather',target:'piedra'}),'Recolectar · piedra');
console.log('evidence-aware presentation OK');
"""
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"check.js";p.write_text(runner,encoding="utf-8")
            result=subprocess.run(["node",str(p),str(legacy_html_path(ROOT))],
                                  capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn("evidence-aware presentation OK",result.stdout)

    def test_interface_exposes_raw_data_only_in_technical_details(self):
        self.assertIn('class="technical-details"',HTML)
        self.assertIn('Información técnica',HTML)
        self.assertIn('agendaCondition(t.cuando)',HTML)
        self.assertIn('measurementActionTitle(m)',HTML)
        self.assertIn('measurementSummary(m)',HTML)
        self.assertIn("CONCLUSIÓN REGISTRADA",HTML)
        self.assertIn("ACCIÓN COMPLETADA",HTML)


if __name__=="__main__":
    unittest.main()
