"""I3c.7h: deterministic yoke is not a causal control; shuffled signs are."""
import unittest

from experiments.neurolab.e09_i3c7h_contingency_permutation import (
    PROTOCOL,SEEDS,RESERVED_CONFIRMATION,MODES,PHASES,
    EFFECTIVE_MANIPULATION_FRACTION,MIN_SEEDS_EFFECTIVE,
    context_stratified_permutation,run_seed,run_all,
)


class C1ContingencyDegradation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.one=run_seed(1800)

    def test_seeds_and_arms_preregistered(self):
        self.assertEqual(PROTOCOL,"NL-EXP-I3c7h-v1")
        self.assertEqual(SEEDS,tuple(range(1800,1820)))
        self.assertTrue(set(SEEDS).isdisjoint(RESERVED_CONFIRMATION))
        self.assertEqual(MODES,("B","Y","P","F"))
        self.assertEqual(len(PHASES),2)
        self.assertEqual(MIN_SEEDS_EFFECTIVE,16)
        self.assertEqual(EFFECTIVE_MANIPULATION_FRACTION,.10)
        with self.assertRaises(ValueError):
            run_seed(1400)
        with self.assertRaises(ValueError):
            run_seed(1820)

    def test_permutation_keeps_null_slots_and_sign_counts_by_context(self):
        contexts=(0,1)*128
        tape=tuple(
            None if i%17==0 else i%5<3
            for i in range(256)
        )
        shuffled=context_stratified_permutation(tape,contexts,1800,0)
        self.assertEqual(len(shuffled),256)
        for context in (0,1):
            for value in (True,False,None):
                self.assertEqual(
                    sum(x is value and c==context
                        for x,c in zip(tape,contexts)),
                    sum(x is value and c==context
                        for x,c in zip(shuffled,contexts)),
                )
        self.assertEqual(
            [i for i,x in enumerate(tape) if x is None],
            [i for i,x in enumerate(shuffled) if x is None],
        )
        self.assertEqual(
            shuffled,context_stratified_permutation(tape,contexts,1800,0)
        )
        with self.assertRaises(ValueError):
            context_stratified_permutation(tape[:-1],contexts,1800,0)
        with self.assertRaises(TypeError):
            context_stratified_permutation(
                tape[:10]+(2,)+tape[11:],contexts,1800,0
            )
        with self.assertRaises(ValueError):
            context_stratified_permutation(tape,contexts,1400,0)
        with self.assertRaises(ValueError):
            context_stratified_permutation(tape,contexts,1800,2)

    def test_exact_yoke_replays_original_brain_every_tick(self):
        for phase in ("first","reversed"):
            p=self.one["phases"][phase]
            self.assertTrue(p["B_exact_I3c7e_M0_reference"])
            self.assertTrue(p["B_Y_neural_each_tick_equal"])
            self.assertTrue(p["B_Y_F_chemical_each_tick_equal"])
            self.assertEqual(
                p["training"]["B"]["neural_after_each_tick_sha256"],
                p["training"]["Y"]["neural_after_each_tick_sha256"],
            )
            for mode in ("Y","F"):
                self.assertEqual(
                    p["training"]["B"]["chemistry_after_each_tick_sha256"],
                    p["training"][mode]["chemistry_after_each_tick_sha256"],
                )
            self.assertEqual(p["training"]["B"]["end_state_sha256"],
                             p["training"]["Y"]["end_state_sha256"])
            self.assertEqual(p["readouts"]["B"],p["readouts"]["Y"])

    def test_permuted_budgets_exposure_slots_unchanged(self):
        for phase in ("first","reversed"):
            p=self.one["phases"][phase]
            b,p_tape=p["b_tape"],p["p_tape"]
            contexts=tuple(x for block in p["training_blocks"] for x in (block,)*8)
            self.assertEqual(len(b),256)
            self.assertEqual(len(p_tape),256)
            self.assertEqual(p["permutation_seed"],60520+1000*1800+
                            (0 if phase=="first" else 1))
            self.assertEqual(p["n_reward_sign_changes"],
                             sum(x!=y for x,y in zip(b,p_tape)))
            self.assertEqual(p["n_reward_sign_changes"]%2,0)
            for context in (0,1):
                for sign in (True,False,None):
                    self.assertEqual(
                        sum(v is sign and c==context for v,c in zip(b,contexts)),
                        sum(v is sign and c==context for v,c in zip(p_tape,contexts)),
                    )
            self.assertEqual(
                p["training"]["B"]["n_deliveries"],
                p["training"]["P"]["n_deliveries"],
            )
            self.assertEqual(
                p["training"]["B"]["n_positive"],
                p["training"]["P"]["n_positive"],
            )
            self.assertEqual(
                p["training"]["B"]["n_negative"],
                p["training"]["P"]["n_negative"],
            )
            self.assertEqual(len(p["training"]["P"]["frames"]),256)
            self.assertEqual(len(p["training"]["B"]["frames"]),256)

    def test_F_never_acquires_synaptic_plasticity_during_training(self):
        for phase in ("first","reversed"):
            f=self.one["phases"][phase]["training"]["F"]
            self.assertEqual(f["end_weights"]["strengths"],[2]*8)
            self.assertEqual(f["end_weights"]["stw"],[0]*8)
            self.assertEqual(f["end_weights"]["ltw"],[0]*8)
            self.assertEqual(f["synapse_events"],{
                "effect":0,"gain":0,"lose":0,"lost_connection":0,
            })
            for mode in MODES:
                for readout in ("frozen","active_no_new_reward"):
                    obs=self.one["phases"][phase]["readouts"][mode][readout]
                    self.assertEqual(obs["new_feedback_events"],0)
                    self.assertEqual(obs["n_ticks"],128)

    def test_one_seed_result_has_correct_statistical_unit(self):
        one=run_all((1801,))
        self.assertEqual(one["cohort"],[1801])
        self.assertEqual(one["n_seeds"],1)
        self.assertIsNone(one["effective_gate_at_least16_of20"])
        self.assertFalse(one["precommitted_interest_gate"])
        self.assertEqual(len(one["per_seed_sha256"]),1)
        self.assertEqual(one["gates"]["G05"],"OPEN")
        for phase in ("first","reversed"):
            diff=one["paired_contrasts"][phase]["B_minus_Y"][
                "active_no_new_reward"]
            self.assertEqual(diff["mean"],0)
            self.assertEqual(diff["ci95"],[0,0])
            self.assertEqual(diff["n_seeds"],1)

    def test_seed_duplication_and_holdout_leakage_rejected(self):
        for cohort in ((),(1800,1800),(1400,),(1820,),[1800]):
            with self.subTest(cohort=cohort):
                with self.assertRaises(ValueError):
                    run_all(cohort)


if __name__=="__main__":
    unittest.main()
