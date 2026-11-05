"""0.5.9.3.24: contorno de intervención solo en objetivos físicos verificables."""
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

from world import new_world, set_tile, tile_key, forage_source, execute_action
from intervention import active_intervention, _inspection_site
from nilo import initial_state

ROOT=Path(__file__).resolve().parent.parent
HTML=(ROOT/'interfaz.html').read_text(encoding='utf-8')


class PhysicalTileTests(unittest.TestCase):
    def setUp(self):
        state=initial_state(7321)
        self.w=state['world']
        self.p=state['person']
        self.p['pos']=[15,10,0]
        self.p['items']=[]
        self.p['inventory']['alimento']=0

    def reveal(self,x,y,z=0,ch='.'):
        set_tile(self.w,x,y,z,ch)
        key=tile_key(x,y,z)
        if key not in self.w['revealed']:
            self.w['revealed'].append(key)
        return key

    def target(self,step,nav=None):
        pending={'step':step,'remaining':6,'total':10}
        if nav is not None:pending['navigation']=nav
        return active_intervention(self.w,self.p,pending)

    def test_explicit_terrain_coordinate_and_portable_inspection(self):
        self.reveal(16,10,0,'T')
        self.assertEqual(self.target({'op':'inspect','x':16,'y':10}),
                         {'x':16,'y':10,'z':0,'op':'inspect'})
        self.assertEqual(self.target({'op':'inspect','target':'árbol (16,10)'}),
                         {'x':16,'y':10,'z':0,'op':'inspect'})
        self.p['items'].append({'id':'obj-1','name':'Hacha','form':'filo',
                                'resistance':6,'hardness':6,'durability':90})
        self.assertIsNone(self.target({'op':'inspect','target':'obj-1'}))

    def test_no_unseen_offmap_or_out_of_range_coordinates(self):
        self.assertIsNone(self.target({'op':'inspect','x':30,'y':10}))
        self.assertIsNone(self.target({'op':'inspect','x':999,'y':999}))
        self.assertIsNone(self.target({'op':'inspect','x':17,'y':10})
                          if tile_key(17,10,0) not in self.w['revealed'] else
                          self.target({'op':'inspect','x':30,'y':10}))

    def test_gather_targets_resource_not_working_tile(self):
        self.reveal(16,10,0,'o')
        self.w['deposits'][tile_key(16,10,0)]=3
        marker=self.target({'op':'gather','target':'mineral oscuro'})
        self.assertEqual(marker,{'x':16,'y':10,'z':0,'op':'gather'})
        self.assertNotEqual(marker['x'],self.p['pos'][0])
        self.assertIsNone(self.target({'op':'gather','target':'mineral oscuro'},
                                      {'kind':'gather','destination':[15,10],
                                       'resource_at':[16,10],'route':[[15,10]]}))

    def test_foraging_uses_same_actual_selector(self):
        self.reveal(15,10,0,'.')
        self.reveal(15,9,0,'T')
        self.reveal(16,10,0,'T')
        self.w['forage_deposits']={tile_key(15,9,0):0,
                                   tile_key(16,10,0):2}
        source=forage_source(self.w,self.p)
        self.assertEqual(source,(16,10))
        self.assertEqual(self.target({'op':'forage'}),
                         {'x':16,'y':10,'z':0,'op':'forage'})
        self.assertIsNone(self.target({'op':'forage'}, {'kind':'go','route':[[16,10]]}))
        self.p['inventory']['alimento']=12
        self.assertIsNone(self.target({'op':'forage'}))
        self.p['inventory']['alimento']=0
        self.w['forage_deposits'][tile_key(16,10,0)]=0
        self.assertIsNone(self.target({'op':'forage'}))

    def test_excavation_requires_real_rock_and_tool(self):
        self.reveal(15,9,0,'^')
        op={'op':'excavate','x':15,'y':9}
        self.assertIsNone(self.target(op))
        tool={'id':'pick','name':'Pico','form':'punta',
              'resistance':7,'hardness':8,'durability':100}
        self.p['items']=[tool]
        self.assertEqual(self.target(op),{'x':15,'y':9,'z':0,'op':'excavate'})
        self.assertEqual(self.target({'op':'use','item':'pick','method':'excavar','x':15,'y':9}),
                         {'x':15,'y':9,'z':0,'op':'use'})
        self.assertIsNone(self.target({'op':'excavate','x':14,'y':10})
                          if self.w['levels']['0'][10][14] not in '^#o' else
                          self.target({'op':'excavate','x':40,'y':40}))

    def test_works_and_portables_have_distinct_sites(self):
        self.reveal(15,10,0,'h')
        work={'id':'obra-1','name':'Refugio','pos':[16,10,0]}
        self.w['structures']=[work]
        self.reveal(16,10,0,'.')
        self.assertEqual(self.target({'op':'modify','item':'obra-1'}),
                         {'x':16,'y':10,'z':0,'op':'modify'})
        self.assertEqual(self.target({'op':'dismantle','item':'obra-1'}),
                         {'x':16,'y':10,'z':0,'op':'dismantle'})
        self.assertIsNone(self.target({'op':'modify','item':'desconocido'}))
        self.assertIsNone(self.target({'op':'craft','name':'punta'}))
        self.assertEqual(self.target({'op':'build','name':'refugio'}),
                         {'x':15,'y':10,'z':0,'op':'build'})

    def test_no_marker_during_navigation_or_unconsciousness(self):
        self.reveal(16,10,0,'T')
        pending={'step':{'op':'inspect','x':16,'y':10},
                 'navigation':{'kind':'go','route':[[16,10]]}}
        self.assertIsNone(active_intervention(self.w,self.p,pending))
        self.assertIsNone(active_intervention(self.w,self.p,None))
        self.p['unconscious']=True
        self.assertIsNone(active_intervention(self.w,self.p,
                           {'step':{'op':'inspect','x':16,'y':10}}))

    def test_layer_requires_revealed_target(self):
        self.p['pos']=[15,10,-1]
        self.assertIsNone(self.target({'op':'inspect','x':16,'y':10}))
        self.reveal(16,10,-1,':')
        self.assertEqual(self.target({'op':'inspect','x':16,'y':10}),
                         {'x':16,'y':10,'z':-1,'op':'inspect'})


