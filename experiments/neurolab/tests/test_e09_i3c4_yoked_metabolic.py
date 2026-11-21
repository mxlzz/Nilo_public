"""I3c4 preregistered four-arm yoked chemical experiment and controls."""
import unittest

from experiments.neurolab.c1_context_brain import C1ContextBrain
from experiments.neurolab.e09_coupled_brain import initial_coupled
from experiments.neurolab.e09_context_protocol import MAPPING_A
from experiments.neurolab.e09_delayed_distractors_protocol import trials
from experiments.neurolab.e09_i3_metabolic_protocol import (
    selected_genes, metabolic_step,
    add_environment_precursors as original_precursors,
)
from experiments.neurolab.e09_i3c3_dynamic_context import DynamicContextBrain
from experiments.neurolab.e09_i3c4_yoked_metabolic import (
    SEEDS, MODES, TAPE_LENGTH, explicit_wiring, migration_tape,
    start, coupled_step, add_environment_precursors, run_phase,
    run_seed, run_all,
)


class DynamicYokedChemistryTests(unittest.TestCase):
    def test_fixed_cohort_four_arms_and_wiring_without_mapping_leak(self):
        self.assertEqual(SEEDS,tuple(range(900,920)))
        self.assertEqual(MODES,("B","Y","P","F"))
        self.assertEqual(TAPE_LENGTH,16384)
        self.assertEqual(explicit_wiring(900),(0x1000,0x2000,0x2000,0x1000))
        self.assertEqual(explicit_wiring(901),(0x2000,0x1000,0x1000,0x2000))
        self.assertEqual(migration_tape(900),migration_tape(900))
        self.assertNotEqual(migration_tape(900),migration_tape(901))
        with self.assertRaises(ValueError):
            run_seed(200)

    def test_chemical_step_is_same_upstream_pipeline_as_I3(self):
        receptors,reactions=selected_genes()
        dyn=DynamicContextBrain(900,migration_enabled=False)
        state=start(dyn,receptors,explicit_wiring(900),())
        original=C1ContextBrain(900)
        original_state=initial_coupled(original,receptors)
        for ctx in (0,0,1,1,0):
            state,_,_=coupled_step(
                dyn,state,ctx,receptors,reactions,learn=True)
            original_state,_,_=metabolic_step(
                original,original_state,ctx,receptors,reactions,
                plasticity=True)
            self.assertEqual(state.chemistry,original_state.chemistry)
            self.assertEqual(state.brain.tick,original_state.brain.tick)

    def test_precursors_identical_to_original_I3_pool_math(self):
        receptors,_reactions=selected_genes()
        dyn=DynamicContextBrain(900)
        original=C1ContextBrain(900)
        for good in (False,True):
            left=add_environment_precursors(
                start(dyn,receptors,explicit_wiring(900),()),good)
            right=original_precursors(
                initial_coupled(original,receptors),correct=good)
            self.assertEqual(left.chemistry,right.chemistry)

    def test_one_phase_yoking_requires_B_feedback_and_replays_chemical_exactly(self):
        receptors,reactions=selected_genes()
        b=DynamicContextBrain(900,migration_enabled=False)
        y=DynamicContextBrain(900,migration_enabled=True)
        wiring=explicit_wiring(900)
        tape=migration_tape(900)
        train=trials(900,50000,10)
        sB,infoB,chemB,coreB,_=run_phase(
            b,start(b,receptors,wiring,tape),train,
            MAPPING_A,receptors,reactions,mode="B",train=True)
        with self.assertRaises(ValueError):
            run_phase(
                y,start(y,receptors,wiring,tape),train,
                MAPPING_A,receptors,reactions,mode="Y",train=True)
        sY,infoY,chemY,coreY,_=run_phase(
            y,start(y,receptors,wiring,tape),train,
            MAPPING_A,receptors,reactions,mode="Y",
            feedback_reference=tuple(infoB["feedback_events"]),
            expected_chemistry=chemB,train=True)
        self.assertEqual(chemB,chemY)
        self.assertEqual(infoB["chem_trajectory_sha256"],
                         infoY["chem_trajectory_sha256"])
        self.assertEqual(infoB["feedback_events"],infoY["feedback_events"])
        self.assertEqual(infoB["ticked_steps"],infoY["ticked_steps"])
        self.assertEqual(len(sB.brain.links),4)
        self.assertEqual(len(sY.brain.links),4)

    def test_one_seed_all_modes_include_inverse_and_frozen_control(self):
        record=run_seed(900)
        self.assertEqual(record["seed"],900)
        self.assertEqual(record["initial_wiring"],[
            "0x1000","0x2000","0x2000","0x1000"])
        for phase in ("first","reversed"):
            row=record[phase]
            self.assertEqual(row["n_train_trials"],60)
            self.assertEqual(row["n_holdout_trials"],36)
            self.assertTrue(row["B_Y_F_identical_chemical_every_tick"])
            self.assertEqual(set(row["train"]),set(MODES))
            self.assertEqual(set(row["holdout"]),set(MODES))
            for mode in MODES:
                self.assertEqual(row["holdout"][mode]["target_choices"],36)
                self.assertEqual(row["holdout"][mode]["feedback_deliveries"],0)
            self.assertEqual(row["train"]["B"]["random_cursor"],0)
            self.assertEqual(row["train"]["F"]["random_cursor"],0)
            self.assertEqual(row["train"]["F"]["migration_acceptances"],0)

    def test_same_seed_replays_without_hidden_randomness(self):
        self.assertEqual(run_seed(901),run_seed(901))

    def test_subset_aggregates_do_not_claim_learning(self):
        doc=run_all((900,))
        self.assertEqual(doc["seeds"],[900])
        self.assertEqual(doc["n_contacts"],4)
        self.assertEqual(doc["n_train_trials_per_phase"],60)
        self.assertEqual(doc["n_holdout_trials_per_phase"],36)
        self.assertTrue(doc["all_B_Y_F_chemical_trajectories_identical"])
        self.assertEqual(doc["gate_G05_G09"],
                         "NOT EVALUATED; I3 general learning remains negative")
        self.assertIn("Y_minus_B",doc["contrasts"]["first"])
        self.assertEqual(doc["contrasts"]["first"]["Y_minus_B"]["n_seeds"],1)
        with self.assertRaises(ValueError):
            run_all((900,900))
        with self.assertRaises(ValueError):
            run_all((200,))


if __name__=="__main__":
    unittest.main()
