"""E09g.5 C1 direct vs I3 original nominal atrophy: no new cohort."""
import unittest

from experiments.neurolab.e09_i3c7d_loss_regime_audit import (
    NOMINAL, MODES, SNAPSHOTS, FIXTURE_SEED, run,
)


class DirectMetabolicLossComparability(unittest.TestCase):
    def test_source_control_tokens_match_genetic_nominal(self):
        r=run()
        self.assertEqual(FIXTURE_SEED,0)
        self.assertEqual(MODES,("Z","L","F"))
        self.assertEqual(SNAPSHOTS,(0,4,5,9,10,16,20))
        self.assertEqual(NOMINAL,(0,0,16,16))
        self.assertEqual(r["nominal_from_original_gen"],[0,0,16,16])
        self.assertEqual(r["direct_control_tokens"],{
            "ZERO":[0,0,0,0],
            "REWARD":[255,0,0,0],
            "PUNISHMENT":[0,255,0,0],
        })

    def test_strength_cadence_and_clear(self):
        r=run()
        z=r["mechanical_regimes"]["Z"]
        l=r["mechanical_regimes"]["L"]
        f=r["mechanical_regimes"]["F"]
        self.assertEqual(l["events"]["5"]["lose"],8)
        self.assertEqual(l["events"]["10"]["lost_connection"],8)
        self.assertEqual(z["counts"]["lose"],0)
        self.assertEqual(f["counts"]["lose"],0)
        for t in ("0","4"):
            self.assertEqual(l["snapshots"][t]["strengths"],[2]*8)
        self.assertEqual(l["snapshots"]["5"]["strengths"],[1]*8)
        self.assertEqual(l["snapshots"]["9"]["strengths"],[1]*8)
        for t in ("10","16","20"):
            self.assertEqual(l["snapshots"][t]["strengths"],[0]*8)
            self.assertEqual(z["snapshots"][t]["strengths"],[2]*8)
            self.assertEqual(f["snapshots"][t]["strengths"],[2]*8)

    def test_original_numerical_oracle_all_160_ticks(self):
        r=run()
        self.assertEqual(r["mechanical_regimes"]["Z"]["counts"]["witness_checks"],160)
        self.assertEqual(r["mechanical_regimes"]["L"]["counts"]["witness_checks"],160)
        self.assertEqual(r["mechanical_regimes"]["F"]["counts"]["witness_checks"],0)
        self.assertFalse(r["mechanical_regimes"]["F"]["learn"])
        self.assertTrue(r["mechanical_regimes"]["L"]["learn"])
        self.assertTrue(r["mechanical_regimes"]["Z"]["learn"])

    def test_no_g05_claim_and_deterministic_replay(self):
        a=run()
        self.assertEqual(a,run())
        self.assertEqual(a["G05_G09_G00H"],"OPEN")
        self.assertIn("loss regime",a["interpretation"])
        self.assertIn("not claim exact chemical trajectories",a["limitations"])


if __name__=="__main__":
    unittest.main()
