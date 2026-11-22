"""NR01.03-C deterministic toy tests. No scientific seeds or model libraries."""
import unittest
from experiments.neurolab.nr01_decoder import RewardDecoder

class TestNR01Decoder(unittest.TestCase):
    def test_tie_and_hand_gradient(self):
        d=RewardDecoder(2)
        self.assertEqual(d.choose((1.,0.)),"D0")
        d.apply_reward((1.,0.),"D0",-1)
        self.assertEqual(d.weights,[0.125,0.0,0.125])
        self.assertEqual(d.choose((1.,0.)),"D1")

    def test_positive_reward(self):
        d=RewardDecoder(1)
        d.apply_reward((1.,),"D0",1)
        self.assertEqual(d.weights,[-0.125,-0.125])

    def test_checkpoint(self):
        a=RewardDecoder(2)
        for x,r in [((1.,0.),-1),((0.,1.),1),((1.,1.),-1)]:
            a.apply_reward(x,a.choose(x),r)
        b=RewardDecoder.restore(a.snapshot())
        self.assertEqual(a.snapshot(),b.snapshot())
        for x,r in [((0.,0.),-1),((1.,0.),1),((0.,1.),-1)]:
            for d in (a,b): d.apply_reward(x,d.choose(x),r)
        self.assertEqual(a.snapshot(),b.snapshot())

    def test_invalid_inputs_preserve_state(self):
        d=RewardDecoder(2)
        before=d.snapshot()
        for x,action,reward in [((1.,),"D0",1),((float("nan"),0.),"D0",1),
                                ((1.,0.),"D1",1),((1.,0.),"D0",0)]:
            with self.assertRaises(ValueError): d.apply_reward(x,action,reward)
            self.assertEqual(d.snapshot(),before)

    def test_invalid_snapshot(self):
        for raw in [b"{}",b'{"schema":"wrong"}',b"not-json"]:
            with self.assertRaises((ValueError,TypeError)):
                RewardDecoder.restore(raw)

if __name__ == "__main__":
    unittest.main()
