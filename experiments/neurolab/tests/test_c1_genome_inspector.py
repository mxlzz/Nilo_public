"""Tests autocontenidos del lector C1: fixtures sintéticos, SIN genomas del juego."""
import unittest
from experiments.neurolab.c1_genome_inspector import (
    decode_lobe_record, decode_rule, inspect, compare, markers
)


def mock_lobe(x=4, y=13, width=7, height=16, *,
              threshold=10, state_rule=None, dend0=None, dend1=None):
    body = bytearray(112)
    body[:4] = bytes((x, y, width, height))
    body[5] = threshold
    if state_rule:
        body[9:9 + len(state_rule)] = bytes(state_rule)
    if dend0:
        body[18:65] = bytes(dend0)
    if dend1:
        body[65:112] = bytes(dend1)
    return b"gene" + bytes((0, 0, 1, 0, 0, 0)) + bytes(body)


class C1GenomeInspectorTests(unittest.TestCase):
    def test_rule_operators_and_end(self):
        self.assertEqual(decode_rule(bytes((9,23,12,24,13,0,0,0))),
                         ["STATE","PLUS","TYPE0","MINUS","TYPE1"])
        self.assertEqual(decode_rule(bytes((14,0,0,0,0,0,0,0))), ["ANDTYPE0"])
        with self.assertRaises(ValueError):
            decode_rule(bytes((9, 23)))

    def test_122_byte_lobe_header_and_coordinates(self):
        record = mock_lobe()
        self.assertEqual(len(record), 122)
        data = decode_lobe_record(record, 0, 71)
        self.assertEqual((data["x"],data["y"],data["width"],data["height"]),(4,13,7,16))
        self.assertEqual(data["neurons_nominal"],112)
        self.assertEqual(data["threshold"],10)
        self.assertEqual(data["offset"],71)

    def test_dendrite_layout_decision_fixture(self):
        dend = bytearray(47)
        dend[:14] = bytes((8,128,128,0,8,0,0,2,4,1,48,80,128,3))
        dend[31:39] = bytes((10,22,16,0,0,0,0,0))
        dend[39:47] = bytes((5,0,0,0,0,0,0,0))
        data = decode_lobe_record(
            mock_lobe(x=53,y=15,width=1,height=16,threshold=0,
                      state_rule=(9,23,12,24,13),dend0=dend),6,0
        )
        self.assertEqual(data["neurons_nominal"],16)
        self.assertEqual(data["state_rule"],["STATE","PLUS","TYPE0","MINUS","TYPE1"])
        self.assertEqual(data["dendrites"][0]["source_lobe"],8)
        self.assertEqual(data["dendrites"][0]["min_count"],128)
        self.assertEqual(data["dendrites"][0]["max_count"],128)
        self.assertEqual(data["dendrites"][0]["migration_type"],1)
        self.assertEqual(data["dendrites"][0]["susceptibility_rule"],
                         ["OUTPUT","TRUE","INPUT"])
        self.assertEqual(data["dendrites"][0]["reinforcement_rule"],["CHEM0"])

    def test_9_lobe_nominal_total_from_independent_grid_table(self):
        # Es un fixture creado a mano con datos publicados: no prueba el binario del usuario.
        dims=((4,13,7,16),(34,30,8,2),(15,24,8,5),(37,24,8,2),
              (21,3,20,2),(32,34,8,4),(53,15,1,16),(44,30,5,8),(12,6,40,16))
        genome=b"".join(mock_lobe(x,y,w,h) for x,y,w,h in dims)+b"gend"
        o=inspect(genome)
        self.assertEqual(o["lobe_count"],9)
        self.assertEqual(o["neurons_nominal"],952)
        self.assertEqual(o["marker_gene_count"],9)

    def test_diff_reports_only_changed_byte_positions(self):
        a=mock_lobe()
        b=bytearray(a)
        b[15]=99
        res=compare(a,bytes(b))
        self.assertTrue(res["gene_marker_positions_identical"])
        self.assertEqual(res["different_offsets_shared_length"],[15])
        self.assertFalse(res["lobes_bytes_identical"])

    def test_reject_invalid_record_and_grid(self):
        with self.assertRaises(ValueError):
            decode_lobe_record(b"junk",0,0)
        with self.assertRaises(ValueError):
            decode_lobe_record(mock_lobe(60,13,7,16),0,0)
        with self.assertRaises(ValueError):
            decode_lobe_record(mock_lobe(4,13,0,16),0,0)

    def test_markers_only_recognize_literal_gene(self):
        self.assertEqual(markers(b"xxgeneabcgene___gend"),[2,9])


if __name__=="__main__":
    unittest.main()
