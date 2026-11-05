"""Nilo 0.5.9.2: el motor contrasta predicciones, no prueba causalidad."""
import tempfile
import unittest
from pathlib import Path

from action_results import ActionResult
from brain import normalize_decision, context_for
from nilo import Simulation, initial_state
from research_cycle import begin_prediction, finish_prediction, normalize_prediction


def pred(metric="retencion_pct",operator="gte",threshold=70):
    return {"hypothesis":"El filtro podría retener partículas",
            "expected_effect":"El agua pasará con menos partículas",
            "metric":metric,"operator":operator,"threshold":threshold}


class PredictionContract(unittest.TestCase):
    def setUp(self):
        self.p=initial_state()["person"]
        self.step={"op":"use","item":"filtro","method":"contener",
                   "target":"agua","prediction":pred()}

    def check(self,physical,success=True,no_evaluable=False):
        step=self.step
        begun=begin_prediction(self.p,step,"Día 1 · 09:00")
        self.assertEqual(begun["status"],"pendiente")
        result=ActionResult.from_legacy(step,["Cualquier narrativa"],success,False,
                                        no_evaluable=no_evaluable,physical=physical)
        return finish_prediction(self.p,begun["id"],result,"Día 1 · 09:32",
                                 measurement_id="med-1",action_id="act-1")

    def test_numeric_prediction_matches_metric_only(self):
        row=self.check({"kind":"recipiente","metrics":{"retencion_pct":90}})
        self.assertEqual(row["status"],"prediccion_coincide")
        self.assertEqual(row["measured_value"],90)
        self.assertIn("no prueba",row["scope"] if "no prueba" in row["scope"] else
                      "no prueba la hipótesis")
        self.assertEqual(row["action_id"],"act-1")

    def test_predicted_variable_unmeasured_despite_success(self):
        self.step["prediction"]=pred("particulas_retenidas_pct")
        row=self.check({"kind":"recipiente","metrics":{"retencion_pct":90}})
        self.assertEqual(row["status"],"variable_no_medida")
        self.assertTrue(row["operation_success"])
        self.assertIsNone(row["measured_value"])
        self.assertEqual(row["available_metrics"],["retencion_pct"])
        self.assertEqual(self.p.get("proposals",[]),[])

    def test_numeric_prediction_disagrees_even_when_operation_succeeds(self):
        row=self.check({"kind":"recipiente","metrics":{"retencion_pct":12}})
        self.assertEqual(row["status"],"prediccion_no_coincide")
        self.assertTrue(row["operation_success"])

    def test_no_evaluable_is_not_physical_failure(self):
        row=self.check(None,success=False,no_evaluable=True)
        self.assertEqual(row["status"],"sin_modelo_evaluable")
        self.assertEqual(row["evaluation_status"],"no_evaluable")

    def test_text_does_not_become_measurement(self):
        row=self.check(None)
        self.assertEqual(row["status"],"variable_no_medida")
        self.assertIsNone(row["measured_value"])

    def test_qualitative_prediction_does_not_claim_proof(self):
        self.step["prediction"]={"hypothesis":"Se filtrará","expected_effect":"Agua limpia"}
        row=self.check({"kind":"recipiente","metrics":{"retencion_pct":90}})
        self.assertEqual(row["status"],"prediccion_cualitativa")

    def test_invalid_prediction_and_nonfinite_number_disallowed(self):
        self.assertIsNone(normalize_prediction({"hypothesis":"x"}))
        candidate=normalize_prediction(pred(threshold=float("nan")))
        self.assertIsNone(candidate["threshold"])
        self.assertEqual(candidate["operator"],"")

    def test_double_completion_does_not_change_result(self):
        row=self.check({"kind":"recipiente","metrics":{"retencion_pct":90}})
        result=ActionResult.from_legacy(self.step,["x"],True,False,
                                        physical={"metrics":{"retencion_pct":10}})
        self.assertIsNone(finish_prediction(self.p,row["id"],result,"Día 2"))
        self.assertEqual(row["measured_value"],90)


class Integration(unittest.TestCase):
    def test_normalizer_preserves_safe_predictions(self):
        raw={"cuaderno":"Creo que esta prueba puede ayudar","plan":[
            {"op":"experiment","target":"piedra","method":"golpear",
             "prediction":pred("dureza","gte",1)}]}
        result=normalize_decision(raw)
        self.assertEqual(result["plan"][0]["prediction"]["metric"],"dureza")

    def test_real_tick_links_measurement_prediction_and_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            sim=Simulation(db_path=Path(tmp)/"world.sqlite3")
            try:
                p=sim.s["person"]
                sim.s["planning"]=True
                p["plan"]=[{"op":"experiment","target":"piedra","method":"golpear",
                            "prediction":pred("dureza","gte",0)}]
                sim.change_speed(speed=60)
                for _ in range(6):sim.tick(15)
                self.assertTrue(p.get("prediction_log"))
                row=p["prediction_log"][-1]
                self.assertEqual(row["status"],"prediccion_coincide")
                self.assertTrue(row["action_id"])
                self.assertTrue(row["measurement_id"])
                self.assertEqual(p["action_outcomes"][-1]["prediction_id"],row["id"])
                self.assertEqual(sim.public_state()["prediction_log"][0]["id"],row["id"])
                ctx=context_for(sim.s["world"],p,[],sim.stamp(),scenario=sim.scenario)
                self.assertEqual(ctx["predicciones_contrastadas"][-1]["status"],
                                 "prediccion_coincide")
                archived=sim.conn.execute("SELECT payload FROM history WHERE category='prediction'").fetchall()
                self.assertEqual(len(archived),1)
                revisions=sim.conn.execute("SELECT count(*) FROM history_revisions WHERE category='prediction'").fetchone()[0]
                self.assertEqual(revisions,2)
            finally:sim.conn.close()

    def test_no_predictions_do_not_add_fictitious_records(self):
        state=initial_state()
        context=context_for(state["world"],state["person"],[],"Día 1")
        self.assertNotIn("predicciones_contrastadas",context)


if __name__=="__main__":
    unittest.main()
