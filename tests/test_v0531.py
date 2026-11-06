"""Nilo 05.3.1: orillas, diagnósticos y novedades sin repetición."""
from __future__ import annotations
from ui_fixture import legacy_markup, legacy_html_path
import json, random, sqlite3, tempfile, unittest, subprocess, re
from pathlib import Path
import nilo
from brain import context_for, normalize_decision
from world import (new_world, reveal, resolve_go, reachable_shores, tile, tile_key,
                   pathfind, execute_action, prepare_navigation, advance_navigation,
                   navigation_result, DIRS, set_tile)

ROOT=Path(__file__).resolve().parent.parent


class ShoreRoutingTests(unittest.TestCase):
    def setUp(self):
        self.w=new_world();self.p=nilo.initial_state()['person'];self.p['pos']=[15,10,0]

    def show_shore(self):
        # El escenario positivo supone que Nilo ya conocía el recorrido a la orilla.
        route=pathfind(self.w,tuple(self.p['pos']),(15,1,0))
        for x,y in route:reveal(self.w,x,y,0,1)
        reveal(self.w,15,0,0,2)
        self.assertIn(tile_key(15,0,0),self.w['revealed'])
        return (15,0)

    def test_initial_does_not_claim_to_know_distant_water(self):
        dest,water,reason=resolve_go(self.w,self.p,{'op':'go','target':'agua'})
        self.assertIsNone(dest)
        self.assertIn('No tengo localizada',reason)

    def test_known_water_maps_to_reachable_land_without_boat(self):
        self.show_shore()
        dest,water,reason=resolve_go(self.w,self.p,{'op':'go','x':15,'y':0})
        self.assertEqual(dest,(15,1));self.assertEqual(water,(15,0));self.assertFalse(reason)
        route=pathfind(self.w,tuple(self.p['pos']),(dest[0],dest[1],0))
        self.assertEqual(len(route),9)
        self.assertTrue(all(tile(self.w,x,y,0)!='~' for x,y in route))

    def test_named_water_navigation_moves_gradually_and_allows_drinking(self):
        self.show_shore()
        step={'op':'go','target':'agua'}
        decision=normalize_decision({'cuaderno':'Buscaré la orilla','plan':[step]})
        self.assertEqual(decision['plan'][0],step)
        nav=prepare_navigation(self.w,self.p,step,random.Random(1))
        self.assertEqual(nav['destination'],[15,1]);self.assertEqual(nav['water_at'],[15,0])
        advance_navigation(self.w,self.p,nav,len(nav['route']))
        self.assertEqual(self.p['pos'],[15,1,0])
        result=navigation_result(nav,self.p)
        self.assertTrue(result[1]);self.assertIn('orilla',result[0][0])
        _,facts,ok,_=execute_action(self.w,self.p,{'op':'drink'},random.Random(1))
        self.assertTrue(ok);self.assertIn('Bebí',facts[0])

    def test_explicit_water_coords_not_rejected_by_planner(self):
        self.show_shore()
        with tempfile.TemporaryDirectory() as tmp:
            old=nilo.DB;nilo.DB=Path(tmp)/'world.sqlite3'
            try:
                sim=nilo.Simulation()
                sim.s['world']=self.w;sim.s['person']=self.p
                validated=sim.validate_plan([{'op':'go','x':15,'y':0},{'op':'drink'}])
                self.assertEqual(len(validated),2)
                sim.conn.close()
            finally:nilo.DB=old

    def test_exact_message_if_water_without_accessible_shore(self):
        self.show_shore()
        for dx,dy in DIRS:
            x,y=15+dx,0+dy
            if 0<=x<37 and 0<=y<21:set_tile(self.w,x,y,0,'^')
        _,_,reason=resolve_go(self.w,self.p,{'op':'go','x':15,'y':0})
        self.assertIn('agua',reason)
        self.assertIn('orilla conocida',reason)
        self.assertNotIn('arena',reason)

    def test_rock_diagnostic_names_actual_obstacle_not_hypothetical(self):
        self.show_shore()
        self.assertEqual(tile(self.w,0,3,0),'^')
        reveal(self.w,0,3,0,1)
        _,_,reason=resolve_go(self.w,self.p,{'op':'go','x':0,'y':3})
        self.assertIn('roca',reason)
        self.assertNotIn('arboleda',reason)

    def test_known_land_route_is_unchanged(self):
        dest,water,reason=resolve_go(self.w,self.p,{'op':'go','x':15,'y':11})
        self.assertEqual(dest,(15,11));self.assertIsNone(water);self.assertFalse(reason)

    def test_already_at_shore_reports_it_without_fictitious_travel(self):
        self.show_shore();self.p['pos']=[15,1,0]
        _,facts,ok,_=execute_action(self.w,self.p,{'op':'go','target':'agua'},random.Random(1))
        self.assertTrue(ok);self.assertIn('Ya estoy en la orilla',facts[0])

    def test_new_obstacle_during_travel_reports_the_exact_terrain(self):
        self.show_shore()
        nav=prepare_navigation(self.w,self.p,{'op':'go','target':'agua'},random.Random(1))
        next_x,next_y=nav['route'][0]
        set_tile(self.w,next_x,next_y,0,'^')
        advance_navigation(self.w,self.p,nav,1)
        self.assertTrue(nav['blocked'])
        facts,success,_=navigation_result(nav,self.p)
        self.assertFalse(success)
        self.assertIn('roca',facts[-1])
        self.assertNotIn('inesperado',facts[-1])

    def test_can_still_navigate_in_water_with_vehicle(self):
        self.show_shore();self.p['vehicle_id']='barca-verificada'
        dest,water,reason=resolve_go(self.w,self.p,{'op':'go','x':15,'y':0})
        self.assertEqual(dest,(15,0));self.assertIsNone(water);self.assertFalse(reason)

    def test_context_tells_model_where_the_reachable_shore_is(self):
        self.show_shore()
        c=context_for(self.w,self.p,[],'Día 1')
        self.assertEqual(c['orillas_agua_conocidas_alcanzables'][0]['orilla'],[15,1])


