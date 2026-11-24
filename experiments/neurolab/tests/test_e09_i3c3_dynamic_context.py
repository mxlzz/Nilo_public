"""I3c.3 preregistered schema, pointer, Type1, scheduler and replay contracts."""
import json
import unittest
from dataclasses import replace

from experiments.neurolab.c1_context_brain import C1ContextBrain
from experiments.neurolab.c1_dendrite_tick import DendriteState
from experiments.neurolab.c1_synapse_integrated import (
    C1SynapseState, DECISION_EXCITATORY_GENE, DECISION_INHIBITORY_GENE,
)
from experiments.neurolab.c1_migration import RandStream
from experiments.neurolab.e09_i3c3_dynamic_context import (
    SCHEMA, SOURCE_POINTERS, SLOT_IDENTITIES,
    DEFAULT_SYNTHETIC_MIGRATION_CONFIG,
    DynamicConnection, DynamicBrainState, DynamicContextBrain,
    attempt_type1, class_signal, synthetic_probe,
)

WIRING=(0x1000,0x2000,0x2000,0x1000)


def disconnected(owner=0,kind="exc",ptr=0x1000):
    return DynamicConnection(
        owner,kind,ptr,C1SynapseState(DendriteState(),0)
    )


class FourContactDynamicBrainTests(unittest.TestCase):
    def test_four_slots_and_explicit_identity_no_extra_neurons(self):
        brain=DynamicContextBrain(501)
        with self.assertRaisesRegex(TypeError,"wiring"):
            brain.initial()
        with self.assertRaises(ValueError):
            brain.initial(wiring=(0x1000,)*3)
        with self.assertRaises(ValueError):
            brain.initial(wiring=(0x1000,0x2000,0xDEAD,0x1000))
        state=brain.initial(wiring=WIRING,random_draws=(1,0,0))
        self.assertEqual(len(state.links),4)
        self.assertEqual(tuple((x.owner,x.kind) for x in state.links),SLOT_IDENTITIES)
        self.assertEqual(tuple(x.source_pointer for x in state.links),WIRING)
        self.assertEqual(state.random_tape.draws,(1,0,0))
        self.assertEqual(len(C1ContextBrain(501).initial().dendrites),8)
        self.assertEqual(DECISION_EXCITATORY_GENE.migration_type,1)
        self.assertEqual(DECISION_INHIBITORY_GENE.migration_type,1)

    def test_pointer_changes_actual_signal_no_evaluator_label(self):
        brain=DynamicContextBrain(501,migration_enabled=False)
        state=brain.initial(wiring=WIRING)
        strong=C1SynapseState(DendriteState(0,128,0),2)
        links=list(state.links)
        links[0]=replace(links[0],synapse=strong,source_pointer=0x1000)
        first=replace(state,links=tuple(links),concept_outputs=(255,0))
        links[0]=replace(links[0],source_pointer=0x2000)
        second=replace(first,links=tuple(links))
        self.assertGreater(class_signal(first.concept_outputs,first.links[0]),0)
        self.assertEqual(class_signal(second.concept_outputs,second.links[0]),0)
        trace_a=brain.step(first,0,(0,0,0,0),learn=False)
        trace_b=brain.step(second,0,(0,0,0,0),learn=False)
        self.assertGreater(trace_a.class_signals[0],trace_b.class_signals[0])
        self.assertEqual(trace_a.class_signals[1:],trace_b.class_signals[1:])
        self.assertEqual(trace_a.after.links,first.links)
        self.assertEqual(trace_b.after.links,second.links)

    def test_existing_type1_accepted_with_exact_draw_consumption(self):
        con=disconnected()
        updated,rng,wit=attempt_type1(
            con,recipient_output=255,random_tape=RandStream((1,0,0)))
        self.assertTrue(wit.migrated)
        self.assertEqual(wit.reason,"accepted")
        self.assertEqual(updated.source_pointer,0x2000)
        self.assertEqual(updated.synapse.strength,2)
        self.assertEqual(updated.synapse.dendrite,DendriteState())
        self.assertEqual(rng.cursor,3)
        self.assertEqual((wit.cursor_before,wit.cursor_after),(0,3))
        self.assertEqual(con.source_pointer,0x1000)

    def test_original_type1_duplicate_and_inactive_controls(self):
        con=disconnected()
        identical,rng,wit=attempt_type1(
            con,recipient_output=255,random_tape=RandStream((0,)))
        self.assertEqual(identical,con)
        self.assertEqual(wit.reason,"duplicate_source")
        self.assertFalse(wit.migrated)
        self.assertEqual(rng.cursor,1)
        zero,rng2,wit2=attempt_type1(
            con,recipient_output=0,random_tape=RandStream(()))
        self.assertEqual(zero,con)
        self.assertEqual(wit2.reason,"inactive_recipient")
        self.assertEqual(rng2.cursor,0)
        healthy=replace(con,synapse=C1SynapseState(DendriteState(),2))
        untouched,rng3,wit3=attempt_type1(
            healthy,recipient_output=255,random_tape=RandStream(()))
        self.assertEqual(wit3.reason,"no_disconnected_dendrite")
        self.assertEqual(untouched,healthy)
        self.assertEqual(rng3.cursor,0)
        with self.assertRaisesRegex(RuntimeError,"se agot"):
            attempt_type1(con,recipient_output=255,random_tape=RandStream(()))

    def test_post_wta_active_owner_type1_is_reached(self):
        brain=DynamicContextBrain(502)
        state=brain.initial(
            wiring=(0x1000,0x2000,0x2000,0x1000),
            random_draws=(1,0,0),
        )
        links=list(state.links)
        links[0]=disconnected()
        state=replace(
            state,links=tuple(links),
            neuron_states=(255,0),concept_outputs=(255,0),
        )
        tick=brain.step(state,0,(0,0,0,0))
        self.assertGreater(tick.winner_outputs[0],0)
        self.assertEqual(tick.action,"D0")
        self.assertEqual(tick.after.links[0].source_pointer,0x2000)
        self.assertEqual(tick.after.links[0].synapse.strength,2)
        self.assertEqual(tick.after.random_tape.cursor,3)
        self.assertEqual(tick.migration[0].reason,"accepted")
        self.assertEqual(len(tick.after.links),4)
        # No migration of healthy slots.
        self.assertTrue(all(
            e.reason in ("no_disconnected_dendrite","inactive_recipient")
            for e in tick.migration[1:]
        ))

    def test_no_migration_when_reader_frozen_and_disabled(self):
        enabled=DynamicContextBrain(503)
        disabled=DynamicContextBrain(503,migration_enabled=False)
        state=enabled.initial(wiring=WIRING,random_draws=(1,0,0))
        links=list(state.links)
        links[0]=disconnected()
        state=replace(state,links=tuple(links),neuron_states=(255,0))
        read=enabled.step(state,0,(0,0,0,0),learn=False)
        self.assertEqual(read.after.links,state.links)
        self.assertEqual(read.after.random_tape,state.random_tape)
        self.assertEqual(read.migration,())
        no_migrate=disabled.step(state,0,(0,0,0,0))
        self.assertEqual(no_migrate.after.links[0].source_pointer,0x1000)
        self.assertEqual(no_migrate.after.random_tape,state.random_tape)
        self.assertEqual(no_migrate.migration,())

    def test_checkpoint_exact_roundtrip_and_continuation(self):
        brain=DynamicContextBrain(504)
        original=brain.initial(
            wiring=WIRING,random_draws=tuple((1,0,0)*90),
        )
        seq=(0,0,1,1,0,1,0,0,1,0,1,0,1,1,0,0,1,1,0,1)
        for context in seq[:12]:
            original=brain.step(original,context,(5,0,0,0)).after
        stored=brain.checkpoint(original)
        restored=brain.restore(stored)
        self.assertEqual(restored,original)
        self.assertEqual(stored,brain.checkpoint(restored))
        for context in seq[12:]:
            tr_a=brain.step(original,context,(5,0,0,0))
            tr_b=brain.step(restored,context,(5,0,0,0))
            self.assertEqual(tr_a,tr_b)
            original,restored=tr_a.after,tr_b.after
        self.assertEqual(brain.checkpoint(original),brain.checkpoint(restored))

    def test_corrupted_checkpoint_rejected(self):
        brain=DynamicContextBrain(505)
        state=brain.initial(wiring=WIRING,random_draws=(1,0,0))
        blob=json.loads(brain.checkpoint(state))
        altered=dict(blob)
        altered["unknown"]=True
        with self.assertRaises(ValueError):
            brain.restore(json.dumps(altered))
        altered=json.loads(brain.checkpoint(state))
        altered["protocol"]=SCHEMA+"-bad"
        with self.assertRaises(ValueError):
            brain.restore(json.dumps(altered))
        altered=json.loads(brain.checkpoint(state))
        altered["state"]["links"][0]["source_pointer"]=0xBAD
        with self.assertRaises(ValueError):
            brain.restore(json.dumps(altered))
        altered=json.loads(brain.checkpoint(state))
        altered["state"]["links"][0]["kind"]="inh"
        with self.assertRaises(ValueError):
            brain.restore(json.dumps(altered))
        altered=json.loads(brain.checkpoint(state))
        altered["state"]["random_tape"]["cursor"]=4
        with self.assertRaises(ValueError):
            brain.restore(json.dumps(altered))
        another=DynamicContextBrain(506)
        with self.assertRaises(ValueError):
            another.restore(brain.checkpoint(state))

    def test_synthetic_probe_audits_oracles_without_learning_claim(self):
        info=synthetic_probe()
        self.assertEqual(info["n_units"],6)
        self.assertEqual(info["n_decision_connections"],4)
        self.assertTrue(info["checkpoint_roundtrip_identical"])
        self.assertTrue(info["checkpoint_resume_identical"])
        self.assertTrue(info["type1_accepted"]["migrated"])
        self.assertFalse(info["type1_duplicate_rejected"]["migrated"])
        self.assertEqual(info["gate_learning"],"NOT EVALUATED; G05/G09 OPEN")
        self.assertEqual(info,synthetic_probe())


if __name__=="__main__":
    unittest.main()
