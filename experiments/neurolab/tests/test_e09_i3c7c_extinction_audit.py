"""I3c.7c post-hoc analyst: true original hash only for full 20-seed input."""
from copy import deepcopy
import tempfile
from pathlib import Path
import unittest

from experiments.neurolab.e09_i3c7b_paired_signal import run_all
from experiments.neurolab.e09_i3c7c_extinction_audit import (
    EXPECTED_SHA256, _sha_row, inspect_file, summarize,
)


class ExtinctionAuditContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.small=run_all((1500,))

    def test_subset_reproduces_original_four_arm_structure(self):
        result=summarize(self.small,full=False)
        self.assertEqual(result["n_seeds"],1)
        self.assertEqual(result["n_mapping_coordinates"],4)
        self.assertEqual(result["n_branches"],16)
        self.assertEqual(result["G05_G09_G00H"],"OPEN")
        self.assertEqual(result["initial_signs"],{"True":2,"False":2})
        self.assertEqual(
            result["timeline"]["C"]["10"]["all_eight_strength_zero"],4
        )
        self.assertEqual(
            result["timeline"]["F"]["128"]["mean_strength_positive"],8
        )

    def test_readout_transition_reconciliation(self):
        result=summarize(self.small,full=False)
        for mode in ("N","M","C","F"):
            for t in ("7","9","16","128"):
                record=result["readout_transitions"][mode][t]
                self.assertEqual(record["n"],4)
                self.assertEqual(sum(record[k] for k in (
                    "neutral_wrong_to_wrong","neutral_wrong_to_right",
                    "neutral_right_to_wrong","neutral_right_to_right",
                )),4)
                self.assertEqual(record["accuracy_delta_vs_neutral"],
                     (record["neutral_wrong_to_right"]
                      -record["neutral_right_to_wrong"])/4)

    def test_per_seed_hash_must_match_entire_original_trace(self):
        altered=deepcopy(self.small)
        altered["per_seed_sha256"]["1500"]="0"*64
        with self.assertRaisesRegex(AssertionError,"SHA mismatch"):
            summarize(altered,full=False)

    def test_bad_frame_rejected_after_recomputing_sha(self):
        altered=deepcopy(self.small)
        altered["per_seed"][0]["episodes"][0]["arms"]["C"]["frames"][2][
            "post_strength_positive"]=9
        altered["per_seed_sha256"]["1500"]=_sha_row(altered["per_seed"][0])
        with self.assertRaisesRegex(AssertionError,"invalid neural trace"):
            summarize(altered,full=False)

    def test_reject_truncated_original_under_strict_sha(self):
        self.assertEqual(len(EXPECTED_SHA256),64)
        with tempfile.TemporaryDirectory() as t:
            file=Path(t)/"not-original.json"
            file.write_text("{}",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"SHA-locked"):
                inspect_file(file)

    def test_full_validation_rejects_only_one_seed(self):
        with self.assertRaisesRegex(AssertionError,"full original 20-seed"):
            summarize(self.small,full=True)


if __name__=="__main__":
    unittest.main()
