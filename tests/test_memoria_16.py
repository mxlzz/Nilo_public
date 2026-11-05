"""Nilo 0.7 etapa 16: memoria, hipótesis y procedencia verificable."""
from __future__ import annotations

import copy
import json
import unittest

from brain import context_for, build_deliberation_request
from nilo import initial_state
from auditar_contexto_llm import extract_sent_context, PROVIDERS
from episodic_memory import recall_relevant
from cognition import register_research, consolidate_research
from research_cycle import normalize_prediction, recent_predictions
from experiment_log import observational_conclusion
from laboratory import compare
from nilo_runtime.cognition import memory, research, evidence, predictions, topics
from nilo_runtime.agent.budget import compact_context


def experience(rid="exp-uno",action_id="act-uno",measurement_id=None):
    row={"id":rid,"action":"descend","successful":True,
         "fact":"Bajé al subsuelo y observé un pasaje.",
         "when":"Día 1","position_at_end":[10,11,0]}
    if action_id:row["action_id"]=action_id
    if measurement_id:row["measurement_id"]=measurement_id
    return row


def person():
    return {"pos":[10,10,0],"project":{"id":"p1","title":"Investigar la madera",
                 "reason":"Entender el material","state":"Continuar"},
            "research":[],"measurements":[],"conclusions":[],
            "action_outcomes":[],"life_history":[],"prediction_log":[],
            "active_research":None}


def world(revealed=()):
    return {"sites":{"cueva":{"x":10,"y":11,"z":0}},
            "revealed":list(revealed)}


def measurement(rid="med-a",op="experiment",status="comprobado",facts=None):
    return {"id":rid,"op":op,"evaluation_status":status,
            "verified_facts":facts if facts is not None else ["Observé un cambio físico."],
            "success":status=="comprobado"}


class Memory16(unittest.TestCase):
    def test_hidden_site_does_not_retrieve_a_transition_by_proximity(self):
        p=person()
        p["project"]=None
        p["life_history"]=[experience()]
        self.assertEqual(recall_relevant(p,world(),limit=6),[])
        shown=recall_relevant(p,world(["10,11,0"]),limit=6)
        self.assertEqual(len(shown),1)
        self.assertIn("transicion_cercana_registrada",shown[0]["criterios_recuperacion"])

    def test_unknown_terrain_does_not_affect_read(self):
        p=person()
        p["project"]=None
        p["life_history"]=[experience()]
        w=world()
        before=copy.deepcopy((p,w))
        for _ in range(4):
            self.assertEqual(recall_relevant(p,w,limit=6),[])
        self.assertEqual((p,w),before)

    def test_distinct_verified_actions_not_collapsed_by_equal_fact(self):
        p=person()
        p["project"]={"id":"p1","title":"Explorar cueva"}
        p["life_history"]=[
            {**experience(rid="exp-1",action_id="act-1"),"project_id":"p1"},
            {**experience(rid="exp-2",action_id="act-2"),"project_id":"p1"}]
        selected=recall_relevant(p,world(["10,11,0"]))
        self.assertEqual(len(selected),2)
        self.assertEqual({r["accion_id"] for r in selected},{"act-1","act-2"})

    def test_links_are_resolved_by_id_not_by_story(self):
        p=person()
        p["life_history"]=[{**experience(measurement_id="med-a"),
                             "project_id":"p1"}]
        p["measurements"]=[measurement()]
        selected=recall_relevant(p,world(["10,11,0"]))
        self.assertEqual(selected[0]["fuente_medicion"]["trazabilidad"],
                         "registro_disponible")
        self.assertEqual(selected[0]["fuente_medicion"]["tipo"],"medicion")
        p["measurements"]=[]
        expired=recall_relevant(p,world(["10,11,0"]))
        self.assertEqual(expired[0]["fuente_medicion"]["trazabilidad"],
                         "fuera_de_memoria_activa")
        self.assertNotIn("ensayo_fisico",expired[0]["fuente_medicion"])

    def test_legacy_memory_is_labeled_without_evidence_fabrication(self):
        p=person()
        p["project"]["title"]="Explorar cueva"
        p["life_history"]=[experience(action_id=None)]
        row=recall_relevant(p,world(["10,11,0"]))[0]
        self.assertEqual(row["procedencia"],"registro_biografico_legacy")
        self.assertNotIn("fuente_medicion",row)


