"""E09h.5 isolated chemical emitters: synthetic oracles, no original EXE."""
import unittest

from experiments.neurolab.e09_historical_emitter import Emitter, emitter_tick


def pool(**values):
    data = [0]*256
    for label, n in values.items():
        data[int(label[1:])] = n
    return tuple(data)


def gene(i=123,lobe=8,locus=1,chemical=52,threshold=0,
         sample_rate=1,gain=255,flags=1):
    return Emitter(i,0,lobe,locus,chemical,threshold,sample_rate,gain,flags)


class HistoricalEmitterTests(unittest.TestCase):
    def test_unchanged_three_original_brain_gene_fields(self):
        # Extracted from the previously verified E00 GEN documentation.
        # This test does not claim that the original GEN is read in CI.
        genes=(gene(),gene(i=124,lobe=6,chemical=53),
               gene(i=125,lobe=6,locus=2,chemical=70))
        self.assertEqual([(g.lobe,g.locus,g.chemical,g.sample_rate,g.flags)
                          for g in genes],[(8,1,52,1,1),(6,1,53,1,1),(6,2,70,1,1)])
        for g in genes:
            result=emitter_tick(g,pool(),80,0)
            self.assertEqual((result.calculated_amount,result.added_to_pool,
                              result.pool[g.chemical],result.source),(79,79,79,0))

    def test_gain255_shift8_not_divide255(self):
        result=emitter_tick(gene(),pool(),255,0)
        self.assertEqual((result.calculated_amount,result.pool[52]),(254,254))

    def test_flags1_consumes_source_and_prevents_repeat(self):
        original=pool()
        result=emitter_tick(gene(),original,80,0)
        again=emitter_tick(gene(),result.pool,result.source,0)
        self.assertTrue(result.eligible)
        self.assertFalse(again.eligible)
        self.assertEqual(again.pool[52],79)
        self.assertEqual(original[52],0)

    def test_sample_rate_and_threshold_do_not_consume(self):
        g=gene(sample_rate=2)
        waiting=emitter_tick(g,pool(),80,1)
        self.assertEqual((waiting.source,waiting.added_to_pool,waiting.eligible),(80,0,False))
        below=emitter_tick(gene(threshold=80),pool(),80,0)
        self.assertEqual((below.source,below.eligible),(80,False))
        above=emitter_tick(gene(threshold=80),pool(),81,0)
        self.assertEqual((above.source,above.calculated_amount),(0,0))
        self.assertTrue(above.eligible)

    def test_saturate_existing_concentration_and_consume_source(self):
        r=emitter_tick(gene(),pool(c52=245),80,0)
        self.assertEqual((r.pool[52],r.calculated_amount,r.added_to_pool,r.source),
                         (255,79,10,0))

    def test_flag2_full_gain_and_no_reset_when_flag1_clear(self):
        r=emitter_tick(gene(gain=71,flags=2),pool(),1,0)
        self.assertEqual((r.pool[52],r.source),(71,1))

    def test_flag4_inverts_source_before_threshold(self):
        r=emitter_tick(gene(flags=4),pool(),240,0)
        self.assertEqual((r.calculated_amount,r.source),(14,240))
        r0=emitter_tick(gene(flags=4),pool(),255,0)
        self.assertFalse(r0.eligible)

    def test_chemical_zero_still_consumes_on_eligible_tick(self):
        # Explicit deviation from initial H5 preregistered false assumption.
        r=emitter_tick(gene(chemical=0),pool(),80,0)
        self.assertTrue(r.eligible)
        self.assertEqual((r.source,r.added_to_pool,r.pool[0]),(0,0,0))
        self.assertEqual(r.calculated_amount,79)

    def test_validation_and_determinism(self):
        with self.assertRaises(ValueError):
            gene(sample_rate=0)
        for bad in (-1,256,True):
            with self.assertRaises(ValueError):
                emitter_tick(gene(),pool(),bad,0)
        with self.assertRaises(ValueError):
            emitter_tick(gene(),pool(),80,-1)
        with self.assertRaises(ValueError):
            emitter_tick(gene(),(0,),80,0)
        a=emitter_tick(gene(),pool(),80,3)
        b=emitter_tick(gene(),pool(),80,3)
        self.assertEqual(a,b)


if __name__=="__main__":
    unittest.main()
