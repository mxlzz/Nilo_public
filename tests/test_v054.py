"""Nilo 05.4: auditoría de posibles inconsistencias y lectura automática."""
from __future__ import annotations
from ui_fixture import legacy_markup, legacy_html_path
import json, sqlite3, tempfile, unittest
from pathlib import Path
import nilo
from inventions import (ensure_records, submit_debug_report, review_proposal, record_action_outcome)
from brain import normalize_decision, context_for

ROOT=Path(__file__).resolve().parent.parent

def candidate(**changes):
    return dict(op='report_issue',title='No encuentro una orilla accesible',
                expected='Poder llegar a tierra adyacente al agua conocida',
                observed='Un desplazamiento no llegó hasta la orilla',
                rationale='Las rutas conocidas parecen atravesables',**changes)

class DebugProposalTests(unittest.TestCase):
    def setUp(self):
        self.p=nilo.initial_state()['person'];ensure_records(self.p)
        self.one=record_action_outcome(self.p,dict(op='go',x=14,y=0),False,
                                       ['No pude transitar el destino: agua.'],'Día 2 · 11:00',[15,4,0])
    def test_report_is_suspicion_and_contains_only_engine_evidence(self):
        ok,info=submit_debug_report(self.p,candidate(evidence_ids=[self.one['id'],'act-falso']), 'Día 2 · 11:30')
        self.assertTrue(ok,info)
        report=self.p['proposals'][0]
        self.assertEqual(report['type'],'debug')
        self.assertEqual(report['status'],'pendiente')
        self.assertEqual([r['id'] for r in report['evidence']],[self.one['id']])
        self.assertFalse(report['evidence'][0]['success'])
        self.assertIn('solicitud',info)
    def test_automatic_failure_evidence_is_real(self):
        ok,_=submit_debug_report(self.p,candidate(related_action='go'),'Día 2')
        self.assertTrue(ok)
        self.assertEqual(self.p['proposals'][0]['evidence'][0]['id'],self.one['id'])
    def test_missing_evidence_is_declared_not_fabricated(self):
        self.p['action_outcomes'].clear()
        ok,info=submit_debug_report(self.p,candidate(evidence_ids=['act-falso']),'Día 2')
        self.assertTrue(ok)
        self.assertFalse(self.p['proposals'][0]['evidence'])
        self.assertIn('sin acciones comprobables',info)
    def test_duplicate_pending_report_is_blocked(self):
        submit_debug_report(self.p,candidate(),'Día 2')
        ok,_=submit_debug_report(self.p,candidate(),'Día 3')
        self.assertFalse(ok)
    def test_can_supply_evidence_after_request_for_more(self):
        ok,_=submit_debug_report(self.p,candidate(),'Día 2')
        report=self.p['proposals'][0]
        review_proposal(self.p,report['id'],'ampliar','Necesito otros ensayos','Día 3')
        ok,_=submit_debug_report(self.p,candidate(),'Día 4')
        self.assertFalse(ok)  # No alcanza con repetir lo mismo.
        different=candidate();different['observed']='Falló nuevamente desde otra casilla'
        ok,_=submit_debug_report(self.p,different,'Día 5')
        self.assertTrue(ok)
        self.assertEqual(report['status'],'pendiente')
        self.assertEqual(report['review_history'][0]['reason'],'Necesito otros ensayos')
        self.assertEqual(len(self.p['proposals']),1)
    def test_no_empty_or_unfounded_report(self):
        for field in ('title','expected','observed','rationale'):
            invalid=candidate();invalid[field]=''
            ok,_=submit_debug_report(self.p,invalid,'Día 2')
            self.assertFalse(ok,field)
    def test_each_human_classification_without_silent_fix(self):
        for choice,status in [('bug','error_confirmado_pendiente_de_correccion'),
                              ('limite','limitacion_valida'),('capacidad','capacidad_no_implementada'),
                              ('interpretacion','interpretacion_equivocada'),('ampliar','requiere_ampliacion')]:
            p=nilo.initial_state()['person']
            submit_debug_report(p,candidate(),'Día 2')
            reviewed=review_proposal(p,p['proposals'][0]['id'],choice,'Porque observé X','Día 3')
            self.assertEqual(reviewed['status'],status)
            self.assertEqual(reviewed['review']['reason'],'Porque observé X')
            with self.assertRaises(ValueError):review_proposal(p,p['proposals'][0]['id'],'bug','otra','Día 4')
    def test_does_not_erase_physics_proposals(self):
        from inventions import submit_proposal
        ok,_=submit_proposal(self.p,dict(phenomenon='presión',missing_capability='presión de vapor',
                  rationale='Quiero probar si aparece fuerza',experiment='Cerrar recipiente',context='estudio'), 'Día 1',())
        self.assertTrue(ok)
        self.assertEqual(self.p['proposals'][0]['type'],'physics')
        reviewed=review_proposal(self.p,self.p['proposals'][0]['id'],'aprobar','Estudiar','Día 2')
        self.assertEqual(reviewed['status'],'aceptada_pendiente_de_motor')
        with self.assertRaises(ValueError):review_proposal(self.p,'id-inexistente','bug','X','Día 3')
    def test_context_contains_outcomes_and_review_for_nilo(self):
        submit_debug_report(self.p,candidate(evidence_ids=[self.one['id']]),'Día 2')
        review_proposal(self.p,self.p['proposals'][0]['id'],'interpretacion','El agua no es transitable','Día 3')
        s=nilo.initial_state();s['person']=self.p
        context=context_for(s['world'],self.p,[],'Día 3')
        self.assertEqual(context['resultados_de_acciones'][-1]['id'],self.one['id'])
        self.assertEqual(context['propuestas_pendientes'][-1]['review']['reason'],'El agua no es transitable')
    def test_new_op_is_accepted(self):
        normalized=normalize_decision(dict(cuaderno='Tengo una duda',plan=[candidate()]))
        self.assertEqual(normalized['plan'][0]['op'],'report_issue')
    def test_simulation_path_persists_debug_report_and_review(self):
        with tempfile.TemporaryDirectory() as temp:
            old=nilo.DB;nilo.DB=Path(temp)/'nilo.sqlite3'
            try:
                sim=nilo.Simulation();sim.think=lambda:None
                sim.s['speed']=60
                p=sim.s['person']
                outcome=record_action_outcome(p,dict(op='go',target='agua'),False,['No se pudo alcanzar orilla'],'Día 1',[15,10,0])
                p['plan']=[candidate(evidence_ids=[outcome['id']])]
                sim.tick(1)    # inicia acción
                sim.tick(20)   # adelanta la acción
                sim.tick(20)   # completa
                proposals=sim.s['person']['proposals']
                self.assertEqual(len(proposals),1)
                self.assertEqual(proposals[0]['evidence'][0]['id'],outcome['id'])
                sim.write()
                self.assertEqual(sim.archive.counts()['proposal'],1)
                self.assertEqual(sim.archive.counts()['diagnostic'],1)
                response=sim.review_rule(proposals[0]['id'],'limite','No entrar al agua; sí a la orilla')
                self.assertEqual(response['status'],'limitacion_valida')
                saved=sim.conn.execute('SELECT payload FROM snapshot WHERE id=1').fetchone()[0]
                self.assertEqual(json.loads(saved)['person']['proposals'][0]['review']['reason'],
                                 'No entrar al agua; sí a la orilla')
                sim.conn.close()
            finally:nilo.DB=old
    def test_read_markers_remain_monotonic_and_dont_delete_records(self):
        with tempfile.TemporaryDirectory() as temp:
            old=nilo.DB;nilo.DB=Path(temp)/'nilo.sqlite3'
            try:
                sim=nilo.Simulation()
                for idx in range(3):
                    sim.archive.add('news',dict(id=f'n{idx}',when='Día 1',title=f'Noticia {idx}'))
                sim.conn.commit()
                sim.mark_read('news','n1')
                self.assertEqual(sim.archive.count_unread('news'),1)
                sim.mark_read('news','n0')
                self.assertEqual(sim.archive.count_unread('news'),1)
                self.assertEqual(sim.archive.counts()['news'],3)
                sim.conn.close()
            finally:nilo.DB=old
    def test_read_exactly_one_item_does_not_mark_other_news(self):
        with tempfile.TemporaryDirectory() as temp:
            old=nilo.DB;nilo.DB=Path(temp)/'nilo.sqlite3'
            try:
                sim=nilo.Simulation()
                for idx in range(3):
                    item=dict(id=f'z{idx}',when='Día 1',title=f'Noticia {idx}')
                    sim.s['news'].append(item);sim.archive.add('news',item)
                sim.write()
                sim.mark_one_read('news','z2')
                self.assertEqual(sim.archive.count_unread('news'),2)
                self.assertEqual(sim.archive.position('news'),0)
                states={n['id']:n['read'] for n in sim.public_state()['news']}
                self.assertEqual(states,{'z0':False,'z1':False,'z2':True})
                self.assertEqual([e['id'] for e in sim.archive.unread('news')],['z0','z1'])
                self.assertEqual(sim.catchup()['total'],2)
                sim.mark_all_read(['news'])
                self.assertEqual(sim.archive.count_unread('news'),0)
                sim.conn.close()
            finally:nilo.DB=old
    def test_browser_auto_read_is_wired_to_card_click(self):
        html=legacy_markup(Path(__file__).resolve().parents[1])
        self.assertIn("el('feed').addEventListener('click',async ev=>",html)
        self.assertIn("if(tab==='notes'||(tab==='activity'&&card.dataset.entryId)",html)
        self.assertIn("markRead(tab==='notes'?'journal':'news',id,true)",html)
        self.assertIn('restoreFeedExpandedDetails(expanded)',html)
        self.assertIn('renderedFeedTab===tab?feedExpandedDetails():new Set()',html)

