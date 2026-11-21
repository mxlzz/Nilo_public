"""I3: original fixture provenance, temporal lag, no leakage and smoke run.

Scientific gate is read from run_all() on 20 preregistered seeds via separate
CI workflow. A unittest passing is NOT evidence of learning.
"""
from dataclasses import replace
import inspect
import unittest

from experiments.neurolab.c1_context_brain import C1ContextBrain
from experiments.neurolab.e09_coupled_brain import initial_coupled
from experiments.neurolab.e09_i3_metabolic_protocol import (
    SEEDS,RATES,LAB_RATE,PRECURSOR_DOSE,selected_genes,
    add_environment_precursors,metabolic_step,run_all,
)


class MetabolicI3SmokeTests(unittest.TestCase):
    def test_cohort_rates_dose_and_existing_genes_frozen(self):
        self.assertEqual(SEEDS,tuple(range(200,220)))
        self.assertEqual(LAB_RATE,40)
        self.assertEqual(PRECURSOR_DOSE,80)
        self.assertEqual(len(RATES),256)
        self.assertEqual(set(RATES),{40})
        receptors,reactions=selected_genes()
        self.assertEqual({r.gene_index for r in receptors},
                         {88,89,126,127,128,129})
        self.assertEqual([r.gene_index for r in reactions],[57,71,111,112])

    def test_external_feedback_is_precursor_not_target_in_brain(self):
        receptors,_=selected_genes()
        brain=C1ContextBrain(200)
        before=initial_coupled(brain,receptors)
        positive=add_environment_precursors(before,correct=True)
        negative=add_environment_precursors(before,correct=False)
        self.assertEqual((positive.chemistry.pool[33],
                          positive.chemistry.pool[1]),(80,80))
        self.assertEqual(negative.chemistry.pool[17],80)
        self.assertEqual(negative.chemistry.pool[49],0)
        self.assertEqual(positive.chemistry.pool[49],0)
        self.assertEqual(positive.brain,before.brain)
        self.assertEqual(before.chemistry.pool[33],0)
        params=set(inspect.signature(metabolic_step).parameters)
        self.assertFalse({"correct_action","target","reward","mapping"} & params)

    def test_precursor_saturates_pool_but_not_brain(self):
        receptors,_=selected_genes()
        brain=C1ContextBrain(200)
        before=initial_coupled(brain,receptors)
        high=list(before.chemistry.pool)
        high[33]=220
        state=replace(before,chemistry=replace(before.chemistry,pool=tuple(high)))
        state=add_environment_precursors(state,correct=True)
        self.assertEqual(state.chemistry.pool[33],255)
        self.assertEqual(state.chemistry.pool[1],80)
        self.assertEqual(state.brain,before.brain)
        with self.assertRaises(ValueError):
            add_environment_precursors(state,correct=True,dose=-1)

    def test_actual_chained_reactions_have_two_stage_brain_lag(self):
        receptors,reactions=selected_genes()
        brain=C1ContextBrain(200)
        state=initial_coupled(brain,receptors)
        state=add_environment_precursors(state,correct=True)
        state1,_,trace1=metabolic_step(brain,state,0,receptors,reactions,
                                      plasticity=True)
        self.assertEqual(trace1.read_chem[0],0)
        self.assertEqual(state1.chemistry.decision_chem[0],0)
        self.assertGreater(state1.chemistry.pool[49],0)
        state2,_,trace2=metabolic_step(brain,state1,1,receptors,reactions,
                                      plasticity=True)
        self.assertEqual(trace2.read_chem[0],0)
        self.assertGreater(state2.chemistry.decision_chem[0],0)
        _,_,trace3=metabolic_step(brain,state2,0,receptors,reactions,
                                  plasticity=True)
        self.assertGreater(trace3.read_chem[0],0)

    def test_single_seed_smoke_does_not_apply_full_cohort_gate(self):
        result=run_all((200,))
        self.assertIsNone(result["gate_M_exploratory"])
        self.assertEqual(result["n_units"],6)
        self.assertEqual(result["dendrites"],8)
        self.assertEqual(result["precursor_dose"],80)
        self.assertEqual(set(result["mean_holdout_target_accuracy"]),{
            "first","reversed"
        })
        self.assertEqual(set(result["mean_holdout_target_accuracy"]["first"]),{
            "M","F","C","Q"
        })
        self.assertEqual(len(result["per_seed"]),1)
        self.assertEqual(result["per_seed"][0]["first"]["training_trials"],60)
        self.assertEqual(result["per_seed"][0]["first"]["holdout_trials"],36)

    def test_repeatability_first_seed_no_hidden_random_mutations(self):
        x=run_all((200,))
        y=run_all((200,))
        self.assertEqual(x,y)


if __name__=="__main__":
    unittest.main()
