"""E09h.3: receptor transfer fixtures and a synthetic C1 gene, no proprietary data."""
import unittest

from experiments.neurolab.e09_historical_receptor import (
    Receptor, parse_receptors, receptor_value, original_fixtures,
)


def pool(**values):
    result=[0]*256
    for id_string, quantity in values.items():
        result[int(id_string.removeprefix("c"))]=quantity
    return tuple(result)


class HistoricalReceptorTests(unittest.TestCase):
    def test_reward_punishment_brain_receptors(self):
        reward=Receptor(88,0,6,13,49,0,0,255,0)
        punishment=Receptor(89,0,6,14,50,0,0,255,0)
        before=pool(c49=12,c50=12)
        self.assertEqual(receptor_value(reward,before),11)
        self.assertEqual(receptor_value(punishment,before),11)
        self.assertEqual(receptor_value(reward,pool()),0)
        self.assertEqual(before[49],12)

    def test_inhibitory_atrophy_receptor(self):
        rec=Receptor(127,0,6,15,53,0,16,255,1)
        self.assertEqual(receptor_value(rec,pool(c53=12)),5)
        self.assertEqual(receptor_value(rec,pool(c53=40)),0)
        self.assertEqual(receptor_value(rec,pool()),16)

    def test_conash_nominal_four(self):
        rec=Receptor(126,0,8,14,52,0,4,255,1)
        self.assertEqual(receptor_value(rec,pool(c52=5)),1)

    def test_flags_constant_effect_only_above_threshold(self):
        rec=Receptor(1,0,6,13,49,10,2,7,2)
        self.assertEqual(receptor_value(rec,pool(c49=12)),9)
        self.assertEqual(receptor_value(rec,pool(c49=10)),2)
        self.assertEqual(receptor_value(rec,pool(c49=4)),2)

    def test_sat_and_missing_chemical(self):
        rec=Receptor(1,0,6,13,49,0,250,255,0)
        self.assertEqual(receptor_value(rec,pool(c49=12)),255)
        blank=Receptor(1,0,6,13,0,0,0,255,0)
        self.assertIsNone(receptor_value(blank,pool()))

    def test_synthetic_genome_parser_preserves_all_fields(self):
        raw=bytes((0,6,13,49,0,0,255,0))
        gene=b"gene"+bytes((1,0,0,0,0,0))+raw
        parsed=parse_receptors(gene+b"gend")
        self.assertEqual(len(parsed),1)
        self.assertEqual(parsed[0],Receptor(0,*raw))

    def test_validation_and_wrong_original_hash(self):
        with self.assertRaises(ValueError):
            Receptor(1,0,6,13,49,0,0,300,0)
        with self.assertRaises(ValueError):
            receptor_value(Receptor(1,0,6,13,49,0,0,255,0),(0,))
        with self.assertRaises(ValueError):
            original_fixtures(b"not user original")


if __name__ == "__main__":
    unittest.main()