class NewsTests(unittest.TestCase):
    def test_new_news_does_not_repeat_title_inside_detail(self):
        with tempfile.TemporaryDirectory() as tmp:
            old=nilo.DB;nilo.DB=Path(tmp)/'world.sqlite3'
            try:
                sim=nilo.Simulation()
                sim.event(['Construí un refugio temporal.','La cubierta todavía no fue probada.'],'resultado',True)
                note=sim.s['news'][-1]
                self.assertEqual(note['title'],'Construí un refugio temporal.')
                self.assertEqual(note['detail'],'La cubierta todavía no fue probada.')
                sim.event(['Construí una estructura de piedra.'],'resultado',True)
                self.assertEqual(sim.s['news'][-1]['detail'],'')
                sim.conn.close()
            finally:nilo.DB=old

    def test_legacy_news_extra_does_not_repeat_title_in_browser(self):
        html=legacy_markup(Path(__file__).resolve().parents[1])
        code=html.split('function newsExtra(n){',1)[1].split('function drawFeed(){',1)[0]
        script=('function newsExtra(n){'+code+
                '\nlet data={read_positions:{news:0},news:[{id:"old1",seq:1,kind:"resultado",when:"Día 2",title:"Construí un refugio.",detail:"Construí un refugio. Tiene una cubierta inclinada."},{id:"old2",seq:2,kind:"resultado",when:"Día 3",title:"Llené un recipiente.",detail:"Llené un recipiente."}]};'
                '\nfunction esc(v){return String(v)};'
                '\nconsole.log(JSON.stringify({a:newsExtra(data.news[0]),b:newsExtra(data.news[1]),html:renderNews()}));')
        proc=subprocess.run(['node','-e',script],text=True,capture_output=True,check=True)
        data=json.loads(proc.stdout)
        self.assertEqual(data['a'],'Tiene una cubierta inclinada.')
        self.assertEqual(data['b'],'')
        self.assertEqual(data['html'].count('news-more'),1)
        self.assertIn('article class="news-entry',data['html'])

if __name__=='__main__':unittest.main()
