"""E09.02f.5b — pre-registered type1/type2 C1 migration tests.

Only machine-derived semantics are claimed. RandStream is an explicit
tape of CRT rand() return values; the global game PRNG is not replayed.
"""
import random
import unittest

from experiments.neurolab.c1_migration import (
    Dendrite, MigrationConfig, MigrationState, RandStream, SourceNeuron,
    concept_checksum, concept_migrate, decision_migrate,
)

A=SourceNeuron(0x10010,1)
B=SourceNeuron(0x10020,1)
C=SourceNeuron(0x10030,2)
D=SourceNeuron(0x10040,0)
CFG=MigrationConfig(5,7,2,4)


class C1MigrationTests(unittest.TestCase):
    def test_decision_duplicate_aborts_without_retry(self):
        state=MigrationState((
            Dendrite(A.pointer,30,20,4),
            Dendrite(B.pointer,0,0,0),
        ),loose_counter=1)
        result=decision_migrate(state,(A,C),CFG,RandStream((0,1,2)),
                                recipient_output=50)
        self.assertFalse(result.migrated)
        self.assertEqual(result.reason,"duplicate_source")
        self.assertEqual(result.state,state)
        self.assertEqual(result.random.cursor,1)

    def test_decision_first_loose_replaced_with_two_random_draws(self):
        state=MigrationState((
            Dendrite(A.pointer,30,20,4),
            Dendrite(B.pointer,0,0,0),
        ),loose_counter=1)
        result=decision_migrate(state,(A,C),CFG,RandStream((1,1,2)),
                                recipient_output=50)
        self.assertTrue(result.migrated)
        self.assertEqual(result.state.dendrites[0],state.dendrites[0])
        self.assertEqual(result.state.dendrites[1],
                         Dendrite(C.pointer,6,6,4,0))
        self.assertEqual(result.state.loose_counter,0)
        self.assertEqual(result.random.cursor,3)

    def test_decision_checks_first_loose_only(self):
        state=MigrationState((
            Dendrite(A.pointer,0,0,0),
            Dendrite(B.pointer,0,0,0),
        ),loose_counter=2)
        result=decision_migrate(state,(C,D),CFG,RandStream((0,0,0)),
                                recipient_output=10)
        self.assertTrue(result.migrated)
        self.assertEqual(result.state.dendrites[0].source_pointer,C.pointer)
        self.assertEqual(result.state.dendrites[1].source_pointer,B.pointer)
        self.assertEqual(result.state.loose_counter,1)

    def test_decision_inactive_or_empty_or_no_loose_avoids_rand(self):
        state=MigrationState((Dendrite(A.pointer,0,0,0),))
        rng=RandStream(())
        self.assertEqual(decision_migrate(state,(B,),CFG,rng,
                                          recipient_output=0).reason,
                         "inactive_recipient")
        self.assertEqual(decision_migrate(state,(),CFG,rng,
                                          recipient_output=100).reason,
                         "no_active_source")
        healthy=MigrationState((Dendrite(A.pointer,30,20,2),))
        self.assertEqual(decision_migrate(healthy,(B,),CFG,rng,
                                          recipient_output=100).reason,
                         "no_disconnected_dendrite")

    def test_concept_exclusivity_rejects_first_window(self):
        state=MigrationState((
            Dendrite(A.pointer,0,0,0),
            Dendrite(B.pointer,0,0,0),
        ),loose_counter=1)
        tape=RandStream((0,1,2,3,1,2,0,0))
        result=concept_migrate(state,(A,B,C,D),CFG,tape)
        self.assertTrue(result.migrated)
        self.assertEqual(result.attempts,("exclusive:0","accepted:1"))
        self.assertEqual(tuple(x.source_pointer for x in result.state.dendrites),
                         (B.pointer,C.pointer))
        self.assertEqual((result.state.dendrites[0].stw,result.state.dendrites[0].strength),
                         (6,4))
        self.assertEqual((result.state.dendrites[1].ltw,result.state.dendrites[1].strength),
                         (5,2))
        self.assertEqual(result.random.cursor,8)
        self.assertEqual(len(result.state.dendrites),2)

    def test_concept_shuffle_is_exposed_to_caller(self):
        state=MigrationState((Dendrite(A.pointer,0,0,0),))
        # Swap sources 0 and 1; remaining swaps are identities.
        result=concept_migrate(state,(A,B,C,D),CFG,
                               RandStream((1,1,2,3,0,0)))
        self.assertEqual(result.sources_order,(B,A,C,D))
        self.assertEqual(result.state.dendrites[0].source_pointer,B.pointer)
        self.assertEqual(result.random.cursor,6)

    def test_concept_checksum_rejects_before_next_window(self):
        pool=(SourceNeuron(A.pointer),SourceNeuron(B.pointer),
              SourceNeuron(C.pointer),SourceNeuron(D.pointer))
        state=MigrationState((Dendrite(A.pointer,0,0,0),
                              Dendrite(B.pointer,0,0,0)))
        tape=RandStream((0,1,2,3, 0,0,0,0, 1,2,1,2))
        result=concept_migrate(state,pool,CFG,tape,
                               other_active_wirings=((A.pointer,B.pointer),))
        self.assertTrue(result.migrated)
        self.assertEqual(result.attempts,("checksum:0","accepted:1"))
        self.assertEqual(tuple(d.source_pointer for d in result.state.dendrites),
                         (B.pointer,C.pointer))
        # Rejected candidate also consumes four random initializers.
        self.assertEqual(result.random.cursor,12)

    def test_concept_checksum_uses_raw_addresses_and_can_collide(self):
        first=(0x10000,0x20000)
        second=(0x14000,0x1C000)
        self.assertNotEqual(set(first),set(second))
        self.assertEqual(concept_checksum(first),concept_checksum(second))
        self.assertEqual(concept_checksum(first),concept_checksum(tuple(reversed(first))))

    def test_concept_all_candidates_rejected_restores_old_sources(self):
        pool=(SourceNeuron(A.pointer),SourceNeuron(B.pointer),
              SourceNeuron(C.pointer),SourceNeuron(D.pointer))
        state=MigrationState((
            Dendrite(0x20010,32,25,0,7),
            Dendrite(0x20020,80,70,3,9),
        ),loose_counter=2)
        tape=RandStream((0,1,2,3)+(0,0,0,0)*3)
        others=((A.pointer,B.pointer),(B.pointer,C.pointer),
                (C.pointer,D.pointer))
        result=concept_migrate(state,pool,CFG,tape,
                               other_active_wirings=others)
        self.assertFalse(result.migrated)
        self.assertEqual(result.reason,"no_valid_wiring")
        self.assertEqual(result.attempts,("checksum:0","checksum:1","checksum:2"))
        self.assertEqual(tuple(x.source_pointer for x in result.state.dendrites),
                         (0x20010,0x20020))
        self.assertTrue(all(x.strength==x.stw==x.ltw==0
                            for x in result.state.dendrites))
        self.assertEqual(tuple(x.susceptibility for x in result.state.dendrites),(7,9))
        self.assertEqual(result.state.loose_counter,2)
        self.assertEqual(result.random.cursor,16)

    def test_concept_exclusivity_all_conflict_restores_without_weight_draws(self):
        pool=(SourceNeuron(A.pointer,7),SourceNeuron(B.pointer,7))
        state=MigrationState((Dendrite(A.pointer,0,0,0),
                              Dendrite(B.pointer,20,20,3)))
        result=concept_migrate(state,pool,CFG,RandStream((0,1)))
        self.assertEqual(result.attempts,("exclusive:0",))
        self.assertFalse(result.migrated)
        self.assertEqual(result.random.cursor,2)
        self.assertTrue(all(x.strength==0 for x in result.state.dendrites))

    def test_concept_insufficient_sources_or_unselected_avoids_rand(self):
        state=MigrationState((Dendrite(A.pointer,0,0,0),
                              Dendrite(B.pointer,0,0,0)))
        no_sources=concept_migrate(state,(C,),CFG,RandStream(()))
        self.assertEqual(no_sources.reason,"insufficient_sources")
        skipped=concept_migrate(state,(A,B,C),CFG,RandStream(()),
                                selected_recipient=False)
        self.assertEqual(skipped.reason,"not_selected")
        self.assertEqual(skipped.state,state)

    def test_concept_no_loose_does_not_touch_wiring(self):
        state=MigrationState((Dendrite(A.pointer,10,10,4),))
        result=concept_migrate(state,(A,B),CFG,RandStream(()))
        self.assertEqual(result.reason,"no_disconnected_dendrite")
        self.assertEqual(result.state,state)

    def test_random_tape_rejects_exhaustion_and_invalid_values(self):
        for bad in (-1,32768,True,1.2):
            with self.assertRaises(ValueError):
                RandStream((bad,))
        with self.assertRaises(RuntimeError):
            RandStream(()).pick(1)
        with self.assertRaises(ValueError):
            RandStream((0,)).pick(0)
        with self.assertRaises(ValueError):
            SourceNeuron(0)
        with self.assertRaises(ValueError):
            MigrationConfig(9,8,2,4)

    def test_randomized_bounded_invariants_twenty_seeds(self):
        pool=tuple(SourceNeuron(0x10000+16*i,i % 4) for i in range(8))
        for seed in range(20):
            def run():
                rng=random.Random(seed)
                tape=RandStream(tuple(rng.randrange(32768) for _ in range(2000)))
                state=MigrationState((Dendrite(pool[0].pointer,0,0,0),
                                      Dendrite(pool[1].pointer,0,0,0)),loose_counter=2)
                snapshots=[]
                for _ in range(20):
                    result=concept_migrate(state,pool,CFG,tape,
                                           other_active_wirings=((pool[2].pointer,
                                                                  pool[3].pointer),))
                    state=result.state
                    tape=result.random
                    self.assertEqual(len(state.dendrites),2)
                    self.assertTrue(all(0<=d.strength<=255 and 0<=d.stw<=255
                                        and 0<=d.ltw<=255
                                        for d in state.dendrites))
                    snapshots.append((state,result.sources_order,result.attempts))
                    # A new atrophy event is inserted into the fixture only,
                    # to exercise multiple independent migrations.
                    state=MigrationState(tuple(
                        Dendrite(d.source_pointer,d.stw,d.ltw,0,d.susceptibility)
                        if i==0 else d for i,d in enumerate(state.dendrites)
                    ),state.loose_counter)
                return snapshots
            self.assertEqual(run(),run())


if __name__=="__main__":
    unittest.main()
