"""C1 reaction gene inspector — synthetic oracles for original 9-byte chemistry."""
import unittest

from experiments.neurolab.c1_reaction_inspector import parse_reactions,summary


def gene_reaction(payload:tuple[int,...],sequence:int=0)->bytes:
    assert len(payload)==9
    return b"gene"+bytes((1,2,sequence,0,0,0))+bytes(payload)


class ChemistryGeneTests(unittest.TestCase):
    def setUp(self):
        self.pain_increase=(1,17,1,0,1,1,1,50,8)
        self.pain_decrease=(1,33,1,1,1,49,1,0,8)
        self.reward_echo=(1,49,1,0,1,51,1,54,16)
        self.punishment_echo=(1,50,1,0,1,51,1,55,16)
        self.genome=(b"".join(gene_reaction(payload,i) for i,payload in enumerate((
            self.pain_increase,self.pain_decrease,
            self.reward_echo,self.punishment_echo
        )))+b"gend")

    def test_drive_increase_punishment(self):
        reactions=parse_reactions(self.genome)
        self.assertEqual(reactions[0].source_ids,(17,))
        self.assertEqual(reactions[0].target_ids,(1,50))
        self.assertEqual(reactions[0].rate,8)

    def test_drive_decrease_reward(self):
        r=parse_reactions(self.genome)[1]
        self.assertEqual(r.source_ids,(33,1))
        self.assertEqual(r.target_ids,(49,))
        self.assertEqual(r.rate,8)

    def test_reward_punishment_feed_same_reinforcement(self):
        a,b=parse_reactions(self.genome)[2:]
        self.assertEqual(a.source_ids,(49,))
        self.assertEqual(a.target_ids,(51,54))
        self.assertEqual(b.source_ids,(50,))
        self.assertEqual(b.target_ids,(51,55))
        self.assertEqual(a.rate,b.rate)
        self.assertEqual(a.rate,16)

    def test_exact_gene_count_and_offset_on_fixture(self):
        out=summary(self.genome)
        self.assertEqual(out["reaction_gene_count"],4)
        self.assertEqual(out["learning_reaction_count"],4)
        r=parse_reactions(self.genome)
        self.assertEqual([x.offset for x in r],[0,19,38,57])
        self.assertEqual([x.gene_index for x in r],[0,1,2,3])
        self.assertEqual(out["source_bytes"],80)

    def test_one_unrelated_record_not_parsed(self):
        distractor=b"gene"+bytes((0,0,0,0,0,0))+bytes(112)
        out=summary(distractor+self.genome)
        self.assertEqual(out["reaction_gene_count"],4)
        self.assertEqual([x.gene_index for x in parse_reactions(distractor+self.genome)],
                         [1,2,3,4])

    def test_reject_broken_terminal_reaction(self):
        raw=gene_reaction(self.reward_echo)[:14]+b"gend"
        with self.assertRaises(ValueError):
            parse_reactions(raw)

    def test_preserve_inputs_without_simulation(self):
        input_copy=self.genome[:]
        a=parse_reactions(self.genome)
        b=parse_reactions(self.genome)
        self.assertEqual(a,b)
        self.assertEqual(self.genome,input_copy)
        self.assertFalse(hasattr(a[0],"chemical_concentration"))
        self.assertFalse(hasattr(a[0],"reaction_velocity"))


if __name__=="__main__":
    unittest.main()
