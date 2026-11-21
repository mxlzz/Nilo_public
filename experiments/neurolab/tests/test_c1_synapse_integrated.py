"""E09.02g.1: frozen-snapshot C1 dendrite with actual dad1.gen SVRules.

Synthetic inputs test the gene-derived numeric path, not environmental
biochemistry or actual gameplay. No game binaries are committed.
"""
import random
import unittest

from experiments.neurolab.c1_dendrite_tick import DendriteState
from experiments.neurolab.c1_synapse_integrated import (
    C1SynapseState,C1SynapticInput,update_c1_synapse,
    DECISION_EXCITATORY_GENE,DECISION_INHIBITORY_GENE,CONCEPT_GENE,
)


def exc(before, tick, *, output=80, source=200, chem=(255,0,0,0)):
    return update_c1_synapse(
        before,DECISION_EXCITATORY_GENE,
        C1SynapticInput(source,owner_state=80,owner_output=output,chemicals=chem),
        tick=tick,
    )


class C1SynapticIntegrationTests(unittest.TestCase):
    def test_decision_first_pulse_uses_old_gain_snapshot(self):
        before=C1SynapseState(DendriteState(),4)
        result=exc(before,1)
        self.assertEqual(result.after,C1SynapseState(DendriteState(4,3,0),4))
        self.assertEqual(result.susceptibility_rule_output,200)
        self.assertEqual(result.reinforcement_rule_output,255)
        self.assertEqual(result.gain_strength_rule_output,0)
        self.assertEqual(result.snapshot.susceptibility,0)
        self.assertEqual(result.snapshot.stw,0)

    def test_decision_second_pulse_gain_sees_old_stw(self):
        before=C1SynapseState(DendriteState(4,3,0),2)
        result=exc(before,3)
        self.assertEqual(result.after,C1SynapseState(DendriteState(8,7,0),3))
        self.assertEqual(result.gain_strength_rule_output,3)
        self.assertNotEqual(result.gain_strength_rule_output,result.after.dendrite.stw)

    def test_atrophy_clears_synapse_and_owning_neuron_flag(self):
        before=C1SynapseState(DendriteState(0,5,0),1)
        result=exc(before,5,output=0,source=0,chem=(0,0,1,0))
        self.assertEqual(result.after,C1SynapseState(DendriteState(),0))
        self.assertTrue(result.owner_neuron_cleared)
        self.assertFalse(result.strength.did_gain)
        self.assertTrue(result.strength.did_lose)

    def test_concept_reinforcement_then_atrophy_suppression_loss(self):
        initial=C1SynapseState(DendriteState(0,128,128),2)
        gain=update_c1_synapse(
            initial,CONCEPT_GENE,
            C1SynapticInput(200,owner_state=100,owner_output=100,
                           chemicals=(51,0,0,0)),tick=2,
        )
        self.assertEqual(gain.after.strength,51)
        self.assertEqual(gain.after.dendrite,DendriteState(0,128,128))
        lose=update_c1_synapse(
            gain.after,CONCEPT_GENE,
            C1SynapticInput(200,owner_state=100,owner_output=100,
                           chemicals=(0,1,0,0)),tick=3,
        )
        self.assertEqual(lose.after.strength,50)
        self.assertFalse(lose.owner_neuron_cleared)

    def test_negative_chemical_only_acts_on_inhibitory_class(self):
        start=C1SynapseState(DendriteState(),4)
        inputs=C1SynapticInput(200,owner_state=80,owner_output=80,
                              chemicals=(255,0,0,0))
        inhibitory=update_c1_synapse(
            start,DECISION_INHIBITORY_GENE,inputs,tick=1
        )
        self.assertEqual(inhibitory.after.dendrite.stw,0)
        self.assertEqual(inhibitory.after.dendrite.susceptibility,4)
        punishing=update_c1_synapse(
            start,DECISION_INHIBITORY_GENE,
            C1SynapticInput(200,owner_state=80,owner_output=80,
                           chemicals=(0,255,0,0)),tick=1
        )
        self.assertEqual(punishing.after.dendrite.stw,3)
        self.assertEqual(punishing.reinforcement_rule_output,255)

    def test_dad1_lobe_gene_rates_and_rules_as_bytes(self):
        self.assertEqual(
            (DECISION_EXCITATORY_GENE.source_lobe,
             DECISION_EXCITATORY_GENE.migration_type,
             DECISION_EXCITATORY_GENE.rates.susceptibility_decay,
             DECISION_EXCITATORY_GENE.rates.stw_relax,
             DECISION_EXCITATORY_GENE.rates.ltw_rate,
             DECISION_EXCITATORY_GENE.gain_rate,
             DECISION_EXCITATORY_GENE.lose_rate),
            (8,1,48,80,128,3,5),
        )
        self.assertEqual(
            DECISION_EXCITATORY_GENE.gain_rule,
            bytes((18,22,5,22,19,0,0,0)),
        )
        self.assertEqual(
            DECISION_INHIBITORY_GENE.gain_rule,
            bytes((18,22,6,22,19,0,0,0)),
        )
        self.assertEqual(
            (CONCEPT_GENE.source_lobe,CONCEPT_GENE.migration_type,
             CONCEPT_GENE.gain_rate,CONCEPT_GENE.lose_rate),
            (0,2,2,3),
        )

    def test_no_pulse_cannot_generate_reward_weight(self):
        start=C1SynapseState(DendriteState(),4)
        result=exc(start,1,chem=(0,0,0,0))
        self.assertEqual(result.after.dendrite.stw,0)
        self.assertEqual(result.after.dendrite.susceptibility,4)

    def test_structured_inputs_and_states_are_validated(self):
        with self.assertRaises(ValueError):
            C1SynapticInput(255,0,0,chemicals=(0,0,0))
        with self.assertRaises(ValueError):
            C1SynapticInput(255,0,0,chemicals=(0,256,0,0))
        with self.assertRaises(ValueError):
            C1SynapseState(DendriteState(),256)
        with self.assertRaises(ValueError):
            exc(C1SynapseState(DendriteState(),4),True)

    def test_twenty_seeded_sequences_deterministic_and_bounded(self):
        for seed in range(20):
            def one():
                rng=random.Random(seed)
                state=C1SynapseState(DendriteState(),rng.randint(2,4))
                history=[]
                for tick in range(240):
                    inputs=C1SynapticInput(
                        source_output=rng.randrange(256),
                        owner_state=80,
                        owner_output=rng.randrange(256),
                        chemicals=tuple(rng.randrange(256) for _ in range(4)),
                    )
                    result=update_c1_synapse(
                        state,DECISION_EXCITATORY_GENE,inputs,tick=tick
                    )
                    state=result.after
                    self.assertTrue(0<=state.strength<=255)
                    self.assertTrue(0<=state.dendrite.stw<=255)
                    self.assertTrue(0<=state.dendrite.ltw<=255)
                    history.append(state)
                return history
            self.assertEqual(one(),one())

    def test_owner_cleared_only_on_atrophy_not_gain(self):
        initial=C1SynapseState(DendriteState(4,3,0),2)
        result=exc(initial,3)
        self.assertFalse(result.owner_neuron_cleared)


if __name__=="__main__":
    unittest.main()
