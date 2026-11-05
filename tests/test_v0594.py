"""Regresiones observacionales .4: SQLite intacto, fuentes, cohortes y sesiones."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from archive import History
from evaluar_corridas import analyze, compare, format_markdown, EvaluationError, main
from run_history import RunHistory


class RunEvaluation(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir=Path(self.temp.name)
        (self.dir/"VERSION").write_text("0.5.9.4\n",encoding="utf-8")

    def fixture(self,name="run.sqlite3",seed=7321,version="0.5.9.4",legacy=False):
        path=self.dir/name
        db=sqlite3.connect(path)
        db.execute("CREATE TABLE snapshot (id INTEGER PRIMARY KEY, payload TEXT)")
        archive=History(db)
        sessions=RunHistory(db,self.dir)
        sessions.identity["engine_version"]=version
        person={"clock_minutes":2880,"measurements":[],
                "behavior_metrics":{"actions":3,"novelty_actions":1,
                                    "new_tiles":5,"by_origin":{"llm":2,"agenda":1}}}
        world={"seed":seed,"revealed":["15,10,0"],"structures":[]}
        snapshot={"world":world,"person":person,"scenario_id":"territorio_desconocido"}
        sessions.start(snapshot,"territorio_desconocido","isla_v1","gemini","gemini-test",rng_seed=333)
        sessions.note_llm("gemini","gemini-test")
        measure={"id":"med-01","op":"drink","duration_minutes":8,
                 "start":{"needs":{"hidratacion":95,"energia":90}},
                 "end":{"needs":{"hidratacion":100,"energia":89}},
                 "condition":"orilla","rest_comparable":False,
                 "verified_facts":["Bebí agua."],"success":True}
        archive.add("measurement",measure)
        archive.add("measurement",{"id":"med-02","op":"rest",
                    "duration_minutes":20,"condition":"refugio",
                    "start":{"needs":{"energia":35}},
                    "end":{"needs":{"energia":44}},"rest_comparable":True})
        outcome={"id":"act-01","op":"drink","success":True,
                 "physical_result":{"measurement_id":"med-01"},
                 "evaluation_status":"verified_success","contract_status":"ok"}
        if not legacy:
            outcome.update({"origin":"llm","project_id":None})
        archive.add("diagnostic",outcome)
        nav={"id":"act-02","op":"explore","success":True,
             "physical_result":{"measurement_id":"med-02"}}
        if not legacy:
            nav.update({"origin":"agenda","exploration_trace":{
                "requested_direction":"north","discovered_tiles":5,
                "traveled_tiles":3}})
        archive.add("diagnostic",nav)
        archive.add("llm_decision",{"id":"llm-01","context_sha256":"a"*64})
        archive.add("project",{"id":"p-01","title":"Investigar"})
        db.execute("INSERT INTO snapshot(id,payload) VALUES(1,?)",
                   (json.dumps(snapshot,ensure_ascii=False),))
        db.commit()
        db.close()
        return path

    def test_read_only_does_not_modify_db_or_create_session(self):
        path=self.fixture()
        prior=path.read_bytes()
        result=analyze(path)
        self.assertEqual(path.read_bytes(),prior)
        self.assertEqual(result["identity"]["versions"],["0.5.9.4"])
        self.assertEqual(result["actions"]["total_archived"],2)
        self.assertEqual(result["actions"]["by_origin_verified"],{"agenda":1,"llm":1})
        self.assertEqual(result["actions"]["directed_exploration_with_trace"],1)
        self.assertEqual(result["actions"]["directed_exploration_with_discoveries"],1)
        self.assertEqual(result["actions"]["directed_exploration_traveled_tiles"],3)
        self.assertEqual(result["needs"]["maintenance_with_initial_reserve_at_least_90"],{"drink":1})
        self.assertEqual(result["needs"]["high_reserve_actions_by_origin"],{"drink:llm":1})
        self.assertEqual(result["needs"]["rest_measured_comparable"],1)
        self.assertEqual(result["evidence"]["measurements_archived"],2)
        self.assertEqual(result["evidence"]["archived_not_active"],2)
        self.assertEqual(result["autonomy"]["llm_decisions_archived"],1)
        self.assertEqual(result["identity"]["actual_models_used"][0]["calls"],1)
        self.assertEqual(len(result["identity"]["first_session_state_sha256"]),64)
        self.assertEqual(result["identity"]["first_session_rng_seed"],333)
        self.assertNotIn("Investigar",json.dumps(result))

    def test_legacy_without_new_columns_has_unknown_origin(self):
        path=self.fixture("legacy.sqlite3",legacy=True)
        db=sqlite3.connect(path)
        db.execute("UPDATE engine_sessions SET start_state_sha256=NULL,rng_seed=NULL")
        db.commit();db.close()
        report=analyze(path)
        self.assertEqual(report["actions"]["unknown_origin"],2)
        self.assertEqual(report["needs"]["high_reserve_actions_by_origin"],{"drink:desconocido":1})
        self.assertIsNone(report["identity"]["first_session_state_sha256"])
        self.assertTrue(any("No hay huella" in x for x in report["warnings"]))

    def test_older_session_table_schema_is_read_without_migration(self):
        path=self.fixture("old-schema.sqlite3")
        db=sqlite3.connect(path)
        db.execute("ALTER TABLE engine_sessions RENAME TO old_sessions")
        db.execute("""CREATE TABLE engine_sessions (
            id INTEGER,engine_version TEXT,scenario_id TEXT,environment_id TEXT,
            simulated_start_min REAL,simulated_end_min REAL,configured_provider TEXT,
            configured_model TEXT,code_commit TEXT,manifest_sha256 TEXT)""")
        db.execute("""INSERT INTO engine_sessions SELECT id,engine_version,scenario_id,
            environment_id,simulated_start_min,simulated_end_min,
            configured_provider,configured_model,code_commit,manifest_sha256 FROM old_sessions""")
        db.commit();db.close()
        r=analyze(path)
        self.assertIsNone(r["identity"]["first_session_rng_seed"])

    def test_comparison_requires_matching_recorded_seeds_and_state(self):
        a=analyze(self.fixture("a.sqlite3"))
        b=analyze(self.fixture("b.sqlite3"))
        c=compare([a,b])
        self.assertTrue(c["conditions"]["same_world_seed"])
        self.assertTrue(c["conditions"]["same_initial_snapshot_sha256"])
        self.assertTrue(c["conditions"]["same_rng_seed_documented"])
        self.assertFalse(c["can_claim_controlled_comparison"])
        self.assertFalse(c["conditions"]["same_external_llm_response_sequence"])
        bad=analyze(self.fixture("c.sqlite3",seed=33))
        self.assertFalse(compare([a,bad])["conditions"]["same_world_seed"])
        self.assertFalse(compare([a,bad])["conditions"]["same_initial_snapshot_sha256"])
        self.assertIn("No se declara causalidad",format_markdown(
            {"runs":[a,b],"comparison":c}))
        with self.assertRaises(EvaluationError):
            compare([a,a])

    def test_multiple_versions_flagged_not_attributed(self):
        path=self.fixture("multi.sqlite3")
        db=sqlite3.connect(path)
        db.execute("UPDATE engine_sessions SET engine_version='0.5.9.3.35'")
        db.execute("""INSERT INTO engine_sessions
            (started_utc,last_seen_utc,engine_version,scenario_id,environment_id,
             simulated_start_min,simulated_end_min)
            VALUES ('a','a','0.5.9.4','territorio_desconocido','isla_v1',60,2880)""")
        db.commit();db.close()
        r=analyze(path)
        self.assertEqual(r["identity"]["versions"],["0.5.9.3.35","0.5.9.4"])
        self.assertTrue(any("multiversión" in x for x in r["warnings"]))

    def test_command_line_outputs_files_without_modifying_source(self):
        source=self.fixture()
        before=source.read_bytes()
        json_path=self.dir/"report.json"
        md_path=self.dir/"report.md"
        self.assertEqual(main([str(source),"--json",str(json_path),
                               "--markdown",str(md_path)]),0)
        result=json.loads(json_path.read_text(encoding="utf-8"))
        self.assertEqual(result["format"],"nilo-evaluacion-v1")
        self.assertIn("evaluación descriptiva",md_path.read_text(encoding="utf-8"))
        self.assertEqual(source.read_bytes(),before)

    def test_invalid_input_does_not_create_database(self):
        path=self.dir/"absent.sqlite3"
        with self.assertRaises(EvaluationError):
            analyze(path)
        self.assertFalse(path.exists())


if __name__=="__main__":
    unittest.main()
