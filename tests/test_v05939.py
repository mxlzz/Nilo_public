from ui_fixture import legacy_markup, legacy_html_path
"""Regresiones de la serie 0.5.9.3.9 (sin API externa)."""
import unittest
from pathlib import Path
import tempfile
from unittest.mock import patch

import nilo
from diagnostic_guidance import review_recent_attempts
from observer import pending_sources
from archive import History
from review_store import ReviewStore
import sqlite3


class DiagnosticsTests(unittest.TestCase):
    def test_repetitions_grouped_without_reclassifying_failure_as_missing_physics(self):
        p={"action_outcomes":[
            {"id":"act-1","op":"use","target":"recipiente","evaluation_status":"verified_failure","facts":["No contiene agua"]},
            {"id":"act-2","op":"use","target":"recipiente","evaluation_status":"verified_failure","facts":["No contiene agua"]},
            {"id":"act-3","op":"use","target":"vapor","evaluation_status":"no_evaluable","unmodeled_attempt_id":"unm-1","facts":["No evaluable"]},
            {"id":"act-4","op":"go","target":"(40,40)","evaluation_status":"verified_failure","contract_status":"uso_incorrecto","contract_code":"fuera_de_rango","facts":["Fuera de rango"]}]}
        rows=review_recent_attempts(p)
        self.assertEqual([r["clasificacion"] for r in rows],
                         ["fallo_fisico","fenomeno_no_evaluable","uso_incorrecto"])
        self.assertEqual(rows[0]["repeticiones"],2)
        self.assertEqual(rows[0]["ids_reales"],["act-1","act-2"])
        self.assertTrue(rows[0]["requiere_nueva_evidencia"])

    def test_successful_actions_do_not_create_diagnostic_proposals(self):
        p={"action_outcomes":[{"id":"act-ok","op":"go","target":"x","success":True,
                                "evaluation_status":"verified_success","contract_status":"ok"}]}
        self.assertEqual(review_recent_attempts(p), [])
        self.assertNotIn("proposals",p)


class ObserverReviewTests(unittest.TestCase):
    def setUp(self):
        self.conn=sqlite3.connect(':memory:')
        self.archive=History(self.conn)
        self.review=ReviewStore(self.conn)
        self.review.bootstrap({})
        self.state={"person":{"pending":None},"world":{}}

    def tearDown(self):
        self.conn.close()

    def test_distinguishes_routine_omissions_from_unprocessed_high_priority(self):
        for i in range(18):
            self.archive.add('news',{"id":f"important-{i}","title":f"Construí un objeto nuevo {i}"})
        for i in range(4):
            self.archive.add('news',{"id":f"routine-{i}","title":"Rutina: descansé sin cambios"})
        selected, included, remaining, omitted = pending_sources(
            self.state,self.archive,self.review,[],limit=12,include_omitted=True)
        self.assertEqual(len(selected),12)
        self.assertEqual(remaining,6)
        self.assertEqual(len(omitted),4)
        self.assertTrue(all(r["id"].startswith("routine") for r in omitted))
        self.assertFalse({r["id"] for r in included}&{r["id"] for r in omitted})
        self.assertEqual(self.archive.count_unread("news"),22)

    def test_acknowledging_only_processed_snapshot_does_not_erase_later_entry(self):
        self.archive.add('news',{"id":"a","title":"Construí un refugio"})
        self.archive.add('news',{"id":"routine","title":"Rutina: descansé sin cambios"})
        selected, included, _, omitted=pending_sources(
            self.state,self.archive,self.review,[],include_omitted=True)
        sid=self.review.new_summary("Construcciones: un refugio.",included+omitted,"test/model")
        self.archive.add('news',{"id":"later","title":"Descubrí una cueva"})
        self.assertEqual(self.archive.count_unread("news"),3)
        self.review.acknowledge(sid,self.archive)
        self.assertEqual(self.archive.count_unread("news"),1)
        self.assertFalse(self.archive.is_read("news",self.archive.seq_for("news","later")))
        self.review.acknowledge(sid,self.archive)
        self.assertEqual(self.archive.count_unread("news"),1)


class UXTests(unittest.TestCase):
    def test_direct_construction_links_and_historical_materials(self):
        html=legacy_markup(Path(__file__).resolve().parents[1])
        self.assertNotIn('id="builddetail"',html)
        self.assertNotIn('data-open-plans',html)
        self.assertIn("historicMaterialDiff",html)
        self.assertIn("data.structure_cell_lists",html)
        self.assertIn("if(building)openPlanForBuilding(",html)

    def test_speed_controls(self):
        html=legacy_markup(Path(__file__).resolve().parents[1])
        for v in (1,10,60,80):
            self.assertIn(f'data-speed="{v}"',html)
        for v in (300,600):
            self.assertNotIn(f'data-speed="{v}"',html)


if __name__=="__main__":
    unittest.main()
