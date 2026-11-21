"""E09.02i-I1: predeclared chemistry order and negative controls.

Fixtures derive from saved original GEN data; the CI does NOT contain or
reinspect dad1.gen or Creatures.exe.
"""
import json
from pathlib import Path
import unittest

from experiments.neurolab.e09_chemical_bridge import (
    SourcePort, ChemicalBridgeState, chemical_bridge_tick, initial_bridge,
)
from experiments.neurolab.e09_historical_emitter import Emitter
from experiments.neurolab.e09_historical_receptor import Receptor
from experiments.neurolab.e09_historical_reaction_math import process_reactions
from experiments.neurolab.e09_historical_locus import route_brain_chem_loci
from experiments.neurolab.c1_reaction_inspector import Reaction


ROOT = Path(__file__).resolve().parents[3]


def original_receptors():
    record=json.loads((ROOT/"docs/neurolab/resultados/e09h3_receptores_genoma_original.json").read_text())
    assert record["receptor_count"] == 43
    return tuple(Receptor(int(i),**data) for i,data in record["brain_receptors"].items())


def original_reaction(index):
    record=json.loads((ROOT/"docs/neurolab/resultados/e09h2_reacciones_genoma_original.json").read_text())
    assert record["reaction_count"] == 58
    fields=record["sample_original_genes"][str(index)]
    return Reaction(index,0,*[fields[k] for k in (
        "qa","ca","qb","cb","qc","cc","qd","cd","rate")])


def pool(**chemicals):
    values=[0]*256
    for name,value in chemicals.items():
        values[int(name[1:])]=value
    return tuple(values)


class ChemicalBridgeTests(unittest.TestCase):
    def test_reaction_output_not_visible_to_receptors_in_same_tick(self):
        rs=original_receptors()
        reaction=original_reaction(111)
        initial=initial_bridge(rs,pool=pool(c49=20))
        first=chemical_bridge_tick(initial,(),rs,(reaction,))
        self.assertEqual(initial.decision_chem,(0,0,16,16))
        self.assertEqual(initial.concept_chem,(0,4,0,0))
        self.assertEqual(first.decision_at_receptors[0],19)  # 20*255//256
        self.assertEqual(first.concept_at_receptors[0],0)
        self.assertEqual((first.after.pool[49],first.after.pool[51],first.after.pool[54]),
                         (8,12,12))
        self.assertEqual(first.reaction_events[0].reacted_units,12)
        # After one chemistry step, Concept sees Reinforcement from previous call.
        second=chemical_bridge_tick(first.after,(),rs,(reaction,))
        self.assertEqual(second.concept_at_receptors[0],11)
        # Falsification: forbidden reaction-before-receptor gives different t0.
        wrong_pool,_=process_reactions(initial.pool,(reaction,),0)
        wrong_concept=route_brain_chem_loci(rs,wrong_pool,8,initial.concept_chem)
        self.assertEqual(wrong_concept[0],11)
        self.assertNotEqual(first.concept_at_receptors[0],wrong_concept[0])
        self.assertEqual(initial.pool[49],20)
        self.assertEqual(initial.pool[51],0)

    def test_emitter_before_receptor_and_source_consumed(self):
        rs=original_receptors()
        emitter=Emitter(124,0,6,1,53,0,1,255,1)
        state=initial_bridge(rs,ports=(SourcePort(6,1,80),))
        trace=chemical_bridge_tick(state,(emitter,),rs,())
        self.assertEqual(trace.pool_after_emitters[53],79)
        self.assertEqual(trace.after.decision_chem[2],0)  # max(0,16-78)
        self.assertEqual(trace.after.ports,(SourcePort(6,1,0),))
        self.assertEqual(trace.emitter_results[0].calculated_amount,79)
        repeated=chemical_bridge_tick(trace.after,(emitter,),rs,())
        self.assertEqual(repeated.after.pool[53],79)
        self.assertEqual(repeated.emitter_results[0].eligible,False)
        self.assertEqual(state.ports,(SourcePort(6,1,80),))
        self.assertEqual(state.pool[53],0)

    def test_two_lobes_with_same_source_locus_are_independent(self):
        rs=original_receptors()
        emitters=(Emitter(123,0,8,1,52,0,1,255,1),
                  Emitter(124,0,6,1,53,0,1,255,1))
        ports=(SourcePort(8,1,5),SourcePort(6,1,80))
        trace=chemical_bridge_tick(initial_bridge(rs,ports=ports),emitters,rs,())
        self.assertEqual(trace.after.ports,(SourcePort(8,1,0),SourcePort(6,1,0)))
        self.assertEqual(trace.after.pool[52],4)
        self.assertEqual(trace.after.pool[53],79)
        self.assertEqual(trace.after.concept_chem[1],1)  # 4 - floor(4*255/256)=1
        self.assertEqual(trace.after.decision_chem[2],0)

    def test_absent_phases_leave_pool_stable_and_report_no_decay(self):
        rs=original_receptors()
        state=initial_bridge(rs,pool=pool(c49=12,c51=3))
        trace=chemical_bridge_tick(state,(),(),())
        self.assertEqual(trace.after.pool,state.pool)
        self.assertEqual(trace.after.decision_chem,state.decision_chem)
        self.assertIn("NOT IMPLEMENTED",trace.skipped_phase)
        self.assertEqual(trace.after.tick,1)
        again=chemical_bridge_tick(state,(),(),())
        self.assertEqual(trace,again)

    def test_missing_port_and_lobe_out_of_scope_rejected(self):
        rs=original_receptors()
        emitter=Emitter(124,0,6,1,53,0,1,255,1)
        with self.assertRaisesRegex(ValueError,"missing source"):
            chemical_bridge_tick(initial_bridge(rs),(emitter,),rs,())
        outside=Emitter(77,1,6,1,53,0,1,255,1)
        with self.assertRaisesRegex(ValueError,"only brain"):
            chemical_bridge_tick(initial_bridge(rs),(outside,),rs,())

    def test_duplicate_port_is_error_not_silent_override(self):
        rs=original_receptors()
        with self.assertRaisesRegex(ValueError,"duplicate source port"):
            initial_bridge(rs,ports=(SourcePort(6,1,10),SourcePort(6,1,20)))
        with self.assertRaises(ValueError):
            SourcePort(1,1,10)

    def test_receptor_collision_rejected(self):
        r=Receptor(88,0,6,13,49,0,0,255,0)
        twin=Receptor(89,0,6,13,50,0,0,255,0)
        state=initial_bridge((r,))
        with self.assertRaisesRegex(ValueError,"duplicate receptor"):
            chemical_bridge_tick(state,(),(r,twin),())

    def test_pool_validation_and_tick_overflow(self):
        rs=original_receptors()
        with self.assertRaises(ValueError):
            initial_bridge(rs,pool=(0,))
        with self.assertRaises(ValueError):
            initial_bridge(rs,ports=(SourcePort(8,1,256),))
        exhausted=ChemicalBridgeState(pool(),(),(0,0,0,0),(0,0,0,0),0xFFFFFFFF)
        with self.assertRaisesRegex(ValueError,"tick overflow"):
            chemical_bridge_tick(exhausted,(),rs,())

    def test_reaction_gene_is_original_fixture_not_custom_chemistry(self):
        r=original_reaction(111)
        self.assertEqual((r.gene_index,r.chemical_a,r.chemical_c,r.chemical_d,r.rate),
                         (111,49,51,54,16))


if __name__=="__main__":
    unittest.main()
