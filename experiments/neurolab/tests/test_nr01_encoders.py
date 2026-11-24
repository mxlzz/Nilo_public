"""NR01.03-C2 software-only tests, NEVER import/generate scientific cohorts."""
import hashlib
import importlib.util
import unittest

from experiments.neurolab.nr01_encoders import _one_hot, FuzzyART16, KMeansCategories


def obs(v: float) -> tuple[float, ...]:
    return (float(v),) * 16


LIBS_AVAILABLE = (
    importlib.util.find_spec("artlib") is not None
    and importlib.util.find_spec("sklearn") is not None
)


class TestCategoricalContractWithoutLibraries(unittest.TestCase):
    def test_one_hot_index_no_hidden_fallback(self):
        self.assertEqual(_one_hot(0, 4), (1.0, 0.0, 0.0, 0.0))
        self.assertEqual(sum(_one_hot(15, 16)), 1.0)
        for bad in (-1, 16, 17):
            with self.assertRaises(ValueError):
                _one_hot(bad, 16)

    def test_fixed_parameter_grid(self):
        for cls, wrong in ((FuzzyART16, .70), (KMeansCategories, 2)):
            with self.assertRaises(ValueError):
                cls(wrong)


@unittest.skipUnless(LIBS_AVAILABLE, "pinned ARTlib/scikit-learn tested in separate CI")
class TestCategoricalLibrariesToy(unittest.TestCase):
    def test_art_unlabelled_and_frozen_predict(self):
        model = FuzzyART16(.80)
        for v in (.20, .22, .78, .80) * 8:
            model.observe_unlabelled(obs(v))
        self.assertEqual(model.observed, 32)
        self.assertFalse(model.over_budget)
        self.assertGreaterEqual(model.categories, 2)
        self.assertLessEqual(model.categories, 16)
        model.freeze_encoder()
        digest = hashlib.sha256(model.snapshot()).hexdigest()
        for v in (.21, .79, .22):
            feature = model.encode_read_only(obs(v))
            self.assertEqual(len(feature), 16)
            self.assertEqual(sum(feature), 1.0)
        self.assertEqual(digest, hashlib.sha256(model.snapshot()).hexdigest())
        restored = FuzzyART16.restore(model.snapshot())
        self.assertEqual(model.snapshot(), restored.snapshot())
        self.assertEqual(model.encode_read_only(obs(.21)), restored.encode_read_only(obs(.21)))
        restored.over_budget = True
        with self.assertRaises(RuntimeError):
            restored.encode_read_only(obs(.21))
        with self.assertRaises(RuntimeError):
            model.observe_unlabelled(obs(.3))
        with self.assertRaises((ValueError, TypeError)):
            model.encode_read_only(object())

    def test_kmeans_32_block_plus_tail(self):
        model = KMeansCategories(4)
        for i in range(31):
            model.observe_unlabelled(obs((i % 4 + 1) / 5))
        self.assertEqual(model.categories, 0)
        model.observe_unlabelled(obs(.8))
        self.assertEqual(model.categories, 4)
        for i in range(16):
            model.observe_unlabelled(obs((i % 4 + 1) / 5))
        self.assertEqual(len(model.buffer), 16)
        model.freeze_encoder()
        self.assertEqual(len(model.buffer), 0)
        self.assertEqual(model.observed, 48)
        digest = hashlib.sha256(model.snapshot()).hexdigest()
        for v in (.21, .41, .61, .79):
            feature = model.encode_read_only(obs(v))
            self.assertEqual(len(feature), 4)
            self.assertEqual(sum(feature), 1.0)
        self.assertEqual(digest, hashlib.sha256(model.snapshot()).hexdigest())
        restored = KMeansCategories.restore(model.snapshot())
        self.assertEqual(model.snapshot(), restored.snapshot())
        self.assertEqual(model.encode_read_only(obs(.21)), restored.encode_read_only(obs(.21)))
        with self.assertRaises(RuntimeError):
            model.observe_unlabelled(obs(.3))

    def test_non_tuples_rejected_as_hidden_record(self):
        for model in (FuzzyART16(.60), KMeansCategories(4)):
            with self.assertRaises(ValueError):
                model.observe_unlabelled({"observation": obs(.5),
                                         "latent": (0, 1)})
            self.assertEqual(model.observed, 0)


if __name__ == "__main__":
    unittest.main()