class MapClientTests(unittest.TestCase):
    def test_marker_css_and_explicit_binding(self):
        self.assertIn('.tile.intervened',HTML)
        self.assertIn('data.active_intervention',HTML)
        self.assertIn("ch!==' '",HTML)
        self.assertIn('String(ongoing.z)===activeLayer',HTML)

    def test_real_javascript_map_renders_only_visible_layer_and_tile(self):
        if not shutil.which('node'):self.skipTest('Node.js no disponible')
        src=HTML[HTML.index('function showMap(){'):HTML.index('function show(data2)')]
        runner=r"""
const vm=require('node:vm'),assert=require('node:assert');
const source=require('node:fs').readFileSync(0,'utf8');
const elements={};
const el=id=>elements[id]??=( {style:{setProperty(){}},classList:{toggle(){}},textContent:'',innerHTML:'',value:''} );
const esc=s=>String(s);
const CH={'.':['t-plain','Suelo'],' ':['t-plain','Desconocido'],'@':['t-at','Nilo']};
let data={position:[1,1,0],w:3,h:3,
 maps:{'0':['   ',' . ','   '],'-1':['...','...','...']},
 map:['   ',' . ','   '],trail_layers:{},structure_layers:{},
 active_intervention:{x:1,y:1,z:0,op:'inspect'}};
let mapLayer='follow',mapDisplay='both',view='full',showTrail=true,mapZoom={full:16,near:16};
vm.runInThisContext(source);
showMap();
assert.equal((el('map').innerHTML.match(/class="tile [^"]*intervened/g)||[]).length,1);
data.active_intervention={x:1,y:1,z:-1,op:'inspect'};showMap();
assert.equal((el('map').innerHTML.match(/class="tile [^"]*intervened/g)||[]).length,0);
mapLayer='-1';showMap();
assert.equal((el('map').innerHTML.match(/class="tile [^"]*intervened/g)||[]).length,1);
mapLayer='0';data.active_intervention={x:0,y:0,z:0,op:'inspect'};showMap();
assert.equal((el('map').innerHTML.match(/class="tile [^"]*intervened/g)||[]).length,0);
"""
        proc=subprocess.run(['node','-e',runner],input=src,text=True,capture_output=True,check=False)
        self.assertEqual(proc.returncode,0,proc.stderr)


if __name__=='__main__':
    unittest.main()