class Research16(unittest.TestCase):
    def test_revised_hypothesis_preserves_prior_belief(self):
        p={"research":[],"conclusions":[],"project":{"id":"p1"}}
        first,new=register_research(p,"¿Qué dureza tiene la roca?",
                                    "La roca es dura","Día 1",lambda:"r1")
        self.assertTrue(new)
        second,new=register_research(p,"¿Qué dureza tiene la roca?",
                                     "La roca es blanda","Día 2",lambda:"r2")
        self.assertFalse(new)
        self.assertIs(first,second)
        self.assertEqual(first["hypothesis"],"La roca es blanda")
        self.assertEqual([x["hypothesis"] for x in first["hypothesis_history"]],
                         ["La roca es dura","La roca es blanda"])
        self.assertTrue(all(x["kind"]=="belief" for x in first["hypothesis_history"]))
        self.assertEqual(first["evidence"],[])
        self.assertEqual(len(p["research"]),1)

    def test_unchanged_hypothesis_does_not_duplicate_history(self):
        p={"research":[],"conclusions":[]}
        first,_=register_research(p,"Estudiar el mineral oscuro",
                                  "Es resistente","Día 1",lambda:"r1")
        register_research(p,"Estudiar el mineral oscuro","Es resistente",
                          "Día 2",lambda:"r2")
        self.assertNotIn("hypothesis_history",first)

    def test_integrated_research_preserves_source_of_legacy_notes(self):
        old={"id":"r1","question":"Estudiar la dureza de la roca",
             "hypothesis":"Es dura","state":"abierta","evidence":[]}
        proof={"when":"Día 1","facts":["Una roca parecía dura"]}
        newer={"id":"r2","question":"Estudiar la dureza de la roca",
               "hypothesis":"Es blanda","state":"abierta",
               "evidence":[copy.deepcopy(proof)]}
        p={"research":[old,newer],"active_research":None}
        self.assertEqual(consolidate_research(p),1)
        merged=old["evidence"][0]
        self.assertEqual(merged["source_research_id"],"r2")
        self.assertEqual(merged["evidence_kind"],"registro_legacy_no_verificado")
        self.assertNotIn("source_research_id",newer["evidence"][0])
        self.assertEqual(newer["state"],"integrada")

    def test_concept_of_same_research_does_not_prove_experiment(self):
        p={"research":[{"id":"r1","question":"Probar la madera",
                         "hypothesis":"Resiste cargas","state":"concluida",
                         "evidence_ids":["med-a"]}],
           "measurements":[]}
        row=evidence.projected_research(p)[0]
        self.assertEqual(row["naturaleza"],
                         "investigacion_cerrada_con_referencias_historicas")
        self.assertEqual(row["fuentes_de_evidencia"][0]["trazabilidad"],
                         "fuera_de_memoria_activa")


