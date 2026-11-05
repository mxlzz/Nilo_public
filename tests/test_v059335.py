"""Nilo 0.5.9.3.35: orientación espacial, trazas verificables y compatibilidad."""
import copy
import random
import unittest

from world import (new_world, set_tile, tile_key, choose_frontier,
                   exploration_frontier, prepare_navigation, advance_navigation,
                   navigation_result, execute_action, actual_travel_direction, pathfind)
from brain import normalize_decision


def setting(level=0):
    w=new_world(7321)
    for y in range(5,16):
        for x in range(10,22):
            set_tile(w,x,y,level, ':' if level==-1 else '.')
    w['revealed']=[tile_key(x,y,level) for y in range(9,12) for x in range(14,17)]
    p={'pos':[15,10,level], 'vehicle_id':None, 'clock_minutes':0,
       'inventory':{}, 'items':[]}
    return w,p


class DirectedExploration(unittest.TestCase):
    def test_unqualified_explore_preserves_frontier_and_random_state(self):
        w,p=setting()
        for seed in (1,42,873):
            a=random.Random(seed);b=random.Random(seed)
            old=choose_frontier(w,p,a)
            new,reason=exploration_frontier(w,p,b,{'op':'explore'})
            self.assertEqual(new,old)
            self.assertEqual(reason,'')
            self.assertEqual(a.getstate(),b.getstate())

    def test_each_cardinal_direction_selects_matching_frontier(self):
        for direction,check in (
                ('north',lambda x,y:y<10),
                ('south',lambda x,y:y>10),
                ('east',lambda x,y:x>15),
                ('west',lambda x,y:x<15)):
            with self.subTest(direction=direction):
                w,p=setting()
                dest,diagnostic=exploration_frontier(w,p,random.Random(20),
                    {'op':'explore','direction':direction})
                self.assertFalse(diagnostic)
                self.assertIsNotNone(dest)
                self.assertTrue(check(*dest))
                self.assertIn(tile_key(*dest,0),w['revealed'])
                route=pathfind(w,p['pos'],(*dest,0),known_only=True)
                self.assertTrue(route)
                self.assertTrue(all(tile_key(x,y,0) in w['revealed'] for x,y in route))

    def test_aliases_do_not_invert_north_and_south(self):
        for alias,expected in [('norte','north'),('sur','south'),('este','east'),('oeste','west')]:
            w,p=setting()
            a,_=exploration_frontier(w,p,random.Random(99),
                {'op':'explore','direction':alias})
            b,_=exploration_frontier(w,p,random.Random(99),
                {'op':'explore','direction':expected})
            self.assertEqual(a,b)
        self.assertEqual(actual_travel_direction([15,10],[15,8]),'norte')
        self.assertEqual(actual_travel_direction([15,10],[15,12]),'sur')
        self.assertEqual(actual_travel_direction([15,10],[17,8]),'norte-este')
        self.assertEqual(actual_travel_direction([15,10],[15,10]),'sin desplazamiento')

    def test_missing_sector_never_changes_to_the_opposite_side(self):
        w,p=setting()
        for x in range(14,17):set_tile(w,x,9,0,'^')
        goal,reason=exploration_frontier(w,p,random.Random(3),
                                        {'op':'explore','direction':'north'})
        self.assertIsNone(goal)
        self.assertIn('norte',reason)
        self.assertIn('opuesto',reason)
        self.assertIsNone(prepare_navigation(w,p,{'op':'explore','direction':'north'},random.Random(3)))
        _,facts,success,_=execute_action(w,p,{'op':'explore','direction':'north'},random.Random(3))
        self.assertFalse(success)
        self.assertIn('norte',facts[0])
        self.assertEqual(p['pos'],[15,10,0])

    def test_unknown_region_is_rejected_without_revealing_anything(self):
        w,p=setting();old=copy.deepcopy(w['revealed']);position=p['pos'][:]
        goal,reason=exploration_frontier(w,p,random.Random(4),
                              {'op':'explore','region':{'x':22,'y':12}})
        self.assertIsNone(goal);self.assertIn('No conozco',reason)
        _,facts,success,_=execute_action(w,p,
            {'op':'explore','region':{'x':22,'y':12}},random.Random(4))
        self.assertFalse(success);self.assertIn('No conozco',facts[0])
        self.assertEqual(w['revealed'],old)
        self.assertEqual(p['pos'],position)

    def test_region_is_known_anchor_not_hidden_destination(self):
        w,p=setting()
        goal,reason=exploration_frontier(w,p,random.Random(7),
                       {'op':'explore','region':{'x':14,'y':9},'direction':'east'})
        self.assertFalse(reason)
        self.assertGreater(goal[0],14)
        self.assertIn(tile_key(*goal,0),w['revealed'])
        self.assertNotEqual(goal,(14,9))
        self.assertFalse(any(tile_key(x,y,0) not in w['revealed']
                             for x,y in pathfind(w,p['pos'],(*goal,0),known_only=True)))

    def test_navigation_reports_actual_direction_and_discoveries(self):
        w,p=setting()
        step={'op':'explore','direction':'north'}
        nav=prepare_navigation(w,p,step,random.Random(8))
        self.assertIsNotNone(nav)
        self.assertEqual(nav['origin'],[15,10])
        self.assertEqual(nav['requested_direction'],'north')
        self.assertTrue(all(tile_key(x,y,0) in w['revealed'] for x,y in nav['route']))
        steps=len(nav['route'])
        advance_navigation(w,p,nav,steps)
        facts,success,_=navigation_result(nav,p)
        self.assertTrue(success)
        line=' '.join(facts)
        self.assertIn('sector solicitado: norte',line)
        self.assertIn('dirección neta real: norte',line)
        self.assertIn('frontera elegida:',line)
        self.assertIn('casillas nuevas observadas:',line)
        self.assertEqual(nav['walked'],steps)
        self.assertEqual(p['pos'][1],9)
        self.assertGreater(len(nav['discovered']),0)

    def test_explore_generic_report_does_not_invent_an_intention(self):
        w,p=setting()
        nav=prepare_navigation(w,p,{'op':'explore'},random.Random(14))
        self.assertIsNotNone(nav)
        self.assertNotIn('requested_direction',nav)
        advance_navigation(w,p,nav,len(nav['route']))
        facts,_,_=navigation_result(nav,p)
        self.assertNotIn('sector solicitado',' '.join(facts))

    def test_underground_uses_same_cardinals_and_known_only(self):
        w,p=setting(-1)
        goal,reason=exploration_frontier(w,p,random.Random(14),
                                      {'op':'explore','direction':'north'})
        self.assertEqual(reason,'')
        self.assertEqual(goal[1],9)
        route=pathfind(w,p['pos'],(*goal,-1),known_only=True)
        self.assertTrue(route)
        self.assertTrue(all(tile_key(x,y,-1) in w['revealed'] for x,y in route))

    def test_legacy_pending_navigation_remains_readable(self):
        w,p=setting()
        legacy=prepare_navigation(w,p,{'op':'explore'},random.Random(34))
        self.assertIsNotNone(legacy)
        legacy.pop('origin',None)
        advance_navigation(w,p,legacy,len(legacy['route']))
        facts,success,_=navigation_result(legacy,p)
        self.assertTrue(success)
        self.assertTrue(facts[0].startswith('Recorrí'))


    def test_guided_exploration_uses_stable_rng_across_copies(self):
        w,p=setting()
        a=copy.deepcopy(w);b=copy.deepcopy(w)
        for step in ({'op':'explore','direction':'east'},
                     {'op':'explore','region':{'x':14,'y':9},'direction':'south'}):
            ra=random.Random(491);rb=random.Random(491)
            self.assertEqual(exploration_frontier(a,p,ra,step),
                             exploration_frontier(b,p,rb,step))
            self.assertEqual(ra.getstate(),rb.getstate())

    def test_decision_normalization_preserves_intention(self):
        result=normalize_decision({
            'cuaderno':'Quiero explorar hacia el norte.',
            'accion_proyecto':'sin_proyecto',
            'plan':[{'op':'explore','direction':'norte',
                     'region':{'x':'14','y':'9'}}]})
        self.assertEqual(result['plan'][0]['direction'],'north')
        self.assertEqual(result['plan'][0]['region'],{'x':14,'y':9})
        bad=normalize_decision({'cuaderno':'Decidí probar un rumbo.',
            'accion_proyecto':'sin_proyecto',
            'plan':[{'op':'explore','direction':'arriba'}]})
        self.assertEqual(bad['plan'][0]['direction'],'arriba')  # diagnóstico físico, no fallback ciego


if __name__=='__main__':unittest.main()
