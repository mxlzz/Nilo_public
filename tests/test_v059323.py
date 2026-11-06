from ui_fixture import legacy_markup, legacy_html_path
"""0.5.9.3.23 — La lectura del registro no modifica la autonomía del personaje."""
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
HTML=legacy_markup(Path(__file__).resolve().parents[1])


class ReadabilityInterface(unittest.TestCase):
    def test_needs_help_describes_v059322_not_preexisting_automatic_care(self):
        self.assertNotIn('bebe de manera autónoma al llegar a 45',HTML)
        self.assertNotIn('come automáticamente al llegar a 45',HTML)
        self.assertIn('Nilo decide cuándo beber',HTML)
        self.assertIn('Nilo decide cuándo comer',HTML)
        self.assertIn('6,6 puntos/h',HTML)
        self.assertIn('recupera la conciencia al alcanzar 40',HTML)

    def test_section_help_is_fixed_outside_scroll_and_closes(self):
        self.assertIn('.section-help-popover{position:fixed',HTML)
        self.assertIn('document.body.appendChild(panel)',HTML)
        self.assertIn('function closeSectionHelp(',HTML)
        self.assertIn("event.key==='Escape'&&floatingHelp",HTML)
        self.assertIn("el('feed').addEventListener('scroll',()=>closeSectionHelp()",HTML)
        self.assertNotIn('details.section-help[open]',HTML)

    def test_research_filter_independent_of_existing_projects_filter(self):
        self.assertIn('id="research-filter-wrap"',HTML)
        self.assertIn('id="research-filter"',HTML)
        self.assertIn('function matchesResearchView(q)',HTML)
        self.assertIn("saveLocal('nilo.researchView.v1',researchView)",HTML)
        self.assertIn("el('status-filter').addEventListener('change'",HTML)
        self.assertIn('id="status-filter-wrap"',HTML)

    def test_research_closure_is_grounded_and_predictions_not_filtered(self):
        self.assertIn('q.project_retirement',HTML)
        self.assertIn('project?.closure_reason',HTML)
        self.assertIn('Motivo no registrado',HTML)
        self.assertIn('evidence?.summary',HTML)
        self.assertIn('renderPredictions()',HTML)

    def test_research_filter_initializes_in_real_javascript_execution(self):
        """La sintaxis correcta no alcanza: detectar acceso a const en TDZ."""
        if not shutil.which('node'):
            self.skipTest('Node.js opcional para ejecutar inicialización del navegador')
        start=HTML.index("let data=null,tab='notes'")
        end=HTML.index('function selectedStatusView(',start)
        bootstrap=HTML[start:end]
        harness=(
            "const vm=require('node:vm');"
            "const fs=require('node:fs');"
            "const source=fs.readFileSync(0,'utf8');"
            "const localStorage={getItem(){return null}};"
            "vm.runInNewContext(source+\"\\nif(researchView!=='todas')"
            "throw Error('Filtro no inicializado');\",{localStorage});"
        )
        result=subprocess.run(['node','-e',harness],input=bootstrap,
                              capture_output=True,text=True,check=False)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_javascript_is_syntactically_valid_when_node_is_available(self):
        if not shutil.which('node'):
            self.skipTest('Node.js opcional para validar JavaScript')
        match=re.search(r'<script>(.*?)</script>',HTML,re.DOTALL)
        self.assertIsNotNone(match)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'nilo_interfaz.js'
            path.write_text(match.group(1),encoding='utf-8')
            run=subprocess.run(['node','--check',str(path)],
                capture_output=True,text=True,check=False)
        self.assertEqual(run.returncode,0,run.stderr)


if __name__=='__main__':
    unittest.main()