if __name__=='__main__':unittest.main()

class HttpEndpointsTests(unittest.TestCase):
    def test_review_and_read_over_http(self):
        import threading, urllib.request
        from http.server import ThreadingHTTPServer
        with tempfile.TemporaryDirectory() as tmp:
            previous=nilo.DB;nilo.DB=Path(tmp)/'database.sqlite3'
            sim=nilo.Simulation();nilo.Handler.sim=sim
            issue=candidate()
            ok,_=submit_debug_report(sim.s['person'],issue,sim.stamp())
            self.assertTrue(ok)
            entry=dict(id='evt-1',when='Día 1',title='Hallazgo',detail='Una explicación adicional')
            sim.s['news'].append(entry);sim.write()
            server=ThreadingHTTPServer(('127.0.0.1',0),nilo.Handler)
            worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
            base=f'http://127.0.0.1:{server.server_port}'
            def post(path,payload):
                req=urllib.request.Request(base+path,json.dumps(payload).encode('utf-8'),
                     {'Content-Type':'application/json'},method='POST')
                with urllib.request.urlopen(req,timeout=3) as response:
                    return json.loads(response.read())
            try:
                with urllib.request.urlopen(base+'/api/state',timeout=3) as response:
                    state=json.loads(response.read())
                self.assertEqual(state['proposals'][0]['type'],'debug')
                res=post('/api/review-rule',{'id':state['proposals'][0]['id'],
                         'decision':'interpretacion','reason':'No era un error del motor'})
                self.assertEqual(res['status'],'interpretacion_equivocada')
                post('/api/read',{'category':'news','id':'evt-1'})
                self.assertEqual(sim.archive.count_unread('news'),0)
            finally:
                server.shutdown();server.server_close();sim.conn.close();nilo.DB=previous
