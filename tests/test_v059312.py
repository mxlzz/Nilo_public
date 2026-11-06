from ui_fixture import legacy_markup, legacy_html_path
"""0.5.9.3.12: navigation history, honest excavation, and focused UI."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from world import dig_with_tool, new_world, pathfind, set_tile, tile

ROOT=Path(__file__).resolve().parent.parent

class DiggingDescriptionTests(unittest.TestCase):
    def test_clearing_is_not_claimed_to_open_new_connection(self):
        world=new_world(845)
        # La roca central ya puede rodearse; la comunicación existe antes.
        for x,y in ((10,9),(10,11),(9,9),(9,10),(9,11),(11,9),(11,10),(11,11)):
            set_tile(world,x,y,0,'.')
        set_tile(world,10,10,0,'^')
        self.assertTrue(pathfind(world,(10,9,0),(10,11,0)))
        world['excavation']['10,10,0']=2
        person={'pos':[10,9,0],'inventory':{}}
        success,result,opened=dig_with_tool(world,person,{'name':'Punta'},6.0)
        self.assertTrue(success)
        self.assertTrue(opened)
        self.assertEqual(tile(world,10,10,0),'.')
        self.assertTrue(pathfind(world,(10,9,0),(10,11,0)))
        self.assertIn('despejé la casilla (10,10)',result)
        self.assertNotIn('abrí un paso',result)
        self.assertEqual(person['inventory']['piedra'],2)

class InterfaceNavigationTests(unittest.TestCase):
    def test_back_controls_and_origin_restoration_are_available(self):
        html=legacy_markup(Path(__file__).resolve().parents[1])
        self.assertNotIn('id="record-navigation-back"',html)
        self.assertIn('id="record-dialog-back"',html)
        self.assertIn('function captureRecordLocation()',html)
        self.assertIn('function restoreRecordLocation()',html)
        self.assertIn('feedScroll:el(\'feed\').scrollTop',html)
        self.assertIn('recordNavigationHistory.pop()',html)
        self.assertIn('if(opened)pushRecordLocation(previous)',html)
        self.assertNotIn('La simulación y la memoria se guardan localmente.',html)
        version=(ROOT/'VERSION').read_text('utf-8').strip()
        self.assertIn('Nilo '+version,html)

    def test_javascript_parses(self):
        node=shutil.which('node')
        if not node:self.skipTest('Node.js no disponible')
        html=legacy_markup(Path(__file__).resolve().parents[1])
        js=html.split('<script>',1)[1].rsplit('</script>',1)[0]
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'interface.js'
            path.write_text(js,encoding='utf-8')
            process=subprocess.run([node,'--check',str(path)],
                                   capture_output=True,text=True,timeout=30)
            self.assertEqual(process.returncode,0,process.stderr)

if __name__=='__main__':
    unittest.main()