class Evidence16(unittest.TestCase):
    def test_exact_id_required_and_numeric_references_do_not_validate(self):
        p={"measurements":[measurement()]}
        self.assertEqual(evidence.reference(p,"med-a",expected="medicion")["trazabilidad"],
                         "registro_disponible")
        self.assertEqual(evidence.reference(p,"med-inventado",expected="medicion")["trazabilidad"],
                         "fuera_de_memoria_activa")
        self.assertIsNone(evidence.measured_records(p,["med-a","med-a"]))
        self.assertIsNone(evidence.measured_records(p,[{"id":"med-a"}]))
        self.assertIsNone(evidence.measured_records(p,["med-inventado"]))

    def test_administrative_events_are_not_independent_measurements(self):
        p={"measurements":[measurement("med-1","design"),
                            measurement("med-2","compare")]}
        self.assertIsNone(evidence.measured_records(p,["med-1"]))
        self.assertIsNone(evidence.measured_records(p,["med-1","med-2"]))
        ok,message,conclusion=compare(p,{"op":"compare",
            "evidence_ids":["med-1","med-2"],"metric":"resistencia"},"Día 3")
        self.assertFalse(ok)
        self.assertIsNone(conclusion)

    def test_conclusion_distinguishes_observation_and_missing_evidence(self):
        p={"measurements":[measurement("med-a")],
           "conclusions":[{"id":"con-1","status":"observacion_comprobada",
                           "evidence_ids":["med-a"],"text":"Vi un efecto."},
                          {"id":"con-2","status":"comparacion_medida",
                           "evidence_ids":["med-perdida"],"text":"Antes comparé."}]}
        rows=evidence.projected_conclusions(p)
        self.assertEqual(rows[0]["naturaleza"],"observacion")
        self.assertEqual(rows[0]["trazabilidad"],"ensayos_disponibles")
        self.assertEqual(rows[1]["naturaleza"],"comparacion_descriptiva")
        self.assertEqual(rows[1]["trazabilidad"],
                         "referencias_historicas_no_disponibles")

    def test_no_evaluable_conclusion_does_not_prove_hypothesis(self):
        p={"measurements":[measurement("med-sin","experiment",
                         "no_evaluable",["El método no tiene modelo físico."])],
           "conclusions":[]}
        ok,statement,entry=observational_conclusion(
            p,{"topic":"Fenómeno térmico","evidence_ids":["med-sin"]},"Día 2")
        self.assertTrue(ok,statement)
        self.assertEqual(entry["status"],"observacion_no_evaluable")
        self.assertIn("no constituye verificación",entry["scope"])
        projected=evidence.projected_conclusions(p)
        self.assertEqual(projected[-1]["naturaleza"],"limite_del_modelo")

    def test_observation_rejects_wrong_id_and_derived_records(self):
        p={"measurements":[measurement("med-uno","design")],"conclusions":[]}
        for ids in (["med-uno"],["med-inventado"],[{"id":"med-uno"}]):
            with self.subTest(ids=ids):
                ok,_,conclusion=observational_conclusion(
                    p,{"topic":"Material","evidence_ids":ids},"Día 2")
                self.assertFalse(ok)
                self.assertIsNone(conclusion)


class Context16(unittest.TestCase):
    def test_active_research_is_not_lost_in_provider_budget(self):
        s=initial_state(world_seed=7321)
        p=s["person"]
        p["research"]=[{"id":"r-abierta","question":"¿Cómo resiste la madera?",
                        "hypothesis":"La madera soporta una carga",
                        "state":"abierta","evidence":[]}]
        raw=context_for(s["world"],p,[],"Día 2")
        before=copy.deepcopy(raw)
        for provider,cfg in PROVIDERS.items():
            with self.subTest(provider=provider):
                _,payload,_=build_deliberation_request(cfg,raw)
                actual=extract_sent_context(provider,payload)
                self.assertIn("investigaciones_activas",actual)
                self.assertEqual(actual["investigaciones_activas"][0]["id"],
                                 "r-abierta")
                self.assertEqual(actual["investigaciones_activas"][0]["hypothesis"],
                                 "La madera soporta una carga")
                self.assertNotIn("predisposiciones",actual)
        self.assertEqual(raw,before)

    def test_legacy_prompt_uses_new_factual_rest_distinction(self):
        s=initial_state(world_seed=7321)
        p=s["person"]
        p["project"]={"id":"p-descanso","title":"Investigar recuperación de energía",
                      "reason":"Medir descansos", "state":"En curso"}
        raw=context_for(s["world"],p,[],"Día 2")
        text=raw["condiciones_de_ensayo_descanso"]["aclaracion"]
        self.assertIn("wait",text)
        self.assertIn("sin recuperación de sueño",text)
        self.assertNotIn("la espera pueden recuperar",text)


if __name__=="__main__":
    unittest.main()
